from fast_rub import Client
from fast_rub.button import KeyPad
import asyncio

chat_id = "b..."
text = "test"

bot = Client("test")

async def test():
    sending = await bot.send_text(text, chat_id) # ارسال متن معمولی
    print(sending)
    buttons = KeyPad()
    buttons.append(
        buttons.simple("100", "button 1")
    )
    buttons.append(
        buttons.simple("101", "button 1"),
        buttons.simple("103", "button 2"),
        buttons.simple("104", "button 3")
    )
    sending2 = await bot.send_text(text, chat_id, inline_keypad=buttons.get()) # ارسال کیپد اینلاین
    print(sending2)
    sending3 = await bot.send_text(text, chat_id, keypad=buttons.get()) # ارسال کیپد معمولی
    print(sending3)

asyncio.run(test())