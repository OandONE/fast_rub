<<<<<<< HEAD
from fast_rub import Client
import asyncio

bot = Client("test")
url = "https://..."
type_url = "ReceiveUpdate"

async def test():
    update_end_point = await bot.set_endpoint(url, type_url)
    print(update_end_point)

=======
from fast_rub import Client
import asyncio

bot = Client("test")
url = "https://..."
type_url = "ReceiveUpdate"

async def test():
    update_end_point = await bot.set_endpoint(url, type_url)
    print(update_end_point)

>>>>>>> d3c4aa06cda5b655ec3b0e5c11a02ac64c3f9e1e
asyncio.run(test())