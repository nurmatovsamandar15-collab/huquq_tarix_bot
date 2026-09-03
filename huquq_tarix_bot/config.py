import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# Karta va ega ma'lumotlari yangilandi
PAYMENT_CARD = os.getenv("PAYMENT_CARD", "4073420082003835")
PAYMENT_CARD_OWNER = os.getenv("PAYMENT_CARD_OWNER", "Nurmatov S.")
SUBSCRIPTION_PRICE = int(os.getenv("SUBSCRIPTION_PRICE", "20000"))

OCR_MIN_AMOUNT = int(os.getenv("OCR_MIN_AMOUNT", "18000"))
OCR_MAX_AMOUNT = int(os.getenv("OCR_MAX_AMOUNT", "25000"))

FREE_TESTS_COUNT = 1
QUESTIONS_PER_TEST = 30
QUESTIONS_JSON = "questions.json"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
