from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."

async def test():
    sending = await bot.send_contact(chat_id, "first name", "last name", "+989017760881")
    print(sending)

asyncio.run(test())