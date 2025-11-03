from fast_rub import Client
import asyncio

bot = Client("test")

async def test():
  me = await bot.get_me()
  print(me)
asyncio.run(test())