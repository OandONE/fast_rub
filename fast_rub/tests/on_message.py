from fast_rub import Client
from fast_rub.type import Update

bot = Client("test")

@bot.on_message()
async def test(msg:Update):
    print(msg)
    await msg.reply("this is a reply text from fast rub")

bot.run()