from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."
message_id = "1234567890"
new_text = "new text"

async def test():
    sending = await bot.edit_message_text(chat_id, message_id, new_text)
    print(sending)

asyncio.run(test())