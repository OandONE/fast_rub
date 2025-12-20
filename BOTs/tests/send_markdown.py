from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."
text = "__Hello__ *from* **FastRub**"
text_HTML = "<b>test</b> <a href='https://rubika.ir'>rubika</a>"

async def test():
    sending = await bot.send_text(text,chat_id)
    print(sending)
    sending = await bot.send_text(text_HTML,chat_id,parse_mode="HTML")
    print(sending)

asyncio.run(test())