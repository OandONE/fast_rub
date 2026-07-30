<<<<<<< HEAD
from fast_rub import Client
import asyncio

bot = Client("test")

async def test():
  me = await bot.get_me()
  print(me)
  print(f"description » {me.description}")
  # ...

=======
from fast_rub import Client
import asyncio

bot = Client("test")

async def test():
  me = await bot.get_me()
  print(me)
  print(f"description » {me.description}")
  # ...
>>>>>>> d3c4aa06cda5b655ec3b0e5c11a02ac64c3f9e1e
asyncio.run(test())