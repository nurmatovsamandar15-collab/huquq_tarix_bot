from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from db import (
    get_user, get_active_subscription, increment_free_tests,
    get_random_questions, get_mixed_questions, create_test_session,
    get_active_session, update_session_answer, finish_session
)
from kb import subjects_kb, test_options_kb
from config import FREE_TESTS_COUNT, QUESTIONS_PER_TEST

router = Router()

@router.message(F.text == "📝 Test Yechish")
async def start_test_router(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    sub = await get_active_subscription(user_id)

    if not sub and user and user.get('free_tests_used', 0) >= FREE_TESTS_COUNT:
        await message.answer(
            "⚠️ Bepul test imkoniyatingiz tugagan.\n"
            "Davom ettirish uchun **💳 Obuna bo'lish / Balans** tugmasi orqali obunani yoqing."
        )
        return

    await message.answer("Qaysi fandan test topshirmoqchisiz?", reply_markup=subjects_kb())

@router.callback_query(F.data.startswith("subj_"))
async def process_subject_choice(call: CallbackQuery):
    subject = call.data.split("_")[1]
    user_id = call.from_user.id

    if subject == "mixed":
        questions = await get_mixed_questions(QUESTIONS_PER_TEST)
        session_subject = "mixed"
    else:
        # Callback'dan kelgan 'huquq' yoki 'tarix'ni bazadagidek 'Huquq' / 'Tarix' ko'rinishiga o'tkazamiz
        session_subject = subject.capitalize()
        questions = await get_random_questions(session_subject, QUESTIONS_PER_TEST)

    if not questions:
        await call.message.answer("⚠️ Baza hozircha bu fan bo'yicha savollar yetarli emas.")
        await call.answer()
        return

    q_ids = [q['id'] for q in questions]
    session_id = await create_test_session(user_id, session_subject, q_ids)

    sub = await get_active_subscription(user_id)
    if not sub:
        await increment_free_tests(user_id)

    await call.message.delete()
    await send_next_question(call.message, session_id, questions, 0)

async def send_next_question(message: Message, session_id: int, questions: list, index: int):
    q = questions[index]
    text = (
        f"❓ **{index + 1}/{len(questions)}-savol:**\n\n"
        f"{q['question']}\n\n"
        f"A) {q['option_a']}\n"
        f"B) {q['option_b']}\n"
        f"C) {q['option_c']}\n"
        f"D) {q['option_d']}"
    )
    await message.answer(text, reply_markup=test_options_kb(session_id, q['id']), parse_mode="Markdown")

@router.callback_query(F.data.startswith("ans_"))
async def process_answer(call: CallbackQuery):
    _, session_id_str, q_id_str, option = call.data.split("_")
    session_id = int(session_id_str)
    
    session = await get_active_session(call.from_user.id)
    if not session or session['id'] != session_id:
        await call.answer("⚠️ Test sessiyasi yakunlangan yoki topilmadi.", show_alert=True)
        return

    updated_session = await update_session_answer(session_id, option)
    await call.message.delete()

    if updated_session and updated_session.get('next_question'):
        q = updated_session['next_question']
        idx = updated_session['current_index']
        total = updated_session['total']
        
        text = (
            f"❓ **{idx + 1}/{total}-savol:**\n\n"
            f"{q['question']}\n\n"
            f"A) {q['option_a']}\n"
            f"B) {q['option_b']}\n"
            f"C) {q['option_c']}\n"
            f"D) {q['option_d']}"
        )
        await call.message.answer(text, reply_markup=test_options_kb(session_id, q['id']), parse_mode="Markdown")
    else:
        results = await finish_session(session_id)
        if results:
            text = (
                f"🎉 **Test yakunlandi!**\n\n"
                f"📊 Jami savollar: {results['total_questions']}\n"
                f"✅ To'g'ri javoblar: {results['correct_answers']}\n"
                f"📈 Natijangiz: {results['score_percentage']:.1f}%"
            )
            await call.message.answer(text, parse_mode="Markdown")
    await call.answer()
