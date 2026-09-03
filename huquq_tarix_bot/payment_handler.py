import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from db import (
    save_receipt, is_transaction_used,
    grant_subscription, approve_receipt, reject_receipt
)
from ocr import parse_receipt
from kb import admin_receipt_kb
from config import ADMIN_IDS

router = Router()

@router.message(F.photo)
async def handle_receipt_photo(message: Message, bot: Bot):
    photo = message.photo[-1]
    
    file_info = await bot.get_file(photo.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    image_bytes = downloaded_file.read()

    msg = await message.answer("🔍 Chek tahlil qilinmoqda, kuting...")

    try:
        result = await parse_receipt(image_bytes)
        tx_id = getattr(result, 'transaction_id', None)
        amount = getattr(result, 'amount', None)
        raw_text = getattr(result, 'raw_text', "")
    except Exception as e:
        logging.error(f"OCR error: {e}")
        tx_id, amount, raw_text = None, None, ""

    if tx_id and await is_transaction_used(tx_id):
        await msg.edit_text("❌ Ushbu chek ilgari ishlatilgan!")
        return

    receipt_id = await save_receipt(message.from_user.id, photo.file_id, tx_id, amount, raw_text)
    
    # Chekni adminlarga yuborish
    sent_count = 0
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(
                chat_id=int(admin_id),
                photo=photo.file_id,
                caption=(
                    f"⚠️ **Yangi chek (Qo'lda tasdiqlash):**\n"
                    f"👤 Foydalanuvchi: {message.from_user.full_name} (`{message.from_user.id}`)\n"
                    f"💵 Summa: {amount if amount else 'Noma\'lum'}\n"
                    f"🆔 TX ID: {tx_id if tx_id else 'Noma\'lum'}"
                ),
                reply_markup=admin_receipt_kb(receipt_id),
                parse_mode="Markdown"
            )
            sent_count += 1
        except (TelegramForbiddenError, TelegramBadRequest) as e:
            logging.warning(f"⚠️ Admin {admin_id} botni bloklagan yoki xabar yetib bormadi: {e}")
        except Exception as e:
            logging.error(f"❌ Admin {admin_id} uchun kutilmagan xato: {e}")

    await msg.edit_text("📩 Chekingiz qabul qilindi va admin tekshiruviga yuborildi.")

@router.callback_query(F.data.startswith("approve_"))
async def approve_pay(call: CallbackQuery, bot: Bot):
    receipt_id = int(call.data.split("_")[1])
    user_id = await approve_receipt(receipt_id, call.from_user.id)
    if user_id:
        await grant_subscription(user_id, granted_by="admin")
        try:
            await bot.send_message(user_id, "🎉 Siz yuborgan to'lov admin tomonidan tasdiqlandi! VIP obuna yoqildi.")
        except Exception:
            pass
        await call.message.edit_caption(caption=f"{call.message.caption}\n\n✅ **ADMIN TARAFIDAN TASDIQLANDI**")
    await call.answer()

@router.callback_query(F.data.startswith("reject_"))
async def reject_pay(call: CallbackQuery, bot: Bot):
    receipt_id = int(call.data.split("_")[1])
    user_id = await reject_receipt(receipt_id, call.from_user.id)
    if user_id:
        try:
            await bot.send_message(user_id, "❌ Siz yuborgan chek rad etildi.")
        except Exception:
            pass
        await call.message.edit_caption(caption=f"{call.message.caption}\n\n❌ **RAD ETILDI**")
    await call.answer()
