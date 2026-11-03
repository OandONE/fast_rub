# سرور مستندات Fast Rub

سرور مستندات، قالب‌های HTML را با هش محتوای JSON رندر می‌کند تا صفحات HTML
و فایل‌های JSON مجبور نباشند هر بار دستی هم‌زمان تغییر کنند. تنها منبع داده،
فایل‌های `docs/*.json` هستند.

## اجرا

```bash
pip install fastapi uvicorn
uvicorn docs_server.app:app --host 127.0.0.1 --port 8000
```

سپس:

- `http://127.0.0.1:8000/` — صفحهٔ اصلی
- `http://127.0.0.1:8000/features/index.html` — قابلیت‌ها
- `http://127.0.0.1:8000/docs/features/index.html` — همان صفحه با پیشوند `/docs`

> برای اجرای محلی از `python -m docs_server.app` هم می‌توانید استفاده کنید.
> صفحات را مستقیم با `file://` باز نکنید؛ برای `fetch` به وب‌سرور نیاز است.

اگر صفحات بدون این سرور (مثلاً روی هاست استاتیک) سرو شوند و هش تزریق نشود،
لودر به‌صورت جایگزین نسخهٔ را بدون `?h=` و با `no-cache` می‌گیرد؛
صفحه کار می‌کند ولی مزیت کش immutable را ندارد.

## چطور کار می‌کند؟

1. صفحهٔ HTML یک قالب استاتیک است و فقط یک placeholder دارد:
   ```html
   <meta name="docs-hash" content="__FASTRUB_DOCS_HASH__">
   ```
2. سرور JSON مربوط به همان صفحه را می‌خواند و هش SHA-256 (۱۶ کاراکتر اول)
   محتوایش را جای placeholder می‌گذارد.
3. `docs/docs-data.js` آن هش را می‌خواند و داده را از
   `../<name>.min.json?h=<hash>` می‌گیرد.
4. چون URL شامل هش است:
   - JSON عوض نشده → همان URL → مرورگر از کش می‌خواند و درخواستی به سرور نمی‌زند.
   - JSON عوض شده → هش جدید → URL جدید → نسخهٔ تازه گرفته می‌شود.

### هدرهای کش

| منبع | هدر |
|------|-----|
| HTML صفحه‌ها | `Cache-Control: no-cache` + `ETag` (تغییر نکرده = `304`) |
| JSON با `?h=<hash>` جاری | `Cache-Control: public, max-age=31536000, immutable` |
| JSON بدون هش یا با هش قدیمی | `Cache-Control: no-cache` + `ETag` (`304` در صورت عدم تغییر) |
| `docs-data.js` | `Cache-Control: no-cache` + `ETag` |
| `icon.jpg` | `Cache-Control: public, max-age=86400` |

HTML باید revalidate شود؛ وگرنه مرورگر هش قدیمی را نگه می‌دارد و JSON جدید
هرگز دیده نمی‌شود. در حالت عادی این revalidation یک `304` سبک است.

## مسیرها

| مسیر | توضیح |
|------|-------|
| `/` و `/index.html` | صفحهٔ اصلی (استاتیک) |
| `/features/index.html` و `/features/` | صفحات مستندات (هش‌دار) |
| `/features.json` | JSON خام (pretty)؛ با `?h=` کش immutable |
| `/features.min.json` | JSON مینیفای تولیدشده؛ مصرف اصلی صفحات |
| `/docs/...` | همان مسیرها با پیشوند `/docs` |
| `/docs-data.js` | لودر مشترک JSON |
| `/health` | healthcheck |
| `/manifest.json` | manifest سادهٔ PWA |

`/{page}` بدون اسلش به `/{page}/` ریدایرکت می‌شود. مسیرهای ناشناخته ۴۰۴
می‌دهند؛ نام صفحه‌ها و JSONها در `docs_server/app.py` وایت‌لیست شده‌اند.

## ویرایش مستندات(در صورت مشارکت)

1. فقط `docs/*.json` را تغییر بده.
2. نیازی به اجرای `json_miner.py` نیست: سرور و بیلدر، فایل مینیفای و
   `all.json` را از همان JSONهای pretty می‌سازند. پس اگر فراموش شود،
   سایت با دادهٔ کهنه بالا نمی‌آید.
3. نیازی به ری‌استارت سرور نیست؛ هش‌ها با mtime/size دوباره محاسبه می‌شوند.

> `docs/json_miner.py` فقط برای به‌روزرسانی فایل‌های خامِ کامیت‌شده
> (`.min.json` و `all.json` داخل ریپو) کاربرد دارد و برای اجرای سایت
> لازم نیست. صفحات از `.min.json` تولیدشده می‌خوانند.

## ساخت استاتیک برای GitHub Pages

همان موتور رندر، بدون FastAPI:

```bash
python -m docs_server.build --out _site
```

خروجی `_site` شامل صفحات هش‌دار، JSON مینیفای‌شده، `all.json`،
`docs-data.js`، `manifest.json` و `.nojekyll` است.

workflow آماده در [`.github/workflows/docs.yml`](../.github/workflows/docs.yml)
هست

URL:

- `https://oandone.github.io/fast_rub/`

## نکات باقی‌مانده

- بخشی از JSONها هنوز در فیلدهایی HTML دارند. قدم بعدی
  استفاده از Markdown در JSON و رندر آن در JS باشد (صفحهٔ prerequisites
  از قبل `markdown` را با `marked` رندر می‌کند).
