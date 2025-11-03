from fast_rub import Client
from fast_rub.button import KeyPad
import asyncio

bot = Client("test")

chat_id = "b..."
text = "test"

async def test():
    buttons = KeyPad()
    buttons.add_1row().simple("100", "buttun 1")
    buttons.add_4row().simple("101", "buttun 1", "102", "buttun 2", "103", "buttun 3", "104", "buttun 4")
    sending = await bot.send_message_keypad(chat_id, text, Keypad=buttons.get())
    print(sending)

asyncio.run(test())