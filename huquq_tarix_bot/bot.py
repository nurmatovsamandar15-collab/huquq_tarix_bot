import asyncio
import logging
import json
import os
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, LOG_LEVEL, QUESTIONS_JSON
from db import init_db, count_questions, insert_question
import start
import test_handler
import payment_handler

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

async def load_initial_questions():
    total = await count_questions()
    if total == 0 and os.path.exists(QUESTIONS_JSON):
        with open(QUESTIONS_JSON, 'r', encoding='utf-8') as f:
            questions = json.load(f)
            for q in questions:
                await insert_question(q)
        logger.info(f"✅ {len(questions)} ta savol bazaga yuklandi.")

async def main():
    await init_db()
    await load_initial_questions()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(test_handler.router)
    dp.include_router(payment_handler.router)

    logger.info("🚀 Bot tayyor va ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())