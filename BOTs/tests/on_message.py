from fast_rub import Client
from fast_rub.type import Update
import asyncio

bot = Client("test") # برای استفاده از وبهوک فست روب
bot = Client("test",use_to_fastrub_webhook_on_message="https://Test.com/webhook") # برای استفاده از وبهوک اختصاصی(مقدار use_to_fastrub_webhook_on_message باید وبهوک باشد)

@bot.on_message() # پولینگ - polling
async def test(msg:Update):
    print(msg)
    await msg.reply("this is a reply text from fast rub")

@bot.on_message_updates() # وبهوک - webhook
async def test2(msg: Update):
    print(msg)
    await msg.reply("this is a reply text from fast rub")

asyncio.run(bot.run())
