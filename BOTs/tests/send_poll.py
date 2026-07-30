<<<<<<< HEAD
from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."

async def test():
    list_foods = ["چلو قرمه سبزی", "زرشک پلو با مرغ"]
    sending = await bot.send_poll("chat id", "به چه غذایی علاقه دارید؟", list_foods)
    print(sending)

=======
from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."

async def test():
    list_foods = ["چلو قرمه سبزی", "زرشک پلو با مرغ"]
    sending = await bot.send_poll("chat id", "به چه غذایی علاقه دارید؟", list_foods)
    print(sending)

>>>>>>> d3c4aa06cda5b655ec3b0e5c11a02ac64c3f9e1e
asyncio.run(test())