from fast_rub import Client
from fast_rub.type import Update
from fast_rub.utils import filters
import asyncio

bot = Client("test")

@bot.on_message(filters.has_bold())
async def test1(msg:Update):
    await msg.reply("متن شما دارای بولد میباشد")

@bot.on_message(filters.regex("(hi | hello | سلام | درود)"))
async def test2(msg:Update):
    await msg.reply("درود")

@bot.on_message(filters.starts_with("+"))
async def test(msg:Update):
    # کد های برای مثال ارسال پیام برای هوش مصنوعی ... 
    text_gpt = "سلام خوبی" # برای مثال
    await msg.reply(text_gpt)

asyncio.run(bot.run())
