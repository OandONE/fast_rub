from fast_rub import Client
import asyncio

bot = Client("test")

from_chat_id = "b..."
message_id = "1234567890"
to_chat_id = "b..."

async def test():
    sending = await bot.forward_message(from_chat_id, message_id, to_chat_id)
    print(sending)

asyncio.run(test())