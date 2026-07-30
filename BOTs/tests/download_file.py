<<<<<<< HEAD
from fast_rub import Client
import asyncio

bot = Client("test")

file_id = "1234567890"
save_as = "test.txt"

async def test():
  await bot.download_file(file_id,save_as)

=======
from fast_rub import Client
import asyncio

bot = Client("test")

file_id = "1234567890"
save_as = "test.txt"

async def test():
  await bot.download_file(file_id,save_as)

>>>>>>> d3c4aa06cda5b655ec3b0e5c11a02ac64c3f9e1e
asyncio.run(test())