# fast_rub : 2.4.3
from fast_rub import Client
from fast_rub.types import Update

bot = Client("bot_speaker")

@bot.on_message_updates()
async def main(message: Update):
    try:
        response = await bot.network.request(f"https://api.parssource.ir/spokesperson/?text={message.text}",type_send="GET")
        answer = response.json()["result"]
        if answer:
            await message.reply(answer)
    except Exception as e:
        print(e)

bot.run()