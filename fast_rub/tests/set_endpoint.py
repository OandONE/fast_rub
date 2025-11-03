from fast_rub import Client
import asyncio

bot = Client("test")
url = "https://..."
type_url = "ReceiveUpdate"

async def test():
    update_end_point = await bot.set_endpoint(url, type_url)
    print(update_end_point)

asyncio.run(test())