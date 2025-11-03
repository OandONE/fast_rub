from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."
message_id = "1234567890"

async def test():
    sending = await bot.delete_message(chat_id, message_id)
    print(sending)

asyncio.run(test())