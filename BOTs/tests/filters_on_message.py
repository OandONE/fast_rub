<<<<<<< HEAD
from fast_rub import Client
from fast_rub.types import Update
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
async def test3(msg:Update):
    # کد های برای مثال ارسال پیام برای هوش مصنوعی ... 
    text_gpt = "سلام خوبی" # برای مثال
    await msg.reply(text_gpt)

class custom_filter(filters.Filter):
    def __call__(self, update: Update) -> bool:
        return update.text == "/start"

@bot.on_message(custom_filter())
async def test4(msg: Update):
    await msg.reply("your text is /start")

=======
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
async def test3(msg:Update):
    # کد های برای مثال ارسال پیام برای هوش مصنوعی ... 
    text_gpt = "سلام خوبی" # برای مثال
    await msg.reply(text_gpt)

class custom_filter(filters.Filter):
    def __call__(self, update: Update) -> bool:
        return update.text == "/start"

@bot.on_message(custom_filter())
async def test4(msg: Update):
    await msg.reply("your text is /start")

>>>>>>> d3c4aa06cda5b655ec3b0e5c11a02ac64c3f9e1e
asyncio.run(bot.run())