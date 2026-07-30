from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import os
from fast_rub import Client
from typing import List

app = FastAPI()

BASE_DOMAIN = "https://api.fast-rub.ParsSource.ir"

# ==================== توابع کمکی ====================

def load_tokens() -> List[str]:
    """بارگذاری لیست توکن‌ها"""
    return load_json_file("list_tokens.json", [])

def load_banned_tokens() -> List[str]:
    """بارگذاری لیست توکن‌های مسدود شده"""
    return load_json_file("list_bans_tokens.json", [])

def load_json_file(filename: str, default):
    """بارگذاری فایل JSON"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=4)
        return default

def save_json_file(filename: str, data):
    """ذخیره فایل JSON"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def log_request(method: str, endpoint: str):
    """ثبت لاگ درخواست"""
    pass

async def is_token_valid(token: str) -> bool:
    """بررسی معتبر بودن توکن"""
    bot = Client(token, token)
    try:
        await bot.get_updates()
        return True
    except:
        return False

def save_update(token: str, data: dict, update_type: str = "message"):
    """ذخیره آپدیت"""
    filename = f"Updatas/{token}_{update_type}.json"
    updates = load_json_file(filename, [])
    
    updates.append(data)
    if len(updates) > 200:
        updates = updates[-200:]
    
    save_json_file(filename, updates)

def get_updates(token: str, update_type: str = "message") -> List[dict]:
    """دریافت آپدیت‌ها"""
    filename = f"Updatas/{token}_{update_type}.json"
    updates = load_json_file(filename, [])
    
    save_json_file(filename, [])
    
    return updates

# ==================== endpointها ====================

@app.get("/set_token")
async def set_token(token: str):
    """
    ثبت توکن جدید
    
    - **token**: توکن ربات
    - **returns**: آدرس endpointهای webhook
    """
    normalized_token = token.upper()
    
    banned_tokens = load_banned_tokens()
    if normalized_token in banned_tokens:
        return JSONResponse(
            status_code=403,
            content={"status": False, "error": "token baned !"}
        )
    
    if not await is_token_valid(normalized_token):
        return JSONResponse(
            status_code=400,
            content={"status": False, "error": "token is invalid"}
        )
    
    result = {
        "status": True,
        "url_endpoint_message": f"{BASE_DOMAIN}/updates/{normalized_token}/ReceiveUpdate",
        "url_endpoint_button": f"{BASE_DOMAIN}/updates/{normalized_token}/ReceiveInlineMessage",
        "url_webhook_message": f"{BASE_DOMAIN}/ReceiveUpdate/{normalized_token}",
        "url_webhook_button": f"{BASE_DOMAIN}/ReceiveInlineMessage/{normalized_token}",
        "url_webhook_all": f"{BASE_DOMAIN}/AllMessages/{normalized_token}"
    }
    tokens = load_tokens()
    if normalized_token in tokens:
        return JSONResponse(
            status_code=200,
            content=result
        )
    
    # ثبت توکن جدید
    tokens.append(normalized_token)
    save_json_file("list_tokens.json", tokens)
    
    save_json_file(f"Updatas/{normalized_token}_message.json", [])
    save_json_file(f"Updatas/{normalized_token}_button.json", [])
    
    return JSONResponse(
        status_code=200,
        content=result
    )

# ==================== Webhook Receivers ====================

@app.post("/updates/{token}/ReceiveUpdate")
async def receive_message_update(token: str, request: Request):
    """
    دریافت آپدیت پیام‌ها از ربات
    """
    
    normalized_token = token.upper()
    
    banned_tokens = load_banned_tokens()
    if normalized_token in banned_tokens:
        return JSONResponse(
            status_code=403,
            content={"status": False, "error": "token baned !"}
        )
    
    tokens = load_tokens()
    if normalized_token not in tokens:
        return JSONResponse(
            status_code=404,
            content={"status": False, "error": "token isn't exists"}
        )
    
    try:
        data = await request.json()
        save_update(normalized_token, data, "message")
        
        return JSONResponse(
            status_code=200,
            content={"status": True}
        )
    except:
        return JSONResponse(
            status_code=400,
            content={"status": False, "error": "Invalid JSON"}
        )

@app.post("/updates/{token}/ReceiveInlineMessage")
async def receive_button_update(token: str, request: Request):
    """
    دریافت آپدیت کلیک‌های دکمه‌ها از ربات
    """
    
    normalized_token = token.upper()
    
    banned_tokens = load_banned_tokens()
    if normalized_token in banned_tokens:
        return JSONResponse(
            status_code=403,
            content={"status": False, "error": "token baned !"}
        )
    
    tokens = load_tokens()
    if normalized_token not in tokens:
        return JSONResponse(
            status_code=404,
            content={"status": False, "error": "token isn't exists"}
        )
    
    try:
        data = await request.json()
        save_update(normalized_token, data, "button")
        
        return JSONResponse(
            status_code=200,
            content={"status": True}
        )
    except:
        return JSONResponse(
            status_code=400,
            content={"status": False, "error": "Invalid JSON"}
        )

# ==================== Webhook Getters ====================

@app.get("/ReceiveUpdate/{token}")
async def get_message_updates(token: str):
    """
    دریافت آپدیت‌های پیام‌ها
    """
    
    normalized_token = token.upper()
    
    banned_tokens = load_banned_tokens()
    if normalized_token in banned_tokens:
        return JSONResponse(
            status_code=403,
            content={"status": False, "error": "token baned !"}
        )
    
    tokens = load_tokens()
    if normalized_token not in tokens:
        return JSONResponse(
            status_code=404,
            content={"status": False, "error": "token is invalid."}
        )
    
    updates = get_updates(normalized_token, "message")
    
    return JSONResponse(
        status_code=200,
        content={
            "status": True,
            "updates": updates
        }
    )

@app.get("/ReceiveInlineMessage/{token}")
async def get_button_updates(token: str):
    """
    دریافت آپدیت‌های دکمه‌ها
    """
    
    normalized_token = token.upper()
    
    banned_tokens = load_banned_tokens()
    if normalized_token in banned_tokens:
        return JSONResponse(
            status_code=403,
            content={"status": False, "error": "token baned !"}
        )
    
    tokens = load_tokens()
    if normalized_token not in tokens:
        return JSONResponse(
            status_code=404,
            content={"status": False, "error": "token is invalid."}
        )
    
    updates = get_updates(normalized_token, "button")
    
    return JSONResponse(
        status_code=200,
        content={
            "status": True,
            "updates": updates
        }
    )

@app.get("/AllMessages/{token}")
async def get_all_updates(token: str):
    """
    دریافت تمامی آپدیت‌ها
    """
    
    normalized_token = token.upper()
    
    banned_tokens = load_banned_tokens()
    if normalized_token in banned_tokens:
        return JSONResponse(
            status_code=403,
            content={"status": False, "error": "token baned !"}
        )
    
    tokens = load_tokens()
    if normalized_token not in tokens:
        return JSONResponse(
            status_code=404,
            content={"status": False, "error": "token is invalid."}
        )
    
    messages = get_updates(normalized_token, "message")
    buttons = get_updates(normalized_token, "button")
    
    return JSONResponse(
        status_code=200,
        content={
            "status": True,
            "updates": {
                "messages": messages,
                "button_clicks": buttons
            }
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    if not os.path.exists("Updatas"):
        os.makedirs("Updatas")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )
