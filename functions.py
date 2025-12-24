import random
import string
import requests
import functions
from main import bot
from aiogram import types

def generate_random_code(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

async def get_cb_balance():
    headers = {"Crypto-Pay-API-Token": "138591:AA0pzFpAYk3cbo7qDDCdkTr2XQu3VjERE5H"}
    r = requests.get("https://pay.crypt.bot/api/getBalance", headers=headers).json()
    for currency_data in r['result']:
        if currency_data['currency_code'] == 'USDT':
            usdt_balance = currency_data['available']
            break
    return usdt_balance

async def create_invoice(amount):
    headers = {"Crypto-Pay-API-Token": "138591:AA0pzFpAYk3cbo7qDDCdkTr2XQu3VjERE5H"}
    data = {"asset": "USDT", "amount": float(amount)}
    r = requests.get("https://pay.crypt.bot/api/createInvoice", data=data, headers=headers).json()
    return r['result']['bot_invoice_url']

async def transfer(amount, us_id, message):
    bal = await get_cb_balance()
    bal = float(bal)
    amount = float(amount)
    keyb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Перейти", url=f"tg://user?id={us_id}"))
    if bal < amount:
        await bot.send_message(us_id, f"<b>[🔔] Вам пришло системное уведомление:</b>\n\n<b><blockquote>Ваш выигрыш ⌊ {amount}$ ⌉ будет зачислен вручную администратором!</blockquote></b>")
        await bot.send_message(-1002193220334, f"<b>[🔔] Мало суммы в казне для выплаты!</b>\n\n<b><blockquote>Пользователь: {us_id}\nСумма: {amount}$</blockquote></b>", reply_markup=keyb)
        return
    spend_id = functions.generate_random_code(length=10)
    headers = {"Crypto-Pay-API-Token": "138591:AA0pzFpAYk3cbo7qDDCdkTr2XQu3VjERE5H"}
    data = {"asset": "USDT", "amount": float(amount), "user_id": us_id, "spend_id": spend_id}
    requests.get("https://pay.crypt.bot/api/transfer", data=data, headers=headers)
    await bot.send_message(-1002193220334, f"<b>[🧾] Перевод!</b>\n\n<b>[💠] Сумма: {amount} USDT</b>\n<b>[🚀] Пользователю: {us_id}</b>", reply_markup=keyb)
    await message.reply(f"Выплачено! ({amount}$)")

async def transfer2(amount, us_id):
    bal = await get_cb_balance()
    bal = float(bal)
    amount = float(amount)
    keyb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Перейти", url=f"tg://user?id={us_id}"))
    if bal < amount:
        await bot.send_message(us_id, f"<b>[🔔] Вам пришло системное уведомление:</b>\n\n<b><blockquote>Ваш выигрыш ⌊ {amount}$ ⌉ будет зачислен вручную администратором!</blockquote></b>")
        await bot.send_message(-1002193220334, f"<b>[🔔] Мало суммы в казне для выплаты!</b>\n\n<b><blockquote>Пользователь: {us_id}\nСумма: {amount}$</blockquote></b>", reply_markup=keyb)
        return
    try:
        spend_id = functions.generate_random_code(length=10)
        headers = {"Crypto-Pay-API-Token": "138591:AA0pzFpAYk3cbo7qDDCdkTr2XQu3VjERE5H"}
        data = {"asset": "USDT", "amount": float(amount), "user_id": us_id, "spend_id": spend_id}
        requests.get("https://pay.crypt.bot/api/transfer", data=data, headers=headers)
        await bot.send_message(-1002193220334, f"<b>[🧾] Перевод!</b>\n\n<b>[💠] Сумма: {amount} USDT</b>\n<b>[🚀] Пользователю: {us_id}</b>", reply_markup=keyb)
    except Exception as e:
        print(e)
        return e

async def convert(amount_usd):
    headers = {"Crypto-Pay-API-Token": "138591:AA0pzFpAYk3cbo7qDDCdkTr2XQu3VjERE5H"}
    r = requests.get("https://pay.crypt.bot/api/getExchangeRates", headers=headers).json()
    for data in r['result']:
        if data['source'] == 'USDT' and data['target'] == 'RUB':
            rate = data['rate']
            amount_rub = float(amount_usd) * float(rate)
    return amount_rub

async def create_check(amount, userid):
    bal = await get_cb_balance()
    bal = float(bal)
    amount = float(amount)
    keyb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Перейти", url=f"tg://user?id={userid}"))
    if bal < amount:
        await bot.send_message(userid, f"<b>[🔔] Вам пришло системное уведомление:</b>\n\n<b><blockquote>Ваш выигрыш ⌊ {amount}$ ⌉ будет зачислен вручную администратором!</blockquote></b>")
        await bot.send_message(-1002193220334, f"<b>[🔔] Мало суммы в казне для выплаты!</b>\n\n<b><blockquote>Пользователь: {userid}\nСумма: {amount}$</blockquote></b>", reply_markup=keyb)
        return
    headers = {"Crypto-Pay-API-Token": "138591:AA0pzFpAYk3cbo7qDDCdkTr2XQu3VjERE5H"}
    data = {"asset": "USDT", "amount": float(amount), "pin_to_user_id": userid}
    r = requests.get("https://pay.crypt.bot/api/createCheck", headers=headers, data=data).json()
    await bot.send_message(-1002193220334, f"<b>[🧾] Создан чек!</b>\n\n<b>[💠] Сумма: {amount} USDT</b>\n<b>[🚀] Прикрепен за юзером: {userid}</b>", reply_markup=keyb)
    print(r)
    return r["result"]["bot_check_url"]