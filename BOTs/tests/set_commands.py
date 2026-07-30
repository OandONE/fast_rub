<<<<<<< HEAD
from fast_rub import Client
import asyncio

bot = Client("test")

async def test():
    await bot.add_commands("/help", "راهنمای ربات")
    sending = await bot.set_commands()
    print(sending)
    deleting = await bot.delete_commands()
    print(deleting)

=======
from fast_rub import Client
import asyncio

bot = Client("test")

async def test():
    await bot.add_commands("/help", "راهنمای ربات")
    sending = await bot.set_commands()
    print(sending)
    deleting = await bot.delete_commands()
    print(deleting)

>>>>>>> d3c4aa06cda5b655ec3b0e5c11a02ac64c3f9e1e
asyncio.run(test())