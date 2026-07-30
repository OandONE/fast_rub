<<<<<<< HEAD
from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."

async def test():
    sending = await bot.send_location(chat_id, "35.6892", "51.3890")
    print(sending)

=======
from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."

async def test():
    sending = await bot.send_location(chat_id, "35.6892", "51.3890")
    print(sending)

>>>>>>> d3c4aa06cda5b655ec3b0e5c11a02ac64c3f9e1e
asyncio.run(test())