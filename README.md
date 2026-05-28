<img src="https://fast-rub.ParsSource.ir/icon.jpg">

# Fast Rub - فست روب

This is where FastRub combines speed, power, and efficiency, allowing you to write the best Rubika bots. 🔥
اینجاست که فست روب سرعت، قدرت و بهینه بودن رو با هم ترکیب کرده تا بهترین ربات های روبیکا رو بنویسی 🔥

## Fast Rub - فست روب

- 1 The fastest Rubika robots library for Python - سریع ترین کتابخانه ربات های روبیکا پایتون
- 2 power - قدرت
- 3 efficiency - بهینه بودن

## install - نصب :

```bash
pip install --upgrade fastrub
```

## نحوه نصب در صورت ملی بودن اینترنت از میرور رانفلر :
```bash
pip install -i https://mirror-pypi.runflare.com/simple fastrub
```

# [Documents - مستندات کامل](https://fast-rub.ParsSource.ir/index.html)

## [GitHub - گیت هاب](https://github.com/OandONE/fast_rub)

## [PyPI - پای پی آی](https://pypi.org/project/fastrub)


<h3><div style="color: blue;">نکته در مورد قسمت یوزر بات کتابخانه :
قسمت PyRubi این کتابخانه فورک کتابخانه <a href="https://github.com/AliGanji1/pyrubi">پایروبی</a> است</div></h3>

## توضیحات کوتاه(توضیحات کامل در مستندات)

### گرفتن آپدیت پیام ها - پولینگ
```python
from fast_rub import Client
from fast_rub.type import Update
import asyncio

async def robot():
  bot = Client("name_session", run_start=False)

  await bot.start()

  @bot.on_message()
  async def getting(message:Update):
      await message.reply("__Hello__ *from* **FastRub** !")

  await bot.run()

asyncio.run(robot())
```

### گرفتن کلیک های دکمه های اینلاین(شیشه ای)
```python
from fast_rub import Client
from fast_rub.type import UpdateButton
import asyncio

async def robot():
  bot = Client("name_session", run_start=False)
  # در صورتی که میخواید از endpoint خودتون استفاده کنید » 
  # url_webhook_on_button = "https://..."
  # bot = Client("name_session", use_to_fastrub_webhook_on_button = url_webhook_on_button)

  await bot.start()

  @bot.on_button()
  async def getting(message: UpdateButton):
    print(f"""button id » {message.button_id}
text » {message.text}
chat id » {message.chat_id}
message id » {message.message_id}
sender_id » {message.sender_id}

====================""")

  await bot.run()

asyncio.run(robot())
```

## سایر دستورات

### ارسال KeyPad
```python
from fast_rub import Client
from fast_rub.button import KeyPad
import asyncio

async def setting():
    bot = Client("test", run_start=False)

    await bot.start()

    button = KeyPad()
    button.append(
        button.simple("button id 1", "text 1")
    )
    button.append(
        button.simple("button id 2", "text 2"),
        button.simple("button id 3", "text 3")
    )
    await bot.send_text("test KeyPad", keypad=button.get())

asyncio.run(setting())
```

### ارسال KeyPad Inline
```python
from fast_rub import Client
from fast_rub.button import KeyPad
import asyncio

async def setting():
    bot = Client("test", run_start=False)

    await bot.start()

    button = KeyPad()
    button.append(
        button.simple("button id 1", "text 1")
    )
    button.append(
        button.simple("button id 2", "text 2"),
        button.simple("button id 3", "text 3")
    )
    await bot.send_text("test KeyPad", inline_keypad=button.get())

asyncio.run(setting())
```

## ارسال فایل

### ارسال فایل
```python
from fast_rub import Client
import asyncio

async def send_file():
    chat_id = "b..."
    file = "..."
    text = None

    bot = Client("test", run_start=False)

    await bot.start()

    await bot.send_file(chat_id,file,text=text)

asyncio.run(send_file())
```

### ارسال بقیه رسانه ها
```python
from fast_rub import Client
import asyncio

bot = Client("test")

async def send_medias():
    chat_id = "b..."
    image = "..."
    video = "..."
    voice = "..."
    text = None

    bot = Client("test", run_start=False)

    await bot.start()

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
    chat_id = "b..."
    id_sticker = "..."

    bot = Client("test", run_start=False)

    await bot.start()
    
    await bot.send_sticker(chat_id,id_sticker)

asyncio.run(send_sticker())
```

## دانلود

### دانلود فایل
```python
from fast_rub import Client
import asyncio

async def download_file():
    id_file = "..."
    path_save = "test.bin"

    bot = Client("test", run_start=False)

    await bot.start()

    await bot.download_file(id_file,path_save)

asyncio.run(download_file())
```

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

### متود ها

ریپلای پیام

`reply(
text: Optional[str] = None,
keypad_inline: Optional[list] = None,
inline_keypad: Optional[list] = None,
keypad: Optional[list] = None,
resize_keyboard: bool | None = True,
on_time_keyboard: bool | None = False,
auto_delete: Optional[int] = None,
parse_mode: Literal['Markdown', 'HTML', None] = "Markdown",
meta_data: Optional[list] = None,
file: Union[str , Path , bytes , None] = None,
name_file: Optional[str] = None,
type_file: Literal["File", "Image", "Voice", "Music", "Gif" , "Video"] = "File",
file_id: Optional[str] = None,
show_progress: bool = True,
question: Optional[str] = None,
options: Optional[list] = None,
type_poll: Literal["Regular", "Quiz"] = "Regular",
is_anonymous: bool = True,
correct_option_index: Optional[int] = None,
allows_multiple_answers: bool = False,
hint: Optional[str] = None,
latitude: Optional[str] = None,
longitude: Optional[str] = None,
first_name: Optional[str] = None,
last_name: Optional[str] = None,
phone_number: Optional[str] = None,  
chat_id: Optional[str] = None,
reply_to_message_id: Optional[str] = None
)`

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

## فیلتر های دکوراتور on_message و on_message_updates

نحوه استفاده »

```python
from fast_rub import Client, filters
from fast_rub.type import Update
import asyncio

async def robot():
    bot = Client("test", run_start=False)

    await bot.start()

    @bot.on_message(filters.text("تست"))
    async def test_filters(msg: Update):
        await msg.reply("__hello__ *from* **fast_rub**")
    
    await bot.run()

asyncio.run(robot())
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

برقراری تمامی فیلتر ها

`and_filter(*filters)`

برقراری یکی از فیلتر ها

`or_filter(*filters)`

برقرار نبودن فیلتر

`not_filter(filter)`

#### ساخت فیلتر سفارشی

```python
from fast_rub import Client, filters
from fast_rub.type import Update
import asyncio

# Sync
class sticker_emoji_filter(filters.Filter):
    """فیلتر تشخیص ایموجی استیکر"""
    def __init__(self, sticker_emoji_character: str):
        self.sticker_emoji_character = sticker_emoji_character
    def __call__(self, update: Update) -> bool:
        return str(update.sticker_emoji_character) == self.sticker_emoji_character

# Async
import database as db # مثال
class is_admin_filter(filters.AsyncFilter):
    """فیلتر ادمین بودن کاربر"""
    async def __acall__(self, update: Update) -> bool:
        return bool(
            await db.exists(
                "admins",
                {
                    "chat_id": update.chat_id
                }
            )
        )

async def robot():
    bot = Client("test", run_start=False)

    await bot.start()

    @bot.on_message(sticker_emoji_filter("😂"))
    async def test_filter1(msg: Update):
        await msg.reply("خخخ")
    
    @bot.on_message(is_admin_filter())
    async def test_filter2(msg: Update):
        await msg.reply("شما ادمین میباشید")
    
    await bot.run()

asyncio.run(robot())
```



<hr>
<h1>Seyyed Mohamad Hosein Moosavi (01)</h1>
