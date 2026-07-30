<<<<<<< HEAD
from fast_rub import Client
import asyncio

bot = Client("test")

file_id = "1234567890"

async def test():
  url = await bot.get_download_file_url(file_id)
  print(url)

=======
from fast_rub import Client
import asyncio

bot = Client("test")

file_id = "1234567890"

async def test():
  url = await bot.get_download_file_url(file_id)
  print(url)

>>>>>>> d3c4aa06cda5b655ec3b0e5c11a02ac64c3f9e1e
asyncio.run(test())