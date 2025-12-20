from fast_rub import Client
import asyncio

bot = Client("test")

async def test():
    await bot.add_commands("/help", "راهنمای ربات")
    sending = await bot.set_commands()
    print(sending)
    deleting = await bot.delete_commands()
    print(deleting)

asyncio.run(test())