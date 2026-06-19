<p align="center">
  <img src="https://fast-rub.ParsSource.ir/icon.jpg" width="200" alt="Fast Rub">
</p>

<h1 align="center">Fast Rub ⚡</h1>
<p align="center"><strong>سریع‌ترین، هوشمندترین و کامل‌ترین فریم‌ورک ربات روبیکا برای پایتون</strong></p>

<p align="center">
  <a href="https://pypi.org/project/fastrub/"><img src="https://img.shields.io/pypi/v/fastrub?color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/fastrub/"><img src="https://img.shields.io/pypi/pyversions/fastrub" alt="Python 3.10+"></a>
  <a href="https://github.com/OandONE/fast_rub/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow" alt="License: MIT"></a>
  <a href="https://fast-rub.ParsSource.ir"><img src="https://img.shields.io/badge/docs-document-6c5ce7" alt="مستندات"></a>
</p>

---

## ✨ ویژگی‌های کلیدی

- ⚡ **HTTP/2 + Async-First** — سریع‌ترین فریم‌ورک روبیکا با `httpx`
- 🧠 **WaitManager** — مدیریت هوشمند Rate Limit (فقط به Client بدهید — بقیه خودکار)
- 📋 **DataForm** — فرم‌های هوشمند با اعتبارسنجی، کیبورد و callbackهای شرطی
- 💬 **Conversation** — مکالمات چندمرحله‌ای با State Machine داخلی (کلاسیک + مدرن)
- 🔍 **۲۰۰+ فیلتر** — فیلترهای آماده و ترکیبی (AND/OR/NOT) + Inline Filters
- 🔄 **Hot Reload** — توسعهٔ سریع بدون توقف ربات
- ⏰ **Scheduler** — زمان‌بندی کارها (interval + daily at)
- 📡 **Signals** — سیستم Event-driven برای ارتباط ماژول‌ها
- 🔌 **Plugins** — سیستم پلاگین با لود خودکار از پوشه
- 🗄️ **ORM داخلی** — دیتابیس SQLite با API ساده و SQL پارامتری
- 📸 **Snapshots** — Version Control برای تنظیمات ربات
- 🌐 **Webhook Server** — سرور داخلی (FastAPI/Flask)
- 💻 **CLI** — ابزار خط فرمان (`fastrub new`, `fastrub run --reload`)
- 🛡️ **AntiSpam** — سیستم ضد اسپم پیشرفته
- 🪶 **فوق‌العاده سبک** — تست شده روی ۲۵۶MB RAM DDR1 با Alpine Linux
- 🔒 **امنیت** — SQL پارامتری، sanitize خودکار، middleware امنیتی

---

## 📥 نصب

```bash
pip install fastrub
```

در صورت قطع شدن میرور اصلی PyPI:

```bash
pip install -i https://mirror-pypi.runflare.com/simple fastrub
```

---

🚀 شروع سریع

دریافت پیام‌ها (Polling)

```python
import asyncio
from fast_rub import Client, filters
from fast_rub.types import Update

async def main():
    bot = Client("my_bot")
    await bot.start()

    @bot.on_message(filters.text("سلام"))
    async def say_hello(msg: Update):
        await msg.reply("**سلام** از طرف فست روب ⚡")

    await bot.run()

asyncio.run(main())
```

کلیک روی دکمه‌های Inline

```python
import asyncio
from fast_rub import Client
from fast_rub.types import UpdateButton

async def main():
    bot = Client("my_bot")
    await bot.start()

    @bot.on_button()
    async def button_click(msg: UpdateButton):
        await msg.send_text(f"دکمهٔ {msg.button_id} فشرده شد")

    await bot.run()

asyncio.run(main())
```

---

🧠 WaitManager — مدیریت هوشمند ترافیک

قوی‌ترین سیستم مدیریت Rate Limit در بین تمام فریم‌ورک‌های روبیکا.
کافی است به Client بدهید — بقیه خودکار انجام می‌شود.

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
        auto_track=True,  # همه چیز خودکار
    )
)

@bot.on_message()
async def handler(msg: Message):
    await msg.reply("سلام!")  # WaitManager خودکار تأخیر را مدیریت می‌کند

await bot.run()
```

کانال‌های قابل ردیابی

کانال کاربرد
sending ارسال پیام
banning اخراج (بن)
forwarding بازنشر (فوروارد)
uploading آپلود فایل
editing ویرایش پیام
deleting حذف پیام

---

📋 DataForm — فرم‌های هوشمند

فقط بگویید «چی می‌خواهید» — اعتبارسنجی، کیبورد، و حرکت بین فیلدها خودکار است.

```python
from fast_rub import Client, Conversation
from fast_rub.core.forms import Text, Number, DataForm

class UserInfo(DataForm):
    name: Text = Text("👤 نام خود را وارد کنید", min_len=3, max_len=30)
    age: Number = Number("🎂 چند سالته؟", min=18, max=60, keypad=True)

register = Conversation(name="register")

@register.entry_form(UserInfo, commands=["/register"])
async def done(msg, data):
    await msg.reply(f"ثبت شد:\n👤 {data['name']}\n🎂 {data['age']}")

bot.add_conversation(register)
```

callbackهای شرطی (پیشرفته)

```python
class AdvancedForm(DataForm):
    name: Text = Text("نام؟", min_len=3,
        repeat_if=lambda v: "admin" in v.lower(),  # دوباره بپرس
    )
    age: Number = Number("سن؟", min=18, max=60)
    job: Text = Text("شغل؟",
        skip_if=lambda data: data.get("age", 0) < 18,  # زیر ۱۸ سال نپرس
    )
    city: Text = Text("شهر؟",
        cancel_if=lambda v: v == "هیچی",  # فرم را کنسل کن
    )
```

---

💬 Conversation — مکالمات چندمرحله‌ای

روش کلاسیک (Entry + State)

```python
register = Conversation(name="register")

@register.entry(commands=["/register"])
async def ask_name(msg, data):
    await msg.reply("اسمت چیه؟")
    return "waiting_name"

@register.state("waiting_name")
async def get_name(msg, data):
    data["name"] = msg.text
    await msg.reply(f"سلام {msg.text}!")
    return Conversation.END

bot.add_conversation(register)
```

---

🔍 فیلترها (۲۰۰+)

```python
from fast_rub import filters

# فیلتر ساده
@bot.on_message(filters.text("/start"))

# ترکیب (AND)
@bot.on_message(filters.text("/admin") & filters.is_user)

# ترکیب (OR)
@bot.on_message(filters.text("/help") | filters.text("راهنما"))

# NOT
@bot.on_message(~filters.is_group)  # فقط PV

# Async — چک دیتابیس
@bot.on_message(filters.db_exists("users", lambda u: {"chat_id": u.chat_id}, db=my_db))

# Inline Filters (دکمه‌های شیشه‌ای)
@bot.on_button(filters.button_id("home") & filters.sender_ids(["admin_id"]))
```

---

⌨️ ساختن کیبورد

```python
from fast_rub.button import KeyPad

keypad = KeyPad()
keypad.append(keypad.simple("btn_1", "دکمه یک"))
keypad.append(keypad.simple("btn_2", "دکمه دو"), keypad.simple("btn_3", "دکمه سه"))

# کیبورد معمولی
await msg.reply("انتخاب کنید:", keypad=keypad.build())

# کیبورد شیشه‌ای
await msg.reply("انتخاب کنید:", inline_keypad=keypad.build())
```

---

🔄 Hot Reload

هر بار فایلی را ذخیره کنید، ربات خودکار ری‌استارت می‌شود.

```python
await bot.run(reload=True)
# یا از CLI:
# $ fastrub run --reload
```

---

⏰ Scheduler

```python
from fast_rub import Scheduler

scheduler = Scheduler()

@scheduler.every(minutes=30)
async def cleanup():
    print("🧹 پاک‌سازی خودکار")

@scheduler.every(at="08:00")
async def report():
    print("📊 گزارش صبحگاهی")
```

---

📡 Signals

```python
from fast_rub import SignalManager

signals = SignalManager()

@signals.on("user_registered")
async def welcome(user_id, chat_id):
    print(f"👋 کاربر {user_id} ثبت‌نام کرد!")

await signals.emit("user_registered", user_id="123", chat_id="456")
```

---

🔌 Plugins

فایل plugins/admin.py:

```python
async def setup(client):
    @client.on_message(commands=["/admin"])
    async def panel(msg):
        await msg.reply("🔧 پنل ادمین")
```

لود خودکار:

```python
await bot.load_plugins("plugins")
```

---

🗄️ ORM داخلی

```python
from fast_rub.db import DataBase

db = DataBase("my_bot.db")
await db.start({"users": {"chat_id": "TEXT", "name": "TEXT"}})

await db.write("users", {"chat_id": "123", "name": "علی"})
user = await db.find("users", "*", {"chat_id": "123"})
```

---

💻 CLI

```bash
fastrub new my_bot     # پروژه جدید
fastrub run            # اجرا
fastrub run --reload   # اجرا با Hot Reload
fastrub version        # نسخه
fastrub docs           # مستندات
```

---

📁 ساختار پروژه

```
fast_rub/
├── core/           # هستهٔ فریم‌ورک (Client، Conversation، Middleware، Plugins...)
├── pyrubi/         # یوزر بات (fork از pyrubi)
├── types/          # Update، Message، Button، MetaData، Errors...
├── core/forms/     # DataForm، Text، Number، Choice
├── utils/          # WaitManager، فیلترها، Cache، AntiSpam، Snapshot...
├── db/             # ORM داخلی (DataBase)
├── button/         # KeyPad
└── network/        # HTTP/2 Client
```

---

📚 مستندات کامل

· مستندات رسمی
· گیت‌هاب
· PyPI

---

⚠️ نکته

بخش pyrubi فورکی از AliGanji1/pyrubi است که برای قسمت یوزر بات استفاده شده.

---

<p align="center">ساخته‌شده با ❤️ توسط <strong>سید محمد حسین موسوی رجا — OandONE</strong></p>
