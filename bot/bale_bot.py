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

# ⭐️ توکن اختصاصی ربات شما در بله
BALE_BOT_TOKEN = "651539429:LyCnzJNqWy8xDJn3kh8eJatAOaWgWLGqRec"

# ⭐️ آدرس سرور API بله
BALE_BASE_URL = "https://tapi.bale.ai/bot"

# اسکرپر مشترک
scraper = GameScraper()

# حافظه وضعیت کاربران
user_sessions = {}

def get_user_session(user_id):
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "query": "",
            "category": "ALL",
            "current_page": 1,
            "last_valid_page": 1,
            "last_results": []
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

def build_results_keyboard(has_next, current_page, results_count, post_urls):
    keyboard = []
    
    # دکمه‌های دریافت لینک برای هر نتیجه
    for idx, (title, url) in enumerate(post_urls, 1):
        short_title = title[:32] + "..." if len(title) > 32 else title
        keyboard.append([
            InlineKeyboardButton(f"📥 دریافت لینک #{idx}: {short_title}", callback_data=f"getlinks_{idx-1}")
        ])

    # نوار صفحه‌بندی
    nav_row = []
    if current_page > 1:
        nav_row.append(InlineKeyboardButton("◀ صفحه قبل", callback_data="nav_prev"))
    
    nav_row.append(InlineKeyboardButton(f"📄 صفحه {current_page}", callback_data="nav_info"))

    if has_next and results_count >= 10:
        nav_row.append(InlineKeyboardButton("صفحه بعد ▶", callback_data="nav_next"))

    keyboard.append(nav_row)
    keyboard.append([
        InlineKeyboardButton("🎯 تغییر دسته‌بندی", callback_data="menu_categories")
    ])

    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_user_session(user_id)
    welcome_text = (
        "🎮 به ربات Game Searcher Pro خوش آمدید!\n\n"
        "🔍 کافیست نام بازی یا نرم‌افزار مورد نظر خود را بنویسید و ارسال کنید.\n"
        "ما آخرین نسخه‌ها (FitGirl, DODI, RUNE, کنسول و ...) را برای شما استخراج می‌کنیم.\n\n"
        "🔻 همچنین از دکمه‌های زیر می‌توانید دسته‌بندی پیش‌فرض را انتخاب نمایید:"
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

    # اجرای اسکرپر در ترد مجزا
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

    # مدیریت صفحات خالی یا ناموجود (بازگشت هوشمند به آخرین صفحه معتبر)
    if status in ["NOT_FOUND", "EMPTY"] or not results:
        if page != session["last_valid_page"] and session["last_valid_page"] >= 1:
            session["current_page"] = session["last_valid_page"]
            fallback_text = (
                f"⚠️ در صفحه {page} نتیجه‌ای یافت نشد!\n"
                f"🔙 بازگشت خودکار به آخرین صفحه معتبر (صفحه {session['last_valid_page']})..."
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
        f"🎮 نتایج جستجو برای: {query}",
        f"📂 دسته‌بندی: {category} | 📄 صفحه: {page}",
        "──────────────────────────────"
    ]

    post_urls = []
    for idx, item in enumerate(results, 1):
        title = item["title"]
        site = item["site"]
        quality = item["quality"]
        link = item["link"]
        post_urls.append((title, link))

        response_lines.append(
            f"{idx}. {title}\n"
            f"🌐 منبع: {site} | 🏷 نسخه: {quality}\n"
        )

    response_text = "\n".join(response_lines)
    keyboard = build_results_keyboard(has_next, page, len(results), post_urls)

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

    if data.startswith("cat_"):
        cat_code = data.replace("cat_", "")
        session["category"] = cat_code
        session["current_page"] = 1
        session["last_valid_page"] = 1
        
        await query.edit_message_text(
            f"✅ دسته‌بندی به {cat_code} تغییر یافت.\n"
            f"در حال جستجوی مجدد نتایج..."
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

    elif data.startswith("getlinks_"):
        idx = int(data.replace("getlinks_", ""))
        results = session.get("last_results", [])
        if 0 <= idx < len(results):
            target_item = results[idx]
            post_url = target_item["link"]
            post_title = target_item["title"]

            waiting_msg = await query.message.reply_text("⏳ در حال استخراج لینک‌های دانلود مستقیم...")

            dl_data = await asyncio.to_thread(scraper.fetch_post_download_links, post_url)
            links = dl_data.get("links", [])
            password = dl_data.get("password", "www.downloadha.com")

            if not links:
                await waiting_msg.edit_text(
                    f"⚠️ لینک دانلودی داخل پست «{post_title}» یافت نشد.\n"
                    f"🔗 مشاهده مستقیم در سایت:\n{post_url}"
                )
            else:
                links_text = [
                    f"📦 لینک‌های دانلود مستقیم:",
                    f"🎮 عنوان: {post_title}",
                    f"🔑 رمز فایل‌ها: {password}",
                    "──────────────────────────────"
                ]
                for l in links:
                    links_text.append(f"📥 {l['text']}:\n{l['url']}\n")

                await waiting_msg.edit_text("\n".join(links_text), disable_web_page_preview=True)

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