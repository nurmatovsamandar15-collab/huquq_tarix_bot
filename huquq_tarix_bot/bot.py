import asyncio
import json
import logging
import os
from aiohttp import web

from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, QUESTIONS_JSON
from db import init_db, count_questions, insert_question

# Handlerlarni import qilish
import start
import test_handler
import payment_handler

logging.basicConfig(level=logging.INFO)

# Render port xatosini oldini olish uchun veb-server
async def handle(request):
    return web.Response(text="Bot muvaffaqiyatli ishlamoqda!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Veb-server {port}-portda ishga tushdi.")

async def load_questions_from_json():
    """questions.json faylidagi savollarni bazaga yuklaydi"""
    if not os.path.exists(QUESTIONS_JSON):
        logging.warning(f"{QUESTIONS_JSON} fayli topilmadi!")
        return

    current_count = await count_questions()
    if current_count == 0:
        logging.info("Baza bo'sh. Savollar json'dan yuklanmoqda...")
        with open(QUESTIONS_JSON, "r", encoding="utf-8") as f:
            questions = json.load(f)
            for q in questions:
                await insert_question(q)
        logging.info(f"{len(questions)} ta savol bazaga yuklandi.")

async def main():
    # Database yaratish va savollarni yuklash
    await init_db()
    await load_questions_from_json()

    # Render porti uchun veb-serverni ishga tushirish
    await start_web_server()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(test_handler.router)
    dp.include_router(payment_handler.router)

    logging.info("Bot tayyor va ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
