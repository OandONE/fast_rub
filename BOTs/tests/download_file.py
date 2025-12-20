from fast_rub import Client
import asyncio

bot = Client("test")

file_id = "1234567890"
save_as = "test.txt"

async def test():
  await bot.download_file(file_id,save_as)

asyncio.run(test())