from fast_rub.pyrubi import Client, filters
from fast_rub.pyrubi.types import Message
import aiofiles
import json
import asyncio
import time
from typing import Optional
import httpx

bot = Client("self")

commands = """📋 **دستورات سلف 01**

**تنظیمات حالت متن**
هر یک از حالت‌های زیر را می‌توان با ارسال نام حالت + روشن یا خاموش فعال/غیرفعال کرد:
بولد - متن ضخیم
اسپویل - متن پنهان (برای نمایش نیاز به کلیک)
کپی - متن مونواسپیس (مناسب برای کد)
ایتالیک - متن مورب
خط خورده - متن با خط وسط
زیر خط - متن زیرخط دار
برعکس - معکوس کردن متن
مثال » `بولد روشن`

**تنظیم فعالیت تنظیم فعالیت**
تایپ کردن - نمایش وضعیت "در حال تایپ"
در حال آپلود - نمایش وضعیت "در حال آپلود"
در حال ضبط صدا - نمایش وضعیت "در حال ضبط صدا"
خاموش - غیرفعال کردن وضعیت
مثال: تنظیم فعالیت تایپ کردن

**دستورات اطلاعاتی**
پینگ یا ping - نمایش سرعت پاسخ سرور
اطلاعات یا info یا ریپلای یا reply - دریافت اطلاعات کاربر پیام ریپلای شده
وضعیت یا status - نمایش تنظیمات فعلی ربات

**سرگرمی‌ها**
جوک - ارسال یک جوک تصادفی
بیو - ارسال یک بیوگرافی تصادفی
دانستنی - ارسال یک دانستنی جالب
فال - ارسال فال روزانه
عدد [عدد] - تبدیل عدد به حروف فارسی (مثال: عدد 1234)
تاریخ - نمایش تاریخ و اطلاعات کامل امروز

کانال » @Fast_Rub"""

async def save_file(name_file: str,data: dict) -> None:
    async with aiofiles.open(name_file,"w",encoding="utf-8") as file:
        await file.write(json.dumps(data,indent=4,ensure_ascii=False))

async def open_file(name_file: str) -> dict:
    try:
        async with aiofiles.open(name_file,"r",encoding="utf-8") as file:
            return json.loads(await file.read())
    except:
        data = {}
        await save_file(name_file,data)
        return data

setting = {}

async def load_files():
    global setting
    setting = await open_file("setting.json")

asyncio.run(load_files())

async def save_setting():
    await save_file("setting.json",setting)

if not "text" in setting:
    setting["text"] = {
        "bold": False,
        "spoiler": False,
        "mono": False,
        "italic": False,
        "strike": False,
        "underline": False,
        "reverse": False
    }
    asyncio.run(save_setting())

if not "active" in setting:
    setting["active"] = "off"
    asyncio.run(save_setting())

text_models = {
    "bold": "بولد",
    "regular": "معمولی",
    "spoiler": "اسپویل",
    "mono": "کپی",
    "italic": "ایتالیک",
    "strike": "خط خورده",
    "underline": "زیر خط",
    "reverse": "برعکس"
}

models = {
    "bold": "**#text**",
    "spoiler": "###text##",
    "mono": "``#text``",
    "italic": "__#text__",
    "strike": "~~#text~~",
    "underline": "--#text--"
}

activing_models = {
    "off": "خاموش",
    "Typing": "تایپ کردن",
    "Uploading": "در حال آپلود",
    "Recording": "در حال ضبط صدا"
}

async def edit_text(object_guid: str,msg_id: str,new_text: str):
    await bot.edit_message(object_guid,new_text,msg_id)

async def edit_msg(msg: Message, new_text: str):
    object_guid = msg.object_guid
    msg_id = msg.message_id
    await edit_text(object_guid,msg_id,new_text)

async def model_text_en_to_fa(en_model: str) -> Optional[str]:
    for en,fa in text_models.items():
        if en == en_model:
            return fa
    return None

async def status_text_models() -> str:
    text_ = ""
    for model,status in setting["text"].items():
        fa_model = await model_text_en_to_fa(model)
        fa_status = "روشن ✅" if status else "خاموش ❌"
        text_ += f"{fa_model} » {fa_status}\n"
    return text_


async def translate_model_active_fa_to_en(fa_name: str):
    for en,fa in activing_models.items():
        if fa == fa_name:
            return en
    return None

async def translate_model_active_en_to_fa(en_name: str):
    for en,fa in activing_models.items():
        if en == en_name:
            return fa
    return None

async def reverse_text(text: str) -> str:
    reverse_text = ""
    list_text = list(text)
    list_text.reverse()
    for t in list_text:
        reverse_text += t
    return reverse_text

async def send_request(url: str) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        return await client.get(url,timeout=30)

@bot.on_message(filters.is_me())
async def main(msg: Message):
    text = msg.text
    object_guid = msg.object_guid
    msg_id = msg.message_id
    reply_msg_id = msg.reply_message_id
    result = None
    for en,fa in text_models.items():
        if text.startswith(fa):
            luck = text.replace(fa + " ","")
            if luck == "روشن":
                setting["text"][en] = True
            elif luck == "خاموش":
                setting["text"][en] = False
            else:
                return None
            await save_setting()
            await edit_msg(msg,f"حالت {fa} {luck} شد ✅")
            return None

    if text.startswith("تنظیم فعالیت "):
        model = text.replace("تنظیم فعالیت ","")
        if not model in activing_models.values():
            await edit_msg(msg,"فعالیت نامعتبر ❌")
            return None
        en_model = await translate_model_active_fa_to_en(model)
        setting["active"] = en_model
        await save_setting()
        await edit_msg(msg,f"نوع فعالیت به {model} تغییر پیدا کرد ✅")
        return None

    elif text in ["پینگ","ping"]:
        now = time.perf_counter()
        await edit_msg(msg,"در حال تست پینگ ...")
        next_time = time.perf_counter()
        ping = next_time - now
        await edit_text(object_guid,msg_id,f"پینگ : {ping} s")
        return None

    elif text in ["ریپلای","reply","info","اطلاعات"]:
        if reply_msg_id:
            rep_info = await msg.reply_info()
            reply_info = await bot.get_chat_info(rep_info.author_guid)
            first_name = reply_info["user"]["first_name"]
            last_name = reply_info["user"]["last_name"] if "last_name" in reply_info["user"] else "ندارد"
            last_name = last_name if last_name else "ندارد"
            username = reply_info["user"]["username"] if "username" in reply_info["user"] else "ندارد"
            username = "@" + username if username else "ندارد"
            bio = reply_info["user"]["bio"] if "bio" in reply_info["user"] else "ندارد"
            bio = bio if bio else "ندارد"
            birth_date = reply_info["user"]["birth_date"] if "birth_date" in reply_info["user"] else "تنظیم نشده"
            birth_date = birth_date if birth_date else "تنظیم نشده"
            user_guid = reply_info["user"]["user_guid"]
            await msg.reply(f"""کاربر {first_name} »
نام خانوادگی » {last_name}
نام کاربری » {username}
بیو » {bio}
تاریخ تولد » {birth_date}
شناسه گوید » ``{user_guid}``""")
        else:
            await edit_msg(msg,"روی پیامی ریپلای نکردید ❌")
            return None
    elif text in ["وضعیت","status"]:
        model_text = await status_text_models()
        active_text = await translate_model_active_en_to_fa(setting["active"])
        await edit_msg(msg,f"""**وضعیت سلف**
نوع متن »
{model_text}

فعالیت » {active_text}""")
        return None

    # hobbies
    elif text == "جوک":
        result = (await send_request("https://api.parssource.ir/jok2/")).json()["result"]
    elif text == "بیو":
        result = (await send_request("https://api.parssource.ir/bio/")).json()["result"]["bio"]
    elif text == "دانستنی":
        result = (await send_request("https://api.parssource.ir/danestani/")).json()["result"]["danestani"]
    elif text == "فال":
        result = (await send_request("https://api.parssource.ir/fal/")).json()["result"]["fal"]
    elif text.startswith("عدد "):
        number = text.replace("عدد ","")
        result = (await send_request(f"https://api.parssource.ir/number_to_words/?number={number}")).json()["result"]
    elif text == "تاریخ":
        result_ = (await send_request("https://api.parssource.ir/date/")).json()["result"]
        result = f"""تاریخ : {result_["jalaly"]["date"]} 📆
ساعت : {result_["jalaly"]["time"]} 🕒
روز هفته : {result_["jalaly"]["dey_week"]} 📆
ماه : {result_["jalaly"]["mont"]} 📅
حیوان سال : {result_["jalaly"]["animal"]} 🐾
فصل : {result_["jalaly"]["season"]} 🌳
مناسبت امروز : {result_["jalaly"]["mon"]} 🌇
مانده به عید : {result_["jalaly"]["eid"]} 🌍
تاریخ میلادی : {result_["Gregorian"]["date"]} 📆
ساعت میلادی : {result_["Gregorian"]["time"]} 🕒"""
    if result:
        await edit_msg(msg,result)
        return None

    # model text
    is_edit = False
    if setting['text']["reverse"]:
        text = await reverse_text(text)
        is_edit = True
    for model,text_model in models.items():
        if not setting["text"][model]:
            continue
        text_new = text_model.replace("#text",text)
        text = text_new
        is_edit = True
    if is_edit:
        await edit_msg(msg,text)

@bot.on_message(filters.not_filter(filters.is_me()))
async def activing(msg: Message):
    object_guid = msg.object_guid
    if setting["active"] != "off":
        await bot.send_chat_activity(object_guid,setting["active"])

bot.run()
