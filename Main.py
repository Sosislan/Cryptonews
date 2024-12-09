import time
import schedule
import requests
from datetime import datetime, timedelta
from translate import Translator
from telebot import TeleBot
from config import Bot_token, API_KEY

# Конфігурація
TELEGRAM_TOKEN = Bot_token
TELEGRAM_CHAT_ID = "@testcrupto"
CRYPTOCOMPARE_API_URL = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
CRYPTOCOMPARE_API_KEY = API_KEY

bot = TeleBot(TELEGRAM_TOKEN)
translator = Translator(to_lang="uk")  # Налаштовуємо переклад на українську
published_ids = set()  # Збереження ID опублікованих новин

def get_crypto_news():
    headers = {"Authorization": f"Apikey {CRYPTOCOMPARE_API_KEY}"}
    response = requests.get(CRYPTOCOMPARE_API_URL, headers=headers)
    if response.status_code == 200:
        news = response.json().get("Data", [])
        print(f"Отримано новин: {len(news)}")
        return news
    print(f"Помилка отримання новин: {response.status_code}")
    return []

def filter_recent_news(news_list):
    """Фільтрувати новини за останню годину"""
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent_news = []
    for news in news_list:
        if "published_on" in news:
            news_time = datetime.fromtimestamp(news["published_on"])
            if news_time > one_hour_ago:
                recent_news.append(news)
    return recent_news


def translate_text(text):
    """Переклад тексту на українську з обмеженням довжини"""
    try:
        if len(text) > 500:  # Обмеження довжини
            text = text[:500]
        translated = translator.translate(text)
        return translated
    except Exception as e:
        print(f"Помилка перекладу: {e}")
        return text  # Повертаємо оригінальний текст у разі помилки

def post_news_to_telegram():
    news_list = get_crypto_news()  # Отримуємо всі новини
    recent_news = filter_recent_news(news_list)  # Фільтруємо за останню годину
    recent_news = [news for news in recent_news if news.get("id") not in published_ids]  # Уникаємо старих новин

    if not recent_news:  # Якщо немає нових новин
        print("Немає нових новин за останню годину.")
        return

    for news in recent_news[:2]:  # Беремо максимум 10 новин
        news_id = news.get("id")
        title = news.get("title", "Без назви")
        #title = translate_text(news.get("title", "Без назви"))
        #description = translate_text(news.get("body", "Опис недоступний"))
        description = news.get("body", "Опис недоступний")
        url = news.get("url", "Без посилання")

        message = f"📰 {title}\n\n{description[:500]}...\n\n🔗 [Читати далі]({url})"
        try:
            time.sleep(2)  # Затримка між повідомленнями
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")
            published_ids.add(news_id)  # Додаємо ідентифікатор в список відправлених
            print(f"Опубліковано: {title}")
        except Exception as e:
            print(f"Помилка надсилання: {e}")



schedule.every().hour.do(post_news_to_telegram)

if __name__ == "__main__":
    print("Бот запущено. Очікування...")
    post_news_to_telegram()
    while True:
        schedule.run_pending()
        time.sleep(1)
