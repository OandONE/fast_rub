from fast_rub import Client
from fast_rub.type import UpdateButton

bot = Client("test")

@bot.on_button()
async def test(msg:UpdateButton):
    print(msg)
    await msg.send_text("this is a text from fast rub")

bot.run()