from flask import Flask, request
import json

my_token = "" # توکن خود را در این متغیر وارد کنید

app = Flask(__name__)

def save_file(name_file: str, data: list):
    with open(name_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def open_file(name_file: str) -> list:
    try:
        with open(name_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except:
        data = []
        save_file(name_file, data)
        return data

messages = open_file("messages.json")
messages_button = open_file("messages_button.json")

@app.route("/message/<token>",methods=['POST'])
def saveing_mes(token):
    if token == my_token :
        raw_data = json.loads(str(request.data.decode('utf-8')))
        messages.append(raw_data)
        return {"status":True}
    return {"status":False,"error":"token isn't valid"}

@app.route("/message_buttons/<token>",methods=['POST'])
def saveing_mes_btn(token):
    if token == my_token :
        raw_data = json.loads(str(request.data.decode('utf-8')))
        messages_button.append(raw_data)
        return {"status":True}
    return {"status":False,"error":"token isn't valid"}

@app.route("/get_messages/<token>")
def getting_msg(token):
    if token == my_token :
        return {"status":True,"updates":messages}
    return {"status":False,"error":"token isn't valid"}

@app.route("/get_messages_btn/<token>")
def getting_msg_btn(token):
    if token == my_token :
        return {"status":True,"updates":messages_button}
    return {"status":False,"error":"token isn't valid"}

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=443)

