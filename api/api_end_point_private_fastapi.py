from fastapi import FastAPI
import json
from typing import List, Dict, Any

my_token = ""  # توکن خود را در این متغیر وارد کنید

app = FastAPI()

# تابع ذخیره فایل
def save_file(name_file: str, data: List[Dict[str, Any]]):
    with open(name_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# تابع باز کردن فایل
def open_file(name_file: str) -> List[Dict[str, Any]]:
    try:
        with open(name_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except:
        data = []
        save_file(name_file, data)
        return data

# بارگذاری پیام‌ها
messages = open_file("messages.json")
messages_button = open_file("messages_button.json")

@app.post("/message/{token}")
async def saving_mes(token: str, request_data: Dict[str, Any]):
    if token == my_token:
        messages.append(request_data)
        save_file("messages.json", messages)
        return {"status": True}
    return {"status": False, "error": "token isn't valid"}

@app.post("/message_buttons/{token}")
async def saving_mes_btn(token: str, request_data: Dict[str, Any]):
    if token == my_token:
        messages_button.append(request_data)
        save_file("messages_button.json", messages_button)
        return {"status": True}
    return {"status": False, "error": "token isn't valid"}

@app.get("/get_messages/{token}")
async def getting_msg(token: str):
    if token == my_token:
        return {"status": True, "updates": messages}
    return {"status": False, "error": "token isn't valid"}

@app.get("/get_messages_btn/{token}")
async def getting_msg_btn(token: str):
    if token == my_token:
        return {"status": True, "updates": messages_button}
    return {"status": False, "error": "token isn't valid"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # برای پورت 443 باید SSL تنظیم شود
