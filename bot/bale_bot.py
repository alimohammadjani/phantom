import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from core.scraper import GameScraper

# پیکربندی لاگ‌ها
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# ⭐️ توکن اختصاصی ربات در پیام‌رسان بله
BALE_BOT_TOKEN = "YOUR_TOKEN"

# ⭐️ آدرس پایه سرور API بله
BALE_BASE_URL = "https://tapi.bale.ai/bot"

# اسکرپر مشترک
scraper = GameScraper()

# حافظه وضعیت برای هر کاربر
user_sessions = {}

def get_user_session(user_id):
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "query": "",
            "category": "ALL",
            "current_page": 1,
            "last_valid_page": 1,
            "last_results": [],
            "current_post_links": []
        }
    return user_sessions[user_id]

def build_category_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🔵 پلی‌استیشن (PS)", callback_data="cat_CONSOLE_PS"),
            InlineKeyboardButton("🟢 ایکس‌باکس (XBOX)", callback_data="cat_CONSOLE_XBOX")
        ],
        [
            InlineKeyboardButton("🔴 نینتندو (Switch)", callback_data="cat_CONSOLE_NINTENDO"),
            InlineKeyboardButton("💻 کامپیوتر (PC)", callback_data="cat_PC_ALL")
        ],
        [
            InlineKeyboardButton("🎮 فقط بازی PC", callback_data="cat_PC_GAME"),
            InlineKeyboardButton("🖥️ نرم‌افزار PC", callback_data="cat_PC_SOFTWARE")
        ],
        [
            InlineKeyboardButton("🌐 همه دسته‌ها (ALL)", callback_data="cat_ALL")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def build_versions_keyboard(has_next, current_page, results):
    """ساخت منوی انتخاب نسخه/بازی‌ها"""
    keyboard = []
    
    # دکمه‌های انتخاب هر نسخه (فقط عنوان نسخه و کلیک برای رفتن به پارت‌ها)
    for idx, item in enumerate(results, 1):
        title = item["title"]
        quality = item.get("quality", "Full")
        short_title = title[:34] + "..." if len(title) > 34 else title
        btn_text = f"📦 نسخه {idx}: {short_title}"
        keyboard.append([
            InlineKeyboardButton(btn_text, callback_data=f"selver_{idx-1}")
        ])

    # نوار صفحه‌بندی
    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton("◀ صفحه قبل", callback_data="nav_prev"))
    
    nav_row.append(InlineKeyboardButton(f"📄 صفحه {current_page}", callback_data="nav_info"))

    if has_next and len(results) >= 10:
        nav_row.append(InlineKeyboardButton("صفحه بعد ▶", callback_data="nav_next"))

    keyboard.append(nav_row)
    keyboard.append([
        InlineKeyboardButton("🎯 تغییر دسته‌بندی", callback_data="menu_categories")
    ])

    return InlineKeyboardMarkup(keyboard)

def build_parts_keyboard(links, post_idx):
    """ساخت لیست دکمه‌های پارت‌ها همراه با دکمه باز کردن و دکمه کپی"""
    keyboard = []

    for idx, l in enumerate(links, 1):
        raw_text = l.get("text", f"پارت {idx}")
        # خلاصه‌سازی نام پارت مثل: پارت ۱ یا پارت ۲
        short_name = f"پارت {idx}"
        if "پارت" in raw_text:
            short_name = raw_text.split(" - ")[0] if " - " in raw_text else raw_text

        # ردیف ۳تایی: [عنوان پارت] | [🌐 باز کردن] | [📋 کپی لینک]
        row = [
            InlineKeyboardButton(f"📦 {short_name}", callback_data="none"),
            InlineKeyboardButton("🌐 باز کردن", url=l["url"]),
            InlineKeyboardButton("📋 کپی", callback_data=f"copylink_{idx-1}")
        ]
        keyboard.append(row)

    # دکمه کپی همه لینک‌ها یکجا + بازگشت به لیست نسخه‌ها
    keyboard.append([
        InlineKeyboardButton("📋 کپی همه لینک‌ها یکجا", callback_data="copy_all_parts")
    ])
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به لیست نسخه‌ها", callback_data="back_to_versions")
    ])

    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_user_session(user_id)
    welcome_text = (
        "🎮 به ربات Game Searcher Pro خوش آمدید!"
        "🔍 کافیست نام بازی یا نرم‌افزار مورد نظر خود را بنویسید و بفرستید."
        "ما لیست نسخه‌ها را پیدا می‌کنیم و می‌توانید پارت‌ها را مستقیم باز یا کپی کنید."
        "🔻 دسته‌بندی پیش‌فرض:"
    )
    await update.message.reply_text(
        welcome_text,
        reply_markup=build_category_keyboard()
    )

async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.message.text.strip()

    if not query:
        return

    session = get_user_session(user_id)
    session["query"] = query
    session["current_page"] = 1
    session["last_valid_page"] = 1

    status_msg = await update.message.reply_text(f"🔎 در حال جستجوی «{query}» در دانلودها...")
    await perform_search_and_render(update, context, status_msg)

async def perform_search_and_render(update: Update, context: ContextTypes.DEFAULT_TYPE, message_to_edit=None):
    user_id = update.effective_user.id
    session = get_user_session(user_id)

    query = session["query"]
    category = session["category"]
    page = session["current_page"]

    data = await asyncio.to_thread(
        scraper.search_downloadha_paginated,
        query=query,
        category=category,
        app_page_num=page,
        target_count=10
    )

    results = data.get("results", [])
    status = data.get("status", "OK")
    has_next = data.get("has_next", False)

    if status in ["NOT_FOUND", "EMPTY"] or not results:
        if page != session["last_valid_page"] and session["last_valid_page"] >= 1:
            session["current_page"] = session["last_valid_page"]
            fallback_text = (
                f"⚠️ در صفحه {page} نتیجه‌ای یافت نشد!"
                f"🔙 بازگشت به آخرین صفحه معتبر (صفحه {session['last_valid_page']})..."
            )
            if message_to_edit:
                await message_to_edit.edit_text(fallback_text)
            elif update.callback_query:
                await update.callback_query.message.reply_text(fallback_text)
            return
        else:
            not_found_text = f"❌ هیچ نتیجه‌ای برای «{query}» در این دسته‌بندی یافت نشد."
            if message_to_edit:
                await message_to_edit.edit_text(not_found_text)
            elif update.callback_query:
                await update.callback_query.edit_message_text(not_found_text)
            return

    session["last_valid_page"] = page
    session["last_results"] = results

    response_lines = [
        f"🎯 نسخه‌های یافت شده برای: {query}",
        f"📂 دسته‌بندی: {category} | 📄 صفحه: {page}",
        "──────────────────────────────",
        "👇 لطفاً نسخه مورد نظر خود را برای مشاهده پارت‌های دانلود انتخاب کنید:"
    ]

    response_text = "\n".join(response_lines)
    keyboard = build_versions_keyboard(has_next, page, results)

    if message_to_edit:
        await message_to_edit.edit_text(response_text, reply_markup=keyboard)
    elif update.callback_query:
        await update.callback_query.edit_message_text(response_text, reply_markup=keyboard)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    session = get_user_session(user_id)
    data = query.data

    if data == "none":
        return

    if data.startswith("cat_"):
        cat_code = data.replace("cat_", "")
        session["category"] = cat_code
        session["current_page"] = 1
        session["last_valid_page"] = 1
        
        await query.edit_message_text(
            f"✅ دسته‌بندی به {cat_code} تغییر یافت.\nدر حال جستجوی مجدد نتایج..."
        )
        if session["query"]:
            await perform_search_and_render(update, context)

    elif data == "menu_categories":
        await query.edit_message_text(
            "🎛 دسته‌بندی مورد نظر خود را انتخاب کنید:",
            reply_markup=build_category_keyboard()
        )

    elif data == "nav_next":
        session["current_page"] += 1
        await query.edit_message_text("⏳ در حال دریافت صفحه بعد...")
        await perform_search_and_render(update, context)

    elif data == "nav_prev":
        if session["current_page"] > 1:
            session["current_page"] -= 1
            await query.edit_message_text("⏳ در حال بازگشت به صفحه قبل...")
            await perform_search_and_render(update, context)

    elif data == "back_to_versions":
        # بازگشت به منوی نسخه‌ها
        results = session.get("last_results", [])
        if results:
            response_text = f"🎯 لیست نسخه‌های یافت شده برای: {session['query']}\nلطفاً نسخه مورد نظر را انتخاب کنید:"
            keyboard = build_versions_keyboard(True, session["current_page"], results)
            await query.edit_message_text(response_text, reply_markup=keyboard)

    elif data.startswith("selver_"):
        # کاربر یکی از نسخه‌ها را انتخاب کرده تا پارت‌های آن نمایش داده شود
        idx = int(data.replace("selver_", ""))
        results = session.get("last_results", [])
        if 0 <= idx < len(results):
            target_item = results[idx]
            post_url = target_item["link"]
            post_title = target_item["title"]

            await query.edit_message_text(f"⏳ در حال استخراج پارت‌های دانلود برای:\n«{post_title}»...")

            dl_data = await asyncio.to_thread(scraper.fetch_post_download_links, post_url)
            links = dl_data.get("links", [])
            password = dl_data.get("password", "www.downloadha.com")
            session["current_post_links"] = links
            session["current_post_password"] = password
            session["current_post_title"] = post_title

            if not links:
                await query.edit_message_text(
                    f"⚠️ لینک دانلودی برای این پست یافت نشد.\n🔗 مشاهده مستقیم در سایت:\n{post_url}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 بازگشت به لیست نسخه‌ها", callback_data="back_to_versions")
                    ]])
                )
            else:
                text_msg = (
                    f"📦 پارت‌های دانلود مستقیم:\n"
                    f"🎮 عنوان: {post_title}\n"
                    f"🔑 رمز فایل‌ها: {password}\n"
                    f"──────────────────────────────\n"
                    f"👇 از دکمه‌های زیر برای باز کردن یا کپی کردن هر پارت استفاده کنید:"
                )
                keyboard = build_parts_keyboard(links, idx)
                await query.edit_message_text(text_msg, reply_markup=keyboard)

    elif data.startswith("copylink_"):
        # کپی لینک یک پارت خاص و ارسال لینک قابل کپی با یک لمس به کاربر
        part_idx = int(data.replace("copylink_", ""))
        links = session.get("current_post_links", [])
        if 0 <= part_idx < len(links):
            target_link = links[part_idx]
            url = target_link["url"]
            text = target_link.get("text", f"پارت {part_idx+1}")
            # ارسال پیام اختصاصی با لینک جهت کپی در بله
            await query.message.reply_text(
                f"📋 لینک {text}:\n{url}\n\n💡 برای کپی، روی لینک بالا لمس طولانی کنید."
            )

    elif data == "copy_all_parts":
        # ارسال همه لینک‌ها یکجا
        links = session.get("current_post_links", [])
        password = session.get("current_post_password", "www.downloadha.com")
        if links:
            all_urls = "\n".join([l['url'] for l in links])
            await query.message.reply_text(
                f"📋 تمامی لینک‌های پارت‌ها یکجا:\n\n{all_urls}\n\n🔑 رمز فایل‌ها: {password}"
            )

def start_bale_bot():
    """تابع اصلی استارت ربات بله"""
    print("🤖 در حال اتصال به سرورهای پیام‌رسان بله...")
    
    app = (
        ApplicationBuilder()
        .token(BALE_BOT_TOKEN)
        .base_url(BALE_BASE_URL)
        .build()
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_query))
    app.add_handler(CallbackQueryHandler(callback_handler))

    print("✅ ربات بله با موفقیت فعال شد و آماده دریافت پیام است!")
    app.run_polling()

if __name__ == "__main__":
    start_bale_bot()
