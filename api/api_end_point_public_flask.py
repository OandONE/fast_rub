from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import os
import datetime
import asyncio
from fast_rub import Client
from typing import List, Dict, Any

app = FastAPI()

async def test_bot(token: str):
    bot = Client(token, token)
    try:
        up = await bot.get_updates()
        if up['status'] == "INVALID_INPUT":
            return False
        else:
            return True
    except:
        return False

def open_file(name_file, type_file="dict"):
    try:
        with open(name_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except:
        if type_file == "dict":
            with open(name_file, "w", encoding="utf-8") as file:
                file.write("{}")
            return {}
        else:
            with open(name_file, "w", encoding="utf-8") as file:
                file.write("[]")
            return []

def save_file(name_file, data):
    with open(name_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

list_tokens = open_file("list_tokens.json", "list")
list_bans_tokens = open_file("list_bans_tokens.json", "list")

if not os.path.exists("Updatas"):
    os.makedirs("Updatas")

def log_request(method, url):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {method} request to: {url}\n"
    with open("LOG_FILE.log", 'a', encoding='utf-8') as f:
        f.write(log_entry)


@app.get("/set_token")
async def seting_token(token: str = None):
    global list_tokens
    if not token:
        return JSONResponse(content={"status": False, "error": "token is invalid", "t": 1})
    
    list_bans_tokens_local = open_file("list_bans_tokens.json", "list")
    if token in list_bans_tokens_local:
        return JSONResponse(content={"status": False, "error": "token baned !", "t": 3})
    
    token_input = token.upper()
    log_request("get", f"set_token?token={token_input}")
    
    result_isvalid = await test_bot(token_input)
    if result_isvalid:
        if token_input in list_tokens:
            return JSONResponse(content={
                "status": False,
                "error": "This token exists",
                "url_token": f"https://fast-rub.ParsSource.ir/geting_button_updates/get?token={token_input}",
                "url_token_on": f"https://fast-rub.ParsSource.ir/geting_button_updates/get_on?token={token_input}",
                "url_endpoint": f"https://fast-rub.ParsSource.ir/geting_button_updates/{token_input}"
            })
        else:
            list_tokens.append(token_input)
            save_file("list_tokens.json", list_tokens)
            save_file(f"Updatas/{token_input}.json", [])
            return JSONResponse(content={
                "status": True,
                "result": "created",
                "url_token": f"https://fast-rub.ParsSource.ir/geting_button_updates/get?token={token_input}",
                "url_token_on": f"https://fast-rub.ParsSource.ir/geting_button_updates/get_on?token={token_input}",
                "url_endpoint": f"https://fast-rub.ParsSource.ir/geting_button_updates/{token_input}"
            })
    else:
        return JSONResponse(content={"status": False, "error": "token is invalid", "t": 2})

@app.post("/geting_button_updates/{token}/ReceiveInlineMessage")
async def geting_button_updates_receiveInlineMessage(token: str, request: Request):
    global list_tokens
    token = str(token).upper()
    list_bans_tokens_local = open_file("list_bans_tokens.json", "list")
    if token in list_bans_tokens_local:
        return JSONResponse(content={"status": False, "error": "token baned !", "t": 2})
    log_request("post", f"/geting_button_updates/{token}/ReceiveInlineMessage")
    
    if token in list_tokens:
        l_ = open_file(f"Updatas/{token}.json", "list")
        raw_data = await request.json()
        l_.append(raw_data)
        if len(l_) >= 201:
            l_.pop(0)
        save_file(f"Updatas/{token}.json", l_)
        return JSONResponse(content={"status": True})
    else:
        return JSONResponse(content={"status": False, "error": "token isn't exists", "t": 1})

@app.post("/geting_button_updates/{token}/ReceiveUpdate")
async def geting_button_updates_receiveInlineMessage_(token: str, request: Request):
    global list_tokens
    token = str(token).upper()
    list_bans_tokens_local = open_file("list_bans_tokens.json", "list")
    if token in list_bans_tokens_local:
        return JSONResponse(content={"status": False, "error": "token baned !", "t": 2})
    log_request("post", f"/geting_button_updates/{token}/ReceiveUpdate")
    
    if token in list_tokens:
        l_ = open_file(f"Updatas/{token}_message.json", "list")
        raw_data = await request.json()
        l_.append(raw_data["update"])
        if len(l_) >= 201:
            l_.pop(0)
        save_file(f"Updatas/{token}_message.json", l_)
        return JSONResponse(content={"status": True})
    else:
        return JSONResponse(content={"status": False, "error": "token isn't exists", "t": 1})

@app.get("/geting_button_updates/get")
async def geting_button_updates_get(token: str = None):
    global list_tokens
    if not token:
        return JSONResponse(content={"status": False, "error": "token is invalid.", "t": 1})
    
    list_bans_tokens_local = open_file("list_bans_tokens.json", "list")
    if token in list_bans_tokens_local:
        return JSONResponse(content={"status": False, "error": "token baned !", "t": 2})
    
    token_input = token.upper()
    log_request("get", f"geting_button_updates/get?token={token_input}")
    
    if token_input in list_tokens:
        l_ = open_file(f"Updatas/{token_input}.json", "list")
        save_file(f"Updatas/{token_input}.json", [])
        return JSONResponse(content={"status": True, "updates": l_})
    else:
        return JSONResponse(content={"status": False, "error": "token is invalid.", "t": 1})

@app.get("/geting_button_updates/get_on")
async def geting_button_updates_get_(token: str = None):
    global list_tokens
    if not token:
        return JSONResponse(content={"status": False, "error": "token is invalid.", "t": 1})
    
    list_bans_tokens_local = open_file("list_bans_tokens.json", "list")
    if token in list_bans_tokens_local:
        return JSONResponse(content={"status": False, "error": "token baned !", "t": 2})
    
    token_input = token.upper()
    log_request("get", f"geting_button_updates/get_on?token={token_input}")
    
    if token_input in list_tokens:
        l_ = open_file(f"Updatas/{token_input}_message.json", "list")
        save_file(f"Updatas/{token_input}_message.json", [])
        return JSONResponse(content={"status": True, "updates": l_})
    else:
        return JSONResponse(content={"status": False, "error": "token is invalid.", "t": 1})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=443, ssl_keyfile="key.pem", ssl_certfile="cert.pem")
