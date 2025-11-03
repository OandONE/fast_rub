from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."

async def test():
    sending = await bot.send_location(chat_id, "35.6892", "51.3890")
    print(sending)

asyncio.run(test())