from fast_rub import Client
from fast_rub.type import Update
import asyncio

bot = Client("test")

@bot.on_message()
async def test(msg: Update):
    sending = await msg.reply("this is a test befor edit.")
    await bot.auto_edit(
        msg.chat_id,
        sending.message_id,
        "this is a text after edit. 5s.",
        5
    )

asyncio.run(bot.run())