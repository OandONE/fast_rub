from fast_rub import Client
from fast_rub.button import KeyPad
import asyncio

chat_id = "b..."
text = "test"

bot = Client("test")

async def test():
    sending = await bot.send_text(text, chat_id)
    buttons = KeyPad()
    buttons.add_1row().simple("100", "buttun 1")
    buttons.add_4row().simple("101", "buttun 1", "102", "buttun 2", "103", "buttun 3", "104", "buttun 4")
    sending2 = await bot.send_text(text, chat_id, inline_keypad=buttons.get())
    print(sending)
    print(sending2)

asyncio.run(test())