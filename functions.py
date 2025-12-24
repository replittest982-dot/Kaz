import random
import string
import requests
import config  # <--- Важный импорт
from aiogram import types
# import main # Убрал циклический импорт, бот передается в аргументы или берется из контекста, если нужно

def generate_random_code(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

async def get_cb_balance():
    # БЕРЕМ ТОКЕН ИЗ КОНФИГА
    headers = {"Crypto-Pay-API-Token": config.crypto_pay_token}
    r = requests.get("https://pay.crypt.bot/api/getBalance", headers=headers).json()
    usdt_balance = 0
    if 'result' in r:
        for currency_data in r['result']:
            if currency_data['currency_code'] == 'USDT':
                usdt_balance = currency_data['available']
                break
    return usdt_balance

async def create_invoice(amount):
    headers = {"Crypto-Pay-API-Token": config.crypto_pay_token}
    data = {"asset": "USDT", "amount": float(amount)}
    r = requests.get("https://pay.crypt.bot/api/createInvoice", data=data, headers=headers).json()
    return r['result']['bot_invoice_url']

async def transfer(amount, us_id, message):
    bal = await get_cb_balance()
    bal = float(bal)
    amount = float(amount)
    
    # Чтобы избежать циклического импорта main -> functions -> main
    # Импортируем bot прямо внутри функции, если нужно отправить сообщение
    from main import bot 

    if bal < amount:
        await bot.send_message(
            config.admins[0], 
            f"<b>[🔔] Не хватает средств на CryptoBot для автовывода!</b>\n"
            f"Юзер: {us_id}\nСумма: {amount}$"
        )
        return False
    
    headers = {"Crypto-Pay-API-Token": config.crypto_pay_token}
    random_code = generate_random_code(10)
    data = {
        "asset": "USDT",
        "amount": amount,
        "user_id": us_id,
        "spend_id": random_code
    }
    r = requests.get("https://pay.crypt.bot/api/transfer", data=data, headers=headers).json()
    
    if r['ok']:
        return True
    else:
        # Логируем ошибку админу
        await bot.send_message(config.admins[0], f"Ошибка вывода: {r}")
        return False

async def get_exchange_rate(amount_usd):
    headers = {"Crypto-Pay-API-Token": config.crypto_pay_token}
    r = requests.get("https://pay.crypt.bot/api/getExchangeRates", headers=headers).json()
    amount_rub = 0
    if 'result' in r:
        for data in r['result']:
            if data['source'] == 'USDT' and data['target'] == 'RUB':
                rate = data['rate']
                amount_rub = float(amount_usd) * float(rate)
    return amount_rub

async def create_check(amount, userid):
    from main import bot # Импорт внутри функции
    
    bal = await get_cb_balance()
    bal = float(bal)
    amount = float(amount)
    
    keyb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Перейти", url=f"tg://user?id={userid}"))
    
    if bal < amount:
        await bot.send_message(userid, f"<b>[🔔] Вам пришло системное уведомление:</b>\n\n<b><blockquote>Ваш выигрыш ⌊ {amount}$ ⌉ будет зачислен вручную администратором!</blockquote></b>")
        # Отправляем в канал логов или админу (берем ID из конфига)
        await bot.send_message(config.channel_id, f"<b>[🔔] Мало суммы в казне для выплаты!</b>\n\n<b><blockquote>Пользователь: {userid}\nСумма: {amount}$</blockquote></b>", reply_markup=keyb)
        return

    headers = {"Crypto-Pay-API-Token": config.crypto_pay_token}
    data = {"asset": "USDT", "amount": str(amount)}
    r = requests.get("https://pay.crypt.bot/api/createCheck", data=data, headers=headers).json()
    
    if r['ok']:
        check_url = r['result']['bot_check_url']
        await bot.send_message(userid, f"<b>💰 Ваш чек на {amount}$ создан!</b>", 
                               reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Забрать", url=check_url)))
    else:
        await bot.send_message(config.admins[0], f"Ошибка создания чека: {r}")
