import aiosqlite
from datetime import datetime, timedelta

DB_PATH = "bot_database.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                is_banned INTEGER DEFAULT 0,
                free_tests_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                granted_by TEXT,
                expires_at TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                question TEXT,
                option_a TEXT,
                option_b TEXT,
                option_c TEXT,
                option_d TEXT,
                correct_option TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS test_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subject TEXT,
                questions_json TEXT,
                current_index INTEGER DEFAULT 0,
                answers_json TEXT,
                score INTEGER DEFAULT 0,
                is_finished INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                file_id TEXT,
                tx_id TEXT,
                amount INTEGER,
                status TEXT DEFAULT 'pending',
                raw_ocr TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS used_transactions (
                tx_id TEXT PRIMARY KEY,
                user_id INTEGER
            )
        """)
        await db.commit()

async def get_or_create_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name)
        )
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def ban_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def increment_free_tests(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET free_tests_used = free_tests_used + 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_active_subscription(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM subscriptions WHERE user_id = ? AND expires_at > CURRENT_TIMESTAMP ORDER BY expires_at DESC LIMIT 1",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def grant_subscription(user_id: int, granted_by: str = "auto", days: int = 30):
    async with aiosqlite.connect(DB_PATH) as db:
        expires_at = datetime.now() + timedelta(days=days)
        await db.execute(
            "INSERT INTO subscriptions (user_id, granted_by, expires_at) VALUES (?, ?, ?)",
            (user_id, granted_by, expires_at)
        )
        await db.commit()

async def revoke_subscription(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM subscriptions WHERE user_id = ?", (user_id,))
        await db.commit()

async def count_questions():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM questions") as cursor:
            res = await cursor.fetchone()
            return res[0] if res else 0

async def insert_question(q: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO questions (subject, question, option_a, option_b, option_c, option_d, correct_option) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (q["subject"], q["question"], q["option_a"], q["option_b"], q["option_c"], q["option_d"], q["correct_option"])
        )
        await db.commit()

async def get_random_questions(subject: str, count: int = 30):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM questions WHERE subject = ? ORDER BY RANDOM() LIMIT ?",
            (subject, count)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_mixed_questions(count: int = 30):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT ?", (count,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

import json

async def create_test_session(user_id: int, subject: str, question_ids: list):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO test_sessions (user_id, subject, questions_json, answers_json) VALUES (?, ?, ?, ?)",
            (user_id, subject, json.dumps(question_ids), json.dumps([]))
        )
        await db.commit()
        return cursor.lastrowid

async def get_active_session(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM test_sessions WHERE user_id = ? AND is_finished = 0 ORDER BY id DESC LIMIT 1",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_session_answer(session_id: int, option: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM test_sessions WHERE id = ?", (session_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            
            session = dict(row)
            q_ids = json.loads(session["questions_json"])
            answers = json.loads(session["answers_json"])
            answers.append(option)
            curr_idx = session["current_index"] + 1

            if curr_idx >= len(q_ids):
                await db.execute(
                    "UPDATE test_sessions SET answers_json = ?, current_index = ? WHERE id = ?",
                    (json.dumps(answers), curr_idx, session_id)
                )
                await db.commit()
                return None
            else:
                await db.execute(
                    "UPDATE test_sessions SET answers_json = ?, current_index = ? WHERE id = ?",
                    (json.dumps(answers), curr_idx, session_id)
                )
                await db.commit()
                
                async with db.execute("SELECT * FROM questions WHERE id = ?", (q_ids[curr_idx],)) as q_cursor:
                    q_row = await q_cursor.fetchone()
                    return {
                        "next_question": dict(q_row),
                        "current_index": curr_idx,
                        "total": len(q_ids)
                    }

async def finish_session(session_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM test_sessions WHERE id = ?", (session_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            session = dict(row)

        q_ids = json.loads(session["questions_json"])
        answers = json.loads(session["answers_json"])
        
        correct_count = 0
        for q_id, ans in zip(q_ids, answers):
            async with db.execute("SELECT correct_option FROM questions WHERE id = ?", (q_id,)) as q_cursor:
                q_row = await q_cursor.fetchone()
                if q_row and q_row[0] == ans:
                    correct_count += 1

        total = len(q_ids)
        score_pct = (correct_count / total * 100) if total > 0 else 0

        await db.execute(
            "UPDATE test_sessions SET score = ?, is_finished = 1 WHERE id = ?",
            (correct_count, session_id)
        )
        await db.commit()

        return {
            "total_questions": total,
            "correct_answers": correct_count,
            "score_percentage": score_pct
        }

async def expire_old_sessions():
    pass

async def get_user_stats(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*), AVG(score), MAX(score) FROM test_sessions WHERE user_id = ? AND is_finished = 1",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row and row[0] > 0:
                return {"total": row[0], "avg_score": row[1] or 0, "best_score": row[2] or 0}
            return {"total": 0, "avg_score": 0, "best_score": 0}

async def save_receipt(user_id: int, file_id: str, tx_id: str, amount: int, raw_ocr: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO receipts (user_id, file_id, tx_id, amount, raw_ocr) VALUES (?, ?, ?, ?, ?)",
            (user_id, file_id, tx_id, amount, raw_ocr)
        )
        await db.commit()
        return cursor.lastrowid

async def is_transaction_used(tx_id: str):
    if not tx_id:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM used_transactions WHERE tx_id = ?", (tx_id,)) as cursor:
            return await cursor.fetchone() is not None

async def mark_transaction_used(tx_id: str, user_id: int):
    if not tx_id:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO used_transactions (tx_id, user_id) VALUES (?, ?)", (tx_id, user_id))
        await db.commit()

async def approve_receipt(receipt_id: int, admin_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            receipt = dict(row)

        await db.execute("UPDATE receipts SET status = 'approved' WHERE id = ?", (receipt_id,))
        await db.commit()

        if receipt["tx_id"]:
            await mark_transaction_used(receipt["tx_id"], receipt["user_id"])

        return receipt["user_id"]

async def reject_receipt(receipt_id: int, admin_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            receipt = dict(row)

        await db.execute("UPDATE receipts SET status = 'rejected' WHERE id = ?", (receipt_id,))
        await db.commit()
        return receipt["user_id"]

async def get_pending_receipts():
    pass

async def get_global_stats():
    pass
