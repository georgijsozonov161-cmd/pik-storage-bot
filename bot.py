import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
WEBSITE_URL = "https://www.pik.ru/search/volp/storehouse"
user_chat_id = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_storage_urls():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(WEBSITE_URL, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        links = set()
        for a in soup.find_all('a', href=True):
            if '/storage/' in a['href']:
                url = a['href']
                if url.startswith('/'):
                    url = 'https://www.pik.ru' + url
                links.add(url)
        return links
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return set()

def start(update: Update, context: CallbackContext):
    global user_chat_id
    user_chat_id = update.effective_chat.id
    update.message.reply_text("✅ Бот запущен! Слежу за новыми кладовыми на pik.ru")

def check(context: CallbackContext):
    global user_chat_id
    if user_chat_id is None:
        return
    current = get_storage_urls()
    if not hasattr(check, 'previous'):
        check.previous = current
        logger.info("Первый запуск. Сохранено кладовых: %d", len(current))
        return
    new = current - check.previous
    if new:
        for url in list(new)[:3]:
            context.bot.send_message(chat_id=user_chat_id, text=f"🆕 Новая кладовая!\n{url}")
        check.previous = current
        logger.info("Обнаружено новых кладовых: %d", len(new))
    else:
        logger.info("Новых кладовых нет.")

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    updater.job_queue.run_repeating(check, interval=300, first=10)
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
