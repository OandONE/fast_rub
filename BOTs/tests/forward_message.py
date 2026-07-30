<<<<<<< HEAD
from fast_rub import Client
import asyncio

bot = Client("test")

from_chat_id = "b..."
message_id = "1234567890"
to_chat_id = "b..."

async def test():
    sending = await bot.forward_message(from_chat_id, message_id, to_chat_id)
    print(sending)

=======
from fast_rub import Client
import asyncio

bot = Client("test")

from_chat_id = "b..."
message_id = "1234567890"
to_chat_id = "b..."

async def test():
    sending = await bot.forward_message(from_chat_id, message_id, to_chat_id)
    print(sending)

>>>>>>> d3c4aa06cda5b655ec3b0e5c11a02ac64c3f9e1e
asyncio.run(test())