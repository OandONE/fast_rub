<<<<<<< HEAD
from fast_rub import Client
from fast_rub.types import UpdateButton
import asyncio

bot = Client("test") # برای استفاده از وبهوک فست روب
bot = Client("test",use_to_fastrub_webhook_on_button="https://Test.com/webhook") # برای استفاده از وبهوک اختصاصی(مقدار use_to_fastrub_webhook_on_button باید وبهوک باشد)

@bot.on_button()
async def test(msg: UpdateButton):
    print(msg)
    await msg.send_text("this is a text from fast rub")

asyncio.run(bot.run())
=======
from fast_rub import Client
from fast_rub.type import UpdateButton
import asyncio

bot = Client("test") # برای استفاده از وبهوک فست روب
bot = Client("test",use_to_fastrub_webhook_on_button="https://Test.com/webhook") # برای استفاده از وبهوک اختصاصی(مقدار use_to_fastrub_webhook_on_button باید وبهوک باشد)

@bot.on_button()
async def test(msg: UpdateButton):
    print(msg)
    await msg.send_text("this is a text from fast rub")

asyncio.run(bot.run())
>>>>>>> d3c4aa06cda5b655ec3b0e5c11a02ac64c3f9e1e
