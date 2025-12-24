from pyrogram import Client
import config
from pyrogram.types import Message
import asyncio

api_id = config.api_id
api_hash = config.api_hash

app = Client('bot', api_id=api_id, api_hash=api_hash)

async def send_bet(username, summa, bet_type) -> int:
    await app.start()

    message_text = (
        "**[<emoji id=5343636681473935403>🔥</emoji>] Новая ставка!\n\n"
        f"> <emoji id=5341357711697134290>💎</emoji> Игрок {username}\n\n"
        f"> <emoji id=5357592447557848986>⚡️</emoji> Ставит на {bet_type}\n\n"
        f"> <emoji id=5283232570660634549>💰</emoji> Сумма ставки: {summa}$**"
    )

    try:
        message: Message = await app.send_message(
            chat_id=config.channel_id,
            text=message_text
        )

        return message.id
    finally:
        await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(send_bet('testusername', 100, 'больше'))
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        try:
            loop.run_until_complete(app.stop())
        except Exception as e:
            print(f"An error occurred while stopping the client: {e}")