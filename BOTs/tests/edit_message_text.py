from fast_rub import Client
from fast_rub.button import KeyPad
import asyncio

bot = Client("test")

chat_id = "b..."
message_id = "1234567890"
new_text = "new text"

async def test():
    button = KeyPad()
    button.append(
        button.simple("100", "This Is A Test.")
    )
    sending = await bot.edit_message_text(chat_id, message_id, new_text)
    print(sending)
    sending_keypad = await bot.edit_message_text(chat_id, message_id, new_text, inline_keypad=button.get())
    print(sending_keypad)


asyncio.run(test())