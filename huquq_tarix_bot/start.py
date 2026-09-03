from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from db import get_or_create_user, get_active_subscription, get_user_stats
from kb import main_menu_kb
from config import PAYMENT_CARD, PAYMENT_CARD_OWNER, SUBSCRIPTION_PRICE

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )
    
    welcome_text = (
        f"Salom, {message.from_user.first_name}!\n\n"
        f"📚 Huquq va Tarix fanlaridan Milliy Sertifikat test botiga xush kelibsiz.\n\n"
        f"🎁 Sizga **1 ta bepul test** imkoniyati berilgan."
    )
    await message.answer(welcome_text, reply_markup=main_menu_kb(), parse_mode="Markdown")

@router.message(F.text == "💳 Obuna bo'lish / Balans")
async def show_subscription(message: Message):
    sub = await get_active_subscription(message.from_user.id)
    if sub:
        await message.answer(f"✅ Sizda faol obuna mavjud!\n📅 Amal qilish muddati: {str(sub['expires_at'])[:10]}")
    else:
        text = (
            f"❌ Sizda faol obuna mavjud emas.\n\n"
            f"💰 Obuna narxi: **{SUBSCRIPTION_PRICE:,} so'm** (30 kun)\n\n"
            f"💳 **To'lov uchun karta:** `{PAYMENT_CARD}`\n"
            f"👤 **Ega:** {PAYMENT_CARD_OWNER}\n\n"
            f"📸 To'lovni amalga oshirgach, chek rasmini yuboring."
        )
        await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    stats = await get_user_stats(message.from_user.id)
    text = (
        f"📊 **Sizning natijalaringiz:**\n\n"
        f"📝 Ishlangan testlar: {stats.get('total', 0)} ta\n"
        f"📈 O'rtacha ko'rsatkich: {stats.get('avg_score', 0):.1f}%\n"
        f"🏆 Eng yaxshi natija: {stats.get('best_score', 0):.1f}%"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "ℹ️ Yordam")
async def show_help(message: Message):
    text = (
        "❓ **Savol va Murojaatlar uchun:**\n"
        "Bot yuzasidan muammo bo'lsa, adminga murojaat qilishingiz mumkin."
    )
    await message.answer(text, parse_mode="Markdown")