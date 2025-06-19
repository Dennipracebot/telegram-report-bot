import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from telegram.error import Conflict
from deep_translator import GoogleTranslator

# 🔑 Твій токен і Telegram ID
TOKEN = os.getenv('TOKEN')
ADMIN_ID = int(os.getenv(ADMIN_ID))

# 📁 Папка для фото
PHOTO_DIR = "received_photos"
os.makedirs(PHOTO_DIR, exist_ok=True)

# ▶️ Стартова команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вітаю! Напишіть опис виконаних робіт та фото (за потреби).\nDobrý den! Napište popis provedených prací a fotku (pokud je potřeba).")

# 📨 Обробка повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message.text or "Надіслано файл або фото"

    # 🌐 Переклад на чеську
    translated_msg = GoogleTranslator(source='auto', target='cs').translate(msg)
    full_message = f"{msg}\n\nPřeklad do češtiny:\n{translated_msg}"

    # 👤 Інформація про користувача
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    username = f"@{user.username}" if user.username else "(без username)"
    user_info = f"{first_name} {last_name}".strip()

    # 💾 Якщо є фото — зберігаємо
    if update.message.photo:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_path = os.path.join(PHOTO_DIR, f"{user.id}_{file.file_id}.jpg")
        await file.download_to_drive(file_path)
        full_message += f"\n\n[Збережено фото: {file_path}]"

    # 📤 Надсилаємо адміну
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Звіт від {user_info} {username} (ID: {user.id}):\n{full_message}"
    )

    # ✅ Відповідь працівнику
    await update.message.reply_text("Звіт надіслано адміну. Очікуйте відповідь.\nHlášení bylo odesláno administrátorovi.")

# 🔁 Команда відповіді
async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Формат: /reply <user_id> <текст>")
        return

    user_id = context.args[0]
    message_text = " ".join(context.args[1:])
    try:
        await context.bot.send_message(chat_id=int(user_id), text=f"Повідомлення від адміністратора:\n\n{message_text}")
        await update.message.reply_text("Відповідь надіслано.")
    except Exception as e:
        await update.message.reply_text(f"Помилка: {e}")

# 🚀 Запуск
if __name__ == '__main__':
    try:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("reply", reply_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(MessageHandler(filters.PHOTO, handle_message))
        app.run_polling()
    except Conflict:
        print("❌ Бот вже запущений в іншому вікні. Закрий його і спробуй знову.")