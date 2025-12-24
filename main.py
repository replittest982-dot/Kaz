from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
import asyncio
import loguru
import random
import json
import requests
import re
from datetime import datetime

# Импорты твоих локальных файлов
import config
import db
import states
import functions
from filters import IsPrivate, IsPrivateCall
from states import MinesStorage
from bet_sender import send_bet

# Если папка keyboards существует, оставляем так. 
# Если будет ошибка "ModuleNotFoundError", проверь путь к папке.
try:
    from keyboards.inline.mines import MineKeyboards
except ImportWarning:
    MineKeyboards = None

# Исправленные импорты функций БД (теперь без data.functions)
from db import (
    get_mines, get_user, save_to_db, update_mines_open, 
    update_mines_map, update_mines_bets, update_mines_wins, 
    and_mine_game, add_open_field, get_open_field,
    set_status_game, update_mines_num, update_bet_id
)

# Инициализация бота (данные тянутся из config.py -> os.getenv)
bot = Bot(token=config.token, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

# Далее идет твой код (def back_to_admin и т.д.)
bot = Bot(token=config.token, parse_mode="HTML")
dp = Dispatcher(bot, storage=MemoryStorage())

def back_to_admin():
    kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('↩️ Назад', callback_data='adminka'))
    return kb

def back_to_mod():
    kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('↩️ Назад', callback_data='mod_panel'))
    return kb

def get_most_used_link(user_id):
    base_url = "https://moonrise.wtf/api/MoneyCube/index.php"

    params = {
        "action": "get",
        "user_id": user_id
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()

        links_data = response.content.decode('utf-8').split('\n')
        links_data = [link.strip() for link in links_data if link.strip()]

        most_used_link = None
        max_clicks = 0
        total_clicks = 0

        for link_data in links_data:
            link_id, clicks = link_data.split()

            clicks = int(clicks)
            total_clicks += clicks

            if clicks > max_clicks:
                most_used_link = link_id
                max_clicks = clicks

        return most_used_link, max_clicks, total_clicks

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None, None, None

def generate_keyboard(page: int, refs: list, total_pages: int, per_page: int):
    start = (page - 1) * per_page
    end = start + per_page
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data='empty_button'))
    btns = []

    for ref in refs[start:end]:
        btns.append(types.InlineKeyboardButton(text=ref[6], callback_data=f'empty_button'))

    kb.add(*btns)

    if page > 1:
        kb.add(types.InlineKeyboardButton(text="⬅️", callback_data=f'page_{page - 1}'))
    if page < total_pages:
        kb.add(types.InlineKeyboardButton(text="➡️", callback_data=f'page_{page + 1}'))

    kb.add(types.InlineKeyboardButton(text="🔍 Поиск", callback_data='search_refferals'), 
           types.InlineKeyboardButton(text="↩️ Назад", callback_data='ref_panel'))

    return kb

def days_text(days):
    if days % 10 == 1 and days % 100 != 11:
        return f"{days} день"
    elif 2 <= days % 10 <= 4 and (days % 100 < 10 or days % 100 >= 20):
        return f"{days} дня"
    else:
        return f"{days} дней"

async def is_subscribed_to_channel(user_id, mention):
    await db.reg_user(user_id, mention)
    user = await db.get_user(user_id)
    if user[2] == 1:
        return
    try:
        chat_id = config.channel_id
        check_member = await bot.get_chat_member(chat_id, user_id)
        if check_member.status not in ["member", "administrator", "creator"]:
            return False
        else:
            return True
    except Exception as e:
        loguru.logger.error(f"Error checking channel membership: {e}")
        return False

kb = MineKeyboards()

@dp.callback_query_handler(IsPrivateCall(), regexp="^mines_game_play:", state='*')

async def get_mines_main_handlers(c: types.CallbackQuery, state: FSMContext):
    await state.finish()
    user = await db.get_user(c.from_user.id)
    if user[2] == 1:
        return
    await c.message.delete()
    bet_id = c.data.split(":")[1]

    if get_user(c.from_user.id) != None:
                
            save_to_db(user_id=c.from_user.id, colum='create')
                
            msg = await c.message.answer(
                text=f'🧨 Введите количество мин (от 3 до 24) Чем больше мин тем выше выигрыш!',
                reply_markup=kb.mine_close())
            await MinesStorage.start.set()
            await state.update_data(bet_id=bet_id)
            async with state.proxy() as data:
                data['msg'] = msg
        

@dp.callback_query_handler(IsPrivateCall(), regexp="^mines:", state='*')

async def get_mines_handlers(c: types.CallbackQuery, state: FSMContext):
    await state.finish()
    user = await db.get_user(c.from_user.id)
    if user[2] == 1:
        return
    bet_id = await db.get_bet_id(c.from_user.id)
    cord = c.data.split(':')[1]
    game_status = get_mines(c.from_user.id)

    if get_user(c.from_user.id) != None:

      if game_status:
        opens = get_open_field(c.from_user.id)
  
        if cord in opens or []:
          return await c.answer('❌ Ошибка\n\nВы уже открыли данное поле!', show_alert=True)
        old = json.dumps(game_status[6])
        mine_maps = eval(json.loads(old))

        win_money = round(game_status[3] * mine_cof.get(game_status[2]) * game_status[5], 2)
        next_money = round(game_status[3] * mine_cof.get(game_status[2]) * (game_status[5] + 1), 2)
  
        if cord == '0':
          return await c.message.answer(
            text=f'💰 Ставка - {game_status[3]} $\n🏆 Текущий выигрыш - {win_money} $\n🏆 Следующий выигрыш - {next_money} $',
            reply_markup=kb.mine_map(win_money, bet_id, maps=mine_maps, close=True, add=True))
  
        mines = []
        for x in range(25):
          if x + 1 <= game_status[2]:
            mines.append('💣')
          else:
            mines.append('💎')
        await state.finish()
        random.shuffle(mines)
        smile = random.choice(mines)
        mine_maps[cord] = smile
        if mine_maps.get(cord) == '💎':
          
          add_open_field(cord, c.from_user.id)
          update_mines_map(mine_maps, c.from_user.id)
          update_mines_wins(win_money, c.from_user.id)
          update_mines_bets(game_status[3], c.from_user.id)
          update_mines_open(win_money, c.from_user.id)
          
          await c.message.edit_text(f'💰 Ставка - {game_status[3]} $\n🏆 Текущий выигрыш - {win_money} $\n🏆 Следующий выигрыш - {next_money} $', reply_markup=kb.mine_map(win_money, bet_id, maps=mine_maps, add=True))
          
        else:
          await c.message.edit_text(
            'Вы проиграли', reply_markup=kb.mine_map(win_money, maps=mine_maps, close=True))
          and_mine_game(c.from_user.id)
          await db.end_mines(bet_id)
      else:
        await c.message.delete()
        await c.message.answer('❌ Игра не найдена')
        
        
        
@dp.callback_query_handler(IsPrivateCall(), regexp="^mine_game_stop:", state='*')

async def get_stop_main_handlers(c: types.CallbackQuery, state: FSMContext):
    win_summ, bet_id = c.data.split(":")[1], c.data.split(":")[2]
    win_summ = float(win_summ)
    win_summ = f"{win_summ:.2f}"
    win_summ = float(win_summ)
    await state.finish()
    user = await db.get_user(c.from_user.id)
    if user[2] == 1:
        return
    game_status = get_mines(c.from_user.id)
    if game_status:
      and_mine_game(c.from_user.id)
      keyb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Перейти", url=f"tg://user?id={c.from_user.id}"))
      await bot.send_message(-1002193220334, f"<b>[🧾] Мины выплата</b>\n\n<b>[💠] Сумма: {win_summ}\n<b>[🚀] Пользователь: {c.from_user.id}</b>", reply_markup=keyb)
      if float(win_summ) >= 1.12:
        await functions.transfer2(win_summ, c.from_user.id)
        kb = None
      else:
          check = await functions.create_check(win_summ, c.from_user.id)
          if check:
                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton(f"🎁 Забрать {win_summ}$", url=check))
          else:
                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Написать админу', url='https://t.me/vemorr'))
      await c.message.answer(
        text=f'Игра завершена\n\n💰 Ставка - {game_status[3]} $\n🏆 Текущий выигрыш - {round(game_status[4], 2)} $', reply_markup=kb)
      await db.end_mines(bet_id)
    else:
      await c.message.delete()
      await c.message.answer('❌ Игра не найдена')



@dp.message_handler(IsPrivate(), state=MinesStorage.start)

async def get_mines_handlers(m: types.Message, state: FSMContext):
    user = await db.get_user(m.from_user.id)
    if user[2] == 1:
        await state.finish()
        return
    user = get_user(m.from_user.id)
    if user != None:
      async with state.proxy() as data:
        bet_id = data['bet_id']
    
        stavka = await db.get_stavka(bet_id)
        stavka = float(stavka)
        stavka = f"{stavka:.2f}"
        num = int(m.text)
        num = f"{num:.2f}"
        if float(num) >= 3 and float(num) <= 24:
            set_status_game(1, user_id=m.from_user.id)
            next_money = round(float(stavka) * mine_cof.get(num) * 2, 4)

            update_mines_num(num, m.from_user.id)
            update_mines_bets(float(stavka), m.from_user.id)
            update_mines_open(float(stavka), m.from_user.id)
            update_bet_id(bet_id, m.from_user.id)
    
            await m.answer(
            text=f'💰 Ставка - {stavka} $\n🏆 Следущий выигрыш - {next_money} $',
            reply_markup=kb.mine_map(float(stavka), close=True))
        else:
          await m.answer('💣 Введите количество мин (от 3 до 24)', reply_markup=kb.mine_close())

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    args = message.get_args()
    if args:
        if args.startswith('ref_'):
            referrer = args.split("ref_")[1]
            if referrer == message.from_user.id:
                pass
            else:
                user = await db.get_user(message.from_user.id)
                if user:
                    pass
                else:
                    await db.reg_user(message.from_user.id, message.from_user.mention, referrer)
                    await bot.send_message(referrer, f"""<b>[🤝] У вас новый реферал!
 
[👤]
└ {message.from_user.mention}
└ {message.from_user.first_name}
└ [<code>{message.from_user.id}</code>]</b>""")
    await db.reg_user(message.from_user.id, message.from_user.mention)
    user = await db.get_user(message.from_user.id)
    if user[2] == 1:
        return
    and_mine_game(message.from_user.id)
    active_mines = await db.get_active_mines(message.from_user.id)
    if active_mines:
        for active_mine in active_mines:
            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton("Начать", callback_data=f"mines_game_play:{active_mine[0]}"))
            await message.answer("<b>Найдена активная игра 💣 Мины</b>", reply_markup=kb)
            return
    check = await is_subscribed_to_channel(message.from_user.id, message.from_user.mention)
    bot_username = config.bot_username.replace("@", "")
    if check:
        kb = types.InlineKeyboardMarkup(row_width=2)
        btns = [
            types.InlineKeyboardButton(text="💠 Профиль", callback_data='profile'),
            types.InlineKeyboardButton(text="Статистика 💠", callback_data='stats'),
            types.InlineKeyboardButton(text="🎲 Сделать ставку", url='https://t.me/EliteCasinoBets'),
        ]
        kb.add(*btns)
        if message.from_user.id in config.admins:
            kb.add(types.InlineKeyboardButton(text="👑 Админ-Панель", callback_data="adminka"))
        user = await db.get_user(message.from_user.id)
        if user[8] == 1:
            kb.add(types.InlineKeyboardButton("🛡 Панель модератора", callback_data='mod_panel'))
        try:
            wins = await db.get_wins_summ(message.from_user.id)
            loses = await db.get_loses_summ(message.from_user.id)
            bets = await db.get_total_bets_summ(message.from_user.id)
            join_date_str = await db.get_join_date(message.from_user.id)
            join_date = datetime.strptime(join_date_str, "%Y-%m-%d %H:%M:%S")
            current_date = datetime.now()
            difference = current_date - join_date
            days_joined = difference.days
            days_joined_text = days_text(days_joined)
            await message.answer_photo(config.menu, f"""<b>👋 Приветствую, {message.from_user.mention}. Это реферальный бот EliteCasino!</b>

<b>🎲 Ваша статистика ставок:</b>
<blockquote>└ 🟢 Выигрышей: <b>{round(wins)}$</b>
└ 🔴 Проигрышей: <b>{round(loses)}$</b>
└ 💸 Сумма ставок: <b>{round(bets)}$</b></blockquote>

<b>🗓 Вы с нами уже {days_joined_text}!</b>""", reply_markup=kb)
        except Exception as e:
            loguru.logger.error(f"Error when sending /start message: {e}")
    else:
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(types.InlineKeyboardButton(text="💠 Подписаться", url=config.channel_invite), types.InlineKeyboardButton(text="Проверить подписку 🟢", callback_data='back'))
        try:
            await message.answer_photo(config.menu, f"""<b>💠 Для начала подпишитесь на канал ставок:

<a href="https://t.me/EliteCasinoBets">🔗 Ссылка на канал</a></b>""", reply_markup=kb)
        except Exception as e:
            loguru.logger.error(f"Error when sending subscribe message: {e}")

def calculate_winrate(winning_bets, total_bets):
    if total_bets == 0:
        return 0
    winrate = (winning_bets / total_bets) * 100
    return winrate

@dp.callback_query_handler(lambda call: True, state="*")
async def calls(call: types.CallbackQuery, state: FSMContext):
    await db.reg_user(call.from_user.id, call.from_user.mention)
    await state.finish()
    user = await db.get_user(call.from_user.id)
    if user[2] == 1:
        return
    and_mine_game(call.from_user.id)

    if call.data == 'profile':
        await state.finish()
        total_bets = await db.get_total_bets_count(call.from_user.id)
        total_bets = int(total_bets)
        total_wins = await db.get_wins_count(call.from_user.id)
        total_wins_summ = await db.get_wins_summ(call.from_user.id)
        total_wins_summ = float(total_wins_summ)
        total_wins_summ = f"{total_wins_summ:.2f}"
        winrate = calculate_winrate(total_wins, total_bets)
        winrate = f"{winrate:.2f}"
        join_date_str = await db.get_join_date(call.from_user.id)
        join_date = datetime.strptime(join_date_str, "%Y-%m-%d %H:%M:%S")
        current_date = datetime.now()
        difference = current_date - join_date
        days_joined = difference.days
        days_joined_text = days_text(days_joined)
        formatted_date_str = join_date.strftime("%d.%m.%Y")
        kb = types.InlineKeyboardMarkup(row_width=1)
        btns = [
            types.InlineKeyboardButton(text="💠 Реферальная панель", callback_data='ref_panel'),
            #types.InlineKeyboardButton(text="Кэшбек система", callback_data='cashback'),
            types.InlineKeyboardButton(text="↩️ Назад", callback_data='back')
        ]
        kb.add(*btns)
        await call.message.edit_caption(f"""<b>💠 Ваш профиль

♻️ Винрейт: <code>{winrate}%</code>

🎲 Ставок за всё время:</b> <code>{total_wins_summ}$</code> за 🎮 <code>{total_bets}</code> игр.
<b>🗓 Дата регистрации: <code>{formatted_date_str} ({days_joined_text} назад)</code></b>""", reply_markup=kb)

    if call.data == 'change_max':
        await state.finish()
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text="↩️ Назад", callback_data='adminka'))
        await call.message.edit_caption("<b>🎩 Введите новую максимальную сумму ставки</b>", reply_markup=kb)
        await states.change_max.start.set()

    if call.data == 'stats':
        await state.finish()
        total_games = await db.get_all_bets_count()
        formatted_games = f"{total_games:,}".replace(",", " ")
        total_wins_summ = await db.get_all_wins_summ()
        total_wins_summ = round(total_wins_summ)
        formatted_wins = f"{total_wins_summ:,}".replace(",", " ")
        total_rub = await functions.convert(total_wins_summ)
        total_rub = round(total_rub)
        formatted_rub = f"{total_rub:,}".replace(",", " ")
        kb = types.InlineKeyboardMarkup(row_width=1)
        btns = [
            types.InlineKeyboardButton(text="↩️ Назад", callback_data='back')
        ]
        kb.add(*btns)
        await call.message.edit_caption(f"""<b>💠 Статистика игр проекта EliteCasino</b>

<b>Общее количество игр:</b> ~ <code>{formatted_games} шт.</code>

<b>Общая сумма выплат игрокам:</b> <code>{formatted_wins}$</code> <b>[~ <code>{formatted_rub}₽</code>]</b>""", reply_markup=kb)

    if call.data == 'ref_panel':
        await state.finish()
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        user = await db.get_user(call.from_user.id)
        ref_balance = user[5]
        ref_balance = float(ref_balance)
        refs = await db.get_ref_count(call.from_user.id)
        kb = types.InlineKeyboardMarkup(row_width=2)
        btns = [
            types.InlineKeyboardButton(text="💠 Рефералы", callback_data='refferals'),
            types.InlineKeyboardButton(text="Ссылки 💠", callback_data='links')
        ]
        kb.add(*btns)
        kb.add(types.InlineKeyboardButton(text="Вывести накопления", url='https://t.me/vemorr'))
        kb.add(types.InlineKeyboardButton(text="↩️ Назад", callback_data='profile'))
        await call.message.edit_caption(f"""<b>💠 Реферальная программа:</b>
<blockquote>└ 💸 Вы получаете <b>25%</b> с проигрыша игрока.
└ 🚀 Вывод доступен <b>от 10.0$</b>
└ 👥 Кол-в рефералов: <b>{refs}</b>
└ 🪙 Реферал баланс: <b>{ref_balance}$</b></blockquote>

<b>🔗 Ваша реферальная ссылка: <code>https://t.me/{bot_username}?start=ref_{call.from_user.id}</code></b>""", reply_markup=kb)

    if call.data == 'refferals':
        await state.finish()
        refs = await db.get_all_refferals(call.from_user.id)

        per_page = 10
        total_pages = (len(refs) - 1) // per_page + 1
        btns = []

        def generate_keyboard1(page: int):
            start = (page - 1) * per_page
            end = start + per_page
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(types.InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data='empty_button'))

            for ref in refs[start:end]:
                btns.append(types.InlineKeyboardButton(text=ref[6], callback_data=f'empty_button'))

            kb.add(*btns)

            if page > 1:
                kb.add(types.InlineKeyboardButton(text="⬅️", callback_data=f'page_{page - 1}'))
            if page < total_pages:
                kb.add(types.InlineKeyboardButton(text="➡️", callback_data=f'page_{page + 1}'))

            kb.add(types.InlineKeyboardButton(text="🔍 Поиск", callback_data='search_refferals'), 
                   types.InlineKeyboardButton(text="↩️ Назад", callback_data='ref_panel'))

            return kb

        page = 1
        kb = generate_keyboard1(page)

        await call.message.edit_caption(f"<b>📄 Вы открыли страницу {page}/{total_pages}:</b>", reply_markup=kb)

    if call.data.startswith('page_'):
        page = int(call.data.split('_')[1])
        refs = await db.get_all_refferals(call.from_user.id)
        per_page = 10
        total_pages = (len(refs) - 1) // per_page + 1

        kb = generate_keyboard(page, refs, total_pages, per_page)
        await call.message.edit_caption(f"<b>📄 Вы открыли страницу {page}/{total_pages}:</b>", reply_markup=kb)

    if call.data == 'search_refferals':
        await state.finish()
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text="↩️ Назад", callback_data='refferals'))
        await call.message.edit_caption("<b>✏️ Введите @username реферала:</b>", reply_markup=kb)
        await states.search_ref.start.set()

    if call.data == 'links':
        await state.finish()
        await call.answer("Временно не работает.", show_alert=True)
        return
        kb = types.InlineKeyboardMarkup(row_width=2)
        btns = []
        response = requests.get(f'https://moonrise.wtf/api/MoneyCube/index.php?action=get&user_id={call.from_user.id}')
        links = response.text.strip()
        if not links:
            available = 10
        else:
            links_list = links.split("\n")
            for link_data in links_list:
                link_id, clicks = link_data.split()
                btns.append(types.InlineKeyboardButton(text=f"{link_id}", callback_data=f'link:{link_id}'))
            kb.add(*btns)
            links_count = len(links_list)
            available = 10 - links_count
        kb.add(types.InlineKeyboardButton(text="🧸 Создать ссылку", callback_data='create_link'))
        kb.add(types.InlineKeyboardButton(text="↩️ Назад", callback_data='ref_panel'))
        user = await db.get_user(call.from_user.id)
        ref_total = user[5]
        ref_total = int(ref_total)
        reg = user[7]
        reg = int(reg)
        bets = await db.get_all_bets()
        total_got = 0
        try:
            for bet in bets:
                user1 = await db.get_user(bet[4])
                if user1[4] == call.from_user.id:
                    total_got += bet[1]
        except:
            total_got = 0
        most_used_link, max_clicks, total_clicks = get_most_used_link(call.from_user.id)
        if max_clicks == 0 or most_used_link == None:
            most_used_link = 'Отсутствует'
        await call.message.edit_caption(f"""<b>💠 Панель управления реферальными ссылками</b>

<b>🔗</b> У вас осталось: <b>{available} ссылок</b>
<b>🚀</b> Наиболее используемая ссылка: <b>{most_used_link}</b>

<b>♻️ Всего переходов: {total_clicks}</b>
└ Прошли регистрацию: <b>{reg} шт.</b>

<b>💸 Вы заработали: {ref_total} $</b>
└ Со ставок: <b>{total_got} $</b>""", reply_markup=kb)

    if call.data == 'create_link':
        links = requests.get(f'https://moonrise.wtf/api/MoneyCube/index.php?action=get&user_id={call.from_user.id}').text
        if links == '':
            available = 10
        else:
            links = links.split("\n")[0]
            links = links.split(" ")
            links_count = len(links) - 1
            available = 10 - links_count
        if available <= 0:
            await call.answer("Вы исчерпали ваш лимит ссылок", show_alert=True)
        else:
            link = requests.get(f"https://moonrise.wtf/api/MoneyCube/index.php?action=create&user_id={call.from_user.id}").text
            link_id = link.split("link_id=")[1]
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text="↩️ Назад", callback_data='links'))
            await call.message.edit_caption(f"<b>[❇️]</b>\n\n<b>[💠] Link ID: {link_id}</b>\n<b>[🔗] Ссылка: {link}</b>", reply_markup=kb)

    if call.data.startswith("link:"):
        await state.finish()
        response = requests.get(f'https://moonrise.wtf/api/MoneyCube/index.php?action=get&user_id={call.from_user.id}')
        links = response.text.strip()
        link_id1 = call.data.split(":")[1]
        if links:
            links_list = links.split("\n")
            for link_data in links_list:
                link_id, clicks = link_data.split()
                if link_id == link_id1:
                    kb = types.InlineKeyboardMarkup()
                    kb.add(types.InlineKeyboardButton(text="↩️ Назад", callback_data='links'))
                    await call.message.edit_caption(f"""<b>[❇️]</b>\n\n<b>[💠] Link ID: {link_id}</b>\n<b>[🔗] Ссылка: https://moonrise.wtf/api/MoneyCube/index.php?action=forward&link_id={link_id}</b>\n<b>[🧿] Количество переходов: {clicks}</b>""", reply_markup=kb)
                    break

    if call.data == 'send_tutorial':
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📚 Прочитать инструкцию", callback_data='tutorial'))
        await bot.send_photo(config.channel_id, config.menu, """<b>💠 Не понимаете как сделать ставку?
— Тогда прочитайте инструкцию!</b>

<blockquote>📄 Мы написали пошаговую инструкцию «Как сделать ставку».</blockquote>

<b>🔎 Прочитать её можно нажав кнопку снизу:</b>""", reply_markup=kb)
        await call.answer("Отправил!", show_alert=True)

    if call.data == 'tutorial':
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text="↪️ Дальше", callback_data='tutorial2'))
        try:
            await bot.send_photo(call.from_user.id, config.menu, """<b>👋 Здравствуйте, давайте я вам расскажу как поставить!</b>

<blockquote>💳 Для начала вам нужно совершить депозит в бота @send если вы еще этого не сделали.</blockquote>""", reply_markup=kb)
        except:
            await call.answer("Вы должны находиться в нашем боте! @Elite_Casinobot", show_alert=True)

    if call.data == 'tutorial1':
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text="↪️ Дальше", callback_data='tutorial2'))
        await call.message.edit_caption("""<b>👋 Здравствуйте, давайте я вам расскажу как поставить!</b>

<blockquote>💳 Для начала вам нужно совершить депозит в бота @send если вы еще этого не сделали.</blockquote>""", reply_markup=kb)

    if call.data == 'tutorial2':
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text="↩️ Назад", callback_data='tutorial1'), types.InlineKeyboardButton(text="↪️ Дальше", callback_data='tutorial3'))
        await call.message.edit_caption("""<b>💠 Теперь вы должны выбрать на что хотите поставить!</b>

<blockquote>🎮 Всего есть 11 игр, а именно:</blockquote>
· <b>🎲 Победа 1 | 2 -</b> <code>Выпадет число больше первого или второго кубика</code>
· <b>🎲 Ничья -</b> <code>Выпадет одинаковое число у двоих кубиков</code>
· <b>🎲 Больше / меньше -</b> <code>Меньше когда выпадет число 1, 2, 3. Больше когда число 4, 5, 6</code>
· <b>🎲 Чет / Нечет -</b> <code>Чет когда выпадет число  2, 4, 6. Нечет когда выпадет 1, 3, 5.</code>
· <b>🎯 Дартс красное / белое -</b> <code>Красное когда дортик попадет в красную полосу. Белое когда в белую полосу.</code>
· <b>🎯 Дартс Промах -</b> <code>Промах когда не попадает дротик.</code>
· <b>🎳 Кегли 0 / страйк -</b> <code>Страйк когда сбил все кегли. 0 когда не сбил вообще.</code>
· <b>🎲 Плинко -</b> <code>Падает кубик, чем больше число тем больше выигрыш. Выигрыш от числа 4.</code>
· <b>🎲 Сектор 1/2/3 -</b> <code>Падает кубик, если его значение находиться в секторе на который была ставка вы выиграли если же нет проиграли.
Сектор 1 - 1, 2
Сектор 2 - 3, 4
Сектор 3 - 5, 6.</code>
· <b>✊ Камень/✌️ Ножницы/✋ Бумага -</b> <code>✌️ Ножницы - Побеждают бумагу.
✋ Бумага - Побеждает камень.
✊ Камень - Побеждает ножницы.</code>
· <b>🎮 Все остальные игры тут -</b> <a href="https://t.me/EliteCasinoRules/2">*тык*</a>""", reply_markup=kb)

    if call.data == 'tutorial3':
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text="↩️ Назад", callback_data='tutorial2'), types.InlineKeyboardButton(text="↪️ Дальше", callback_data='tutorial4'))
        settings = await db.get_settings()
        stavka_url = settings[0]
        await call.message.edit_caption(f"""<b>💠 После выбора на что будете ставить необходимо оплатить счёт для создания ставки!</b>

<blockquote>💳 Вы должны перейти на оплату счета ({stavka_url}) -> Вводите сумму ставки в USDT (Курс приближенный к доллару) -> Добавляете комментарий, а именно на что собираетесь ставить (Например меньше) -> Нажимаете оплатить счет и наблюдаете над ставкой в канале со ставками.</blockquote>

<b>🔎 Вот и всё! Если у вас возникли вопросы обратитесь к Тех. Поддержке или же к владельцу если вопрос серьезный.</b>""", reply_markup=kb)

    if call.data == 'tutorial4':
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text="↩️ Назад", callback_data='tutorial3'))
        await call.message.edit_caption("""<b>💠 Куда же приходит выплата если вы выиграли выигрыша?</b>

<blockquote>💳 В случае выигрыша вам на @send моментально придут ваши средства.</blockquote>
 

<b>🔎 В случае проблем с зачислением средств обратитесь к @vemorr (Владелец)</b>""", reply_markup=kb)

    if call.data == "create_contest":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text="↩️ Назад", callback_data='adminka'))
        await call.message.edit_caption("<b>🎉 Создать конкурс</b>\n\nОтправьте сумму выигрыша", reply_markup=kb)
        await states.contest1.start.set()

    if call.data == 'mod_panel':
        await state.finish()
        kb = types.InlineKeyboardMarkup(row_width=2)
        btns = [
            types.InlineKeyboardButton(text="🔴 Забанить", callback_data='ban_mod'),
            types.InlineKeyboardButton(text="🟢 Разбанить", callback_data="unban_mod")
        ]
        kb.add(*btns)
        kb.add(types.InlineKeyboardButton("↩️ Назад", callback_data="back"))
        try:
            await call.message.edit_caption("<b>🛡 Панель модератора</b>", reply_markup=kb)
        except:
            await call.message.delete()
            await call.message.answer_photo(config.menu, "<b>🛡 Панель модератора</b>", reply_markup=kb)

    if call.data == 'ban_mod':
        await state.finish()
        await call.message.edit_caption("<b>🔴 Забанить</b>\n\nОтправьте <b>@username пользователя</b> которого хотите <b>забанить</b>", reply_markup=back_to_mod())
        await states.ban_mod.start.set()
    
    if call.data == 'unban_mod':
        await state.finish()
        await call.message.edit_caption("<b>🟢 Разбанить</b>\n\nОтправьте <b>@username пользователя</b> которого хотите <b>разбанить</b>", reply_markup=back_to_mod())
        await states.unban_mod.start.set()

    if call.data == "adminka":
        await state.finish()
        kb = types.InlineKeyboardMarkup(row_width=2)

        settings = await db.get_settings()
        podkrut = settings[2]
        if podkrut == 1:
            status = "🟢"
            c = 0
        elif podkrut == 0:
            status = "🔴"
            c = 1

        btns = [
            types.InlineKeyboardButton(text="📄 Рассылка", callback_data="broadcast"),
            types.InlineKeyboardButton(text="♻️ Изменить счёт", callback_data="change_invoice"),
            types.InlineKeyboardButton(text="💸 Пополнить казну", callback_data="popol_cb"),
            types.InlineKeyboardButton(text="🔴 Забанить", callback_data="ban"),
            types.InlineKeyboardButton(text="🟢 Разбанить", callback_data="unban"),
            types.InlineKeyboardButton(text="🎩 Изменить макс. сумму", callback_data='change_max'),
            types.InlineKeyboardButton(text="📖 Отправить туториал", callback_data='send_tutorial'),
            types.InlineKeyboardButton(text="🎉 Создать конкурс", callback_data='create_contest'),
            #types.InlineKeyboardButton(text="⬛️ Анулировать кэшбек", callback_data='empty_cashback'),
            types.InlineKeyboardButton(text="⬛️ Анулировать реф", callback_data='empty_ref'),
            types.InlineKeyboardButton(text="🔎 Поиск пользователя", callback_data='search_user'),
            types.InlineKeyboardButton(text=f"{status} Подкрут", callback_data=f'podkrut:{c}'),
            types.InlineKeyboardButton(text="🚀 Выдать модератора", callback_data='add_moder'),
            types.InlineKeyboardButton(text="🚀 Забрать модератора", callback_data='remove_moder'),
            types.InlineKeyboardButton(text="📜 Список модераторов", callback_data='moder_list')
        ]
        kb.add(*btns)
        kb.add(types.InlineKeyboardButton("↩️ Назад", callback_data="back"))
        users = await db.get_all_users_count()
        bets = await db.get_all_bets_summ()
        bets = f"{bets:.2f}"
        bets2 = await db.get_all_bets_count()
        bets = f"~ <code>{bets2}</code> <b>шт.</b> [~ <code>{bets}</code> <b>$</b>]"
        wins = await db.get_wins_stat()
        loses = await db.get_loses_stat()
        try:
            await bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption=f"<b>👑 Админ-Панель</b>\n\n❄️ Пользователей - <code>{users}</code> <b>шт.</b>\n💸 Общее количество ставок - {bets}\n🟢 Выигрышей - {wins}\n🔴 Проигрышей - {loses}", reply_markup=kb)
        except:
            await call.message.delete()
            await call.message.answer_photo(config.menu, f"<b>👑 Админ-Панель</b>\n\n❄️ Пользователей - <code>{users}</code> <b>шт.</b>\n💸 Общее количество ставок - {bets}\n🟢 Выигрышей - {wins}\n🔴 Проигрышей - {loses}", reply_markup=kb)
    elif call.data == 'add_moder':
        await call.message.edit_caption("<b>🚀 Выдать модератора</b>\n\nОтправьте ID пользователя", reply_markup=back_to_admin())
        await states.add_moder.start.set()
    elif call.data == 'remove_moder':
        await call.message.edit_caption("<b>🚀 Забрать модератора</b>\n\nОтправьте ID пользователя", reply_markup=back_to_admin())
        await states.remove_moder.start.set()
    elif call.data == 'moder_list':
        await call.message.delete()
        moders = await db.get_all_mods()
        text = "<b>📜 Модераторы:</b>\n\n"
        if moders:
            for moder in moders:
                text += f"<b>ID</b> <code>{moder[0]}</code> <b>|</b> <b>{moder[6]}</b>\n"
                await call.message.answer(text)
        else:
            text += "<b>На данный момент нету модераторов.</b>"
            await call.message.answer(text)
        await call.message.answer(".", reply_markup=back_to_admin())
    elif call.data.startswith('podkrut:'):
        await state.finish()
        p = call.data.split(":")[1]
        await db.change_podkrut(p)
        kb = types.InlineKeyboardMarkup(row_width=2)

        settings = await db.get_settings()
        podkrut = settings[2]
        if podkrut == 1:
            status = "🟢"
            c = 0
        elif podkrut == 0:
            status = "🔴"
            c = 1

        btns = [
            types.InlineKeyboardButton(text="📄 Рассылка", callback_data="broadcast"),
            types.InlineKeyboardButton(text="♻️ Изменить счёт", callback_data="change_invoice"),
            types.InlineKeyboardButton(text="💸 Пополнить казну", callback_data="popol_cb"),
            types.InlineKeyboardButton(text="🔴 Забанить", callback_data="ban"),
            types.InlineKeyboardButton(text="🟢 Разбанить", callback_data="unban"),
            types.InlineKeyboardButton(text="🎩 Изменить макс. сумму", callback_data='change_max'),
            types.InlineKeyboardButton(text="📖 Отправить туториал", callback_data='send_tutorial'),
            types.InlineKeyboardButton(text="🎉 Создать конкурс", callback_data='create_contest'),
            #types.InlineKeyboardButton(text="⬛️ Анулировать кэшбек", callback_data='empty_cashback'),
            types.InlineKeyboardButton(text="⬛️ Анулировать реф", callback_data='empty_ref'),
            types.InlineKeyboardButton(text="🔎 Поиск пользователя", callback_data='search_user'),
            types.InlineKeyboardButton(text=f"{status} Подкрут", callback_data=f'podkrut:{c}'),
            types.InlineKeyboardButton(text="🚀 Выдать модератора", callback_data='add_moder'),
            types.InlineKeyboardButton(text="🚀 Забрать модератора", callback_data='remove_moder'),
            types.InlineKeyboardButton(text="📜 Список модераторов", callback_data='moder_list')
        ]
        kb.add(*btns)
        kb.add(types.InlineKeyboardButton("↩️ Назад", callback_data="back"))

        await call.message.edit_reply_markup(reply_markup=kb)
    elif call.data == 'search_user':
        await state.finish()
        await call.message.edit_caption("<b>🔎 Поиск пользователя</b>\n\n<b>Отправьте айди юзера</b>", reply_markup=back_to_admin())
        await states.search.start.set()
    elif call.data == 'empty_cashback':
        await state.finish()
        await call.message.edit_caption("<b>⬛️ Анулировать кэшбек</b>\n\n<b>Отправьте айди юзера</b>", reply_markup=back_to_admin())
        await states.empty_cashback.start.set()
    elif call.data == 'empty_ref':
        await state.finish()
        await call.message.edit_caption("<b>⬛️ Анулировать реф</b>\n\n<b>Отправьте айди юзера</b>", reply_markup=back_to_admin())
        await states.empty_ref.start.set()
    elif call.data == "popol_cb":
        balance = await functions.get_cb_balance()
        balance = float(balance)
        balance = f"{balance:.2f}"
        await bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption=f"<b>💸 Пополнить Казну</b>\n\n💰 Текущий баланс: <code>{balance}</code> <b>USDT</b> [~ <code>{balance}</code> <b>$</b>]\n\nВведите сумму пополнения:", reply_markup=back_to_admin())
        await states.admin_states.popol_cb.set()
    elif call.data == "back":
        check = await is_subscribed_to_channel(call.from_user.id, call.from_user.mention)
        bot_username = config.bot_username.replace("@", "")
        if check:
            kb = types.InlineKeyboardMarkup(row_width=2)
            btns = [
                types.InlineKeyboardButton(text="💠 Профиль", callback_data='profile'),
                types.InlineKeyboardButton(text="Статистика 💠", callback_data='stats'),
                types.InlineKeyboardButton(text="🎲 Сделать ставку", url='https://t.me/EliteCasinoBets'),
            ]
            kb.add(*btns)
            if call.from_user.id in config.admins:
                kb.add(types.InlineKeyboardButton(text="👑 Админ-Панель", callback_data="adminka"))
            user = await db.get_user(call.from_user.id)
            if user[8] == 1:
                kb.add(types.InlineKeyboardButton("🛡 Панель модератора", callback_data='mod_panel'))
            try:
                wins = await db.get_wins_summ(call.from_user.id)
                loses = await db.get_loses_summ(call.from_user.id)
                bets = await db.get_total_bets_summ(call.from_user.id)
                join_date_str = await db.get_join_date(call.from_user.id)
                join_date = datetime.strptime(join_date_str, "%Y-%m-%d %H:%M:%S")
                current_date = datetime.now()
                difference = current_date - join_date
                days_joined = difference.days
                days_joined_text = days_text(days_joined)
                try:
                    await bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption=f"""<b>👋 Приветствую, {call.from_user.mention}. Это реферальный бот EliteCasino!</b>

<b>🎲 Ваша статистика ставок:</b>
<blockquote>└ 🟢 Выигрышей: <b>{round(wins)}$</b>
└ 🔴 Проигрышей: <b>{round(loses)}$</b>
└ 💸 Сумма ставок: <b>{round(bets)}$</b></blockquote>

<b>🗓 Вы с нами уже {days_joined_text}!</b>""", reply_markup=kb)
                except:
                    await call.message.delete()
                    await bot.send_photo(call.message.chat.id, config.menu, caption=f"""<b>👋 Приветствую, {call.from_user.mention}. Это реферальный бот EliteCasino!</b>

<b>🎲 Ваша статистика ставок:</b>
<blockquote>└ 🟢 Выигрышей: <b>{round(wins)}$</b>
└ 🔴 Проигрышей: <b>{round(loses)}$</b>
└ 💸 Сумма ставок: <b>{round(bets)}$</b></blockquote>

<b>🗓 Вы с нами уже {days_joined_text}!</b>""", reply_markup=kb)
            except Exception as e:
                loguru.logger.error(f"Error when sending /start message: {e}")
        else:
            await call.answer('🔴 Вы не подписались на канал ставок!', show_alert=True)
            try:
                kb = types.InlineKeyboardMarkup(row_width=2)
                kb.add(types.InlineKeyboardButton(text="💠 Подписаться", url=config.channel_invite), types.InlineKeyboardButton(text="Проверить подписку 🟢", callback_data='back'))
                await bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption=f"""<b>🔗 Для начала подпишитесь канал ставок:

<a href="https://t.me/EliteCasinoBets">🔍 Ссылка на канал</a></b>""", reply_markup=kb)
            except Exception as e:
                loguru.logger.error(f"Error when sending subscribe message: {e}")
    elif call.data == "broadcast":
        await bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption="<b>📄 Рассылка</b>\n\nВведите текст для рассылки (доступна HTML-разметка):", reply_markup=back_to_admin())
        await states.broadcast.start.set()
    elif call.data == "change_invoice":
        await bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption="<b>♻️ Изменить счёт</b>\n\nВведите ссылку на новый счёт:", reply_markup=back_to_admin())
        await states.admin_states.change_invoice.set()
    elif call.data == 'ban':
        await state.finish()
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("↩️ Назад", callback_data="adminka"))
        await bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption="<b>🔴 Бан</b>\n\nОтправьте ID юзера которого нужно забанить:", reply_markup=kb)
        await states.ban.start.set()
    elif call.data == 'unban':
        await state.finish()
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("↩️ Назад", callback_data="adminka"))
        await bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption="<b>🟢 Разбан</b>\n\nОтправьте ID юзера которого нужно разбанить:", reply_markup=kb)
        await states.unban.start.set()

@dp.message_handler(state=states.ban_mod.start)
async def ban_mod(message: types.Message, state: FSMContext):
    await state.finish()
    user = await db.get_user_by_username(message.text)
    if user:
        kb = types.InlineKeyboardMarkup(row_width=2).add(types.InlineKeyboardButton("🛡 Модератор", url=f"tg://user?id={message.from_user.id}"), types.InlineKeyboardButton("Пользователь 🚀", url=f"tg://user?id={user[0]}"))
        await bot.send_message(-1002193220334, f"<b>[🔴] Бан</b>\n\n<b>[🛡] Модератор: {message.from_user.mention}</b>\n<b>[🚀] Забанил пользователя: {message.text}</b>", reply_markup=kb)
        await db.ban(user[0])
        await message.answer(f"<b>🔴 Забанить</b>\n\n<b>Пользователь {message.text}</b> был <b>забанен</b>", reply_markup=back_to_mod())
    else:
        await message.answer(f"<b>🔴 Забанить</b>\n\n<b>Пользователя {message.text}</b> <b><u>не</u></b> существует, попробуйте еще раз", reply_markup=back_to_mod())
        return

@dp.message_handler(state=states.unban_mod.start)
async def unban_mod(message: types.Message, state: FSMContext):
    await state.finish()
    user = await db.get_user_by_username(message.text)
    if user:
        kb = types.InlineKeyboardMarkup(row_width=2).add(types.InlineKeyboardButton("🛡 Модератор", url=f"tg://user?id={message.from_user.id}"), types.InlineKeyboardButton("Пользователь 🚀", url=f"tg://user?id={user[0]}"))
        await bot.send_message(-1002193220334, f"<b>[🟢] Разбан</b>\n\n<b>[🛡] Модератор: {message.from_user.mention}</b>\n<b>[🚀] Разбанил пользователя: {message.text}</b>", reply_markup=kb)
        await db.unban(user[0])
        await message.answer(f"<b>🟢 Разбанить</b>\n\n<b>Пользователь {message.text}</b> был <b>разбанен</b>", reply_markup=back_to_mod())
    else:
        await message.answer(f"<b>🟢 Разбанить</b>\n\n<b>Пользователя {message.text}</b> <b><u>не</u></b> существует, попробуйте еще раз", reply_markup=back_to_mod())
        return

@dp.message_handler(state=states.add_moder.start)
async def add_moder(message: types.Message, state: FSMContext):
    user = await db.get_user(message.text)
    if user:
        await state.finish()
        await db.add_moder(message.text)
        await message.answer("<b>🚀 Выдать модератора</b>\n\nМодератор выдан!", reply_markup=back_to_admin())
    else:
        await message.answer("<b>🚀 Выдать модератора</b>\n\nДанный пользователь не найден! Попробуйте еще раз", reply_markup=back_to_admin())
        return

@dp.message_handler(state=states.remove_moder.start)
async def remove_moder(message: types.Message, state: FSMContext):
    user = await db.get_user(message.text)
    if user:
        await state.finish()
        await db.remove_moder(message.text)
        await message.answer("<b>🚀 Забрать модератора</b>\n\nМодератор отозван!", reply_markup=back_to_admin())
    else:
        await message.answer("<b>🚀 Забрать модератора</b>\n\nДанный пользователь не найден! Попробуйте еще раз", reply_markup=back_to_admin())
        return

@dp.message_handler(state=states.search.start)
async def search(message: types.Message, state: FSMContext):
    user = await db.get_user(message.text)
    if not user:
        await message.answer("Пользователь не найден! Попробуйте еще раз", reply_markup=back_to_admin())
        return
    ban = user[2]
    ban = str(ban)
    ban = ban.replace("0", "🔓 Не заблокирован")
    ban = ban.replace("1", "🔒 Заблокирован")
    await state.finish()
    await message.answer(f"<b>🔎 Пользователь найден!</b>\n\n<b>ID: <code>{user[0]}</code></b>\n<b>Имя пользователя: {user[6]}</b>\n<b>Статус блокировки: {ban}</b>\n<b>Кэшбек: <code>{user[3]} $</code></b>\n<b>Реф. Баланс: <code>{user[5]} $</code></b>", reply_markup=back_to_admin())

@dp.message_handler(state=states.contest1.start)
async def contest1_handler(message: types.Message, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="↩️ Назад", callback_data='adminka'))
    if message.text.isdigit():
        await state.update_data(summa=message.text)
        await message.answer("<b>🎉 Создать конкурс</b>\n\nА теперь отправьте дату окончания конкурса (Пример: <code>13.06.2024 13:10</code>)", reply_markup=kb)
        await states.contest2.start.set()
    else:
        await message.answer("<b>🎉 Создать конкурс</b>\n\nОтправлять нужно числом!", reply_markup=kb)

@dp.message_handler(state=states.empty_cashback.start)
async def empty_cashback(message: types.Message, state: FSMContext):
    user = await db.get_user(message.text)
    if not user:
        await message.answer("<b>⬛️ Анулировать кэшбек</b>\n\nПользователь не найден! Попробуйте еще раз", reply_markup=back_to_admin())
        return
    await state.finish()
    await db.update_cashback(message.text, 0)
    await message.answer("<b>⬛️ Анулировать кэшбек</b>\n\nКэшбек анулирован!", reply_markup=back_to_admin())

@dp.message_handler(state=states.empty_ref.start)
async def empty_ref(message: types.Message, state: FSMContext):
    user = await db.get_user(message.text)
    if not user:
        await message.answer("<b>⬛️ Анулировать реф</b>\n\nПользователь не найден! Попробуйте еще раз", reply_markup=back_to_admin())
        return
    await state.finish()
    await db.update_ref_balance(message.text, 0)
    await message.answer("<b>⬛️ Анулировать реф</b>\n\nРеф анулирован!", reply_markup=back_to_admin())

@dp.message_handler(state=states.contest2.start)
async def contest2_handler(message: types.Message, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="↩️ Назад", callback_data='adminka'))
    data = await state.get_data()
    summa = data.get('summa')
    await state.finish()
    pattern = re.compile(r"^\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}$")
    if pattern.match(message.text):
        settings = await db.get_settings()
        stavka_url = settings[0]
        kb2 = types.InlineKeyboardMarkup()
        kb2.add(types.InlineKeyboardButton(text="Сделать ставку", url=stavka_url))
        msg = await bot.send_photo(config.channel_id, config.menu, f"""<b>[🎁] Ежедневный конкурс от <a href="https://t.me/Elite_Casinobot">EliteCasino</a>!</b>

⌛️ <b>Игрок</b> который cделает самую <b>крупную</b> ставку до <b>{message.text}</b>
<b>— Получит {summa}$</b>

<b>[🏆] Претенденты на приз:</b>

<blockquote><b>№ 1</b>
Игрок: <b>Пустое место</b>
Сумма: <b>0.0$</b>

<b>№ 2</b>
Игрок: <b>Пустое место</b>
Сумма: <b>0.0$</b>

<b>№ 3</b>
Игрок: <b>Пустое место</b>
Сумма: <b>0.0$</b></blockquote>

<a href="{stavka_url}">🛎 Сделать ставку</a>""", reply_markup=kb2)
        await db.create_contest(summa, message.text, msg.message_id)
        await message.answer("<b>🎉 Создать конкурс</b>\n\nКонкурс создан!", reply_markup=kb)
    else:
        await message.answer("<b>🎉 Создать конкурс</b>\n\nОтправьте дату в казаном формате! (Пример: <code>13.06.2024 13:10</code>)", reply_markup=kb)

@dp.message_handler(state=states.ban.start)
async def ban_handler(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        await db.ban(message.text)
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("↩️ Назад", callback_data="adminka"))
        await state.finish()
        await message.answer(f"<b>🔴 Бан</b>\n\nПользователь <code>{message.text}</code> был забанен", reply_markup=kb)
    else:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("↩️ Назад", callback_data="adminka"))
        await message.answer("<b>🔴 Бан</b>\n\nОтправьте ID пользователя!!", reply_markup=kb)

@dp.message_handler(state=states.unban.start)
async def unban_handler(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        await db.unban(message.text)
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("↩️ Назад", callback_data="adminka"))
        await state.finish()
        await message.answer(f"<b>🟢 Разбан</b>\n\nПользователь <code>{message.text}</code> был разбанен", reply_markup=kb)
    else:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("↩️ Назад", callback_data="adminka"))
        await message.answer("<b>🟢 Разбан</b>\n\nОтправьте ID пользователя!!", reply_markup=kb)

@dp.message_handler(state=states.search_ref.start)
async def ref_search(message: types.Message, state: FSMContext):
    await state.finish()
    user = await db.get_user_by_username(message.text)
    if not user:
        await message.answer(f"<b>🔴 {message.text} не существует!</b>")
    else:
        if user[4] != message.from_user.id:
            await message.answer(f"<b>🔴 {message.text} не ваш реферал!</b>")
        else:
            await message.answer(f"<b>🟢 {message.text} ваш реферал!</b>")

@dp.message_handler(state=states.admin_states.popol_cb)
async def popol_handle(message: types.Message, state: FSMContext):
    if '/start' in message.text:
        await state.finish()
        await start(message)
        return

    await state.finish()
    url = await functions.create_invoice(message.text)
    kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton("*тык*", url=url))
    kb.add(types.InlineKeyboardButton("Назад", callback_data="adminka"))
    await message.answer("<b>💸 Пополнить казну</b>", reply_markup=kb)

@dp.message_handler(state=states.broadcast.start)
async def broadcast_handle(message: types.Message, state: FSMContext):
    if '/start' in message.text:
        await state.finish()
        await start(message)
        return

    if message.text == 'Я подтверждаю рассылку':
        data = await state.get_data()
        content = data.get('text')
        msg_id = data.get('msg_id')
        await bot.delete_message(message.chat.id, msg_id)
        await state.finish()
        counter_error = 0
        counter_yes = 0
        users = await db.get_all_users()
        for user in users:
            try:
                await bot.send_message(user[0], content, parse_mode="HTML")
                counter_yes += 1
            except Exception as e:
                print(f"Ошибка при отправке сообщения (рассылка): {e}")
                counter_error += 1
        
        await message.answer(f"<b>📄 Рассылка</b>\n\nУспешно: {counter_yes}\nНе успешно: {counter_error}", reply_markup=back_to_admin())
        return
    elif message.text == "Отменить":
        data = await state.get_data()
        msg_id = data.get('msg_id')
        await bot.delete_message(message.chat.id, msg_id)
        await state.finish()
        await message.answer("<b>📄 Рассылка</b>\n\nОтправка отменена!", reply_markup=back_to_admin())
        return

    await state.update_data(text=message.text)
    await message.answer("<b>📄 Рассылка</b>\n\nВы уверены что хотите отправить данное сообщение? (Ниже пример что увидят юзеры)\n\n<i>Для подтверждения напишите <code>Я подтверждаю рассылку</code> если хотите отменить напишите <code>Отменить</code></i>")
    msg = await bot.send_message(message.chat.id, message.text, parse_mode="HTML")
    await state.update_data(msg_id=msg.message_id)

@dp.message_handler(state=states.admin_states.change_invoice, content_types=types.ContentTypes.TEXT)
async def invoice_handle(message: types.Message, state: FSMContext):
    invoice = message.text
    await state.finish()
    await db.change_invoice(invoice)
    await message.answer("<b>♻️ Изменить счёт</b>\n\nСчёт успешно изменён!", reply_markup=back_to_admin())

@dp.message_handler(state=states.change_max.start)
async def change_max_handler(message: types.Message, state: FSMContext):
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="↩️ Назад", callback_data='adminka'))
    await db.change_max(message.text)
    await message.answer("<b>🎩 Максимальная сумма ставки изменена!</b>", reply_markup=kb)

import os

queue_file = 'bet_queue.txt'
processing_lock = asyncio.Lock()

async def add_bet_to_queue(user_id, username, amount, comment):
    with open(queue_file, 'a', encoding='utf-8') as file:
        file.write(f"{user_id}‎ {username}‎ {amount}‎ {comment}\n")

@dp.channel_post_handler()
async def check_messages(message: types.Message):
    await check_contest()
    if message.chat.id == -1002193220334:
        if '[отправил\(а\)]' in message.md_text:
            if 'tg://user?id=' not in message.md_text:
                await message.reply("Не вижу ID человека!")
                return
            if '💬' in message.md_text:
                text = message.md_text
                text = text.replace("[🪙](tg://emoji?id=5215699136258524363)", "")
                text = text.replace("[🪙](tg://emoji?id=5215276644620586569)", "")
                global lose, win
                win = False
                lose = False
                start_index = text.find("tg://user?id=") + len("tg://user?id=")
                end_index = text.find(")", start_index)
                user_id1 = text[start_index:end_index]

                amount_start_index = text.find(") *") + 1
                if 'USDT' in text:
                    amount_end_index = text.find(" USDT", amount_start_index)
                elif 'TON' in text:
                    amount_end_index = text.find(" TON", amount_start_index)
                elif 'GRAM' in text:
                    amount_end_index = text.find(" GRAM", amount_start_index)
                elif 'NOT' in text:
                    amount_end_index = text.find(" NOT", amount_start_index)
                elif 'MY' in text:
                    amount_end_index = text.find(" MY", amount_start_index)
                elif 'BTC' in text:
                    amount_end_index = text.find(" BTC", amount_start_index)
                elif 'LTC' in text:
                    amount_end_index = text.find(" LTC", amount_start_index)
                elif 'ETH' in text:
                    amount_end_index = text.find(" ETH", amount_start_index)
                elif 'BNB' in text:
                    amount_end_index = text.find(" BNB", amount_start_index)
                elif 'TRX' in text:
                    amount_end_index = text.find(" TRX", amount_start_index)
                elif 'USDC' in text:
                    amount_end_index = text.find(" USDC", amount_start_index)

                amount1 = text[amount_start_index:amount_end_index].strip().replace("\\", "")
                amount1 = amount1.replace("*", "")
                amount1 = float(amount1)
                stavka_url = await db.get_invoice()
                username_start_index = text.find("[*")
                username_end_index = text.find("*]", username_start_index)
                username1 = text[username_start_index + 2:username_end_index]
                username1 = username1.replace("\\", "")
                if '@' in username1:
                    username1 = re.sub(r'@[\w]+', '@Elite_Casinobot', username1)

                lines1 = text.split('\n')
                comment = lines1[-1]
                comment_lower1 = comment.lower()
                comment_lower1 = str(comment_lower1)
                comment_lower1 = comment_lower1.replace("💬 ", "")
                settings = await db.get_settings()

                async with processing_lock:
                    await add_bet_to_queue(user_id1, username1, amount1, comment_lower1)
                    await asyncio.sleep(1)

                    if os.path.exists(queue_file):
                        with open(queue_file, 'r', encoding='utf-8') as file:
                            lines = file.readlines()

                        processed_lines = []
                        for line in lines:
                            parts = line.strip().split('‎ ')
                            if len(parts) != 4:
                                continue

                            user_id, username, amount, comment_lower = parts
                            amount = float(amount)
                            amount = f"{amount:.2f}"
                            amount = float(amount)

                            try:
                                user = await db.get_user(user_id)
                                if user[2] == 1:
                                    if amount >= 1.12:
                                        await functions.transfer2(amount, user_id)
                                        await message.reply("Человек заблокирован! Бэкнул")
                                    else:
                                        check = await functions.create_check(amount, user_id)
                                        if check:
                                            kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await bot.send_message(config.channel_id, f"<b>🧿 {username}, вы заблокированны в нашем боте! Заберите ваши деньги ниже</b>", reply_markup=kb)
                                        await message.reply("Человек заблокирован! Бэкнул")
                                    processed_lines.append(line)
                                    with open(queue_file, 'w', encoding='utf-8') as file:
                                        for line in lines:
                                            if line not in processed_lines:
                                                file.write(line)
                                    return
                            except:
                                if amount >= 1.12:
                                    await functions.transfer2(amount, user_id)
                                    kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                    await bot.send_message(config.channel_id, f"<b>🧿 {username}, вы не находитесь в нашем боте! Деньги были возвращены</b> <i>(Чтобы такого не повторялось зайдите в нашего бота @Elite_Casinobot)</i>", reply_markup=kb)
                                else:
                                    check = await functions.create_check(amount, user_id)
                                    if check:
                                        kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                    else:
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                    await bot.send_message(config.channel_id, f"<b>🧿 {username}, вы не находитесь в нашем боте! Заберите ваши деньги ниже</b> <i>(Чтобы такого не повторялось зайдите в нашего бота @Elite_Casinobot)</i>", reply_markup=kb)

                                await message.reply("Человек не находиться в боте! Бэкнул")
                                processed_lines.append(line)
                                with open(queue_file, 'w', encoding='utf-8') as file:
                                    for line in lines:
                                        if line not in processed_lines:
                                            file.write(line)
                                return

                            if int(amount) >= int(settings[1]):
                                if amount >= 1.12:
                                    await functions.transfer2(amount, user_id)
                                else:
                                    check = await functions.create_check(amount, user_id)
                                    if check:
                                        kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                    else:
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                    await bot.send_message(config.channel_id, f"<b>❌ {username}, вы превысили максимальную ставку в нашем боте! Заберите ваши деньги ниже</b>", reply_markup=kb)
                                await message.answer("Превысил лимит! Бэкнул")
                                processed_lines.append(line)
                                with open(queue_file, 'w', encoding='utf-8') as file:
                                    for line in lines:
                                        if line not in processed_lines:
                                            file.write(line)
                                return

                            bet_msg = await send_bet(username, amount, comment_lower)

                            await db.add_deposit(amount, user_id)
                            if comment_lower in ['фут гол', 'фут мимо', 'фут попал', 'фут попадание', 'фут промах', 'футбол промах', 'футбол мимо', 'футбол гол', 'футбол попал', 'футбол попадание']:
                                dice = await bot.send_dice(config.channel_id, emoji='⚽️')
                                if dice.dice.value in (3, 4, 5):
                                    result = "goal"
                                elif dice.dice.value in (1, 2):
                                    result = "miss"
                                if comment_lower in ['фут гол', 'фут попал', 'фут попадание', 'футбол гол', 'футбол попал', 'футбол попадание']:
                                    if result == 'goal':
                                        win_amount = amount * 1.8
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await bot.send_photo(config.channel_id, config.win, f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Мяч попал!
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай футбол и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                    elif result == 'miss':
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await bot.send_photo(config.channel_id, config.lose, f"""<blockquote><b>Вы проиграли!</b>\n\n<b>Мяч промахнулся!
Кидай футбол и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                elif comment_lower in ['фут мимо', 'фут промах', 'футбол мимо', 'футбол промах']:
                                    if result == 'goal':
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await bot.send_photo(config.channel_id, config.lose, f"""<blockquote><b>Проигрыш!</b>\n\n<b>Мяч попал!
Кидай футбол и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                    elif result == 'miss':
                                        win_amount = amount * 1.8
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await bot.send_photo(config.channel_id, config.win, f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Мяч промахнулся!
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай футбол и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                            elif comment_lower == 'камень' or comment_lower == 'ножницы' or comment_lower == 'бумага':
                                rock = "✊"
                                scissors = "✌️"
                                paper = "✋"
                                if comment_lower == 'камень':
                                    emoji = 'rock'
                                    await bot.send_message(config.channel_id, rock)
                                elif comment_lower == 'ножницы':
                                    emoji = 'scissors'
                                    await bot.send_message(config.channel_id, scissors)
                                elif comment_lower == 'бумага':
                                    emoji = 'paper'
                                    await bot.send_message(config.channel_id, paper)
                                podkrut = settings[2]
                                if podkrut == 0:
                                    choose_emoji = ['rock', 'paper', 'scissors']
                                    oponent = random.choice(choose_emoji)
                                    await asyncio.sleep(0.7)
                                    if oponent == 'rock':
                                        await bot.send_message(config.channel_id, rock)
                                    elif oponent == 'paper':
                                        await bot.send_message(config.channel_id, paper)
                                    elif oponent == 'scissors':
                                        await bot.send_message(config.channel_id, scissors)

                                    if emoji == 'paper' and oponent == 'scissors' or emoji == 'rock' and oponent == 'paper' or emoji == 'scissors' and oponent == 'rock':
                                        lose = True
                                        if oponent == 'rock':
                                            emoji = rock
                                        elif oponent == 'paper':
                                            emoji = paper
                                        elif oponent == 'scissors':
                                            emoji = scissors
                                    elif emoji == oponent:
                                        draw = True
                                        if oponent == 'rock':
                                            emoji = rock
                                        elif oponent == 'paper':
                                            emoji = paper
                                        elif oponent == 'scissors':
                                            emoji = scissors
                                    else:
                                        win = True
                                        if oponent == 'rock':
                                            emoji = rock
                                        elif oponent == 'paper':
                                            emoji = paper
                                        elif oponent == 'scissors':
                                            emoji = scissors
                                    
                                    await asyncio.sleep(1)
                                    
                                    if win == True:
                                        win_amount = amount * 1.9
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await bot.send_photo(config.channel_id, config.win, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Выпало значение {emoji}.
Выигрыш {win_amount}$ зачислен на ваш баланс. Испытай свою удачу игрой «цу-е-фа»!</b></blockquote>""", reply_markup=kb)
                                    elif lose == True:
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await bot.send_photo(config.channel_id, config.lose, caption=f"""<blockquote><b>Проигрыш!</b>\n\n<b>Выпало значение {emoji}.
Испытай свою удачу игрой «цу-е-фа»!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                    elif draw == True:
                                        compinsation = (50 / 100) * amount
                                        compinsation = float(compinsation)
                                        compinsation = f"{compinsation:.2f}"
                                        if compinsation >= 1.12:
                                            await functions.transfer(compinsation, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(compinsation, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {compinsation}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await bot.send_photo(config.channel_id, config.draw, caption=f"""<b>Ничья!</b>\n\n<blockquote><b>Выпало значение {emoji}.
Выигрыш {compinsation}$ зачислен на ваш баланс. Испытай свою удачу игрой «цу-е-фа»!</b></blockquote>""", reply_markup=kb)
                                elif podkrut == 1:
                                    if emoji == 'paper':
                                        oponent = 'scissors'
                                    elif emoji == 'rock':
                                        oponent = 'paper'
                                    elif emoji == 'scissors':
                                        oponent = 'rock'

                                    await asyncio.sleep(0.7)
                                    if oponent == 'rock':
                                        await bot.send_message(config.channel_id, rock)
                                    elif oponent == 'paper':
                                        await bot.send_message(config.channel_id, paper)
                                    elif oponent == 'scissors':
                                        await bot.send_message(config.channel_id, scissors)
                                    
                                    await asyncio.sleep(1)

                                    if emoji == 'paper' and oponent == 'scissors' or emoji == 'rock' and oponent == 'paper' or emoji == 'scissors' and oponent == 'rock':
                                        lose = True
                                        if oponent == 'rock':
                                            emoji = rock
                                        elif oponent == 'paper':
                                            emoji = paper
                                        elif oponent == 'scissors':
                                            emoji = scissors
                                    elif emoji == oponent:
                                        draw = True
                                        if oponent == 'rock':
                                            emoji = rock
                                        elif oponent == 'paper':
                                            emoji = paper
                                        elif oponent == 'scissors':
                                            emoji = scissors
                                    else:
                                        win = True
                                        if oponent == 'rock':
                                            emoji = rock
                                        elif oponent == 'paper':
                                            emoji = paper
                                        elif oponent == 'scissors':
                                            emoji = scissors
                                    
                                    await asyncio.sleep(1)
                                    
                                    if win == True:
                                        win_amount = amount * 1.9
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await bot.send_photo(config.channel_id, config.win, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Выпало значение {emoji}.
Выигрыш {win_amount}$ зачислен на ваш баланс. Испытай свою удачу игрой «цу-е-фа»!</b></blockquote>""", reply_markup=kb)
                                    elif lose == True:
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await bot.send_photo(config.channel_id, config.lose, caption=f"""<blockquote><b>Проигрыш!</b>\n\n<b>Выпало значение {emoji}.
Испытай свою удачу игрой «цу-е-фа»!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                    elif draw == True:
                                        compinsation = (50 / 100) * amount
                                        compinsation = float(compinsation)
                                        compinsation = f"{compinsation:.2f}"
                                        if compinsation >= 1.12:
                                            await functions.transfer(compinsation, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(compinsation, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {compinsation}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await bot.send_photo(config.channel_id, config.draw, caption=f"""<b>Ничья!</b>\n\n<blockquote><b>Выпало значение {emoji}.
Выигрыш {compinsation}$ зачислен на ваш баланс. Испытай свою удачу игрой «цу-е-фа»!</b></blockquote>""", reply_markup=kb)
                            elif 'сектор' in comment_lower and '1' in comment_lower or 'сектор' in comment_lower and '2' in comment_lower or 'сектор' in comment_lower and '3' in comment_lower:
                                dice = await bot.send_dice(config.channel_id)
                                if dice.dice.value == 1 or dice.dice.value == 2:
                                    sector = 1
                                elif dice.dice.value == 3 or dice.dice.value == 4:
                                    sector = 2
                                elif dice.dice.value == 5 or dice.dice.value == 6:
                                    sector = 3
                                if sector == 1 and '1' in comment_lower:
                                    win = 1
                                    image = config.win
                                elif sector == 1 and '1' not in comment_lower:
                                    win = 0
                                    image = config.lose
                                elif sector == 2 and '2' in comment_lower:
                                    win = 1
                                    image = config.win
                                elif sector == 2 and '2' not in comment_lower:
                                    win = 0
                                    image = config.lose
                                elif sector == 3 and '3' in comment_lower:
                                    win = 1
                                    image = config.win
                                elif sector == 3 and '3' not in comment_lower:
                                    win = 0
                                    image = config.lose

                                if win == 1:
                                    win_amount = amount * 2.3
                                    win_amount = f"{win_amount:.2f}"
                                    win_amount = float(win_amount)
                                    await asyncio.sleep(5)
                                    if win_amount >= 1.12:
                                        await functions.transfer(win_amount, user_id, message)
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                    else:
                                        check = await functions.create_check(win_amount, user_id)
                                        if check:
                                            kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                    await db.create_bet(amount, user_id, win=True)
                                    
                                    await bot.send_photo(config.channel_id, photo=image, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Выпал сектор {sector} [{dice.dice.value}]
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                    await contestss(amount, username)
                                    pass
                                elif win == 0:
                                    
                                    lose = True
                                    kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                    await asyncio.sleep(5)
                                    await db.create_bet(amount, user_id, lose=True)
                                    user = await db.get_user(user_id)
                                    
                                    if user[4] is not None:
                                        user1 = await db.get_user(user[4])
                                        ref_balance = user1[5]
                                        percentage_amount = (25 / 100) * amount
                                        new_ref = float(ref_balance) + percentage_amount
                                        await db.update_ref_balance(user[4], new_ref)
                                        await db.add_total_ref(user[4], percentage_amount)
                                    
                                    await bot.send_photo(config.channel_id, photo=image, caption=f"""<b>Вы проиграли!</b><blockquote><b>Выпал сектор {sector} [{dice.dice.value}]
Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                    await contestss(amount, username)
                                    pass
                            elif comment_lower == "плинко":
                                dice = await bot.send_dice(config.channel_id)
                                if dice.dice.value <= 4:
                                    
                                    lose = True
                                    kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                    await asyncio.sleep(5)
                                    await db.create_bet(amount, user_id, lose=True)
                                    user = await db.get_user(user_id)
                                    
                                    if user[4] is not None:
                                        user1 = await db.get_user(user[4])
                                        ref_balance = user1[5]
                                        percentage_amount = (25 / 100) * amount
                                        new_ref = float(ref_balance) + percentage_amount
                                        await db.update_ref_balance(user[4], new_ref)
                                        await db.add_total_ref(user[4], percentage_amount)
                                    
                                    await bot.send_photo(config.channel_id, photo=config.lose, caption=f"""<b>Вы проиграли!</b><blockquote><b>Выпало число меньше [{dice.dice.value}]
Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                    await contestss(amount, username)
                                    pass
                                elif dice.dice.value >= 4:
                                    if dice.dice.value == 4:
                                        win_amount = amount * 1.8
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                    elif dice.dice.value == 5:
                                        win_amount = amount * 2
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                    elif dice.dice.value == 6:
                                        win_amount = amount * 2.5
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                    await asyncio.sleep(5)
                                    if win_amount >= 1.12:
                                        await functions.transfer(win_amount, user_id, message)
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                    else:
                                        check = await functions.create_check(win_amount, user_id)
                                        if check:
                                            kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                    await db.create_bet(amount, user_id, win=True)
                                    await bot.send_photo(config.channel_id, photo=config.win, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Выпало число больше [{dice.dice.value}]
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                    await contestss(amount, username)
                                    pass
                            elif comment_lower == 'больше' or comment_lower == 'меньше' or comment_lower == 'куб больше' or comment_lower == 'куб меньше':
                                dice = await bot.send_dice(config.channel_id)
                                if dice.dice.value >= 4:
                                    if comment_lower == 'больше' or comment_lower == 'куб больше':
                                        win_amount = amount * 1.9
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        await asyncio.sleep(5)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await db.create_bet(amount, user_id, win=True)
                                        user = await db.get_user(user_id)
                                        
                                        await bot.send_photo(config.channel_id, photo=config.win, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Выпало число больше [{dice.dice.value}]
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                    else:
                                        
                                        lose = True
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await asyncio.sleep(5)
                                        await db.create_bet(amount, user_id, lose=True)
                                        
                                        user = await db.get_user(user_id)
                                        if user[4] is not None:
                                            user1 = await db.get_user(user[4])
                                            ref_balance = user1[5]
                                            percentage_amount = (25 / 100) * amount
                                            new_ref = float(ref_balance) + percentage_amount
                                            await db.update_ref_balance(user[4], new_ref)
                                            await db.add_total_ref(user[4], percentage_amount)
                                        await bot.send_photo(config.channel_id, photo=config.more, caption=f"""<b>Вы проиграли!</b><blockquote><b>Выпало число больше [{dice.dice.value}]
Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                elif dice.dice.value <= 3:
                                    if comment_lower == 'меньше' or comment_lower == 'куб меньше':
                                        win_amount = amount * 1.9
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        await asyncio.sleep(5)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await db.create_bet(amount, user_id, win=True)
                                        user = await db.get_user(user_id)
                                        
                                        await bot.send_photo(config.channel_id, photo=config.win, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Выпало число меньше [{dice.dice.value}]
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                    else:
                                        
                                        lose = True
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await asyncio.sleep(5)
                                        await db.create_bet(amount, user_id, lose=True)
                                        
                                        user = await db.get_user(user_id)
                                        if user[4] is not None:
                                            user1 = await db.get_user(user[4])
                                            ref_balance = user1[5]
                                            percentage_amount = (25 / 100) * amount
                                            new_ref = float(ref_balance) + percentage_amount
                                            await db.update_ref_balance(user[4], new_ref)
                                            await db.add_total_ref(user[4], percentage_amount)
                                        await bot.send_photo(config.channel_id, photo=config.less, caption=f"""<b>Вы проиграли!</b><blockquote><b>Выпало число меньше [{dice.dice.value}]
Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                            elif comment_lower == 'чет' or comment_lower == 'не чет' or comment_lower == 'нечет' or comment_lower == 'чёт' or comment_lower == 'не чёт' or comment_lower == 'нечёт' or comment_lower == 'куб чет' or comment_lower == 'куб чёт' or comment_lower == 'куб нечет' or comment_lower == 'куб нечёт' or comment_lower == 'куб не чет' or comment_lower == 'куб не чёт':
                                dice1 = await bot.send_dice(config.channel_id)
                                if dice1.dice.value % 2 == 0:
                                    if comment_lower == 'чет' or comment_lower == 'чёт' or comment_lower == 'куб чет' or comment_lower == 'куб чёт':
                                        win_amount = amount * 1.9
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        await asyncio.sleep(5)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await db.create_bet(amount, user_id, win=True)
                                        user = await db.get_user(user_id)
                                        
                                        await bot.send_photo(config.channel_id, photo=config.win, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Выпало чётное значение [{dice1.dice.value}]
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                    else:
                                        
                                        lose = True
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await asyncio.sleep(5)
                                        await db.create_bet(amount, user_id, lose=True)
                                        
                                        user = await db.get_user(user_id)
                                        if user[4] is not None:
                                            user1 = await db.get_user(user[4])
                                            ref_balance = user1[5]
                                            percentage_amount = (25 / 100) * amount
                                            new_ref = float(ref_balance) + percentage_amount
                                            await db.update_ref_balance(user[4], new_ref)
                                            await db.add_total_ref(user[4], percentage_amount)
                                        await bot.send_photo(config.channel_id, photo=config.lose, caption=f"""<b>Вы проиграли!</b><blockquote><b>Выпало чётное значение [{dice1.dice.value}]
Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                else:
                                    if comment_lower == 'не чет' or comment_lower == 'не чёт' or comment_lower == 'нечет' or comment_lower == 'нечёт' or comment_lower == 'куб нечет' or comment_lower == 'куб нечёт' or comment_lower == 'куб не чет' or comment_lower == 'куб не чёт':
                                        win_amount = amount * 1.9
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        await asyncio.sleep(5)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await db.create_bet(amount, user_id, win=True)
                                        user = await db.get_user(user_id)
                                        
                                        await bot.send_photo(config.channel_id, photo=config.win, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Выпало нечётное значение [{dice1.dice.value}]
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                    else:
                                        
                                        lose = True
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await asyncio.sleep(5)
                                        await db.create_bet(amount, user_id, lose=True)
                                        
                                        user = await db.get_user(user_id)
                                        if user[4] is not None:
                                            user1 = await db.get_user(user[4])
                                            ref_balance = user1[5]
                                            percentage_amount = (25 / 100) * amount
                                            new_ref = float(ref_balance) + percentage_amount
                                            await db.update_ref_balance(user[4], new_ref)
                                            await db.add_total_ref(user[4], percentage_amount)
                                        await bot.send_photo(config.channel_id, photo=config.lose, caption=f"""<blockquote><b>Проигрыш!</b>\n\n<b>Выпало нечётное значение [{dice1.dice.value}]
Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                            elif 'победа' in comment_lower or comment_lower == 'ничья' or 'куб победа' in comment_lower or comment_lower == 'куб ничья':
                                dice1 = await bot.send_dice(config.channel_id)
                                dice2 = await bot.send_dice(config.channel_id)
                                if dice1.dice.value > dice2.dice.value:
                                    if 'победа' in comment_lower and '1' in comment_lower or 'куб победа' in comment_lower and '1' in comment_lower:
                                        win_amount = amount * 1.9
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        await asyncio.sleep(5)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await db.create_bet(amount, user_id, win=True)
                                        user = await db.get_user(user_id)
                                        
                                        await bot.send_photo(config.channel_id, photo=config.win, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Победу одержал первый кубик со счетом [{dice1.dice.value}:{dice2.dice.value}]
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                    else:
                                        
                                        lose = True
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await asyncio.sleep(5)
                                        await db.create_bet(amount, user_id, lose=True)
                                        
                                        user = await db.get_user(user_id)
                                        if user[4] is not None:
                                            user1 = await db.get_user(user[4])
                                            ref_balance = user1[5]
                                            percentage_amount = (25 / 100) * amount
                                            new_ref = float(ref_balance) + percentage_amount
                                            await db.update_ref_balance(user[4], new_ref)
                                            await db.add_total_ref(user[4], percentage_amount)
                                        await bot.send_photo(config.channel_id, photo=config.lose, caption=f"""<blockquote><b>Проигрыш!</b>\n\n<b>Победу одержал первый кубик со счетом [{dice1.dice.value}:{dice2.dice.value}]
Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                elif dice1.dice.value < dice2.dice.value:
                                    if 'победа' in comment_lower and '2' in comment_lower or 'куб победа' in comment_lower and '2' in comment_lower:
                                        win_amount = amount * 1.9
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        await asyncio.sleep(5)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await db.create_bet(amount, user_id, win=True)
                                        user = await db.get_user(user_id)
                                        
                                        await bot.send_photo(config.channel_id, photo=config.win, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Победу одержал второй кубик со счетом [{dice1.dice.value}:{dice2.dice.value}]
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                    else:
                                        
                                        lose = True
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await asyncio.sleep(5)
                                        await db.create_bet(amount, user_id, lose=True)
                                        
                                        user = await db.get_user(user_id)
                                        if user[4] is not None:
                                            user1 = await db.get_user(user[4])
                                            ref_balance = user1[5]
                                            percentage_amount = (25 / 100) * amount
                                            new_ref = float(ref_balance) + percentage_amount
                                            await db.update_ref_balance(user[4], new_ref)
                                            await db.add_total_ref(user[4], percentage_amount)
                                        await bot.send_photo(config.channel_id, photo=config.lose, caption=f"""<blockquote><b>Проигрыш!</b>\n\n<b>Победу одержал второй кубик со счетом [{dice1.dice.value}:{dice2.dice.value}]
Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                elif dice1.dice.value == dice2.dice.value:
                                    if comment_lower == 'ничья' or comment_lower == 'куб ничья':
                                        win_amount = amount * 2.5
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        await asyncio.sleep(5)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await db.create_bet(amount, user_id, win=True)
                                        user = await db.get_user(user_id)
                                        
                                        await bot.send_photo(config.channel_id, photo=config.win, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Сессия закрыта со счётом [{dice1.dice.value}:{dice2.dice.value}], ничья
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                    else:
                                        
                                        lose = True
                                        await asyncio.sleep(5)
                                        await db.create_bet(amount, user_id, lose=True)
                                        
                                        user = await db.get_user(user_id)
                                        if user[4] is not None:
                                            user1 = await db.get_user(user[4])
                                            ref_balance = user1[5]
                                            percentage_amount = (25 / 100) * amount
                                            new_ref = float(ref_balance) + percentage_amount
                                            await db.update_ref_balance(user[4], new_ref)
                                            await db.add_total_ref(user[4], percentage_amount)
                                        compinsation = (50 / 100) * amount
                                        compinsation = float(compinsation)
                                        compinsation = f"{compinsation:.2f}"
                                        if compinsation >= 1.12:
                                            await functions.transfer(compinsation, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(compinsation, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await bot.send_photo(config.channel_id, photo=config.lose, caption=f"""<blockquote><b>Проигрыш!</b>\n\n<b>Сессия закрыта со счётом [{dice1.dice.value}:{dice2.dice.value}], ничья
Кидай кубик и испытай свою удачу!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                            elif 'дартс' in comment_lower or comment_lower == 'красное' or comment_lower == 'белое' or comment_lower == 'промах' or comment_lower == 'мимо':
                                red = [6, 2, 4]
                                white = [3, 5]
                                darts = await bot.send_dice(config.channel_id, emoji="🎯")
                                if darts.dice.value in red:
                                    if 'дартс' in comment_lower and 'красное' in comment_lower or comment_lower == 'красное':
                                        win_amount = amount * 1.8
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        await asyncio.sleep(5)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await db.create_bet(amount, user_id, win=True)
                                        user = await db.get_user(user_id)
                                        
                                        await bot.send_photo(config.channel_id, photo=config.win, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Дротик прилетел на красное
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай дартс и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                    else:
                                        
                                        lose = True
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await asyncio.sleep(5)
                                        await db.create_bet(amount, user_id, lose=True)
                                        
                                        user = await db.get_user(user_id)
                                        if user[4] is not None:
                                            user1 = await db.get_user(user[4])
                                            ref_balance = user1[5]
                                            percentage_amount = (25 / 100) * amount
                                            new_ref = float(ref_balance) + percentage_amount
                                            await db.update_ref_balance(user[4], new_ref)
                                            await db.add_total_ref(user[4], percentage_amount)
                                        await bot.send_photo(config.channel_id, photo=config.lose, caption=f"""<blockquote><b>Проигрыш!</b>\n\n<b>Дротик прилетел на красное
Кидай дартс и испытай свою удачу!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                elif darts.dice.value in white:
                                    if 'дартс' in comment_lower and 'белое' in comment_lower or comment_lower == 'белое':
                                        win_amount = amount * 1.8
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        await asyncio.sleep(5)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await db.create_bet(amount, user_id, win=True)
                                        user = await db.get_user(user_id)
                                        
                                        await bot.send_photo(config.channel_id, photo=config.win, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Дротик прилетел на белое
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай дартс и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                    else:
                                        
                                        lose = True
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await asyncio.sleep(5)
                                        await db.create_bet(amount, user_id, lose=True)
                                        
                                        user = await db.get_user(user_id)
                                        if user[4] is not None:
                                            user1 = await db.get_user(user[4])
                                            ref_balance = user1[5]
                                            percentage_amount = (25 / 100) * amount
                                            new_ref = float(ref_balance) + percentage_amount
                                            await db.update_ref_balance(user[4], new_ref)
                                            await db.add_total_ref(user[4], percentage_amount)
                                        await bot.send_photo(config.channel_id, photo=config.lose, caption=f"""<blockquote><b>Проигрыш!</b>\n\n<b>Дротик прилетел на белое
Кидай дартс и испытай свою удачу!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                else:
                                    if 'дартс' in comment_lower and 'промах' in comment_lower or comment_lower == 'промах' or comment_lower == 'мимо':
                                        win_amount = amount * 1.8
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        await asyncio.sleep(5)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await db.create_bet(amount, user_id, win=True)
                                        user = await db.get_user(user_id)
                                        
                                        await bot.send_photo(config.channel_id, photo=config.win, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Дротик промахнулся
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай дартс и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                    else:
                                        
                                        lose = True
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await asyncio.sleep(5)
                                        await db.create_bet(amount, user_id, lose=True)
                                        
                                        user = await db.get_user(user_id)
                                        if user[4] is not None:
                                            user1 = await db.get_user(user[4])
                                            ref_balance = user1[5]
                                            percentage_amount = (25 / 100) * amount
                                            new_ref = float(ref_balance) + percentage_amount
                                            await db.update_ref_balance(user[4], new_ref)
                                            await db.add_total_ref(user[4], percentage_amount)
                                        await bot.send_photo(config.channel_id, photo=config.lose, caption=f"""<blockquote><b>Проигрыш!</b>\n\n<b>Дротик промахнулся
Кидай дартс и испытай свою удачу!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                            elif 'баскет' in comment_lower or 'баскетбол' in comment_lower:
                                basket = await bot.send_dice(config.channel_id, emoji="🏀")
                                win = [5, 4]
                                if basket.dice.value in win:
                                    if 'баскет' in comment_lower and 'попадание' in comment_lower or 'баскет' in comment_lower and 'попал' in comment_lower or 'баскет' in comment_lower and 'гол' in comment_lower or 'баскетбол' in comment_lower and 'попал' in comment_lower or 'баскетбол' in comment_lower and 'гол' in comment_lower or 'баскетбол' in comment_lower and 'попадание' in comment_lower:
                                        win_amount = amount * 1.8
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        await asyncio.sleep(5)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await db.create_bet(amount, user_id, win=True)
                                        user = await db.get_user(user_id)
                                        await bot.send_photo(config.channel_id, photo=config.win, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Мяч попал
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай баскет и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                    else:
                                        
                                        lose = True
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await asyncio.sleep(5)
                                        await db.create_bet(amount, user_id, lose=True)
                                        
                                        user = await db.get_user(user_id)
                                        if user[4] is not None:
                                            user1 = await db.get_user(user[4])
                                            ref_balance = user1[5]
                                            percentage_amount = (25 / 100) * amount
                                            new_ref = float(ref_balance) + percentage_amount
                                            await db.update_ref_balance(user[4], new_ref)
                                            await db.add_total_ref(user[4], percentage_amount)
                                        await bot.send_photo(config.channel_id, photo=config.lose, caption=f"""<blockquote><b>Проигрыш!</b>\n\n<b>Мяч попал
Кидай баскет и испытай свою удачу!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                else:
                                    if 'баскет' in comment_lower and 'промах' in comment_lower or 'баскет' in comment_lower and 'мимо' in comment_lower or 'баскетбол' in comment_lower and 'мимо' in comment_lower or 'баскетбол' in comment_lower and 'промах' in comment_lower:
                                        win_amount = amount * 1.8
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        await asyncio.sleep(5)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await db.create_bet(amount, user_id, win=True)
                                        user = await db.get_user(user_id)
                                        
                                        await bot.send_photo(config.channel_id, photo=config.win, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Мяч промахнулся
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай баскет и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                    else:
                                        
                                        lose = True
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await asyncio.sleep(5)
                                        await db.create_bet(amount, user_id, lose=True)
                                        
                                        user = await db.get_user(user_id)
                                        if user[4] is not None:
                                            user1 = await db.get_user(user[4])
                                            ref_balance = user1[5]
                                            percentage_amount = (25 / 100) * amount
                                            new_ref = float(ref_balance) + percentage_amount
                                            await db.update_ref_balance(user[4], new_ref)
                                            await db.add_total_ref(user[4], percentage_amount)
                                        await bot.send_photo(config.channel_id, photo=config.lose, caption=f"""<blockquote><b>Проигрыш!</b>\n\n<b>Мяч промахнулся
Кидай баскет и испытай свою удачу!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                            elif 'кегли' in comment_lower:
                                bowling = await bot.send_dice(config.channel_id, emoji="🎳")
                                if bowling.dice.value == 6:
                                    if 'кегли' in comment_lower and 'страйк' in comment_lower:
                                        win_amount = amount * 2.3
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        await asyncio.sleep(5)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await db.create_bet(amount, user_id, win=True)
                                        user = await db.get_user(user_id)
                                        
                                        await bot.send_photo(config.channel_id, photo=config.win, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Были сбиты все кегли
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай кегли и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                    else:
                                        
                                        lose = True
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await asyncio.sleep(5)
                                        await db.create_bet(amount, user_id, lose=True)
                                        
                                        user = await db.get_user(user_id)
                                        if user[4] is not None:
                                            user1 = await db.get_user(user[4])
                                            ref_balance = user1[5]
                                            percentage_amount = (25 / 100) * amount
                                            new_ref = float(ref_balance) + percentage_amount
                                            await db.update_ref_balance(user[4], new_ref)
                                            await db.add_total_ref(user[4], percentage_amount)
                                        await bot.send_photo(config.channel_id, photo=config.lose, caption=f"""<blockquote><b>Проигрыш!</b>\n\n<b>Были сбиты все кегли
Кидай кегли и испытай свою удачу!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                elif bowling.dice.value == 1:
                                    if 'кегли' in comment_lower and '0' in comment_lower:
                                        win_amount = amount * 1.8
                                        win_amount = f"{win_amount:.2f}"
                                        win_amount = float(win_amount)
                                        await asyncio.sleep(5)
                                        if win_amount >= 1.12:
                                            await functions.transfer(win_amount, user_id, message)
                                            kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            check = await functions.create_check(win_amount, user_id)
                                            if check:
                                                kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                            else:
                                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await db.create_bet(amount, user_id, win=True)
                                        user = await db.get_user(user_id)
                                        
                                        await bot.send_photo(config.channel_id, photo=config.win, caption=f"""<blockquote><b>Вы выиграли!</b>\n\n<b>Было сбито 0 кеглей
Выигрыш {win_amount}$ зачислен на ваш баланс. Кидай кегли и испытай свою удачу!</b></blockquote>\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                    else:
                                        
                                        lose = True
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        await asyncio.sleep(5)
                                        await db.create_bet(amount, user_id, lose=True)
                                        
                                        user = await db.get_user(user_id)
                                        if user[4] is not None:
                                            user1 = await db.get_user(user[4])
                                            ref_balance = user1[5]
                                            percentage_amount = (25 / 100) * amount
                                            new_ref = float(ref_balance) + percentage_amount
                                            await db.update_ref_balance(user[4], new_ref)
                                            await db.add_total_ref(user[4], percentage_amount)
                                        await bot.send_photo(config.channel_id, photo=config.lose, caption=f"""<blockquote><b>Проигрыш!</b>\n\n<b>Было сбито 0 кеглей
Кидай кегли и испытай свою удачу!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                        await contestss(amount, username)
                                        pass
                                else:
                                    
                                    lose = True
                                    kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                    await asyncio.sleep(5)
                                    await db.create_bet(amount, user_id, lose=True)
                                    
                                    user = await db.get_user(user_id)
                                    
                                    if user[4] is not None:
                                            user1 = await db.get_user(user[4])
                                            ref_balance = user1[5]
                                            percentage_amount = (25 / 100) * amount
                                            new_ref = float(ref_balance) + percentage_amount
                                            await db.update_ref_balance(user[4], new_ref)
                                            await db.add_total_ref(user[4], percentage_amount)
                                    await bot.send_photo(config.channel_id, photo=config.lose, caption=f"""<blockquote><b>Проигрыш!</b>\n\n<b>Было сбито нное количество кеглей не соответствуещее вашей ставке
Кидай кегли и испытай свою удачу!</b></blockquote>\n\n<b>Играй и зарабатывай вместе со мной в EliteCasino !\n▶<a href="https://t.me/Elite_Casinobot?start=ref_{user_id}">ЗАРАБОТАТЬ</a>◀</b>\n\n\n<b><a href="https://t.me/EliteCasinoRules">Правила</a> | <a href="https://t.me/EliteCasinoNews">Новостной</a> | <a href="https://t.me/vemorr">Поддержка</a> | <a href="https://t.me/Elite_Casinobot">Реферальный бот</a></b>""", reply_markup=kb)
                                    await contestss(amount, username)
                                    pass
                            elif comment_lower == 'мины' or 'мины' in comment_lower:
                                active_mines = await db.get_active_mines(user_id)
                                kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                if active_mines:
                                    if amount >= 1.12:
                                        await functions.transfer(amount, user_id)
                                    else:
                                        check = await functions.create_check(amount, user_id)
                                        if check:
                                            kb2 = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {win_amount}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                        else:
                                            kb2 = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                    await bot.send_photo(config.channel_id, config.mines, caption="<b>🧿 У вас уже есть активная сессия с минами, ставка была возвращенна на баланс</b>", reply_markup=kb2)
                                else:
                                    await db.create_mines(user_id, amount)
                                    await bot.send_photo(config.channel_id, photo=config.mines, caption=f"""<b>Нужно зайти в нашего бота!</b>\n\n<blockquote><b>Для того чтобы начать игру просто зайдите в нашего бота он сам автоматически выведет вам минное поле</b></blockquote>
{config.bot_username} (бот)""", reply_markup=kb)
                            else:
                                start_index = text.find("tg://user?id=") + len("tg://user?id=")
                                end_index = text.find(")", start_index)
                                user_id = text[start_index:end_index]

                                amount_start_index = text.find(") *") + 1

                                if 'USDT' in text:
                                    amount_end_index = text.find(" USDT", amount_start_index)
                                elif 'TON' in text:
                                    amount_end_index = text.find(" TON", amount_start_index)
                                elif 'GRAM' in text:
                                    amount_end_index = text.find(" GRAM", amount_start_index)
                                elif 'NOT' in text:
                                    amount_end_index = text.find(" NOT", amount_start_index)
                                elif 'MY' in text:
                                    amount_end_index = text.find(" MY", amount_start_index)
                                elif 'BTC' in text:
                                    amount_end_index = text.find(" BTC", amount_start_index)
                                elif 'LTC' in text:
                                    amount_end_index = text.find(" LTC", amount_start_index)
                                elif 'ETH' in text:
                                    amount_end_index = text.find(" ETH", amount_start_index)
                                elif 'BNB' in text:
                                    amount_end_index = text.find(" BNB", amount_start_index)
                                elif 'TRX' in text:
                                    amount_end_index = text.find(" TRX", amount_start_index)
                                elif 'USDC' in text:
                                    amount_end_index = text.find(" USDC", amount_start_index)

                                amount = text[amount_start_index:amount_end_index].strip().replace("\\", "")
                                amount = amount.replace("*", "")
                                amount = float(amount)

                                username_start_index = text.find("[*")
                                username_end_index = text.find("*]", username_start_index)
                                username = text[username_start_index + 2:username_end_index]
                                username = username.replace("\\", "")

                                summa = amount - (amount * 0.1)
                                summa = f"{summa:.2f}"
                                summa = float(summa)
                                await db.add_deposit(amount, user_id)
                                await message.reply("Неверный комментарий")
                                if amount >= 1.12:
                                    await functions.transfer2(summa, user_id)
                                    kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton("Сделать ставку", url=stavka_url))
                                else:
                                    check = await functions.create_check(summa, user_id)
                                    if check:
                                        kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {summa}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                    else: 
                                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                                await bot.send_message(config.channel_id, f"""<b>🚫 {username}, вы указали не верный комментарий к платежу!
— Средства с комиссией 10% зачислены на ваш баланс!</b>\n\n👉 <a href="https://t.me/c/2110144414/5">Как сделать ставку?</a> | 👉 <a href="https://t.me/Elite_Casinobot">Реф. программа</a>""", reply_markup=kb, disable_web_page_preview=True)
                            await contestss(amount, username)
                            if lose == True:
                                await message.reply(f"Проебал {amount}$")
                            processed_lines.append(line)
                            await asyncio.sleep(1)
                        with open(queue_file, 'w', encoding='utf-8') as file:
                            for line in lines:
                                if line not in processed_lines:
                                    file.write(line)
                            return
            else:
                start_index = text.find("tg://user?id=") + len("tg://user?id=")
                end_index = text.find(")", start_index)
                user_id = text[start_index:end_index]

                amount_start_index = text.find(") *") + 1

                if 'USDT' in text:
                    amount_end_index = text.find(" USDT", amount_start_index)
                elif 'TON' in text:
                    amount_end_index = text.find(" TON", amount_start_index)
                elif 'GRAM' in text:
                    amount_end_index = text.find(" GRAM", amount_start_index)
                elif 'NOT' in text:
                    amount_end_index = text.find(" NOT", amount_start_index)
                elif 'MY' in text:
                    amount_end_index = text.find(" MY", amount_start_index)
                elif 'BTC' in text:
                    amount_end_index = text.find(" BTC", amount_start_index)
                elif 'LTC' in text:
                    amount_end_index = text.find(" LTC", amount_start_index)
                elif 'ETH' in text:
                    amount_end_index = text.find(" ETH", amount_start_index)
                elif 'BNB' in text:
                    amount_end_index = text.find(" BNB", amount_start_index)
                elif 'TRX' in text:
                    amount_end_index = text.find(" TRX", amount_start_index)
                elif 'USDC' in text:
                    amount_end_index = text.find(" USDC", amount_start_index)

                amount = text[amount_start_index:amount_end_index].strip().replace("\\", "")
                amount = amount.replace("*", "")
                amount = float(amount)
                amount = f"{amount:.2f}"

                username_start_index = text.find("[*")
                username_end_index = text.find("*]", username_start_index)
                username = text[username_start_index + 2:username_end_index]
                username = username.replace("\\", "")

                await bot.send_message(config.channel_id, f"<b>{username} ставит {amount}$</b>", parse_mode='HTML')

                summa = amount - (amount * 0.1)
                summa = f"{summa:.2f}"
                summa = float(summa)
                stavka_url = await db.get_invoice()
                await db.add_deposit(amount, user_id)
                await message.reply("Нету комментария")
                if amount >= 1.12:
                    await functions.transfer2(summa, user_id)
                    kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton("Сделать ставку", url=stavka_url))
                else:
                    check = await functions.create_check(summa, user_id)
                    if check:
                        kb = types.InlineKeyboardMarkup(row_width=2).row(types.InlineKeyboardButton(f"🎁 Забрать {summa}$", url=check), types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                    else:
                        kb = types.InlineKeyboardMarkup(row_width=1).row(types.InlineKeyboardButton('Сделать ставку', url=stavka_url))
                await bot.send_message(config.channel_id, f"""<b>🚫 {username}, вы указали не верный комментарий к платежу!
— Средства с комиссией 10% зачислены на ваш баланс!</b>\n\n👉 <a href="https://t.me/c/2110144414/5">Как сделать ставку?</a> | 👉 <a href="https://t.me/Elite_Casinobot">Реф. программа</a>""", reply_markup=kb, disable_web_page_preview=True)
                return

async def contestss(amount, username):
    stavka_url = await db.get_invoice()
    contests = await db.get_all_contests()
    amount = float(amount)
    if contests:
        for contest in contests:
            kb2 = types.InlineKeyboardMarkup()
            kb2.add(types.InlineKeyboardButton(text="Сделать ставку", url=stavka_url))
            if amount > float(contest[3]):
                if amount > float(contest[2]) and username != contest[4] or username != contest[6]:
                    pass
                else:
                    return
                if contest[2] is not None:
                    await db.update_contest(contest[2], contest[0], top2=True, top2_summa=contest[3])
                if contest[4] is not None:
                    await db.update_contest(contest[4], contest[0], top3=True, top3_summa=contest[5])
                if contest[2] is not None and contest[2] == username:
                    await db.update_contest('Пустое место', contest[0], top1=True, top1_summa=0.0)
                if contest[4] is not None and contest[4] == username:
                    await db.update_contest('Пустое место', contest[0], top2=True, top2_summa=0.0)
                if contest[6] is not None and contest[6] == username:
                    await db.update_contest('Пустое место', contest[0], top3=True, top3_summa=0.0)
                await db.update_contest(username, contest[0], top1=True, top1_summa=amount)
                contest1 = await db.get_contest(contest[0])
                top2 = contest1[4]
                top2_summa = contest1[5]
                if not top2:
                    top2 = 'Пустое место'
                if not top2_summa:
                    top2_summa = 0.0
                top3 = contest1[6]
                top3_summa = contest1[7]
                if not top3:
                    top3 = 'Пустое место'
                if not top3_summa:
                    top3_summa = 0.0
                date_time_str = contest[8]
                date_time_obj = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
                formatted_date_time = date_time_obj.strftime("%d.%m.%Y %H:%M")
                await bot.edit_message_caption(config.channel_id, contest[10], caption=f"""<b>[🎁] Ежедневный конкурс от <a href="https://t.me/Elite_Casinobot">EliteCasino</a>!</b>

⌛️ <b>Игрок</b> который cделает самую <b>крупную ставку</b> до <b>{formatted_date_time}</b>
<b>— Получит {contest[1]}$</b>

<b>[🏆] Претенденты на приз:</b>

<blockquote><b>№ 1</b>
Игрок: <b>{username}</b>
Сумма: <b>{amount}$</b>

<b>№ 2</b>
Игрок: <b>{top2}</b>
Сумма: <b>{top2_summa}$</b>

<b>№ 3</b>
Игрок: <b>{top3}</b>
Сумма: <b>{top3_summa}$</b></blockquote>

<a href="{stavka_url}">🛎 Сделать ставку</a>""", reply_markup=kb2)
                await bot.send_message(config.channel_id, "<b>🔄 Топ обновлён...</b>", reply_to_message_id=contest[10])
            elif amount > float(contest[5]):
                if amount > float(contest[5]) and username != contest[2] or username != contest[6]:
                    pass
                else:
                    return
                if contest[4] is not None:
                    await db.update_contest(contest[4], contest[0], top3=True, top3_summa=contest[5])
                if contest[2] is not None and contest[2] == username:
                    await db.update_contest('Пустое место', contest[0], top1=True, top1_summa=0.0)
                if contest[4] is not None and contest[4] == username:
                    await db.update_contest('Пустое место', contest[0], top2=True, top2_summa=0.0)
                if contest[6] is not None and contest[6] == username:
                    await db.update_contest('Пустое место', contest[0], top3=True, top3_summa=0.0)
                await db.update_contest(username, contest[0], top2=True, top2_summa=amount)
                contest1 = await db.get_contest(contest[0])
                top1 = contest1[2]
                top1_summa = contest1[3]
                if not top1:
                    top1 = 'Пустое место'
                if not top1_summa:
                    top1_summa = 0.0
                top3 = contest1[6]
                top3_summa = contest1[7]
                if not top3:
                    top3 = 'Пустое место'
                if not top3_summa:
                    top3_summa = 0.0
                date_time_str = contest[8]
                date_time_obj = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
                formatted_date_time = date_time_obj.strftime("%d.%m.%Y %H:%M")
                await bot.edit_message_caption(config.channel_id, contest[10], caption=f"""<b>[🎁] Ежедневный конкурс от <a href="https://t.me/Elite_Casinobot">EliteCasino</a>!</b>

⌛️ <b>Игрок</b> который cделает самую <b>крупную ставку</b> до <b>{formatted_date_time}</b>
<b>— Получит {contest[1]}$</b>

<b>[🏆] Претенденты на приз:</b>

<blockquote><b>№ 1</b>
Игрок: <b>{top1}</b>
Сумма: <b>{top1_summa}$</b>

<b>№ 2</b>
Игрок: <b>{username}</b>
Сумма: <b>{amount}$</b>

<b>№ 3</b>
Игрок: <b>{top3}</b>
Сумма: <b>{top3_summa}$</b></blockquote>

<a href="{stavka_url}">🛎 Сделать ставку</a>""", reply_markup=kb2)
                await bot.send_message(config.channel_id, "<b>🔄 Топ обновлён...</b>", reply_to_message_id=contest[10])
            elif amount > float(contest[7]):
                if amount > float(contest[7]) and username != contest[2] or username != contest[4]:
                    pass
                else:
                    return
                if contest[2] is not None and contest[2] == username:
                    await db.update_contest('Пустое место', contest[0], top1=True, top1_summa=0.0)
                if contest[4] is not None and contest[4] == username:
                    await db.update_contest('Пустое место', contest[0], top2=True, top2_summa=0.0)
                if contest[6] is not None and contest[6] == username:
                    await db.update_contest('Пустое место', contest[0], top3=True, top3_summa=0.0)
                await db.update_contest(username, contest[0], top3=True, top3_summa=amount)
                contest1 = await db.get_contest(contest[0])
                top1 = contest1[2]
                top1_summa = contest1[3]
                if not top1:
                    top1 = 'Пустое место'
                if not top1_summa:
                    top1_summa = 0.0
                top2 = contest[4]
                top2_summa = contest1[5]
                if not top2:
                    top2 = 'Пустое место'
                if not top2_summa:
                    top2_summa = 0.0
                date_time_str = contest[8]
                date_time_obj = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
                formatted_date_time = date_time_obj.strftime("%d.%m.%Y %H:%M")
                await bot.edit_message_caption(config.channel_id, contest[10], caption=f"""<b>[🎁] Ежедневный конкурс от <a href="https://t.me/Elite_Casinobot">EliteCasino</a>!</b>

⌛️ <b>Игрок</b> который cделает самую <b>крупную ставку</b> до <b>{formatted_date_time}</b>
<b>— Получит {contest[1]}$</b>

<b>[🏆] Претенденты на приз:</b>

<blockquote><b>№ 1</b>
Игрок: <b>{top1}</b>
Сумма: <b>{top1_summa}$</b>

<b>№ 2</b>
Игрок: <b>{top2}</b>
Сумма: <b>{top2_summa}$</b>

<b>№ 3</b>
Игрок: <b>{username}</b>
Сумма: <b>{amount}$</b></blockquote>

<a href="{stavka_url}">🛎 Сделать ставку</a>""", reply_markup=kb2)
                await bot.send_message(config.channel_id, "<b>🔄 Топ обновлён...</b>", reply_to_message_id=contest[10])

async def check_contest():
    contests = await db.get_all_contests()
    if contests:
        for contest in contests:
            contest_end_str = contest[8]
            contest_end = datetime.strptime(contest_end_str, "%Y-%m-%d %H:%M:%S")
            current_datetime = datetime.now()
            if current_datetime > contest_end:
                await bot.send_message(config.channel_id, f"<b>🎉 Конкурс №{contest[0]} завершён!</b>\n<blockquote><b>Победитель должен забрать приз ({contest[1]}$) у администратора.</b></blockquote>", reply_to_message_id=contest[10])
                await db.set_end(contest[0])

async def on_startup(dp):
    await db.create_tables()
    print("Ready")

if __name__ == '__main__':

    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
