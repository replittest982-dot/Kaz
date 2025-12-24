import aiosqlite
import config
from datetime import datetime

# Путь к базе данных
DB_PATH = "database.db"

# ===================================================
# ИНИЦИАЛИЗАЦИЯ ТАБЛИЦ
# ===================================================

async def create_tables():
    async with aiosqlite.connect(DB_PATH) as conn:
        # Пользователи
        await conn.execute("""CREATE TABLE IF NOT EXISTS users(
            us_id INTEGER PRIMARY KEY,
            join_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_ban INT DEFAULT 0,
            balance REAL DEFAULT 0,
            cashback INT DEFAULT 0,
            ref INT,
            ref_balance INT DEFAULT 0,
            username TEXT,
            ref_total INT DEFAULT 0,
            moder INT DEFAULT 0
        );""")
        
        # Депозиты
        await conn.execute("""CREATE TABLE IF NOT EXISTS deposits(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            summa INT,
            us_id INT
        );""")
        
        # Выводы
        await conn.execute("""CREATE TABLE IF NOT EXISTS withdraws(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            summa INT,
            us_id INT
        );""")
        
        # Ставки (история)
        await conn.execute("""CREATE TABLE IF NOT EXISTS bets(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            summa INT,
            win INT DEFAULT 0,
            lose INT DEFAULT 0,
            us_id INT
        );""")
        
        # Настройки
        await conn.execute("""CREATE TABLE IF NOT EXISTS settings(
            invoice_link TEXT PRIMARY KEY,
            max_amount DEFAULT 25,
            podkrut INT DEFAULT 0
        );""")
        
        # Активные игры Mines
        await conn.execute("""CREATE TABLE IF NOT EXISTS mines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER,
            creator_name TEXT,
            bet_amount INTEGER,
            coeff REAL,
            mines_count INTEGER,
            mines_map TEXT,
            mines_open TEXT,
            status TEXT,
            message_id INTEGER,
            step INTEGER
        );""")
        
        # Конкурсы
        await conn.execute("""CREATE TABLE IF NOT EXISTS contests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            summa INT,
            end_date DATETIME,
            msg_id INT,
            top1_summa INT DEFAULT 0,
            top2_summa INT DEFAULT 0,
            top3_summa INT DEFAULT 0,
            top1 TEXT,
            top2 TEXT,
            top3 TEXT,
            end INT DEFAULT 0
        );""")
        
        await conn.commit()

# ===================================================
# ПОЛЬЗОВАТЕЛИ (Users)
# ===================================================

async def get_user(us_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM users WHERE us_id = ?", (us_id,)) as cursor:
            return await cursor.fetchone()

async def save_to_db(us_id, username, referrer=None):
    if referrer is None:
        referrer = 0
    async with aiosqlite.connect(DB_PATH) as conn:
        user = await get_user(us_id)
        if not user:
            await conn.execute("INSERT OR IGNORE INTO users (us_id, username, ref, balance) VALUES (?, ?, ?, 0)", (us_id, username, referrer))
            await conn.commit()

# !!! ВАЖНО: ЭТО ИСПРАВЛЕНИЕ ТВОЕЙ ОШИБКИ !!!
# main.py вызывает db.reg_user, поэтому мы делаем псевдоним
reg_user = save_to_db 

async def update_balance(us_id, amount):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE users SET balance = balance + ? WHERE us_id = ?", (amount, us_id))
        await conn.commit()

# ===================================================
# ИГРА MINES (Логика сапера)
# ===================================================

async def create_mine_game(creator_id, creator_name, bet_amount, mines_count, mines_map, message_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("DELETE FROM mines WHERE creator_id = ? AND status = 'active'", (creator_id,))
        await conn.execute("""
            INSERT INTO mines (creator_id, creator_name, bet_amount, coeff, mines_count, mines_map, mines_open, status, message_id, step)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (creator_id, creator_name, bet_amount, 0.0, mines_count, mines_map, "", "active", message_id, 0))
        await conn.commit()

async def get_mines(user_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM mines WHERE creator_id = ? AND status = 'active'", (user_id,)) as cursor:
            return await cursor.fetchone()

async def update_mines_open(user_id, new_open_map):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE mines SET mines_open = ? WHERE creator_id = ? AND status = 'active'", (new_open_map, user_id))
        await conn.commit()

async def update_mines_map(user_id, new_map):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE mines SET mines_map = ? WHERE creator_id = ? AND status = 'active'", (new_map, user_id))
        await conn.commit()

async def update_mines_bets(user_id, bet_amount):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE mines SET bet_amount = ? WHERE creator_id = ? AND status = 'active'", (bet_amount, user_id))
        await conn.commit()

async def update_mines_wins(user_id, win_amount):
    # Начисляем выигрыш пользователю
    await update_balance(user_id, win_amount)

async def set_status_game(user_id, status):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE mines SET status = ? WHERE creator_id = ? AND status = 'active'", (status, user_id))
        await conn.commit()

async def and_mine_game(user_id):
    await set_status_game(user_id, 'finished')

async def add_open_field(user_id, field):
    async with aiosqlite.connect(DB_PATH) as conn:
        async with conn.execute("SELECT mines_open FROM mines WHERE creator_id = ? AND status = 'active'", (user_id,)) as cursor:
            row = await cursor.fetchone()
            current = row[0] if row else ""
        
        new_open = f"{current},{field}" if current else field
        await conn.execute("UPDATE mines SET mines_open = ? WHERE creator_id = ? AND status = 'active'", (new_open, user_id))
        await conn.commit()

async def get_open_field(user_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        async with conn.execute("SELECT mines_open FROM mines WHERE creator_id = ? AND status = 'active'", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else ""

async def update_mines_num(user_id, num):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE mines SET mines_count = ? WHERE creator_id = ? AND status = 'active'", (num, user_id))
        await conn.commit()

async def update_bet_id(user_id, msg_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE mines SET message_id = ? WHERE creator_id = ? AND status = 'active'", (msg_id, user_id))
        await conn.commit()

# ===================================================
# КОНКУРСЫ (Contests)
# ===================================================

async def create_contest(amount, end_date, msg_id):
    # end_date приходит строкой или датой. Сохраняем как строку для простоты SQLite
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("""
            INSERT INTO contests(summa, end_date, msg_id, top1_summa, top2_summa, top3_summa, end) 
            VALUES(?, ?, ?, 0, 0, 0, 0)
        """, (amount, end_date, msg_id))
        await conn.commit()

async def get_all_contests():
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM contests WHERE end = 0") as cursor:
            return await cursor.fetchall()

async def get_contest(contest_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM contests WHERE id=?", (contest_id,)) as cursor:
            return await cursor.fetchone()

async def set_end(contest_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE contests SET end=1 WHERE id=?", (contest_id,))
        await conn.commit()

async def update_contest_top(contest_id, top1=None, top1_summa=None, top2=None, top2_summa=None, top3=None, top3_summa=None):
    async with aiosqlite.connect(DB_PATH) as conn:
        if top1:
            await conn.execute("UPDATE contests SET top1=?, top1_summa=? WHERE id=?", (top1, top1_summa, contest_id))
        if top2:
            await conn.execute("UPDATE contests SET top2=?, top2_summa=? WHERE id=?", (top2, top2_summa, contest_id))
        if top3:
            await conn.execute("UPDATE contests SET top3=?, top3_summa=? WHERE id=?", (top3, top3_summa, contest_id))
        await conn.commit()

# ===================================================
# НАСТРОЙКИ (Settings)
# ===================================================

async def get_settings():
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM settings") as cursor:
            res = await cursor.fetchone()
            if not res:
                await conn.execute("INSERT INTO settings (max_amount, podkrut) VALUES (25, 0)")
                await conn.commit()
                return await get_settings()
            return res

async def update_podkrut(value):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE settings SET podkrut = ?", (value,))
        await conn.commit()
