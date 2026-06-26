<p align="center">
  <img src="https://fast-rub.ParsSource.ir/icon.jpg" width="200" alt="Fast Rub">
</p>

# Fast Rub ⚡

سریع‌ترین، هوشمندترین و کامل‌ترین فریم‌ورک ربات روبیکا برای پایتون

Fast Rub یک فریم‌ورک مدرن، Async-First و مبتنی بر HTTP/2 برای توسعه ربات‌های روبیکا است که با تمرکز بر سرعت، سادگی، مقیاس‌پذیری و تجربه توسعه‌دهنده طراحی شده است.

---

## فهرست مطالب

- [✨ ویژگی‌های کلیدی](#ویژگیهای-کلیدی)
- [📥 نصب](#نصب)
- [🚀 شروع سریع](#شروع-سریع)
- [🧠 WaitManager](#waitmanager)
- [📋 DataForm](#dataform)
- [💬 Conversation](#conversation)
- [🔍 فیلترها](#فیلترها)
- [⌨️ ساخت کیبورد](#ساخت-کیبورد)
- [🔄 Hot Reload](#hot-reload)
- [⏰ Scheduler](#scheduler)
- [📡 Signals](#signals)
- [🔌 Plugins](#plugins)
- [🗄️ ORM داخلی](#orm-داخلی)
- [💻 CLI](#cli)
- [📁 ساختار پروژه](#ساختار-پروژه)
- [📚 مستندات کامل](#مستندات-کامل)
- [⚠️ نکته درباره pyrubi](#نکته-درباره-pyrubi)

---

## ویژگیهای کلیدی

- ⚡ HTTP/2 + Async-First
- 🧠 WaitManager — مدیریت هوشمند Rate Limit
- 📋 DataForm — فرم‌های هوشمند
- 💬 Conversation — مکالمات چندمرحله‌ای
- 🔍 بیش از ۲۰۰ فیلتر آماده
- 🔄 Hot Reload
- ⏰ Scheduler
- 📡 Signals
- 🔌 Plugins
- 🗄️ ORM داخلی
- 📸 Snapshots
- 🌐 Webhook Server
- 💻 CLI
- 🛡️ AntiSpam
- 🪶 فوق‌العاده سبک (۲۵۶MB RAM)
- 🔒 امنیت (SQL پارامتری)
- 🚀 توسعه‌پذیر و ماژولار

[⬆ بازگشت به فهرست](#فهرست-مطالب)

---

## نصب

از طریق PyPI:

```bash
pip install fastrub
```

در صورت قطع بودن میرور اصلی:

```bash
pip install -i https://mirror-pypi.runflare.com/simple fastrub
```

[⬆ بازگشت به فهرست](#فهرست-مطالب)

---

# 🚀 شروع سریع

## دریافت پیام‌ها (Polling)

```python
import asyncio

from fast_rub import Client, filters
from fast_rub.types import Update

async def main():

    bot = Client("my_bot")

    await bot.start()

    @bot.on_message(filters.text("سلام"))
    async def say_hello(msg: Update):
        await msg.reply("**سلام** از طرف Fast Rub ⚡")

    await bot.run()

asyncio.run(main())
```

## کلیک روی دکمه‌های Inline

```python
import asyncio

from fast_rub import Client
from fast_rub.types import UpdateButton

async def main():

    bot = Client("my_bot")

    await bot.start()

    @bot.on_button()
    async def button_click(msg: UpdateButton):
        await msg.send_text(
            f"دکمه {msg.button_id} فشرده شد."
        )

    await bot.run()

asyncio.run(main())
```

[⬆ بازگشت به فهرست](#فهرست-مطالب)

---
# 🧠 WaitManager

قوی‌ترین سیستم مدیریت Rate Limit در بین تمام فریم‌ورک‌های روبیکا.

کافی است یک بار به Client معرفی شود؛ تمام تأخیرها و کنترل ترافیک به‌صورت خودکار انجام خواهد شد.

```python
from fast_rub import Client, WaitManager

bot = Client(
    "my_bot",
    wait_manager=WaitManager(
        low_traffic=60,
        medium_traffic=100,
        low_wait=0.0,
        medium_wait=1.0,
        high_wait=3.0,
        time_window=60.0,
        auto_track=True,
    )
)

@bot.on_message()
async def handler(msg):
    await msg.reply("سلام!")

await bot.run()
```

### کانال‌های قابل ردیابی

| کانال | توضیح |
|--------|--------|
| sending | ارسال پیام |
| banning | اخراج (Ban) |
| forwarding | فوروارد |
| uploading | آپلود فایل |
| editing | ویرایش پیام |
| deleting | حذف پیام |

---

### ویژگی‌ها

- مدیریت خودکار Rate Limit
- بدون نیاز به sleep دستی
- کنترل هوشمند ترافیک
- مناسب ربات‌های پرکاربر
- قابل شخصی‌سازی

[⬆ بازگشت به فهرست](#فهرست-مطالب)

---

# 📋 DataForm

DataForm سیستم ساخت فرم‌های هوشمند Fast Rub است.

ویژگی‌ها:

- اعتبارسنجی خودکار
- کیبورد خودکار
- مدیریت مراحل
- پشتیبانی از Callback
- لغو فرم
- تکرار سؤال
- رد کردن سؤال

### مثال

```python
from fast_rub import Conversation
from fast_rub.core.forms import Text, Number, DataForm

class UserInfo(DataForm):

    name: Text = Text(
        "👤 نام خود را وارد کنید",
        min_len=3,
        max_len=30
    )

    age: Number = Number(
        "🎂 چند سالته؟",
        min=18,
        max=60,
        keypad=True
    )

register = Conversation(name="register")

@register.entry_form(UserInfo, commands=["/register"])
async def done(msg, data):

    await msg.reply(
        f"ثبت شد\n"
        f"نام: {data['name']}\n"
        f"سن: {data['age']}"
    )
```

## Callbackهای شرطی

```python
class AdvancedForm(DataForm):

    name: Text = Text(
        "نام؟",
        min_len=3,
        repeat_if=lambda value:
            "admin" in value.lower()
    )

    age: Number = Number(
        "سن؟",
        min=18,
        max=60
    )

    job: Text = Text(
        "شغل؟",
        skip_if=lambda data:
            data.get("age", 0) < 18
    )

    city: Text = Text(
        "شهر؟",
        cancel_if=lambda value:
            value == "هیچی"
    )
```

### قابلیت‌ها

- repeat_if
- skip_if
- cancel_if
- validation
- keypad
- min / max
- min_len / max_len

[⬆ بازگشت به فهرست](#فهرست-مطالب)

---

# 💬 Conversation

سیستم مکالمه چندمرحله‌ای داخلی Fast Rub.

### روش کلاسیک

```python
register = Conversation(name="register")

@register.entry(commands=["/register"])
async def ask_name(msg, data):

    await msg.reply("اسمت چیه؟")

    return "waiting_name"


@register.state("waiting_name")
async def get_name(msg, data):

    data["name"] = msg.text

    await msg.reply(
        f"سلام {msg.text}"
    )

    return Conversation.END

bot.add_conversation(register)
```

### قابلیت‌ها

- State Machine
- مدیریت Session
- ذخیره اطلاعات
- پایان خودکار مکالمه
- چند Conversation همزمان

[⬆ بازگشت به فهرست](#فهرست-مطالب)

---
# 🔍 فیلترها

Fast Rub دارای بیش از **۲۰۰ فیلتر آماده** برای مدیریت انواع رویدادها است.

---

## فیلتر ساده

```python
from fast_rub import filters

@bot.on_message(filters.text("/start"))
async def start(msg):
    await msg.reply("سلام 👋")
```

---

## ترکیب AND

```python
@bot.on_message(
    filters.text("/admin")
    & filters.is_user
)
async def admin(msg):
    ...
```

---

## ترکیب OR

```python
@bot.on_message(
    filters.text("/help")
    | filters.text("راهنما")
)
async def help(msg):
    ...
```

---

## عملگر NOT

```python
@bot.on_message(
    ~filters.is_group
)
async def private(msg):
    ...
```

---

## Async Filter

```python
@bot.on_message(
    filters.db_exists(
        "users",
        lambda u: {
            "chat_id": u.chat_id
        },
        db=my_db
    )
)
async def registered(msg):
    ...
```

---

## Inline Filters

```python
@bot.on_button(
    filters.button_id("home")
    &
    filters.sender_ids(
        ["admin_id"]
    )
)
async def home(msg):
    ...
```

---

### برخی از فیلترهای موجود

- text
- regex
- command
- photo
- video
- voice
- file
- sticker
- location
- contact
- forwarded
- edited
- is_group
- is_private
- is_user
- is_bot
- sender_ids
- button_id
- db_exists
- custom_filter

و بیش از **۲۰۰ فیلتر دیگر**.

[⬆ بازگشت به فهرست](#فهرست-مطالب)

---

# ⌨️ ساخت کیبورد

```python
from fast_rub.button import KeyPad

keypad = KeyPad()

keypad.append(
    keypad.simple(
        "btn_1",
        "دکمه یک"
    )
)

keypad.append(
    keypad.simple(
        "btn_2",
        "دکمه دو"
    ),
    keypad.simple(
        "btn_3",
        "دکمه سه"
    )
)
```

ارسال کیبورد معمولی:

```python
await msg.reply(
    "انتخاب کنید:",
    keypad=keypad.build()
)
```

ارسال کیبورد شیشه‌ای:

```python
await msg.reply(
    "انتخاب کنید:",
    inline_keypad=keypad.build()
)
```

### امکانات

- چند ردیفه
- Inline Keyboard
- Keyboard معمولی
- ساخت پویا
- Callback Data

[⬆ بازگشت به فهرست](#فهرست-مطالب)

---

# 🔄 Hot Reload

با ذخیره هر فایل، ربات به‌صورت خودکار Restart می‌شود.

```python
await bot.run(
    reload=True
)
```

یا از طریق CLI:

```bash
fastrub run --reload
```

### مزایا

- بدون توقف ربات
- مناسب توسعه
- تشخیص خودکار تغییر فایل‌ها
- راه‌اندازی مجدد سریع

[⬆ بازگشت به فهرست](#فهرست-مطالب)

---
# ⏰ Scheduler

سیستم زمان‌بندی داخلی Fast Rub برای اجرای خودکار وظایف در زمان‌های مشخص.

---

## اجرا در بازه زمانی

```python
from fast_rub import Scheduler

scheduler = Scheduler()

@scheduler.every(minutes=30)
async def cleanup():
    print("🧹 پاک‌سازی خودکار")
```

---

## اجرا در ساعت مشخص

```python
@scheduler.every(at="08:00")
async def morning_report():
    print("📊 گزارش صبحگاهی")
```

---

## اجرا هر چند ثانیه

```python
@scheduler.every(seconds=10)
async def heartbeat():
    print("Alive")
```

---

### قابلیت‌ها

- اجرای دوره‌ای
- اجرای روزانه
- اجرای ساعتی
- اجرای دقیقه‌ای
- اجرای ثانیه‌ای
- مدیریت چند Job همزمان

[⬆ بازگشت به فهرست](#فهرست-مطالب)

---

# 📡 Signals

Signals یک سیستم Event-Driven برای ارتباط بین بخش‌های مختلف پروژه است.

---

## تعریف Listener

```python
from fast_rub import SignalManager

signals = SignalManager()

@signals.on("user_registered")
async def welcome(user_id, chat_id):
    print(
        f"👋 کاربر {user_id} ثبت‌نام کرد."
    )
```

---

## ارسال Event

```python
await signals.emit(
    "user_registered",
    user_id="123",
    chat_id="456"
)
```

---

### مزایا

- ارتباط ماژول‌ها
- بدون وابستگی مستقیم
- مدیریت Event
- توسعه‌پذیری بالا

[⬆ بازگشت به فهرست](#فهرست-مطالب)

---

# 🔌 Plugins

Fast Rub دارای سیستم پلاگین داخلی است.

هر پلاگین فقط یک فایل Python است.

### plugins/admin.py

```python
async def setup(client):

    @client.on_message(
        commands=["/admin"]
    )
    async def panel(msg):

        await msg.reply(
            "🔧 پنل مدیریت"
        )
```

---

## بارگذاری خودکار

```python
await bot.load_plugins("plugins")
```

---

### مزایا

- Auto Discovery
- بارگذاری خودکار
- توسعه آسان
- جداسازی ماژول‌ها
- مناسب پروژه‌های بزرگ

[⬆ بازگشت به فهرست](#فهرست-مطالب)

---

# 🗄️ ORM داخلی

Fast Rub دارای ORM داخلی مبتنی بر SQLite است.

---

## ساخت دیتابیس

```python
from fast_rub.db import DataBase

db = DataBase("my_bot.db")

await db.start({
    "users": {
        "chat_id": "TEXT",
        "name": "TEXT"
    }
})
```

---

## درج اطلاعات

```python
await db.write(
    "users",
    {
        "chat_id": "123",
        "name": "علی"
    }
)
```

---

## دریافت اطلاعات

```python
user = await db.find(
    "users",
    "*",
    {
        "chat_id": "123"
    }
)
```

---

## حذف اطلاعات

```python
await db.delete(
    "users",
    {
        "chat_id": "123"
    }
)
```

---

## بروزرسانی اطلاعات

```python
await db.update(
    "users",
    {
        "name": "محمد"
    },
    {
        "chat_id": "123"
    }
)
```

---

### ویژگی‌ها

- SQLite
- SQL پارامتری
- امنیت بالا
- Async
- API ساده
- بدون نیاز به ORM خارجی

[⬆ بازگشت به فهرست](#فهرست-مطالب)

---
# 💻 CLI

Fast Rub دارای ابزار خط فرمان داخلی برای مدیریت پروژه‌ها است.

---

## ساخت پروژه جدید

```bash
fastrub new my_bot
```

---

## اجرای ربات

```bash
fastrub run
```

---

## اجرا با Hot Reload

```bash
fastrub run --reload
```

---

## مشاهده نسخه

```bash
fastrub version
```

---

## مشاهده مستندات

```bash
fastrub docs
```

---

### مزایا

- ساخت پروژه در چند ثانیه
- اجرای سریع
- توسعه آسان
- Hot Reload
- دسترسی مستقیم به مستندات

[⬆ بازگشت به فهرست](#فهرست-مطالب)

---

# 📁 ساختار پروژه

```text
fast_rub/
├── core/
│   ├── client.py
│   ├── conversation.py
│   ├── middleware.py
│   ├── plugin.py
│   └── forms/
│       ├── data_form.py
│       ├── text.py
│       ├── number.py
│       └── choice.py
│
├── pyrubi/
│
├── types/
│   ├── update.py
│   ├── button.py
│   ├── message.py
│   ├── metadata.py
│   └── errors.py
│
├── utils/
│   ├── filters/
│   ├── wait_manager.py
│   ├── cache.py
│   ├── antispam.py
│   └── snapshot.py
│
├── db/
│   └── database.py
│
├── button/
│   └── keypad.py
│
├── network/
│   └── http_client.py
│
└── cli/
```

---

### توضیحات

| مسیر | توضیح |
|--------|--------|
| core | هسته فریم‌ورک |
| pyrubi | بخش User Bot |
| types | انواع داده‌ها |
| forms | DataForm |
| utils | ابزارهای کمکی |
| db | ORM داخلی |
| button | ساخت کیبورد |
| network | HTTP/2 Client |
| cli | ابزار خط فرمان |

[⬆ بازگشت به فهرست](#فهرست-مطالب)

---

# 📚 مستندات کامل

### لینک‌های مفید

- مستندات رسمی
- GitHub Repository
- PyPI Package

---

### موضوعات مستندات

- نصب
- Client
- Filters
- Conversation
- DataForm
- WaitManager
- Scheduler
- Signals
- Plugins
- ORM
- Webhook
- CLI

[⬆ بازگشت به فهرست](#فهرست-مطالب)

---

# ⚠️ نکته درباره pyrubi

بخش `pyrubi` یک فورک از پروژه:

AliGanji1/pyrubi

است که برای قابلیت‌های User Bot در Fast Rub مورد استفاده قرار گرفته و با ساختار Fast Rub یکپارچه شده است.

[⬆ بازگشت به فهرست](#فهرست-مطالب)

---

# ❤️ مشارکت

از Pull Request ها، Issue ها و پیشنهادات استقبال می‌شود.

برای مشارکت:

1. پروژه را Fork کنید.
2. تغییرات خود را اعمال کنید.
3. Commit بگیرید.
4. Pull Request ارسال کنید.

---

# 📄 لایسنس

این پروژه تحت لایسنس MIT منتشر شده است.

---

ساخته شده با ❤️ توسط

**سید محمد حسین موسوی رجا (OandONE)**

---
