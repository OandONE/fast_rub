<<<<<<< HEAD
from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."

async def test():
    sending = await bot.get_chat(chat_id)
    print(sending)
    print(f"first name » {sending.first_name}")
    print(f"user name » {sending.username}")
    # ...

=======
from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."

async def test():
    sending = await bot.get_chat(chat_id)
    print(sending)
    print(f"first name » {sending.first_name}")
    print(f"user name » {sending.username}")
    # ...

>>>>>>> d3c4aa06cda5b655ec3b0e5c11a02ac64c3f9e1e
asyncio.run(test())