import aiosqlite
import functions
from datetime import datetime

async def create_tables():
    conn = await aiosqlite.connect("database.db")
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
    await conn.execute( """CREATE TABLE IF NOT EXISTS "mines" (
        "id"	INTEGER,
        "creator_id"	INTEGER,
        "mines_nums"	INTEGER DEFAULT 0,
        "mine_bets"	NUMERIC DEFAULT 0,
        "current_win"	NUMERIC DEFAULT 0,
        "mines_open"	INTEGER DEFAULT 0,
        "mines_map"	TEXT,
        "open_fields"	TEXT DEFAULT '[]',
        "last_win"	NUMERIC DEFAULT 0,
        "status"	BLOB DEFAULT 0,
        PRIMARY KEY("id")
    )""")
    await conn.execute("""CREATE TABLE IF NOT EXISTS bets_mines(
    id INT PRIMARY KEY,
    us_id INT,
    summa INT,
    end INT DEFAULT 0
);""")
    await conn.execute("""CREATE TABLE IF NOT EXISTS msg_config(
        msg_id INT
);""")
    await conn.execute("""CREATE TABLE IF NOT EXISTS contests(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summa INT,
    top1 TEXT,
    top1_summa INT DEFAULT 0,
    top2 TEXT,
    top2_summa INT DEFAULT 0,
    top3 TEXT,
    top3_summa INT DEFAULT 0,
    end_date DATETIME,
    end INT DEFAULT 0,
    msg_id INT
);""")
    await conn.commit()

async def get_summ_deposits(id):
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT SUM(summa) FROM deposits WHERE us_id=?", (id,))
    deposits = await query.fetchone()
    if deposits[0] is not None:
        return float(deposits[0])
    else:
        return 0.0

async def get_summ_withdraws(id):
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT SUM(summa) FROM withdraws WHERE us_id=?", (id,))
    withdraws = await query.fetchone()
    if withdraws[0] is not None:
        return float(withdraws[0])
    else:
        return 0.0

async def get_wins_summ(id):
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT SUM(summa) FROM bets WHERE us_id=? AND win=1", (id,))
    wins = await query.fetchone()
    if wins[0] is not None:
        return float(wins[0])
    else:
        return 0.0

async def get_loses_summ(id):
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT SUM(summa) FROM bets WHERE us_id=? AND lose=1", (id,))
    loses = await query.fetchone()
    if loses[0] is not None:
        return float(loses[0])
    else:
        return 0.0

async def get_total_bets_summ(id):
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT SUM(summa) FROM bets WHERE us_id=?", (id,))
    bets = await query.fetchone()
    if bets[0] is not None:
        return float(bets[0])
    else:
        return 0.0

async def get_wins_count(id):
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT COUNT(*) FROM bets WHERE us_id=? AND win=1", (id,))
    wins = await query.fetchone()
    if wins[0] is not None:
        return float(wins[0])
    else:
        return 0.0

async def get_total_bets_count(id):
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT COUNT(*) FROM bets WHERE us_id=?", (id,))
    bets = await query.fetchone()
    if bets[0] is not None:
        return float(bets[0])
    else:
        return 0.0

async def add_deposit(summa, us_id):
    conn = await aiosqlite.connect("database.db")
    await conn.execute("INSERT INTO deposits(summa,us_id) VALUES (?,?)", (summa,us_id,))
    await conn.commit()

async def create_bet(summa, us_id, win=None, lose=None):
    conn = await aiosqlite.connect("database.db")
    if win:
        await conn.execute("INSERT INTO bets(summa,us_id,win) VALUES (?,?,1)", (summa,us_id,))
    elif lose:
        await conn.execute("INSERT INTO bets(summa,us_id,lose) VALUES (?,?,1)", (summa,us_id,))
    await conn.commit()

async def reg_user(us_id, username, ref=None):
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT * FROM users WHERE us_id=?", (us_id,))
    exist = await query.fetchone()
    if not exist:
        if not ref:
            await conn.execute("INSERT INTO users(us_id) VALUES(?)", (us_id,))
        else:
            await conn.execute("INSERT INTO users(us_id,ref) VALUES(?,?)", (us_id,ref,))
        await conn.commit()
    else:
        await conn.execute("UPDATE users SET username=? WHERE us_id=?", (username,us_id,))
        await conn.commit()

async def get_invoice():
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT * FROM settings")
    settings = await query.fetchone()
    return settings[0]

async def get_all_users():
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT * FROM users")
    users = await query.fetchall()
    return users

async def get_all_mods():
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT * FROM users WHERE moder=1")
    users = await query.fetchall()
    return users

async def change_invoice(invoice):
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT * FROM settings")
    exist = await query.fetchone()
    if exist:
        await conn.execute("UPDATE settings SET invoice_link=?", (invoice,))
    else:
        await conn.execute("INSERT INTO settings(invoice_link) VALUES (?)", (invoice,))
    await conn.commit()

async def change_max(maximum):
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT * FROM settings")
    exist = await query.fetchone()
    if exist:
        await conn.execute("UPDATE settings SET max_amount=?", (maximum,))
    else:
        await conn.execute("INSERT INTO settings(max_amount) VALUES (?)", (maximum,))
    await conn.commit()

async def change_podkrut(podkrut):
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT * FROM settings")
    exist = await query.fetchone()
    if exist:
        await conn.execute("UPDATE settings SET podkrut=?", (podkrut,))
    else:
        await conn.execute("INSERT INTO settings(podkrut) VALUES (?)", (podkrut,))
    await conn.commit()

async def get_all_users_count():
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT COUNT(*) FROM users")
    users = await query.fetchone()
    return users[0]

async def get_all_bets_summ():
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT SUM(summa) FROM bets")
    bets = await query.fetchone()
    if bets[0] is not None:
        return float(bets[0])
    else:
        return 0.0

async def get_all_bets_count():
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT COUNT(*) FROM bets")
    bets = await query.fetchone()
    if bets[0] is not None:
        return bets[0]
    else:
        return 0

async def get_all_wins_summ():
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT SUM(summa) FROM bets WHERE win=1")
    wins = await query.fetchone()
    if wins[0] is not None:
        return float(wins[0])
    else:
        return 0.0

async def get_all_wins_count():
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT COUNT(*) FROM bets WHERE win=1")
    wins = await query.fetchone()
    return wins[0]

async def get_wins_stat():
    wins_summ = await get_all_wins_summ()
    formatted_summ = f"{wins_summ:.2f}"
    wins_count = await get_all_wins_count()
    return f"~ <code>{wins_count}</code> <b>шт.</b> [~ <code>{formatted_summ}</code> <b>$</b>]"

async def get_all_loses_summ():
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT SUM(summa) FROM bets WHERE lose=1")
    loses = await query.fetchone()
    if loses[0] is not None:
        return float(loses[0])
    else:
        return 0.0

async def get_all_loses_count():
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT COUNT(*) FROM bets WHERE lose=1")
    loses = await query.fetchone()
    return loses[0]

async def get_loses_stat():
    loses_summ = await get_all_loses_summ()
    formatted_summ = f"{loses_summ:.2f}"
    loses_count = await get_all_loses_count()
    return f"~ <code>{loses_count}</code> <b>шт.</b> [~ <code>{formatted_summ}</code> <b>$</b>]"

async def end_mines(bet_id):
    conn = await aiosqlite.connect("database.db")
    await conn.execute("UPDATE bets_mines SET end=1 WHERE id=?", (bet_id,))
    await conn.commit()

async def create_mines(us_id, summa):
    conn = await aiosqlite.connect("database.db")
    bet_id = functions.generate_random_code(length=7)
    bet_id = bet_id
    await conn.execute("INSERT INTO bets_mines(id,us_id,summa) VALUES (?,?,?)", (bet_id,us_id,summa,))
    await conn.commit()
    return bet_id

async def get_stavka(bet_id):
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT * FROM bets_mines WHERE id=?", (bet_id,))
    query_data = await query.fetchone()
    stavka = query_data[2]
    return stavka

async def get_active_mines(us_id):
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT * FROM bets_mines WHERE us_id=? AND end=0", (us_id,))
    active = await query.fetchall()
    return active

async def get_bet_id(us_id):
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT * FROM mines WHERE creator_id=?", (us_id,))
    query_data = await query.fetchone()
    bet_id = query_data[10]
    return bet_id

async def get_join_date(us_id):
    conn = await aiosqlite.connect("database.db")
    query = await conn.execute("SELECT join_date FROM users WHERE us_id=?", (us_id,))
    query_data = await query.fetchone()
    join_date = query_data[0]
    return join_date

async def ban(us_id):
    conn = await aiosqlite.connect("database.db")
    await conn.execute("UPDATE users SET is_ban=1 WHERE us_id=?", (us_id,))
    await conn.commit()

async def unban(us_id):
    conn = await aiosqlite.connect("database.db")
    await conn.execute("UPDATE users SET is_ban=0 WHERE us_id=?", (us_id,))
    await conn.commit()

async def get_user(us_id):
    conn = await aiosqlite.connect("database.db")
    user = await conn.execute("SELECT * FROM users WHERE us_id=?", (us_id,))
    user = await user.fetchone()
    return user

async def edit_msg_id(msg_id):
    conn = await aiosqlite.connect("database.db")
    config = await conn.execute("SELECT * FROM msg_config")
    config = await config.fetchone()
    if config:
        await conn.execute("UPDATE msg_config SET msg_id=?", (msg_id,))
        await conn.commit()
    else:
        await conn.execute("INSERT INTO msg_config(msg_id) VALUES(?)", (msg_id,))
        await conn.commit()

async def get_msg_id():
    conn = await aiosqlite.connect("database.db")
    msg_id = await conn.execute("SELECT * FROM msg_config")
    msg_id = await msg_id.fetchone()
    if msg_id:
        return msg_id[0]

async def update_cashback(us_id, cashback):
    conn = await aiosqlite.connect("database.db")
    await conn.execute("UPDATE users SET cashback=? WHERE us_id=?", (cashback,us_id,))
    await conn.commit()

async def get_ref_count(ref):
    conn = await aiosqlite.connect("database.db")
    refs = await conn.execute("SELECT COUNT(*) FROM users WHERE ref=?", (ref,))
    refs = await refs.fetchone()
    return refs[0]

async def update_ref_balance(us_id, balance):
    conn = await aiosqlite.connect("database.db")
    await conn.execute("UPDATE users SET ref_balance=? WHERE us_id=?", (balance,us_id,))
    await conn.commit()

async def get_all_refferals(ref):
    conn = await aiosqlite.connect("database.db")
    refs = await conn.execute("SELECT * FROM users WHERE ref=?", (ref,))
    refs = await refs.fetchall()
    return refs

async def get_user_by_username(username):
    conn = await aiosqlite.connect("database.db")
    user = await conn.execute("SELECT * FROM users WHERE username=?", (username,))
    user = await user.fetchone()
    return user

async def get_settings():
    conn = await aiosqlite.connect("database.db")
    settings = await conn.execute("SELECT * FROM settings")
    settings = await settings.fetchone()
    return settings

async def add_total_ref(ref, add):
    conn = await aiosqlite.connect("database.db")
    await conn.execute("UPDATE users SET ref_total=ref_total+? WHERE us_id=?", (add,ref,))
    await conn.commit()

async def get_all_bets():
    conn = await aiosqlite.connect("database.db")
    bets = await conn.execute("SELECT * FROM bets")
    bets = await bets.fetchall()
    return bets

async def get_all_contests():
    conn = await aiosqlite.connect("database.db")
    contests = await conn.execute("SELECT * FROM contests WHERE end=0")
    contests = await contests.fetchall()
    return contests

async def update_contest(username, contest_id, top1=False, top1_summa=0, top2=False, top2_summa=0, top3=False, top3_summa=0):
    conn = await aiosqlite.connect("database.db")
    if top1:
        await conn.execute("UPDATE contests SET top1=?, top1_summa=? WHERE id=?", (username,top1_summa,contest_id,))
    if top2:
        await conn.execute("UPDATE contests SET top2=?, top2_summa=? WHERE id=?", (username,top2_summa,contest_id,))
    if top3:
        await conn.execute("UPDATE contests SET top3=?, top3_summa=? WHERE id=?", (username,top3_summa,contest_id,))
    await conn.commit()

async def set_end(contest_id):
    conn = await aiosqlite.connect("database.db")
    await conn.execute("UPDATE contests SET end=1 WHERE id=?", (contest_id,))
    await conn.commit()

async def create_contest(amount, end_date, msg_id):
    conn = await aiosqlite.connect("database.db")
    date_time_str = end_date
    date_time_obj = datetime.strptime(date_time_str, '%d.%m.%Y %H:%M')
    await conn.execute("INSERT INTO contests(summa,end_date,msg_id,top1_summa,top2_summa,top3_summa) VALUES(?,?,?,0,0,0)", (amount,date_time_obj,msg_id,))
    await conn.commit()

async def get_contest(contest_id):
    conn = await aiosqlite.connect("database.db")
    contest = await conn.execute("SELECT * FROM contests WHERE id=?", (contest_id,))
    contest = await contest.fetchone()
    return contest

async def add_moder(us_id):
    conn = await aiosqlite.connect("database.db")
    await conn.execute("UPDATE users SET moder=1 WHERE us_id=?", (us_id,))
    await conn.commit()

async def remove_moder(us_id):
    conn = await aiosqlite.connect("database.db")
    await conn.execute("UPDATE users SET moder=0 WHERE us_id=?", (us_id,))
    await conn.commit()