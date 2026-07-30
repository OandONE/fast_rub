<<<<<<< HEAD
from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."
message_id = "1234567890"

async def test():
    sending = await bot.delete_message(chat_id, message_id)
    print(sending)

=======
from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."
message_id = "1234567890"

async def test():
    sending = await bot.delete_message(chat_id, message_id)
    print(sending)

>>>>>>> d3c4aa06cda5b655ec3b0e5c11a02ac64c3f9e1e
asyncio.run(test())