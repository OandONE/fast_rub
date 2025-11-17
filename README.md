<img src="https://fast-rub.ParsSource.ir/icon.jpg">

# Fast Rub

This Python library is for Rubika bots.

This library is extremely fast and can send requests to the Rubika server in an optimized and ultra-fast manner, handling your bot in the best possible way.

## Fast Rub

- 1 fast
- 2 simple syntax
- 3 Small size of the library

## install :

```bash
pip install --upgrade fastrub
```

[Documents](https://fast-rub.ParsSource.ir/index.html)

[GitHub](https://github.com/OandONE/fast_rub)

قسمت PyRubi این کتابخانه فورک کتابخانه [پایروبی](https://github.com/AliGanji1/pyrubi) است


### نحوه گرفتن آپدیت پیام ها
```python
from fast_rub import Client
from fast_rub.type import Update

bot = Client("name_session")

@bot.on_message()
async def getting(message:Update):
    await message.reply("__Hello__ *from* **FastRub** !")

bot.run()
```
