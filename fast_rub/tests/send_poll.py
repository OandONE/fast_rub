from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."

async def test():
    list_foods = ["چلو قرمه سبزی", "زرشک پلو با مرغ"]
    sending = await bot.send_poll("chat id", "به چه غذایی علاقه دارید؟", list_foods)
    print(sending)

asyncio.run(test())