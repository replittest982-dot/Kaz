import aiosqlite
from datetime import datetime

# Создание таблиц (вызывается из main.py при старте)
async def create_tables():
    async with aiosqlite.connect("database.db") as conn:
        await conn.execute("""CREATE TABLE IF NOT EXISTS users(
        us_id INTEGER PRIMARY KEY,
        join_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_ban INT DEFAULT 0,
        cashback INT DEFAULT 0,
        ref INT,
        ref_balance INT DEFAULT 0,
        username TEXT,
        ref_total INT DEFAULT 0,
        moder INT DEFAULT 0
        );""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS deposits(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        summa INT,
        us_id INT
        );""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS withdraws(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        summa INT,
        us_id INT
        );""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS bets(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        summa INT,
        win INT DEFAULT 0,
        lose INT DEFAULT 0,
        us_id INT
        );""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS settings(
        invoice_link TEXT PRIMARY KEY,
        max_amount DEFAULT 25,
        podkrut INT DEFAULT 0
        );""")
        await conn.execute("""CREATE TABLE IF NOT EXISTS "mines" (
            "id"	INTEGER,
            "creator_id"	INTEGER,
            "creator_name"	TEXT,
            "bet_amount"	INTEGER,
            "coeff"	REAL,
            "mines_count"	INTEGER,
            "mines_map"	TEXT,
            "mines_open"	TEXT,
            "status"	TEXT,
            "message_id"	INTEGER,
            "step"	INTEGER,
            PRIMARY KEY("id" AUTOINCREMENT)
        );""")
        # Таблица конкурсов (была в твоем сниппете)
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

# --- ФУНКЦИИ РАБОТЫ С БД ---

async def get_user(us_id):
    async with aiosqlite.connect("database.db") as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM users WHERE us_id = ?", (us_id,)) as cursor:
            return await cursor.fetchone()

async def save_to_db(us_id, username, referrer=None):
    async with aiosqlite.connect("database.db") as conn:
        user = await get_user(us_id)
        if not user:
            await conn.execute("INSERT INTO users (us_id, username, ref) VALUES (?, ?, ?)", (us_id, username, referrer))
            await conn.commit()

# --- MINES ФУНКЦИИ ---

async def get_mines(user_id):
    async with aiosqlite.connect("database.db") as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM mines WHERE creator_id = ? AND status = 'active'", (user_id,)) as cursor:
            return await cursor.fetchone()

async def update_mines_open(user_id, new_open_map):
    async with aiosqlite.connect("database.db") as conn:
        await conn.execute("UPDATE mines SET mines_open = ? WHERE creator_id = ? AND status = 'active'", (new_open_map, user_id))
        await conn.commit()

async def update_mines_map(user_id, new_map):
    async with aiosqlite.connect("database.db") as conn:
        await conn.execute("UPDATE mines SET mines_map = ? WHERE creator_id = ? AND status = 'active'", (new_map, user_id))
        await conn.commit()

async def update_mines_bets(user_id, bet_amount):
    # Эта функция была в импортах, добавляем заглушку или логику если нужна
    pass 

async def update_mines_wins(user_id, win_amount):
    async with aiosqlite.connect("database.db") as conn:
        # Обновляем выигрыш (обычно это +баланс юзеру)
        await conn.execute("UPDATE users SET ref_balance = ref_balance + ? WHERE us_id = ?", (win_amount, user_id))
        await conn.commit()

async def update_mines_num(user_id, num):
    async with aiosqlite.connect("database.db") as conn:
        await conn.execute("UPDATE mines SET mines_count = ? WHERE creator_id = ? AND status = 'active'", (num, user_id))
        await conn.commit()
        
async def update_bet_id(user_id, msg_id):
    async with aiosqlite.connect("database.db") as conn:
        await conn.execute("UPDATE mines SET message_id = ? WHERE creator_id = ? AND status = 'active'", (msg_id, user_id))
        await conn.commit()

async def set_status_game(user_id, status):
    async with aiosqlite.connect("database.db") as conn:
        await conn.execute("UPDATE mines SET status = ? WHERE creator_id = ? AND status = 'active'", (status, user_id))
        await conn.commit()

async def add_open_field(user_id, field):
    # Добавляем открытую ячейку
    pass

async def get_open_field(user_id):
    async with aiosqlite.connect("database.db") as conn:
         async with conn.execute("SELECT mines_open FROM mines WHERE creator_id = ? AND status = 'active'", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else ""

async def and_mine_game(user_id):
    await set_status_game(user_id, 'finished')

# --- КОНКУРСЫ ---

async def get_all_contests():
    async with aiosqlite.connect("database.db") as conn:
        async with conn.execute("SELECT * FROM contests WHERE end = 0") as cursor:
            return await cursor.fetchall()

# (Остальные функции конкурсов create_contest, update_contest добавь сюда же, если они были в исходнике, они стандартные)
