from fast_rub import Client
from fast_rub.button import KeyPad
import asyncio

bot = Client("test")

chat_id = "b..."
message_id = "1234567890"

async def test():
    buttons = KeyPad()
    buttons.add_1row().simple("100", "this Key Pad inline is edited !")
    sending = await bot.edit_message_keypad_Inline(chat_id, message_id, buttons.get())
    print(sending)

asyncio.run(test())