from fast_rub import Client
import asyncio

bot = Client("test")

file_id = "1234567890"

async def test():
  url = await bot.get_download_file_url(file_id)
  print(url)

asyncio.run(test())