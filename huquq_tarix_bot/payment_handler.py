from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from db import (
    save_receipt, is_transaction_used, mark_transaction_used,
    grant_subscription, approve_receipt, reject_receipt
)
from ocr import parse_receipt
from kb import admin_receipt_kb
from config import ADMIN_IDS, OCR_MIN_AMOUNT, OCR_MAX_AMOUNT

router = Router()

@router.message(F.photo)
async def handle_receipt_photo(message: Message, bot: Bot):
    photo = message.photo[-1]
    
    file_info = await bot.get_file(photo.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    image_bytes = downloaded_file.read()

    msg = await message.answer("🔍 Chek admin tekshiruviga tayyorlanmoqda, kuting...")

    result = await parse_receipt(
        image_bytes=image_bytes,
        min_amount=OCR_MIN_AMOUNT,
        max_amount=OCR_MAX_AMOUNT
    )

    tx_id = result.transaction_id
    amount = result.amount

    if tx_id and await is_transaction_used(tx_id):
        await msg.edit_text("❌ Ushbu chek ilgari ishlatilgan! Takroriy cheklar qabul qilinmaydi.")
        return

    # Barcha cheklar avtomatik tasdiqlanmasdan, to'g'ri admin tekshiruviga yuboriladi
    receipt_id = await save_receipt(message.from_user.id, photo.file_id, tx_id, amount, result.raw_text)
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(
                chat_id=admin_id,
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
        except Exception:
            pass
    
    await msg.edit_text("📩 Chekingiz qabul qilindi va admin tekshiruviga yuborildi. Tez orada obunangiz yoqiladi.")

@router.callback_query(F.data.startswith("approve_"))
async def approve_pay(call: CallbackQuery, bot: Bot):
    receipt_id = int(call.data.split("_")[1])
    user_id = await approve_receipt(receipt_id, call.from_user.id)
    if user_id:
        await grant_subscription(user_id, granted_by="admin")
        await bot.send_message(user_id, "🎉 Siz yuborgan to'lov admin tomonidan tasdiqlandi! 30 kunlik VIP obuna yoqildi.")
        await call.message.edit_caption(caption=f"{call.message.caption}\n\n✅ **ADMIN TARAFIDAN TASDIQLANDI**")
    await call.answer()

@router.callback_query(F.data.startswith("reject_"))
async def reject_pay(call: CallbackQuery, bot: Bot):
    receipt_id = int(call.data.split("_")[1])
    user_id = await reject_receipt(receipt_id, call.from_user.id)
    if user_id:
        await bot.send_message(user_id, "❌ Siz yuborgan chek rad etildi.")
        await call.message.edit_caption(caption=f"{call.message.caption}\n\n❌ **RAD ETILDI**")
    await call.answer()
