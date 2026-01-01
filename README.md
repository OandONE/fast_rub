<img src="https://fast-rub.ParsSource.ir/icon.jpg">

# Fast Rub - فست روب

Fast Rub means the fastest library for Rubika bots. If you want your Rubika bot to be fast and the library syntax you want to work with, it is definitely the best library for Python, Fast Rub!
فست روب یعنی سریع ترین کتابخانه برای ربات های روبیکا . اگر میخواهید ربات روبیکاتون سریع باشه و سینتکست کتابخانه ای که میخواید باهاش کار کنید قطعا برای پایتون بهترین کتابخانه فست روبه !

## Fast Rub - فست روب

- 1 The fastest Rubika robots library for Python - سریع ترین کتابخانه ربات های روبیکا پایتون
- 2 simple syntax - سینتکست ساده
- 3 Small size of the library - حجم پایین نصبت به بقیه کتابخانه ها

## install - نصب :

```bash
pip install --upgrade fastrub
```

[Documents - مستندات](https://fast-rub.ParsSource.ir/index.html)

[GitHub - گیت هاب](https://github.com/OandONE/fast_rub)

قسمت PyRubi این کتابخانه فورک کتابخانه [پایروبی](https://github.com/AliGanji1/pyrubi) است


## دکوراتور ها

### گرفتن آپدیت پیام ها - پولینگ
```python
from fast_rub import Client
from fast_rub.type import Update
import asyncio

bot = Client("name_session")

@bot.on_message()
async def getting(message:Update):
    await message.reply("__Hello__ *from* **FastRub** !")

asyncio.run(bot.run())
```

### گرفتن آپدیت پیام ها - وبهوک
```python
from fast_rub import Client
from fast_rub.type import Update
import asyncio

bot = Client("name_session")
# در صورتی که میخواید از endpoint خودتون استفاده کنید » 
# url_webhook_on_message = "https://..."
# bot = Client("name_session", use_to_fastrub_webhook_on_message = url_webhook_on_message)

@bot.on_message_updates()
async def getting(message:Update):
    await message.reply("__Hello__ *from* **FastRub** !")

asyncio.run(bot.run())
```

### گرفتن کلیک های دکمه های اینلاین
```python
from fast_rub import Client
from fast_rub.type import UpdateButton
import asyncio

bot = Client("name_session")
# در صورتی که میخواید از endpoint خودتون استفاده کنید » 
# url_webhook_on_button = "https://..."
# bot = Client("name_session", use_to_fastrub_webhook_on_button = url_webhook_on_button)

@bot.on_button()
async def getting(message: UpdateButton):
    print(f"""button id » {message.button_id}
text » {message.text}
chat id » {message.chat_id}
message id » {message.message_id}
sender_id » {message.sender_id}

====================""")

asyncio.run(bot.run())
```

### توقف گرفتن آپدیت ها
```python
from fast_rub import Client
from fast_rub.type import Update
import asyncio

bot = Client("name_session")

@bot.on_message()
async def getting(message:Update):
    if message.text == "/off":
        await message.reply("**OK**")
        bot.stop()

asyncio.run(bot.run())
```

## دستورات


### نحوه تنظیم دستورات ربات
```python
from fast_rub import Client
import asyncio

bot = Client("test")

async def setting():
    await bot.add_commands("/start","َشروع")
    await bot.add_commands("/help","راهنما")
    await bot.set_commands()

asyncio.run(setting())
```

### نحوه حذف دستورات ربات
```python
from fast_rub import Client
import asyncio

bot = Client("test")

async def setting():
    await bot.delete_commands()

asyncio.run(setting())
```


### ارسال KeyPad
```python
from fast_rub import Client
from fast_rub.button import KeyPad
import asyncio

bot = Client("test")

async def setting():
    button = KeyPad()
    button.append(
        button.simple("button id 1", "text 1")
    )
    button.append(
        button.simple("button id 2", "text 2"),
        button.simple("button id 3", "text 3")
    )
    await bot.send_text("test KeyPad",keypad=button.get())

asyncio.run(setting())
```

### ارسال KeyPad Inline
```python
from fast_rub import Client
from fast_rub.button import KeyPad
import asyncio

bot = Client("test")

async def setting():
    button = KeyPad()
    button.append(
        button.simple("button id 1", "text 1")
    )
    button.append(
        button.simple("button id 2", "text 2"),
        button.simple("button id 3", "text 3")
    )
    await bot.send_text("test KeyPad Inline",inline_keypad=button.get())

asyncio.run(setting())
```

## ارسال فایل

### ارسال فایل
```python
from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."
file = "..."
text = None

async def send_file():
    await bot.send_file(chat_id,file,text=text)

asyncio.run(send_file())
```

### ارسال بقیه رسانه ها
```python
from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."
image = "..."
video = "..."
voice = "..."
text = None

async def send_medias():
    await bot.send_image(chat_id,image,text=text)
    await bot.send_video(chat_id,video,text=text)
    await bot.send_voice(chat_id,video,text=text)

asyncio.run(send_medias())
```

### ارسال استیکر

```python
from fast_rub import Client
import asyncio

bot = Client("test")

chat_id = "b..."
id_sticker = "..."


async def send_sticker():
    await bot.send_sticker(chat_id,id_sticker)

asyncio.run(send_sticker())
```



## دانلود

### گرفتن لینک دانلود فایل
```python
from fast_rub import Client
import asyncio

bot = Client("test")

id_file = "..."

async def get_download_file_url():
    link_download = await bot.get_download_file_url(id_file)
    print(f"the link download of file » {id_file} is » {link_download}")

asyncio.run(get_download_file_url())
```

### دانلود فایل
```python
from fast_rub import Client
import asyncio

bot = Client("test")

id_file = "..."
path_save = "test.bin"

async def download_file():
    await bot.download_file(id_file,path_save)

asyncio.run(download_file())
```



## تنظیم EndPoint

### تنظیم EndPoint
```python
from fast_rub import Client
import asyncio

bot = Client("test")

url_endpoint = "https://..."
type_endpoint = "ReceiveUpdate"

async def set_endpoint():
    await bot.set_endpoint(url_endpoint,type_endpoint)

asyncio.run(set_endpoint())
```

## سایر متود ها

حذف خودکار پیام بعد از x ثانیه

`auto_delete(chat_id:str,message_id:str,time_sleep:float)`

ویرایش خودکار پیام بعد از x ثانیه

`auto_edit(
        chat_id: str,
        message_id: str,
        text: str,
        aute_edit: int,
        inline_keypad: Optional[list] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: Optional[list] = None
    )`

گرفتن اطلاعات ربات

`get_me()`

تنظیم پارس مود اصلی همه متن ها

`set_main_parse_mode(parse_mode: Literal['Markdown', 'HTML', 'Unknown', None])`

ارسال متن

`send_text(text: str,
        chat_id: str,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        disable_notification: Optional[bool] = False,
        reply_to_message_id: Optional[str] = None,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: Optional[list] = None)`

ارسال نظرسنجی

`send_poll(chat_id: str,
        question: str,
        options: list,
        type_poll: Literal["Regular", "Quiz"] = "Regular",
        is_anonymous: bool = True,
        correct_option_index: Optional[int] = None,
        allows_multiple_answers: bool = False,
        hint: Optional[str] = None,
        disable_notification: bool = False,
        reply_to_message_id: Optional[str] = None,
        auto_delete: Optional[int] = None)`

ارسال موقعیت مکانی(لوکیشن)

`send_location(chat_id: str,
        latitude: str,
        longitude: str,
        chat_keypad : Optional[str] = None,
        disable_notification: Optional[bool] = False,
        reply_to_message_id: Optional[str] = None,
        chat_keypad_type: Optional[str] = None,
        auto_delete: Optional[int] = None)`

ارسال مخاطب

`send_contact(chat_id: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        chat_keypad : Optional[str] = None,
        chat_keypad_type: Optional[str] = None,
        inline_keypad: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        disable_notificatio: Optional[bool] = False,
        auto_delete: Optional[int] = None)`

ارسال انواع پیام

`send_message(chat_id: str,
        text: Optional[str] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        disable_notification: bool = False,
        reply_to_message_id: Optional[str] = None,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: Optional[list] = None,
        # file
        file: Union[str , Path , bytes , None] = None,
        name_file: Optional[str] = None,
        type_file: Literal["File", "Image", "Voice", "Music", "Gif" , "Video"] = "File",
        file_id: Optional[str] = None,
        show_progress: bool = True,
        # poll
        question: Optional[str] = None,
        options: Optional[list] = None,
        type_poll: Literal["Regular", "Quiz"] = "Regular",
        is_anonymous: bool = True,
        correct_option_index: Optional[int] = None,
        allows_multiple_answers: bool = False,
        hint: Optional[str] = None,
        # location
        latitude: Optional[str] = None,
        longitude: Optional[str] = None,
        # contact
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone_number: Optional[str] = None)`

گرفتن اطلاعات چت

`get_chat(chat_id: str)`

گرفتن آپدیت ها(از بالا)

`get_updates(limit : Optional[int] = None, offset_id : Optional[str] = None)`

گرفتن پیام با آیدی پیام

`get_message(chat_id: str,message_id: str,limit_search: int = 100,search_by: Literal["messages", "get_updates", "all"] = "all")`

گرفتن پیام های قبل یک پیام با آیدی پیام

`get_messages(chat_id: str,message_id: str,limit_search: int = 100,get_befor: int = 10, search_by: Literal["messages", "get_updates", "all"] = "all")`

فوروارد پیام

`forward_message(from_chat_id: str,
        message_id: str,
        to_chat_id: str,
        disable_notification : Optional[bool] = False,
        auto_delete: Optional[int] = None)`

فوروارد چند پیام

`forward_messages(from_chat_id: str,
        message_ids: list,
        to_chat_id: str,
        disable_notification : Optional[bool] = False,
        auto_delete: Optional[int] = None)`

ویرایش متن پیام

`edit_message_text(chat_id: str,
        message_id: str,
        text: str,
        inline_keypad: Optional[list] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown",
        meta_data: Optional[list] = None)`

حذف پیام

`delete_message(chat_id: str,
        message_id: str)`

آپلود فایل در سرور روبیکا

`upload_file(url: str, file_name: str, file: Union[str , Path , bytes])`

ارسال فایل با آیدی

`send_file_by_file_id(chat_id: str,
        file_id: str,
        text: Optional[str] = None,
        reply_to_message_id: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        auto_delete: Optional[int] = None,
        parse_mode: Literal["Markdown","HTML",None] = "Markdown")`

بن کاربر

`ban_chat_member(chat_id: str,
        user_id: str)`

آنبن کاربر

`unban_chat_member(chat_id: str,
        user_id: str)`


ران کردن دکوراتور های گرفتن پیام

`run()` # async -> asyncio.run(client.run())
`run_sync()` # sync -> client.run_sync()

توقف پروسس های گرفتن پیام

`stop()`

## کلاس های Update و UpdateButton

### کلاس Update

### پراپرتی ها

<li>text - متن پیام</li>
<li>message_id - آیدی پیام</li>
<li>chat_id - چت آیدی</li>
<li>time - زمان ارسال پیام</li>
<li>sender_type - نوع ارسال کننده پیام</li>
<li>sender_id - ارسال کننده پیام</li>
<li>is_edited - وضعیت ویرایش شدن پیام</li>

#### ریپلای
<li>is_reply - ریپلای شده؟</li>
<li>reply_to_message_id - آیدی پیام ریپلای شده(در صورت ریپلای شده)</li>

#### فایل
<li>file - فایل(در صورت وجود داشتن)</li>
<li>file_id - فایل آیدی(در صورت وجود داشتن)</li>
<li>file_name - نام فایل(در صورت وجود داشتن)</li>
<li>size_file - اندازه فایل (در صورت وجود داشتن)</li>
<li>type_file - نوع فایل(در صورت وجود داشتن)</li>

#### کی پد
<li>button - اطلاعات دیکشنری دکمه(در صورت وجود داشتن)</li>
<li>button_id - آیدی دکمه(در صورت وجود داشتن)</li>

#### متا دیتا
<li>metadata - اطلاعات دیکشنری متادیتا(در صورت وجود داشتن)</li>
<li>meta_data_parts - لیست اطلاعات متا دیتا(در صورت وجود داشتن)</li>

#### فوروارد
<li>is_fowrard - وضعیت فوروارد بودن پیام</li>
<li>forward_from - فوروارد از(در صورت وجود داشتن)</li>
<li>forward_message_id - آیدی پیام فوروارد شده(در صورت وجود داشتن)</li>
<li>forward_from_sender_id - ارسال کننده اصلی پیام فوروارد شده (در صورت وجود داشتن)</li>

#### مخاطب
<li>is_contact - وضعیت مخاطب بودن پیام</li>
<li>contact_phone_number - شماره تلفن مخاطب(در صورت وجود داشتن)</li>
<li>contact_first_name - نام مخاطب(در صورت وجود داشتن)</li>
<li>contact_last_name - نام خانوادگی مخاطب(در صورت وجود داشتن)</li>

#### استیکر
<li>is_sticker - وضعیت استیکر بودن پیام</li>
<li>sticker_emoji_character - ایموجی استیکر(در صورت وجود داشتن)</li>
<li>sticker_sticker_id - آیدی استیکر(در صورت وجود داشتن)</li>
<li>sticker_file - فایل استیکر(در صورت وجود داشتن)</li>

### متود ها

شرط ریجکس

`regex(pattern: str,
        flags: int = 0,
        text: Optional[str] = None)` # sync

گرفتن اطلاعات چت آیدی

``get_chat_id_info(chat_id: Optional[str] = None)``

ریپلای پیام

`reply(
        self,
        text: Optional[str] = None,
        keypad_inline: Optional[list] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: Optional[list] = None,
        # file
        file: Union[str , Path , bytes , None] = None,
        name_file: Optional[str] = None,
        type_file: Literal["File", "Image", "Voice", "Music", "Gif" , "Video"] = "File",
        file_id: Optional[str] = None,
        show_progress: bool = True,
        # poll
        question: Optional[str] = None,
        options: Optional[list] = None,
        type_poll: Literal["Regular", "Quiz"] = "Regular",
        is_anonymous: bool = True,
        correct_option_index: Optional[int] = None,
        allows_multiple_answers: bool = False,
        hint: Optional[str] = None,
        # location
        latitude: Optional[str] = None,
        longitude: Optional[str] = None,
        # contact
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone_number: Optional[str] = None,  
        chat_id: Optional[str] = None,
        reply_to_message_id: Optional[str] = None
    )`

ریپلای متن

`reply_text(text: str,keypad_inline: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: bool | None = True,
        on_time_keyboard: bool | None = False,,auto_delete: Optional[int] = None,parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: Optional[list] = None,
        chat_id: Optional[str] = None,
        reply_to_message_id: Optional[str] = None)`

ریپلای نظرسنجی

`reply_poll(
    question: str,
    options: list,
    type_poll: Literal["Regular", "Quiz"] = "Regular",
    is_anonymous: bool = True,
    correct_option_index: Optional[int] = None,
    allows_multiple_answers: bool = False,
    hint: Optional[str] = None,
    auto_delete: Optional[int] = None,
    chat_id: Optional[str] = None,
        reply_to_message_id: Optional[str] = None
)`

ریپلای مخاطب

`reply_contact(first_name: str, phone_number: str, last_name: Union[str,str] = "",auto_delete: Optional[int] = None,chat_id: Optional[str] = None,
        reply_to_message_id: Optional[str] = None)`

ریپلای موقعیت مکانی(لوکیشن)

`reply_location(latitude: str, longitude: str,auto_delete: Optional[int] = None,chat_id: Optional[str] = None,
        reply_to_message_id: Optional[str] = None)`

ریپلای فایل

`reply_file(
    file: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text: Optional[str] = None,
        type_file: Literal["File", "Image", "Voice", "Music", "Gif","Video"] = "File",
        disable_notification: Optional[bool] = False,
        auto_delete: Optional[int] = None,
        parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
        meta_data: Optional[list] = None,
        inline_keypad: Optional[list] = None,
        keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,
        upload_by: Literal["aiohttp", "httpx"] = "aiohttp",
        show_progress: bool = True,
        chat_id: Optional[str] = None,
        reply_to_message_id: Optional[str] = None
) # فایل`

`reply_image(
    image: Union[str , Path , bytes],
    name_file: Optional[str] = None,
    text: Optional[str] = None,
    disable_notification: Optional[bool] = False,
    auto_delete: Optional[int] = None,
    parse_mode: Literal['Markdown', 'HTML', None] = "Markdown"
) # تصویر`

`reply_voice(...) # ویس`

`reply_music(...) # موزیک`

`reply_gif(...) # گیف`

`reply_video(...) # ویدیو`

فوروارد پیام

`forward(to_chat_id:str,auto_delete: Optional[int] = None)`

دانلود فایل

`download(path : str = "file",
        file_id: Optional[str] = None,
        show_progress: bool = True)`

گرفتن لینک دانلود فایل
`get_download_file_url(file_id: Optional[str] = None)`

حذف پیام

`delete()`

بن کاربر

`ban(chat_id: Optional[str] = None,
        user_id: Optional[str] = None)`

آنبن کاربر

`unban(chat_id: Optional[str] = None,
        user_id: Optional[str] = None)`

بن کاربر ریپلای شده

`ban_reply(chat_id: Optional[str] = None)`

آنبن کاربر ریپلای شده

`unban_reply(chat_id: Optional[str] = None)`

گرفتن پیام ریپلای شده

`get_reply(chat_id: Optional[str] = None,
        message_id: Optional[str] = None)`

تبدیل پیام به دیکشنری

`to_dict()`


### کلاس UpdateButton

### پراپرتی ها

<li>button_id - آیدی دکمه کلیک شده</li>
<li>chat_id - چت آیدی</li>
<li>message_id - آیدی پیام</li>
<li>sender_id - ارسال کننده</li>
<li>text - متن دکمه</li>

### متود ها

ارسال متن

`send_text(text:str,keypad:dict:Optional[list] = None,keypad: Optional[list] = None,
        resize_keyboard: Optional[bool] = True,
        on_time_keyboard: Optional[bool] = False,auto_delete: Optional[int] = None,reply_to_message_id: Optional[str] = None,parse_mode: Literal['Markdown', 'HTML'] = "Markdown")`

ارسال نظرسنجی

`send_pool(
    question: str,
    options : list,
    type_poll: Literal['Regular', 'Quiz'] = "Regular",
    is_anonymous: bool = True,
    correct_option_index: int | None = None,
    allows_multiple_answers: bool = False,
    hint: str | None = None,
    auto_delete: Optional[int] = None
)`

ارسال مخاطب

`send_contact(first_name: str,
        last_name: str,
        phone_number: str,
        auto_delete: Optional[int] = None,
        reply_to_message_id: Optional[str] = None)`

ارسال موقعیت مکانی(لوکیشن)

`send_location(latitude: str,
        longitude: str,
        auto_delete: Optional[int] = None,
        reply_to_message_id: Optional[str] = None)`

ارسال فایل

`send_file(file: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text: Optional[str] = None,
        type_file: Literal['File', 'Image', 'Voice', 'Music', 'Gif', 'Video'] = "File",
        auto_delete: Optional[int] = None,
        reply_to_message_id: Optional[str] = None) # فایل`

`send_image(image: Union[str , Path , bytes],
        name_file: Optional[str] = None,
        text: Optional[str] = None,
        auto_delete: Optional[int] = None,
        reply_to_message_id: Optional[str] = None) # تصویر`

`send_video(...) # ویدیو`

`send_voice(...) # ویدیو`

`send_music(...) # موزیک`

`send_gif(...) # گیف`


## فیلتر های دکوراتور on_message و on_message_updates

نحوه استفاده »

```python
from fast_rub import Client, filters
from fast_rub.type import Update
import asyncio

bot = Client("test")

@bot.on_message(filters.text("تست"))
async def test_filters(msg:Update):
    await msg.reply("__hello__ *from* **fast_rub**")

asyncio.run(bot.run())
```

### فیلتر ها

متن

`text(pattern: str)`

ارسال کننده

`sender_id(user_id: str)`

کاربر بودن

`is_user()`

گروه بودن

`is_group()`

کانال بودن

`is_channel()`

فایل بودن

`is_file()`

اسم فایل

`file_name(name_file: str)`

اندازه فایل

`size_file(size: int)`

ویدیو بودن

`is_video()`

عکس بودن

`is_image()`

آودیو بودن

`is_audio()`

ویس بودن

`is_voice()`

داکیومنت بودن

`is_document()`

فایل وب بودن

`is_web()`

فایل کد بودن

`is_code()`

آرشیو بودن

`is_archive()`

فایل نصبی بودن

`is_executable()`

متن بودن

`is_text()`

الگو ریجکس

`regex(pattern: str, flags=0)`

زمان

`time(from_time:float=0,end_time=float("inf"))`

دستورات

`commands(coms: list)`

سند آیدی ها

`author_guids(guids: list)`

چت آیدی ها

`chat_ids(ids: list)`

داشتن متا دیتا

`is_metadata_type()`

داشتن بولد

`has_bold()`

داشتن ایتالیک

`has_italic()`

داشتن آندرلاین

`has_underline()`

داشتن متن خط خورده

`has_strike()`

داشتن متن کپی

`has_mono()`

داشتن متن اسپویل شده

`has_spoiler()`

داشتن متن هایپر لینک

`has_link()`

بودن متن بولد شده

`is_bold()`

بودن متن ایتالیک

`is_italic()`

بودن متن زیر خط

`is_underline()`

بودن متن خط خورده

`is_strike()`

بودن متن کپی

`is_mono()`

بودن متن اسپویل شده

`is_spoiler()`

بودن متن هایپر لینک

`is_link()`

بودن در متن

`in_text(text: str)`

فورواردن بودن

`is_forward()`

ریپلای بودن

`is_reply()`

طول متن

`text_length(min_len: int = 0, max_len: float = float('inf'))`

شروع با

`starts_with(prefix: str)`

یایان با

`ends_with(suffix: str)`

استیکر بودن

`is_sticker()`

مخاطب بودن

`is_contact()`

برقراری تمامی فیلتر ها

`and_filter(*filters)`

برقراری یکی از فیلتر ها

`or_filter(*filters)`

برقرار نبودن فیلتر

`not_filter(filter)`

<hr>
<h1>Seyyed Mohamad Hosein Moosavi (01)</h1>
