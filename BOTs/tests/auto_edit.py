<<<<<<< HEAD
from fast_rub import Client
from fast_rub.types import Update
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

=======
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

>>>>>>> d3c4aa06cda5b655ec3b0e5c11a02ac64c3f9e1e
asyncio.run(bot.run())