import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime
import logging
import pytz
import sys
import asyncio

# Налаштування логування
logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ініціалізація бота
TOKEN = "7554224281:AAFR9eSa7oxRilNmM2kuh3tIhDWJu1B08ws"
GROUP_ID = -1002411083990

# Кеш для зберігання повідомлень
message_cache = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка команди /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Вітаю, {user.first_name}! 📚\n"
        "Я бот для пошуку книг. Використовуйте:\n"
        "/search назва_книги - для пошуку\n"
        "/status - перевірка статусу\n"
        "/help - допомога"
    )

async def search_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пошук книг"""
    if len(context.args) < 1:
        await update.message.reply_text(
            "ℹ️ Як використовувати пошук:\n"
            "/search назва_книги\n"
            "Наприклад: /search Кобзар"
        )
        return

    query = " ".join(context.args).lower()
    status_message = await update.message.reply_text("🔍 Шукаю книгу...")
    
    try:
        found_books = []
        # Отримуємо останні повідомлення з групи
        messages = await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=GROUP_ID,
            message_id=1,
            disable_notification=True
        )
        
        for msg in messages:
            if hasattr(msg, 'document') and msg.document:
                filename = msg.document.file_name.lower()
                if query in filename:
                    found_books.append(msg)
                    if len(found_books) >= 5:  # Обмежуємо кількість результатів
                        break

        if found_books:
            await status_message.edit_text(f"📚 Знайдено {len(found_books)} книг:")
            for book in found_books:
                await context.bot.forward_message(
                    chat_id=update.effective_chat.id,
                    from_chat_id=GROUP_ID,
                    message_id=book.message_id
                )
            logger.info(f"Знайдено {len(found_books)} книг для запиту: {query}")
        else:
            await status_message.edit_text(
                "❌ Книгу не знайдено.\n"
                "Спробуйте:\n"
                "- Перевірити правильність написання\n"
                "- Використати коротшу назву\n"
                "- Пошукати іншу книгу"
            )
            logger.info(f"Книгу не знайдено для запиту: {query}")
            
    except Exception as e:
        logger.error(f"Помилка пошуку: {str(e)}")
        await status_message.edit_text("⚠️ Помилка при пошуку. Спробуйте пізніше.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перевірка статусу бота"""
    kyiv_tz = pytz.timezone('Europe/Kiev')
    current_time = datetime.now(kyiv_tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    
    await update.message.reply_text(
        f"✅ Бот активний\n"
        f"⏰ Час: {current_time}\n"
        f"📚 База книг: активна\n"
        f"🔍 Пошук: доступний"
    )
    logger.info("Перевірка статусу виконана")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Довідка"""
    await update.message.reply_text(
        "📖 Довідка по використанню бота:\n\n"
        "1️⃣ Пошук книги:\n"
        "/search назва_книги\n"
        "Приклад: /search Кобзар\n\n"
        "2️⃣ Перевірка статусу:\n"
        "/status\n\n"
        "3️⃣ Початок роботи:\n"
        "/start\n\n"
        "❗️ Поради:\n"
        "- Використовуйте частину назви для кращого пошуку\n"
        "- Пошук не чутливий до регістру\n"
        "- Якщо книгу не знайдено, спробуйте інший варіант назви"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка помилок"""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Запуск бота"""
    try:
        # Створення застосунку
        application = Application.builder().token(TOKEN).build()

        # Додавання обробників команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("search", search_book))
        application.add_handler(CommandHandler("status", status))
        application.add_handler(CommandHandler("help", help_command))

        # Додавання обробника помилок
        application.add_error_handler(error_handler)

        # Запуск бота
        logger.info("Бот запущений...")
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Помилка при запуску бота: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
