import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ADMIN_IDS matn ko'rinishida kelsa (masalan "123,456"), uni integer ro'yxatiga o'tkazamiz
raw_admins = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in raw_admins.split(",") if x.strip().isdigit()]

OCR_MIN_AMOUNT = 10000
OCR_MAX_AMOUNT = 500000
