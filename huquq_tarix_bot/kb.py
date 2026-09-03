from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Test Yechish"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="💳 Obuna bo'lish / Balans"), KeyboardButton(text="ℹ️ Yordam")]
        ],
        resize_keyboard=True
    )

def subjects_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚖️ Huquq", callback_data="subj_huquq")],
            [InlineKeyboardButton(text="📜 Tarix", callback_data="subj_tarix")],
            [InlineKeyboardButton(text="🔀 Aralash (Huquq + Tarix)", callback_data="subj_mixed")]
        ]
    )

def test_options_kb(session_id: int, q_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="A", callback_data=f"ans_{session_id}_{q_id}_A"),
                InlineKeyboardButton(text="B", callback_data=f"ans_{session_id}_{q_id}_B")
            ],
            [
                InlineKeyboardButton(text="C", callback_data=f"ans_{session_id}_{q_id}_C"),
                InlineKeyboardButton(text="D", callback_data=f"ans_{session_id}_{q_id}_D")
            ]
        ]
    )

def admin_receipt_kb(receipt_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{receipt_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{receipt_id}")
            ]
        ]
    )