import time
import schedule
import requests
from datetime import datetime, timedelta
from translate import Translator
from telebot import TeleBot
from config import Bot_token, COINGECKO_API_TOKEN

# Конфігурація
TELEGRAM_TOKEN = Bot_token
TELEGRAM_CHAT_ID = "@testcrupto"
COINGECKO_API_URL = "https://cryptopanic.com/api/v1/posts/"
COINGECKO_API_TOKEN = COINGECKO_API_TOKEN
bot = TeleBot(TELEGRAM_TOKEN)
translator = Translator(to_lang="uk")  # Налаштовуємо переклад на українську
published_ids = set()  # Збереження ID опублікованих новин

def get_crypto_news():
    """Отримання новин з CryptoPanic API"""
    params = {"auth_token": COINGECKO_API_TOKEN, "filter": "news"}
    try:
        response = requests.get(COINGECKO_API_URL, params=params)
        if response.status_code == 200:
            news = response.json().get("results", [])
            print(f"Отримано новин: {len(news)}")
            return news
        else:
            print(f"Помилка отримання новин: {response.status_code}")
            return []
    except Exception as e:
        print(f"Помилка підключення до API: {e}")
        return []

def filter_recent_news(news_list):
    """Фільтрування новин за останню годину"""
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent_news = []
    for news in news_list:
        if "published_at" in news:
            news_time = datetime.strptime(news["published_at"], "%Y-%m-%dT%H:%M:%S%z")
            if news_time > one_hour_ago.replace(tzinfo=news_time.tzinfo):
                recent_news.append(news)
    return recent_news

def post_news_to_telegram():
    """Публікація новин у Telegram"""
    news_list = get_crypto_news()  # Отримання всіх новин
    if not news_list:
        print("Немає новин для обробки.")
        return

    recent_news = filter_recent_news(news_list)  # Фільтрування за останню годину
    recent_news = [news for news in recent_news if news.get("id") not in published_ids]  # Уникнення повторів

    if not recent_news:
        print("Немає нових новин за останню годину.")
        return

    for news in recent_news[:5]:  # Публікуємо максимум 5 новин
        news_id = news.get("id")
        title = news.get("title", "Без назви")
        description = news.get("description", "Опис недоступний")
        url = news.get("url", "Без посилання")
        message = f"📰 {title}\n\n{description[:500]}...\n\n🔗 [Читати далі]({url})"
        try:
            time.sleep(2)  # Затримка між повідомленнями
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")
            published_ids.add(news_id)  # Додаємо ID до списку відправлених
            print(f"Опубліковано: {title}")
        except Exception as e:
            print(f"Помилка надсилання: {e}")

# Розклад роботи
schedule.every().hour.do(post_news_to_telegram)

if __name__ == "__main__":
    print("Бот запущено. Очікування...")
    post_news_to_telegram()
    while True:
        schedule.run_pending()
        time.sleep(1)