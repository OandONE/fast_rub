from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."

async def test():
    sending = await bot.get_chat(chat_id)
    print(sending)
    print(f"first name » {sending.first_name}")
    print(f"user name » {sending.username}")
    # ...

asyncio.run(test())