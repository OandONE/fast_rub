<p align="center">
  <img src="https://fast-rub.ParsSource.ir/icon.jpg" width="200" alt="Fast Rub">
</p>

<h1 align="center">Fast Rub ⚡</h1>
<p align="center"><strong>سریع‌ترین کتابخانهٔ ساخت ربات روبیکا برای پایتون</strong></p>

<p align="center">
  <a href="https://pypi.org/project/fastrub/"><img src="https://img.shields.io/pypi/v/fastrub?color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/fastrub/"><img src="https://img.shields.io/pypi/pyversions/fastrub" alt="Python"></a>
  <a href="https://github.com/OandONE/fast_rub/blob/main/LICENSE"><img src="https://img.shields.io/github/license/OandONE/fast_rub" alt="License"></a>
</p>

---

## ✨ ویژگی‌های کلیدی

- ⚡ **سرعت بالا** — استفاده از `httpx` با HTTP/2 و معماری غیرهمزمان (async)
- 🧠 **WaitManager** — مدیریت هوشمند ترافیک برای جلوگیری از برخورد با محدودیت نرخ روبیکا
- 🔍 **بیش از ۲۰۰ فیلتر** — آماده برای پیام، دکمه، فرستنده، نوع چت و...
- 💬 **مکالمهٔ چندمرحله‌ای** — بدون درگیری با منطق پیچیده
- 🪶 **فوق‌العاده سبک** — کاملا بهینه شده
- 🔌 **Middleware و افزونه‌پذیری** — معماری قابل توسعه

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

دریافت پیام‌ها - پولینگ

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

کلیک روی دکمه‌های inline

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

🧠 مدیریت هوشمند ترافیک (WaitManager)

یکی از قدرتمندترین بخش‌های فست روب WaitManager است.
این ماژول با ردیابی تعداد درخواست‌های شما در کانال‌های جداگانه (ارسال، بن، فوروارد، آپلود و...) و در بازه‌های زمانی مشخص، به‌صورت خودکار فاصلهٔ زمانی مورد نیاز قبل از هر درخواست را محاسبه می‌کند تا ربات شما بدون برخورد با محدودیت نرخ روبیکا، با حداکثر سرعت ایمن کار کند.

یک مثال ساده

```python
from fast_rub import WaitManager

# تنظیم پارامترهای ترافیک
wm = WaitManager(
    low_traffic=60,       # ترافیک کم: تا ۶۰ درخواست در هر پنجرهٔ زمانی
    medium_traffic=100,   # ترافیک متوسط: ۶۰ تا ۱۰۰ درخواست
    low_wait=0.0,         # بدون تأخیر در ترافیک کم
    medium_wait=1.0,      # یک ثانیه تأخیر در ترافیک متوسط
    high_wait=3.0,        # سه ثانیه تأخیر در ترافیک بالا
    time_window=60.0,     # اندازهٔ پنجرهٔ زمانی (ثانیه)
    per_chat=True,        # محاسبه به‌ازای هر چت
)

# قبل از ارسال پیام، تأخیر لازم را بگیرید
delay = wm.get_time(channel="sending", chat_id=chat_id)
await asyncio.sleep(delay)

# پس از ارسال، ترافیک را ثبت کنید
wm.add_traffic(channel="sending", chat_id=chat_id)
```

کانال‌های قابل ردیابی

می‌توانید برای هر نوع عملیات یک کانال جداگانه تعریف کنید:

· sending (ارسال پیام)
· banning (اخراج)
· forwarding (بازنشر)
· uploading (آپلود)
· editing (ویرایش)
· deleting (حذف)

---

⌨️ ساختن کیبورد

کیبورد معمولی (Reply)

```python
from fast_rub.button import KeyPad

keypad = KeyPad()
keypad.append(keypad.simple("btn_1", "دکمه یک"))
keypad.append(keypad.simple("btn_2", "دکمه دو"), keypad.simple("btn_3", "دکمه سه"))

await msg.reply("لطفاً انتخاب کنید:", keypad=keypad.build())
```

کیبورد شیشه‌ای (Inline)

```python
keypad.append(keypad.simple("callback_1", "کلیک کن"))

await msg.reply("انتخاب کنید:", inline_keypad=keypad.build())
```

---

🔍 فیلترها

فست روب با بیش از ۲۰۰ فیلتر آماده ارائه می‌شود:

```python
from fast_rub import filters

@bot.on_message(filters.text("تست"))
async def handler(msg: Update):
    ...
```

ترکیب فیلترها:

· filters.and_filter(f1, f2) — هر دو شرط برقرار باشد
· filters.or_filter(f1, f2) — حداقل یکی برقرار باشد
· filters.not_filter(f1) — شرط برقرار نباشد

فیلتر سفارشی(اسنک و سینک)

```python
class MyFilter(filters.Filter):
    def __call__(self, update: Update) -> bool:
        return "خاص" in update.text

@bot.on_message(MyFilter())
async def handler(msg: Update):
    ...
```

---

📁 ساختار پروژه

```
fast_rub/
├── core/           # هستهٔ فریم‌ورک (کلاینت، میدلور، پلاگین‌ها و...)
├── pyrubi/         # یوزر بات (fork از کتابخانهٔ pyrubi)
├── types/          # تایپ‌های Update، Message، Button و...
├── utils/          # WaitManager، فیلترها، کش، لاگر و...
├── db/             # رابط پایگاه داده
├── button/         # ابزار ساخت کیبورد
└── network/        # تنظیمات شبکه و HTTP
```

---

📚 مستندات کامل

· [مستندات رسمی - سایت اصلی](https://fast-rub.ParsSource.ir/docs)
· [مستندات رسمی - گیتهاب](https://fast-rub.ParsSource.ir/docs)

· [گیت‌هاب](https://GitHub.com/OandONE/fast_rub)

· [صفحهٔ PyPI](https://PyPI.org/project/fastrub)

---

⚠️ نکته

بخش pyrubi در این کتابخانه، فورکی از پروژهٔ AliGanji1/pyrubi است که برای قسمت یوزر بات این پروژه استفاده شده

---

<p align="center">ساخته‌شده با ❤️ توسط سید محمد حسین موسوی رجا - OandONE</p>
```

---
