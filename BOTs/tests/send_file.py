from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."
file_path = "test.json"
image_path = "test.png"

async def test():
    sending = await bot.send_file(chat_id, file_path, name_file="data.json", text="this is a caption")
    sending2 = await bot.send_image(chat_id, image_path, name_file="picture.png", text="this is a caption")
    print(sending)
    print(sending2)

asyncio.run(test())