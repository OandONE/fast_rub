from fast_rub import Client
from fast_rub.type import UpdateButton

bot = Client("test") # برای استفاده از وبهوک فست روب
bot = Client("test",use_to_fastrub_webhook_on_button="https://Test.com/webhook") # برای استفاده از وبهوک اختصاصی(مقدار use_to_fastrub_webhook_on_button باید وبهوک باشد)

@bot.on_button()
async def test(msg: UpdateButton):
    print(msg)
    await msg.send_text("this is a text from fast rub")

bot.run()