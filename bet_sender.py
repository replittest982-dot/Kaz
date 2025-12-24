from pyrogram import Client
import config
from pyrogram.types import Message
import asyncio
import os

# Берем данные из обновленного config.py
api_id = config.api_id
api_hash = config.api_hash

# Инициализация клиента. 
# Используем in_memory=True для сессии, чтобы не создавать лишние файлы, 
# если мы хотим использовать авторизацию через переменные (session string),
# но в твоем случае будет создаваться файл 'bot.session'.
app = Client('bot', api_id=api_id, api_hash=api_hash)

async def send_bet(username, summa, bet_type) -> int:
    # Запускаем клиент
    if not app.is_connected:
        await app.start()

    message_text = (
        "**[<emoji id=5343636681473935403>🔥</emoji>] Новая ставка!\n\n"
        f"> <emoji id=5341357711697134290>💎</emoji> Игрок {username}\n\n"
        f"> <emoji id=5357592447557848986>⚡️</emoji> Ставит на {bet_type}\n\n"
        f"> <emoji id=5283232570660634549>💰</emoji> Сумма ставки: {summa}$**"
    )

    try:
        # Отправляем в канал (ID из конфига)
        message: Message = await app.send_message(
            chat_id=config.channel_id,
            text=message_text
        )
        return message.id
    except Exception as e:
        print(f"Ошибка при отправке ставки в канал: {e}")
        return 0
    finally:
        # Не останавливаем app, если планируем отправлять часто, 
        # но для разовых вызовов можно стопать.
        if app.is_connected:
            await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        # Тестовая отправка
        loop.run_until_complete(send_bet('testusername', 100, 'больше'))
    except Exception as e:
        print(f"Error: {e}")
