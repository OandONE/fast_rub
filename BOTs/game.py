# fast_rub : 2.4.3

from fast_rub import Client,filters
from fast_rub.types import Update
from fast_rub.button import KeyPad
import httpx
import jdatetime
import pytz
from translate import Translator
import json
import random
import traceback
import time
from datetime import datetime


bot=Client("bot_sargarmi")
CHAT_ID_owner="b0IS2Uw0DAc04aa76508d5d7640fa51f" # چت آیدی خود را وارد کنید

help_robot="""🎮 راهنمای سرگرمی ربات

🔵 جوک
🔵 دانستنی
🔵 شعر
🔵 بیو
🔵 فال
🔵 تاریخ
🔵 جرات(جرعت)
🔵 حقیقت
🔵 اخبار
🔵 font - /font {text}
🔵 اطلاعات تاریخ تولد - /aboutbirth {date}
🔵 ماشین حساب - /calculator {calcu}
🔵 آب و هوا - /weater {name_city}
🔵 جستجو موزیک - /music {name_music}
🔵 عدد به حروف - /number {number}
🔵 ترجمه - /translate {text}
🔵 اطلاعات من - /about_me

🎲 راهنمای بازی ربات

🔵 موجودی » موجودی

🔵 شرط بندی »
شرط بندی {price} {shart}
شرط بندی 10000 زوج
شرط ها : زوج/فرد/1/2/3/4/5/6

🔵 گردونه » گردونه

🔵 دریافت اطلاعات ماینر » ماینر

🔵 جمع آوردی ماینر » جمع ماینر

🔵 خرید یک ماینر » خرید ماینر

🔵 خرید حداکثر ماینر با موجودی » خرید حداکثر ماینر


🌟 کانال ما : @Fast_Rub""" # این خط پاک نشود برای حمایت از ما و گذاشتن سورس های بیشتر
async def send_requests(url):
    async with httpx.AsyncClient(timeout=60) as cl:
        res=await cl.get(url)
        return res.json()
def detect_language(text):
    unicode_ranges = {
        'fa': ((0x0600, 0x06FF), (0xFB8A, 0xFDFF), (0xFE70, 0xFEFF)),
        'en': ((0x0041, 0x007A),),
        'de': ((0x0041, 0x007A), (0x00C0, 0x00FF)),
        'ja': ((0x3040, 0x309F), (0x30A0, 0x30FF), (0x4E00, 0x9FAF)),
        'ru': ((0x0400, 0x04FF),),
        'ar': ((0x0600, 0x06FF), (0x0750, 0x077F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF))
    }
    lang_counts = {lang: 0 for lang in unicode_ranges}
    for char in text:
        for lang, ranges in unicode_ranges.items():
            for (start, end) in ranges:
                if ord(char) >= start and ord(char) <= end:
                    lang_counts[lang] += 1
                    break
    detected_lang = max(lang_counts, key=lang_counts.get)
    return detected_lang if lang_counts[detected_lang] > 0 else "unknown"
def remove_e(text:str,r1:str,r2:str,okalad_clear:bool=True):
    main_text=text.replace(r1,"").replace(r2,"")
    if okalad_clear:
        main_text=main_text.replace("{","").replace("}","")
    return main_text
def start_swich(text:str,list_:str):
    for value in list_:
        if text.startswith(value):
            return True
    return False
def translate_text_f(input_lang, output_lang, text):
    translator = Translator(
    from_lang=input_lang, to_lang=output_lang)
    translation = translator.translate(text)
    return translation
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
scores=open_file("scores.json")
gardon_users=open_file("gardon.json")
miner=open_file("miner.json")
list_bans=open_file("list_bans.json",type_file="list")
class game:
    def __init__(self):
        pass
    def mojodi(self,guid):
        if guid in scores:
            return scores[guid]
        else:
            m=50000
            scores[guid]=50000
            save_file("scores.json",scores)
            return 50000
    def gardon(self,guid:str):
        if guid in scores:
            if guid in gardon_users:
                tehran_timezone = pytz.timezone('Asia/Tehran')
                current_time = datetime.now(tehran_timezone)
                jalali_date = jdatetime.datetime.fromgregorian(datetime=current_time)
                jalali_date.strftime("%Y/%m/%d %H:%M:%S")
                
                jalali_date=(str(jalali_date).split(" "))[0]
                if jalali_date==gardon_users[guid]:
                    return False
                random.seed(random.randint(0,500))
                gardon_=random.randint(100000,999999)
                gardon_users[guid]=jalali_date
                scores[guid]+=gardon_
                save_file("gardon.json",gardon_users)
                save_file("scores.json",scores)
                return gardon_
            else:
                gardon_users[guid]=""
                save_file("gardon.json",gardon_users)
                return game().gardon(guid=guid)
        else:
            scores[guid]=50000
            save_file("scores.json",scores)
            return game().gardon(guid=guid)
    def shart_bandi(self,price:int,shart:str,guid:str):
        if guid in scores:
            l_=["1","2","3","4","5","6","زوج","فرد"]
            if shart in l_:
                if price>0:
                    if self.mojodi(guid)>=price:
                        random.seed(random.randint(0,500))
                        ra_shart=random.randint(1,6)
                        if shart in l_[:6]:
                            if int(shart)==ra_shart:
                                last_m=scores[guid]
                                scores[guid]+=price*6
                                save_file("scores.json",scores)
                                return {"type":True,"s":True,"mo":self.mojodi(guid),"la":last_m,"sh":str(ra_shart)}
                            else:
                                last_m=scores[guid]
                                scores[guid]-=price
                                save_file("scores.json",scores)
                                return {"type":True,"s":False,"mo":self.mojodi(guid),"la":last_m,"sh":str(ra_shart)}
                        else:
                            zoj=["2","4","6"]
                            if shart=="زوج":
                                if str(ra_shart) in zoj:
                                    last_m=scores[guid]
                                    scores[guid]+=price
                                    save_file("scores.json",scores)
                                    return {"type":True,"s":True,"mo":self.mojodi(guid),"la":last_m,"sh":str(ra_shart)}
                                else:
                                    last_m=scores[guid]
                                    scores[guid]-=price
                                    save_file("scores.json",scores)
                                    return {"type":True,"s":False,"mo":self.mojodi(guid),"la":last_m,"sh":str(ra_shart)}
                            else:
                                if not (str(ra_shart) in zoj):
                                    last_m=scores[guid]
                                    scores[guid]+=price
                                    save_file("scores.json",scores)
                                    return {"type":True,"s":True,"mo":self.mojodi(guid),"la":last_m,"sh":str(ra_shart)}
                                else:
                                    last_m=scores[guid]
                                    scores[guid]-=price
                                    save_file("scores.json",scores)
                                    return {"type":True,"s":False,"mo":self.mojodi(guid),"la":last_m,"sh":str(ra_shart)}
                    else:
                        return {"type":False,"s":"m"}
                else:
                    return {"type":False,"s":"manfi"}
            else:
                return {"type":False,"s":"i"}
        else:
            scores[guid]=50000
            save_file("scores.json",scores)
            game().shart_bandi(price=price,shart=shart,guid=guid)
    def my_miner(self,guid):
        if guid in miner:
            level_miner=miner[guid]['level']
            j_miner=miner[guid]['level'] * (int(time.time())-miner[guid]['time'])
            h_miner=miner[guid]['level'] * (60*60)
            d_miner=miner[guid]['level'] * (60*60*24)
            next_miner_p=(miner[guid]['level']+1) *  1758
            return {"level":level_miner,"j_miner":j_miner,"h_miner":h_miner,"d_miner":d_miner,"n_miner":next_miner_p}
        else:
            miner[guid]={"level":1,"time":int(time.time())}
            save_file("miner.json",miner)
            return game().my_miner(guid)
    def j_miner(self,guid):
        if guid in miner:
            j_miner=miner[guid]['level'] * (int(time.time())-miner[guid]['time'])
            if guid in scores:
                scores[guid]+=j_miner
                miner[guid]['time']=int(time.time())
                save_file("scorce.json",scores)
                save_file("miner.json",miner)
                return {"j":j_miner,"m":self.mojodi(guid)}
            else:
                scores[guid]=50000
                save_file("scores.json",scores)
                return game().j_miner(guid)
        else:
            miner[guid]={"level":1,"time":int(time.time())}
            save_file("miner.json",miner)
            return game().j_miner(guid)
    def buy_miner(self,guid):
        if guid in miner:
            if guid in scores:
                next_miner_p=(miner[guid]['level']+1) *  1758
                if next_miner_p>self.mojodi(guid):
                    return {"buy":False,"m":self.mojodi(guid),"n_miner":next_miner_p,"m_miner":(self.my_miner(guid))['level']}
                else:
                    scores[guid]-=next_miner_p
                    miner[guid]['level']+=1
                    save_file("miner.json",miner)
                    save_file("scores.json",scores)
                    return {"buy":True,"m":self.mojodi(guid),"m_miner":(self.my_miner(guid))['level']}
            else:
                scores[guid]=50000
                save_file("scores.json",scores)
                return game().buy_miner(guid)
        else:
            miner[guid]={"level":1,"time":int(time.time())}
            save_file("miner.json",miner)
            return game().buy_miner(guid)
dass={"help":"راهنما کامل",'jok':"جوک",'danestani':"دانستنی","poem":"شعر","bio":"بیو","fal":"فال","date":"تاریخ",'courage':'جرات','truth':'حقیقت','news':'اخبار',"font {text}":"فونت انگلیسی","aboutbirth {date}":"اطلاعات تاریخ تولد","calculator {calcu}":"ماشین حساب","weater {name_city}":"آب و هوا","music {name_music}":"جستجو موزیک","number {number}":"عدد","translate {text}":"ترجمه","about_me":"اطلاعات من","موجودی":"","گردونه":"","شرط بندی {مقدار شرط} {شرط}":"","ماینر":"","جمع ماینر":"","خرید ماینر":"","خرید حداکثر ماینر":""}
@bot.on_message(filters=filters.is_user())
async def main(message:Update):
    TEXT_MESSAGE=message.text
    CHAT_ID=message.chat_id
    GUID=message.sender_id
    if (GUID in list_bans) or (CHAT_ID in list_bans):
        await bot.send_text(f"""✉️ پیام جدید از لیست ممنوعه ❌ :
{str(message)}""",CHAT_ID_owner)
        return None
    if CHAT_ID==CHAT_ID_owner and TEXT_MESSAGE.startswith("بن "):
        c_g=TEXT_MESSAGE.replace("بن ","")
        list_bans.append(c_g)
        save_file("list_bans.json",list_bans)
        await message.reply("کاربر با موفقیت بن شد ❌")
    if TEXT_MESSAGE in ['اطلاعات من',"/about_me"]:
        about_user=await bot.get_chat(CHAT_ID)
        await message.reply(f"""چت آیدی » {CHAT_ID}
شناسه گوید شما » {message.sender_id}
نام شما : {about_user['data']['chat']['first_name']}
{f"نام خانوادگی شما : {about_user['data']['chat']['last_name']}" if "last_name" in about_user['data']['chat'] else ""}
{f"نام کاربری شما : @{about_user['data']['chat']['username']}" if "username" in about_user['data']['chat'] else ""}""")
    await bot.send_text(f"""✉️ پیام جدید :
{str(message)}""",CHAT_ID_owner)
    u=0
    for com,ds in dass.items():
        if u==10:
            break
        await bot.add_commands(com,ds)
        u+=1
    y=await bot.set_commands()
    await bot.delete_commands()
    if TEXT_MESSAGE in ['راهنما',"دستورات","/help"]:
        buttuns=KeyPad()
        for com,ds in dass.items():
            if detect_language(com)=="fa":
                buttuns.add_1row("100",com)
            else:
                buttuns.add_1row("100","/"+com)
        await message.reply(help_robot,buttuns.get())
    elif TEXT_MESSAGE in ['ربات','/start']:
        await message.reply("جونم؟")
    elif TEXT_MESSAGE in ['جوک','جک','/jok']:
        jok=str((await send_requests("https://api.ParsSource.ir/jok/"))['result']['jok']).replace('\\n', '\n')
        await message.reply(jok)
    elif TEXT_MESSAGE in ['دانستنی','/danestani']:
        danestani=(await send_requests("https://api.ParsSource.ir/danestani/"))['result']['danestani']
        await message.reply(danestani)
    elif TEXT_MESSAGE in ['شعر','/poem']:
        poem=str((await send_requests("https://api.ParsSource.ir/poem/"))['result']['poem']).replace('\\n', '\n')
        await message.reply(poem)
    elif TEXT_MESSAGE in ['بیو','/bio']:
        bio=str((await send_requests("https://api.ParsSource.ir/bio/"))['result']['bio']).replace('\\n', '\n')
        await message.reply(bio)
    elif TEXT_MESSAGE in ['فال','/fal']:
        fal=str((await send_requests("https://api.ParsSource.ir/fal/"))['result']['fal']).replace('\\n', '\n')
        await message.reply(fal)
    elif TEXT_MESSAGE in ['تاریخ','/date']:
        dat=await send_requests("https://api.ParsSource.ir/date/")
        text_date=f"""تاریخ : {dat['result']['jalaly']['date']} 📆
ساعت : {dat['result']['jalaly']['time']} 🕒
روز هفته : {dat['result']['jalaly']['dey_week']} 📆
ماه : {dat['result']['jalaly']['mont']} 📅
حیوان سال : {dat['result']['jalaly']['animal']} 🐾
فصل : {dat['result']['jalaly']['season']} 🌳
مناسبت امروز : {dat['result']['jalaly']['mon']} 🌇
مانده به عید : {str(dat['result']['jalaly']['eid'])} 🌍
تاریخ میلادی : {dat['result']['Gregorian']['date']} 📆
ساعت میلادی : {dat['result']['Gregorian']['time']} 🕒"""
        await message.reply(text_date)
    elif TEXT_MESSAGE in ['جرات','جرعت','/courage']:
        coutage=(await send_requests("https://api.parssource.ir/courage_truth/"))['result']['courage']
        await message.reply(coutage)
    elif TEXT_MESSAGE in ['حقیقت','/truth']:
        truth=(await send_requests("https://api.parssource.ir/courage_truth/"))['result']['truth']
        await message.reply(truth)
    elif TEXT_MESSAGE in ['اخبار','چخبر',"/news"]:
        news=(await send_requests("https://api.parssource.ir/news/"))['result']['news'][0]
        await message.reply(f"""{news['title']}

ادرس خبر : {news['news_url']}
عکس خبر : {news['image_url']}""")
    elif TEXT_MESSAGE.startswith("/font "):
        text_font=remove_e(TEXT_MESSAGE,"/font ","/font ")
        font=(await send_requests(f"https://api.parssource.ir/font/?text={text_font}"))['result']['font']
        await message.reply(font)
    elif TEXT_MESSAGE.startswith("/aboutbirth ") or TEXT_MESSAGE.startswith("اطلاعات تاریخ تولد "):
        date=remove_e(TEXT_MESSAGE,"/aboutbirth ","اطلاعات تاریخ تولد ")
        about_birth=(await send_requests(f"https://api.parssource.ir/about_birth/?birth={date}"))['result']['about_birth']
        await message.reply(about_birth)
    elif TEXT_MESSAGE.startswith("/calculator ") or TEXT_MESSAGE.startswith("ماشین حساب "):
        text_calcu=remove_e(TEXT_MESSAGE,"/calculator ","ماشین حساب ")
        calculator=(await send_requests(f"https://api.parssource.ir/calculator/?calcu={text_calcu}"))
        if calculator['status']:
            await message.reply(calculator['result']['calcued'])
        else:
            await message.reply("""خطا ! لطفا ورودی ها را با فرمت زیر وارد کنید :
روز/ماه/سال""")
    elif TEXT_MESSAGE.startswith("/weater ") or TEXT_MESSAGE.startswith("آب و هوا "):
        name_city=remove_e(TEXT_MESSAGE,"/weater ","آب و هوا ")
        weater=(await send_requests(f"https://api.ParsSource.ir/weater/?name_city={name_city}"))
        if weater['status']:
            await message.reply(weater['result']['about_weater'])
        else:
            await message.reply("خطا ! ورودی نامعتبر")
    elif TEXT_MESSAGE.startswith("/music ") or TEXT_MESSAGE.startswith("موزیک "):
        name_music=remove_e(TEXT_MESSAGE,"/music ","موزیک ")
        music=(await send_requests(f"https://api.ParsSource.ir/search_music/?name_music={name_music}"))['result']
        if len(music)!=0:
            await message.reply(f"""موزیک پیدا شد . لینک دانلود مستقیم موزیک :
{music[0]}""")
        else:
            await message.reply("متاسفانه موزیکی پیدا نشد .")
    elif TEXT_MESSAGE.startswith("/number ") or TEXT_MESSAGE.startswith("عدد "):
        num=remove_e(TEXT_MESSAGE,"/number ","عدد ")
        number_fa=(await send_requests(f"https://api.ParsSource.ir/number_to_words/?number={num}"))
        if number_fa['status']:
            await message.reply(number_fa['result'])
        else:
            await message.reply("خطا ! ورودی نامعتبر")
    elif TEXT_MESSAGE.startswith("/translate ") or TEXT_MESSAGE.startswith("ترجمه "):
        translate_text=remove_e(TEXT_MESSAGE,"/translate ","ترجمه ")
        try:
            lang_text=detect_language(translate_text)
            l_l_h={"fa":"فارسی","en":"انگلیسی","de":"آلمانی","ja":"ژاپنی","ru":"روسی","ar":"عربی"}
            text_trans=f"""متن ورودی : {translate_text}
زبان تشخیص داده شده : {l_l_h.get(lang_text, lang_text)}

"""
            for key,value in l_l_h.items():
                if not key==lang_text:
                    texted=translate_text_f(lang_text,key,translate_text)
                    text_trans+=f"""{value} : {texted} 
"""
            await message.reply(text_trans)
        except Exception as e:
            await message.reply("خطا ! مشکلی پیش آمده است")
    elif TEXT_MESSAGE.startswith("شرط بندی "):
        try:
            vals=TEXT_MESSAGE.split(" ")
            price=int(vals[2])
            shart=str(vals[3])
            try:
                shart=str(int(shart))
            except:pass
            s_=game().shart_bandi(price=price,shart=shart,guid=message.sender_id)
            if s_['type']:
                if s_['s']:
                    await message.reply(f"""تبریک میگم شما بردید ✅🥳
								
تاس رو شده = {s_['sh']} 🎲

مقدار شرط پول = {price:,} 🪙

شرط تاس = {shart} 🎲

موجودی قبلی = {s_['la']:,} 🪙

===========================
		
موجودی اکنونی شما = {s_["mo"]:,} 💰""")
                else:
                    await message.reply(f"""متاسفانه شما باختید ❌🥺
							
تاس رو شده = {s_['sh']} 🎲

مقدار شرط پول = {price:,} 🪙

شرط تاس = {shart} 🎲

موجودی قبلی = {s_['la']:,} 🪙

===========================
		
موجودی اکنونی شما = {s_["mo"]:,} 💰""")
            else:
                if s_['s']=="m":
                    await message.reply(f"""خطا موجودی شما کافی نیست !
موجودی شما : {game().mojodi(guid=message.sender_id):,} 🪙""")
                elif s_['s']=="manfi":
                    await message.reply("شرط بندی با اعداد منفی رخ نمیدهد.")
                else:
                    await message.reply("خطا ! شرط نامعتبر")
        except ValueError:
            await message.reply("خطا ! ورودی نامعتبر")
            price(traceback.format_exc())
    elif TEXT_MESSAGE=="گردونه":
        g=game().gardon(guid=message.sender_id)
        if g==False:
            await message.reply("خطا ! شما امروز گردونه خود را دریافت کرده اید")
        else:
            await message.reply(F"""گردونه با موفقیت زده شد 🎲 شما از گردونه مقدار {g:,} سکه برنده شدید
موجودی شما : {game().mojodi(guid=message.sender_id):,} 🪙""")
    elif TEXT_MESSAGE=="موجودی":
        await message.reply(f"موجودی شما : {game().mojodi(guid=message.sender_id):,} 🪙")
    elif TEXT_MESSAGE=="ماینر":
        miner_user=game().my_miner(message.sender_id)
        await message.reply(f"""🎟 لول ماینر : {miner_user['level']:,}
💵 پروفیت ساعتی : {miner_user['h_miner']:,}
💵 پروفیت روزانه : {miner_user['d_miner']:,}

🔥 میدونستی اگه ماینرتو به لول بعدی برسونی درآمدت رو چند برابر میکنی؟ بگو ارتقا ماینر💡

🔋 قیمت لول بعدی : {miner_user['n_miner']:,} سکه

🪐❓ تا حالا چقدر سکه جمع کردی؟
💸 {miner_user['j_miner']:,} سکه 🤩

🎷میخوای بدست بیاریش؟ بگو جمع ماینر💡""")
    elif TEXT_MESSAGE=="جمع ماینر":
        m_j=game().j_miner(message.sender_id)
        await message.reply(f"""ماینر با موفقیت جمع شد ✅
مقدار پول جمع شده : {m_j['j']:,} 🪙
موجودی کنونی شما : {m_j['m']:,} 🪙""")
    elif TEXT_MESSAGE in ['خرید ماینر','ارتقا ماینر']:
        m=game().buy_miner(message.sender_id)
        if m['buy']:
            await message.reply(f"""ماینر با موفقیت خریداری شد ✅
موجودی کنونی شما : {m['m']:,} 🪙""")
        else:
            await message.reply(f"""خطا ! موجودی شما برای خرید لول بعدی ماینر کافی نیست !
قیمت ماینر لول بعدی : {m['n_miner']:,} 🎟
موجودی شما : {m['m']:,} 🪙""")
    elif TEXT_MESSAGE=="خرید حداکثر ماینر":
        buying=True
        buyed=0
        while buying:
            m=game().buy_miner(message.sender_id)
            if m['buy']:
                last_={"m":m['m'],"m_miner":m['m_miner']}
                buyed+=1
            else:
                if buyed==0:
                    await message.reply(f"""خطا ! موجودی شما برای خرید لول بعدی ماینر کافی نیست !
قیمت ماینر لول بعدی : {m['n_miner']:,} 🎟
موجودی شما : {m['m']:,} 🪙""")
                else:
                    await message.reply(f"""حداکثر ماینر با موفقیت خریداری شد ✅
موجودی کنونی شما : {last_['m']:,} 🪙
لول ماینر شما : {last_['m_miner']:,}
تعداد ماینر های خریداری شده : {buyed:,}""")
                return None

bot.run()
# نویسنده سورس : سید محمد حسین موسوی رجا
# روبیکا : @O_and_ONE_01
# تلگرام : @Hacker123457890
# چنل روبیکا : @Fast_Rub