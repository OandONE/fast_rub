from flask import Flask,request
import sys,io,asyncio,json,os,datetime,traceback
from fast_rub import Client

app=Flask(__name__)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def test_bot(token:str):
    bot=Client(token,token)
    try:
        up=await bot.get_updates()
        if up['status']=="INVALID_INPUT":
            return False
        else:
            return True
    except:
        return False

def open_file(name_file,type_file="dict"):
    try:
        with open(name_file,"r",encoding="utf-8") as file:
            return json.load(file)
    except:
        if type_file=="dict":
            with open(name_file,"w",encoding="utf-8") as file:
                file.write("{}")
            return {}
        else:
            with open(name_file,"w",encoding="utf-8") as file:
                file.write("[]")
            return []

def save_file(name_file,data):
    with open(name_file,"w",encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

list_tokens=open_file("list_tokens.json","list")

@app.route("/")
def main():
    return

if not os.path.exists("Updatas"):
    os.makedirs("Updatas") 

def log_request(method, url):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {method} request to: {url}\n"
    with open("LOG_FILE.log", 'a', encoding='utf-8') as f:
        f.write(log_entry)

@app.route("/set_token")
def seting_token():
    token_input=request.args.get('token')
    token_input = token_input.upper()
    log_request("get",f"set_token?token={token_input}")
    if token_input:
        result_isvalid=asyncio.run(test_bot(token_input))
        if result_isvalid:
            if token_input in list_tokens:
                return {"status":False,"error":"This token exists","url_token":f"https://fast-rub.ParsSource.ir/geting_button_updates/get?token={token_input}","url_token_on":f"https://fast-rub.ParsSource.ir/geting_button_updates/get_on?token={token_input}","url_endpoint":f"https://fast-rub.ParsSource.ir/geting_button_updates/{token_input}"}
            else:
                list_tokens.append(token_input)
                list_tokens.append(token_input)
                save_file("list_tokens.json",list_tokens)
                save_file(f"Updatas/{token_input}.json",[])
                return {"status":True,"result":"created","url_token":f"https://fast-rub.ParsSource.ir/geting_button_updates/get?token={token_input}","url_token_on":f"https://fast-rub.ParsSource.ir/geting_button_updates/get_on?token={token_input}","url_endpoint":f"https://fast-rub.ParsSource.ir/geting_button_updates/{token_input}"}
        else:
            return {"status":False,"error":"token is invalid","t":2}
    else:
        return {"status":False,"error":"token is invalid","t":1}

@app.route("/geting_button_updates/<token>/receiveInlineMessage",methods=['POST'])
def geting_button_updates_receiveInlineMessage(token):
    token = str(token).upper()
    log_request("post",f"/geting_button_updates/{token}/receiveInlineMessage")
    if str(token).upper() in list_tokens:
        l_=open_file(f"Updatas/{token}.json","list")
        raw_data = json.loads(str(request.data.decode('utf-8')))
        l_.append(raw_data)
        if len(l_)>=201:
            l_.remove(l_[-1])
        save_file(f"Updatas/{str(token).upper()}.json",l_)
        return {"status":True}
    else:
        return {"status":False,"error":"token isn't exits"}

@app.route("/geting_button_updates/<token>/receiveUpdate",methods=['POST'])
def geting_button_updates_receiveInlineMessage_(token):
    token = str(token).upper()
    log_request("post",f"/geting_button_updates/{token}/receiveUpdate")
    if str(token).upper() in list_tokens:
        l_=open_file(f"Updatas/{token}_message.json","list")
        raw_data = json.loads(str(request.data.decode('utf-8')))
        save_file("k.txt",raw_data)
        l_.append(raw_data)
        if len(l_)>=201:
            l_.remove(l_[-1])
        save_file(f"Updatas/{str(token).upper()}_message.json",l_)
        save_file("kkkkk.txt",l_)
        return {"status":True}
    else:
        return {"status":False,"error":"token isn't exits"}

@app.route("/geting_button_updates/get")
def geting_button_updates_get():
    token_input=request.args.get('token')
    token_input=token_input.upper()
    log_request("get",f"geting_button_updates/get?token={token_input}")
    if token_input:
        if token_input in list_tokens:
            with open(f"Updatas/{token_input.upper()}.json","r",encoding="utf-8") as fi:
                l_=json.loads(fi.read())
            save_file(f"Updatas/{token_input.upper()}.json",[])
            return {"status":True,"updates":l_}
        else:
            return {"status":False,"error":"token is invalid ."}
    else:
        return {"status":False,"error":"token is invalid."}

@app.route("/geting_button_updates/get_on")
def geting_button_updates_get_():
    token_input=request.args.get('token')
    token_input=token_input.upper()
    log_request("get",f"geting_button_updates/get_on?token={token_input}")
    if token_input:
        if token_input in list_tokens:
            l_=open_file(f"Updatas/{token_input.upper()}_message.json","list")
            save_file(f"Updatas/{token_input.upper()}_message.json",[])
            return {"status":True,"updates":l_}
        else:
            return {"status":False,"error":"token is invalid ."}
    else:
        return {"status":False,"error":"token is invalid."}

@app.route('/<path:subpath>', methods=['GET', 'POST'])
def handle_all_paths(subpath):
    url = request.url
    method = request.method
    
    log_request(method, url)

if __name__=="__main__":
    app.run(host="0.0.0.0",port=443)
