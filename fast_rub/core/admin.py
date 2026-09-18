"""
پنل ادمین FastRub — نمایش لاگ لحظه‌ای، تنظیمات زندهٔ ربات و آمار از طریق وب.
FastRub Admin Panel — real-time logs, live bot settings and stats over the web.

- بک‌اند FastAPI یا Flask (هماهنگ با داشبورد)
- احراز هویت داخلی بدون کتابخانهٔ جدا: رمز + کوکی امضاشده با HMAC + قفل تلاش ناموفق + توکن CSRF
- پنل فقط برای تغییر/مشاهده است؛ توکن ربات هرگز کامل نمایش داده نمی‌شود

استفاده:
    await bot.start_admin(password="my_secret")
    # سپس: http://127.0.0.1:8081/admin
"""
import asyncio
import hashlib
import hmac
import logging
import os
import secrets
import threading
import time
from collections import deque
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from .client import Client

COOKIE_NAME = "fastrub_admin"
LOCKOUT_THRESHOLD = 5      # تعداد تلاش ناموفق
LOCKOUT_WINDOW = 300.0     # پنجرهٔ شمارش تلاش‌ها (ثانیه)
LOCKOUT_TIME = 60.0        # مدت قفل (ثانیه)


class _BufferLogHandler(logging.Handler):
    """هندلر لاگ مستقل پنل ادمین — مستقیم به root logger وصل می‌شود"""

    def __init__(self, on_entry) -> None:
        super().__init__(level=logging.INFO)
        self._on_entry = on_entry

    def emit(self, record: logging.LogRecord) -> None:
        try:
            # نویزهای وب‌سرور/HTTP کلاینت ثبت نشوند — هر poll پنل خودش لاگ می‌سازد
            # و لاگ httpx URL کامل (شامل توکن ربات) را نشان می‌دهد
            name = record.name
            if name.startswith(("uvicorn", "werkzeug", "httpx", "httpcore")):
                return
            self._on_entry(
                {
                    "level": record.levelname,
                    "message": self.format(record),
                    "time": record.created,
                }
            )
        except Exception:
            pass


LOGIN_PAGE = r"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ورود • پنل ادمین FastRub</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  :root{--bg:#0f172a;--card:#1e293b;--text:#e2e8f0;--dim:#94a3b8;--accent:#6366f1;--accent2:#8b5cf6;--red:#ef4444;--border:#334155}
  body{font-family:'Segoe UI',Tahoma,system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:16px;
    background-image:radial-gradient(at 0% 0%,rgba(99,102,241,.18),transparent 50%),radial-gradient(at 100% 0%,rgba(139,92,246,.15),transparent 50%);background-attachment:fixed}
  .box{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:32px;width:100%;max-width:380px;box-shadow:0 20px 60px rgba(0,0,0,.4)}
  .logo{width:56px;height:56px;border-radius:14px;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;font-size:28px;margin:0 auto 16px;box-shadow:0 8px 24px rgba(99,102,241,.35)}
  h1{font-size:18px;text-align:center;margin-bottom:4px}
  .sub{font-size:12px;color:var(--dim);text-align:center;margin-bottom:24px}
  input{width:100%;background:#0f172a;color:var(--text);border:1px solid var(--border);border-radius:10px;padding:12px 14px;font-size:14px;font-family:inherit;outline:none;margin-bottom:14px;direction:ltr;text-align:left}
  input:focus{border-color:var(--accent)}
  button{width:100%;background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;border:none;border-radius:10px;padding:12px;font-size:14px;font-family:inherit;font-weight:700;cursor:pointer}
  button:hover{filter:brightness(1.1)}
  .err{background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.35);color:#fca5a5;border-radius:10px;padding:10px 14px;font-size:13px;margin-bottom:14px;display:none}
  .foot{font-size:11px;color:var(--dim);text-align:center;margin-top:18px}
  .foot a{color:var(--accent);text-decoration:none}
</style>
</head>
<body>
<div class="box">
  <div class="logo">🛡️</div>
  <h1>پنل ادمین FastRub</h1>
  <div class="sub">برای ادامه رمز پنل را وارد کنید</div>
  <div class="err" id="err">رمز اشتباه است یا تعداد تلاش‌ها زیاد است — کمی بعد دوباره تلاش کنید</div>
  <input type="password" id="password" placeholder="رمز پنل ادمین" autocomplete="current-password">
  <button id="btn">ورود</button>
  <div class="foot">ساخته‌شده با ❤️ توسط <a href="https://github.com/OandONE/fast_rub" target="_blank">FastRub</a></div>
</div>
<script>
const BASE = location.pathname.replace(/\/+$/, '').replace(/\/login$/, '');
if(new URLSearchParams(location.search).get('error')) document.getElementById('err').style.display = 'block';
async function login(){
  const btn = document.getElementById('btn');
  btn.disabled = true; btn.textContent = 'در حال ورود…';
  try{
    const r = await fetch(BASE + '/login', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({password: document.getElementById('password').value})
    });
    if(r.ok){ location.replace(BASE); return; }
    if(r.status === 429){ document.getElementById('err').textContent = 'تلاش‌های ناموفق زیاد بود — یک دقیقه صبر کنید'; }
    document.getElementById('err').style.display = 'block';
  }catch(e){ document.getElementById('err').textContent = 'خطا در اتصال به سرور'; document.getElementById('err').style.display = 'block'; }
  btn.disabled = false; btn.textContent = 'ورود';
}
document.getElementById('btn').addEventListener('click', login);
document.getElementById('password').addEventListener('keydown', e => { if(e.key === 'Enter') login(); });
</script>
</body>
</html>
"""


ADMIN_PAGE = r"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>پنل ادمین • FastRub</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  :root{
    --bg:#0f172a;--card:#1e293b;--card2:#172033;--hover:#334155;
    --text:#e2e8f0;--dim:#94a3b8;--accent:#6366f1;--accent2:#8b5cf6;
    --green:#10b981;--yellow:#f59e0b;--red:#ef4444;--border:#334155;
  }
  body{font-family:'Segoe UI',Tahoma,system-ui,sans-serif;background:var(--bg);color:var(--text);padding:20px;min-height:100vh;
    background-image:radial-gradient(at 0% 0%,rgba(99,102,241,.15),transparent 50%),radial-gradient(at 100% 0%,rgba(139,92,246,.12),transparent 50%);background-attachment:fixed}
  .container{max-width:1100px;margin:0 auto}
  header{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid var(--border)}
  .brand{display:flex;align-items:center;gap:12px}
  .logo{width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;font-size:22px}
  h1{font-size:19px}
  .sub{font-size:12px;color:var(--dim);margin-top:2px}
  .tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px}
  .tab-btn{background:var(--card2);color:var(--dim);border:1px solid var(--border);border-radius:10px;padding:9px 16px;font-size:13px;font-family:inherit;cursor:pointer;transition:all .2s}
  .tab-btn:hover{color:var(--text)}
  .tab-btn.active{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;border-color:transparent}
  .panel{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:20px;margin-bottom:16px}
  h2{font-size:16px;margin-bottom:14px}
  h3{font-size:13px;color:var(--dim);margin:16px 0 10px}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:16px}
  .card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:16px}
  .card-label{font-size:12px;color:var(--dim);margin-bottom:8px}
  .card-value{font-size:22px;font-weight:800;font-variant-numeric:tabular-nums}
  .green{color:var(--green)}.yellow{color:var(--yellow)}.purple{color:var(--accent2)}.red{color:var(--red)}
  table{width:100%;border-collapse:collapse}
  th,td{text-align:right;padding:10px 12px;font-size:13px;border-bottom:1px solid var(--border)}
  th{background:var(--card2);color:var(--dim);font-size:11px;font-weight:600}
  tr:last-child td{border-bottom:none}
  tbody tr:hover{background:var(--hover)}
  code{background:var(--card2);border:1px solid var(--border);border-radius:6px;padding:2px 7px;font-size:12px;direction:ltr;display:inline-block}
  .badge{display:inline-block;font-size:11px;padding:3px 10px;border-radius:20px;background:rgba(99,102,241,.15);color:#a5b4fc;border:1px solid rgba(99,102,241,.3)}
  input,select{background:var(--card2);color:var(--text);border:1px solid var(--border);border-radius:10px;padding:10px 13px;font-size:13px;font-family:inherit;outline:none}
  input:focus,select:focus{border-color:var(--accent)}
  .btn{background:var(--card2);color:var(--text);border:1px solid var(--border);border-radius:10px;padding:9px 16px;font-size:13px;font-family:inherit;cursor:pointer;transition:all .2s}
  .btn:hover{border-color:var(--accent)}
  .btn.primary{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;border-color:transparent;font-weight:700}
  .btn.danger:hover{border-color:var(--red);color:#fca5a5}
  .row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
  .field{display:flex;flex-direction:column;gap:6px;margin-bottom:12px;min-width:180px;flex:1}
  .field label{font-size:12px;color:var(--dim)}
  .switch{display:flex;align-items:center;gap:8px;margin-bottom:10px;font-size:13px;cursor:pointer;user-select:none}
  .log-level{font-weight:700;font-size:11px;padding:2px 8px;border-radius:6px}
  .lv-INFO{background:rgba(16,185,129,.15);color:#6ee7b7}
  .lv-WARNING{background:rgba(245,158,11,.15);color:#fcd34d}
  .lv-ERROR,.lv-CRITICAL{background:rgba(239,68,68,.15);color:#fca5a5}
  .lv-DEBUG{background:rgba(148,163,184,.15);color:var(--dim)}
  #logBox{max-height:420px;overflow:auto;border:1px solid var(--border);border-radius:12px;background:#0b1222}
  .hint{font-size:12px;color:var(--dim);margin-top:10px;line-height:1.8}
  .ok-msg{color:var(--green);font-size:13px;font-weight:600}
  .empty{padding:30px;text-align:center;color:var(--dim);font-size:13px}
  .footer{text-align:center;padding:18px 0 4px;color:var(--dim);font-size:12px}
  .footer a{color:var(--accent);text-decoration:none}
  @media(max-width:640px){ body{padding:12px} .card-value{font-size:18px} }
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="brand">
      <div class="logo">🛡️</div>
      <div>
        <h1>پنل ادمین FastRub</h1>
        <div class="sub" id="sessionName">—</div>
      </div>
    </div>
    <div class="row">
      <span class="badge" id="modeBadge">—</span>
      <a class="btn danger" id="logoutBtn" href="__PREFIX__/logout" style="text-decoration:none">خروج</a>
    </div>
  </header>

  <div class="tabs">
    <button class="tab-btn active" data-tab="overview">📊 نمای کلی</button>
    <button class="tab-btn" data-tab="logs">📜 لاگ‌ها</button>
    <button class="tab-btn" data-tab="settings">⚙️ تنظیمات</button>
    <button class="tab-btn" data-tab="stats">📈 آمار</button>
    <button class="tab-btn" data-tab="system">💻 سیستم</button>
    <button class="tab-btn" data-tab="tools">🧰 ابزارها</button>
  </div>

  <!-- نمای کلی -->
  <section id="tab-overview">
    <div class="cards">
      <div class="card"><div class="card-label">وضعیت ربات</div><div class="card-value" id="ovRunning">—</div></div>
      <div class="card"><div class="card-label">⏱️ فعال‌باشد از</div><div class="card-value yellow" id="ovUptime">—</div></div>
      <div class="card"><div class="card-label">🎛️ هندلرها</div><div class="card-value purple" id="ovHandlers">—</div></div>
      <div class="card"><div class="card-label">💬 مکالمات فعال</div><div class="card-value green" id="ovConvUsers">—</div></div>
    </div>
    <div class="panel">
      <h2>🤖 ربات</h2>
      <div id="ovBot">—</div>
      <h3>💬 مکالمات</h3>
      <div id="ovConversations">—</div>
      <h3>🔌 پلاگین‌ها</h3>
      <div id="ovPlugins">—</div>
    </div>
  </section>

  <!-- لاگ‌ها -->
  <section id="tab-logs" hidden>
    <div class="panel">
      <div class="row" style="margin-bottom:12px">
        <select id="logLevel">
          <option value="">همهٔ سطوح</option>
          <option value="INFO">INFO+</option>
          <option value="WARNING">WARNING+</option>
          <option value="ERROR">ERROR+</option>
        </select>
        <label class="switch" style="margin:0"><input type="checkbox" id="logAuto" checked> اسکرول خودکار</label>
        <span style="flex:1"></span>
        <button class="btn" id="logClear">🧹 پاک‌سازی نمایش</button>
      </div>
      <div id="logBox">
        <div class="empty">لاگی ثبت نشده است</div>
      </div>
      <div class="hint">لاگ‌ها هر ۲ ثانیه به‌روز می‌شوند. حداکثر ۱۰۰۰ لاگ آخر در حافظه نگه داشته می‌شود.</div>
    </div>
  </section>

  <!-- تنظیمات -->
  <section id="tab-settings" hidden>
    <div class="panel">
      <h2>⚙️ تنظیمات زندهٔ ربات</h2>

      <h3>عمومی</h3>
      <div class="row">
        <div class="field"><label>Parsing Mode</label>
          <select id="sParseMode">
            <option value="Markdown">Markdown</option>
            <option value="HTML">HTML</option>
            <option value="Null">Null (بدون تبدیل)</option>
          </select>
        </div>
        <div class="field"><label>poll_interval (ثانیه)</label><input type="number" id="sPoll" step="0.1" min="0"></div>
        <div class="field"><label>time_out (ثانیه)</label><input type="number" id="sTimeout" step="1" min="1"></div>
        <div class="field"><label>defult_wait (ثانیه)</label><input type="number" id="sDefWait" step="0.1" min="0"></div>
      </div>

      <h3>رفتار پیام (BotConfig)</h3>
      <label class="switch"><input type="checkbox" id="cValidate"> اعتبارسنجی chat_id (validate_chat_id)</label>
      <label class="switch"><input type="checkbox" id="cStrip"> حذف فاصله‌های اضافی (strip_text)</label>
      <label class="switch"><input type="checkbox" id="cOptimize"> بهینه‌سازی متن (optimize_text)</label>
      <label class="switch"><input type="checkbox" id="cCompress"> برش با «...» (compress_long_text)</label>
      <label class="switch"><input type="checkbox" id="cEscape"> محافظت تزریق (auto_escape)</label>
      <label class="switch"><input type="checkbox" id="cRetry"> تلاش مجدد در timeout (retry_on_timeout)</label>
      <div class="field" style="max-width:260px"><label>max_text_length (خالی = بدون محدودیت)</label><input type="number" id="sMaxLen" min="1"></div>

      <div id="wmGroup">
        <h3>WaitManager</h3>
        <div class="row">
          <div class="field"><label>low_wait</label><input type="number" id="wmLow" step="0.1" min="0"></div>
          <div class="field"><label>medium_wait</label><input type="number" id="wmMed" step="0.1" min="0"></div>
          <div class="field"><label>high_wait</label><input type="number" id="wmHigh" step="0.1" min="0"></div>
          <div class="field"><label>time_window</label><input type="number" id="wmWin" step="1" min="1"></div>
        </div>
      </div>

      <div id="cacheGroup">
        <h3>Cache</h3>
        <div class="row">
          <div class="field"><label>ttl (ثانیه)</label><input type="number" id="caTtl" step="1" min="1"></div>
          <div class="field"><label>max_size</label><input type="number" id="caMax" step="1" min="1"></div>
        </div>
      </div>

      <div class="row" style="margin-top:14px">
        <button class="btn primary" id="saveSettings">💾 ذخیرهٔ تنظیمات</button>
        <span class="ok-msg" id="saveMsg"></span>
      </div>
      <div class="hint">⚠️ ssl_verify و توکن فقط نمایش داده می‌شوند و از پنل تغییر نمی‌کنند (نیاز به ساخت مجدد اتصال شبکه دارند). تنظیمات به‌صورت زنده اعمال می‌شوند؛ برای ماندگاری از SnapshotManager استفاده کنید.</div>
    </div>
  </section>

  <!-- آمار -->
  <section id="tab-stats" hidden>
    <div class="panel">
      <h2>📈 آمار پیام‌ها</h2>
      <div class="cards" id="stCards"></div>
      <div class="row" style="margin-bottom:12px">
        <input type="text" id="stSearch" placeholder="🔍 جستجوی نام یا آیدی…" style="min-width:220px">
        <select id="stSort">
          <option value="count">بیشترین پیام</option>
          <option value="today">بیشترین امروز</option>
          <option value="title">نام (الفبا)</option>
        </select>
      </div>
      <div id="stTable"><div class="empty">—</div></div>
      <div class="hint" id="stHint"></div>
    </div>
  </section>

  <!-- سیستم -->
  <section id="tab-system" hidden>
    <div class="panel">
      <h2>💻 سیستم</h2>
      <div class="cards" id="sysCards"></div>
      <div id="sysTable">—</div>
      <div class="hint" id="sysHint"></div>
    </div>
  </section>

  <!-- ابزارها -->
  <section id="tab-tools" hidden>
    <div class="panel">
      <h2>✉️ ارسال پیام از پنل</h2>
      <div class="row">
        <div class="field" style="max-width:280px"><label>chat_id</label><input type="text" id="tChatId" placeholder="b0123abc..." dir="ltr"></div>
        <div class="field" style="flex:2"><label>متن پیام</label><input type="text" id="tText" placeholder="سلام از پنل ادمین!"></div>
        <button class="btn primary" id="tSend">ارسال</button>
      </div>
      <div class="hint" id="tSendMsg"></div>
    </div>
    <div class="panel">
      <h2>🔍 اطلاعات چت</h2>
      <div class="row">
        <div class="field" style="max-width:280px"><label>chat_id</label><input type="text" id="lChatId" placeholder="b0123abc..." dir="ltr"></div>
        <button class="btn" id="lBtn">جستجو</button>
      </div>
      <div id="lResult" style="margin-top:10px">—</div>
    </div>
    <div class="panel">
      <h2>🧹 نگهداری</h2>
      <div class="row">
        <button class="btn danger" id="cacheBtn">پاک‌سازی کش</button>
        <span class="ok-msg" id="cacheMsg"></span>
      </div>
    </div>
  </section>

  <div class="footer">ساخته‌شده با ❤️ توسط <a href="https://github.com/OandONE/fast_rub" target="_blank">FastRub</a></div>
</div>

<script>
const $ = id => document.getElementById(id);
const BASE = '__PREFIX__'.replace(/\/+$/, '');
const API = BASE + '/api';
const CSRF = '__CSRF__';

function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function formatNumber(n){return new Intl.NumberFormat('fa-IR').format(n)}
function formatUptime(s){
  const d=Math.floor(s/86400),h=Math.floor((s%86400)/3600),m=Math.floor((s%3600)/60);
  const parts=[];
  if(d)parts.push(d+' روز');
  if(h)parts.push(h+' ساعت');
  if(m&&!d)parts.push(m+' دقیقه');
  if(!d&&!h)parts.push((s%60)+' ثانیه');
  return parts.slice(0,2).join(' و ');
}
async function api(path, opts={}){
  opts.headers = Object.assign({'X-CSRF-Token': CSRF}, opts.headers||{});
  const r = await fetch(API + path, opts);
  if(r.status === 401){ location.replace(BASE + '/login'); throw new Error('unauthorized'); }
  const data = await r.json().catch(()=>({}));
  if(!r.ok) throw Object.assign(new Error(data.error || ('HTTP '+r.status)), {status:r.status});
  return data;
}

/* ───── تب‌ها ───── */
let activeTab = 'overview';
document.querySelectorAll('.tab-btn').forEach(btn=>{
  btn.addEventListener('click', ()=>{
    document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    activeTab = btn.dataset.tab;
    ['overview','logs','settings','stats','system','tools'].forEach(t=>{
      $('tab-'+t).hidden = (t !== activeTab);
    });
    if(activeTab==='overview') loadOverview();
    if(activeTab==='settings') loadSettings();
    if(activeTab==='stats') loadStats();
    if(activeTab==='system') loadSystem();
  });
});

/* ───── نمای کلی ───── */
async function loadOverview(){
  try{
    const d = await api('/overview');
    $('sessionName').textContent = d.name_session || '—';
    $('ovRunning').textContent = d.running ? 'در حال اجرا ✅' : 'متوقف ⛔';
    $('ovRunning').className = 'card-value ' + (d.running ? 'green' : 'red');
    $('ovUptime').textContent = formatUptime(d.uptime_seconds);
    $('ovHandlers').textContent = formatNumber(d.handlers);
    $('ovConvUsers').textContent = formatNumber(d.active_conversation_users);
    const modeBadge = $('modeBadge');
    modeBadge.textContent = d.dry_run ? '🧪 Dry Run' : '⚡ اجرای واقعی';
    let bot = '<table><tbody>';
    bot += '<tr><td>نام ربات</td><td>' + escapeHtml(d.bot_title || '—') + '</td></tr>';
    bot += '<tr><td>یوزرنیم</td><td>' + escapeHtml(d.bot_username ? '@'+d.bot_username : '—') + '</td></tr>';
    bot += '<tr><td>Parsing Mode</td><td><code>' + escapeHtml(d.parse_mode ?? 'Null') + '</code></td></tr>';
    bot += '<tr><td>poll_interval</td><td><code>' + d.poll_interval + '</code></td></tr>';
    bot += '<tr><td>Middlewareها</td><td>' + formatNumber(d.middlewares) + '</td></tr>';
    bot += '<tr><td>تسک‌های زمان‌بند</td><td>' + formatNumber(d.scheduler_tasks) + '</td></tr>';
    bot += '<tr><td>تسک‌های بک‌گراند</td><td>' + formatNumber(d.background_tasks) + '</td></tr>';
    bot += '<tr><td>آمار</td><td>' + (d.stats_enabled ? 'فعال ✅' : 'غیرفعال (enable_stats=False)') + '</td></tr>';
    bot += '</tbody></table>';
    $('ovBot').innerHTML = bot;
    let conv = '';
    if(!d.conversations.length) conv = '<div class="empty">مکالمه‌ای ثبت نشده</div>';
    else{
      conv = '<table><thead><tr><th>نام</th><th>Timeout</th><th>کاربران فعال</th></tr></thead><tbody>';
      d.conversations.forEach(c=>{ conv += '<tr><td><code>' + escapeHtml(c.name) + '</code></td><td>' + c.timeout + 's</td><td>' + formatNumber(c.active_users) + '</td></tr>'; });
      conv += '</tbody></table>';
    }
    $('ovConversations').innerHTML = conv;
    $('ovPlugins').innerHTML = d.plugins.length
      ? d.plugins.map(p=>'<span class="badge" style="margin:2px">'+escapeHtml(p)+'</span>').join(' ')
      : '<div class="empty">پلاگینی لود نشده</div>';
  }catch(e){ console.error(e); }
}

/* ───── لاگ‌ها ───── */
let lastLogId = 0;
const LEVEL_ORDER = {DEBUG:10, INFO:20, WARNING:30, ERROR:40, CRITICAL:50};
async function loadLogs(){
  try{
    const d = await api('/logs?after=' + lastLogId);
    if(d.logs.length){
      const box = $('logBox');
      const empty = box.querySelector('.empty'); if(empty) empty.remove();
      const minLevel = $('logLevel').value ? LEVEL_ORDER[$('logLevel').value] : 0;
      const stick = $('logAuto').checked && (box.scrollTop + box.clientHeight >= box.scrollHeight - 40);
      d.logs.forEach(l=>{
        lastLogId = Math.max(lastLogId, l.id);
        if(LEVEL_ORDER[l.level] === undefined || LEVEL_ORDER[l.level] < minLevel) return;
        const row = document.createElement('div');
        row.style.cssText = 'padding:7px 12px;border-bottom:1px solid rgba(51,65,85,.4);font-size:12px';
        row.innerHTML = '<span class="log-level lv-'+escapeHtml(l.level)+'">'+escapeHtml(l.level)+'</span> '
          + '<span style="color:var(--dim);font-size:11px">'+new Date(l.time*1000).toLocaleTimeString('fa-IR')+'</span> '
          + escapeHtml(l.message);
        box.appendChild(row);
      });
      while(box.children.length > 400) box.removeChild(box.firstChild);
      if(stick) box.scrollTop = box.scrollHeight;
    }
  }catch(e){ console.error(e); }
}
$('logClear').addEventListener('click', ()=>{ $('logBox').innerHTML = '<div class="empty">لاگی ثبت نشده است</div>'; });
$('logLevel').addEventListener('change', loadLogs);
setInterval(()=>{ if(activeTab==='logs') loadLogs(); }, 2000);

/* ───── تنظیمات ───── */
async function loadSettings(){
  try{
    const s = await api('/settings');
    $('sParseMode').value = s.main_parse_mode === null ? 'Null' : s.main_parse_mode;
    $('sPoll').value = s.poll_interval;
    $('sTimeout').value = s.time_out;
    $('sDefWait').value = s.defult_wait === null ? '' : s.defult_wait;
    $('cValidate').checked = s.config.validate_chat_id;
    $('cStrip').checked = s.config.strip_text;
    $('cOptimize').checked = s.config.optimize_text;
    $('cCompress').checked = s.config.compress_long_text;
    $('cEscape').checked = s.config.auto_escape;
    $('cRetry').checked = s.config.retry_on_timeout;
    $('sMaxLen').value = s.config.max_text_length === null ? '' : s.config.max_text_length;
    $('wmGroup').style.display = s.wait_manager ? '' : 'none';
    if(s.wait_manager){
      $('wmLow').value = s.wait_manager.low_wait;
      $('wmMed').value = s.wait_manager.medium_wait;
      $('wmHigh').value = s.wait_manager.high_wait;
      $('wmWin').value = s.wait_manager.time_window;
    }
    $('cacheGroup').style.display = s.cache ? '' : 'none';
    if(s.cache){
      $('caTtl').value = s.cache.ttl;
      $('caMax').value = s.cache.max_size;
    }
  }catch(e){ console.error(e); }
}
$('saveSettings').addEventListener('click', async ()=>{
  const payload = {
    main_parse_mode: $('sParseMode').value,
    poll_interval: parseFloat($('sPoll').value || 0),
    time_out: parseFloat($('sTimeout').value || 60),
    defult_wait: $('sDefWait').value === '' ? null : parseFloat($('sDefWait').value),
    config: {
      validate_chat_id: $('cValidate').checked,
      strip_text: $('cStrip').checked,
      optimize_text: $('cOptimize').checked,
      compress_long_text: $('cCompress').checked,
      auto_escape: $('cEscape').checked,
      retry_on_timeout: $('cRetry').checked,
      max_text_length: $('sMaxLen').value === '' ? null : parseInt($('sMaxLen').value),
    }
  };
  if($('wmGroup').style.display !== 'none'){
    payload.wait_manager = {
      low_wait: parseFloat($('wmLow').value || 0),
      medium_wait: parseFloat($('wmMed').value || 0),
      high_wait: parseFloat($('wmHigh').value || 0),
      time_window: parseFloat($('wmWin').value || 60),
    };
  }
  if($('cacheGroup').style.display !== 'none'){
    payload.cache = {
      ttl: parseFloat($('caTtl').value || 300),
      max_size: parseInt($('caMax').value || 100),
    };
  }
  try{
    const d = await api('/settings', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    $('saveMsg').textContent = '✅ ذخیره شد: ' + d.applied.join('، ');
    setTimeout(()=>{ $('saveMsg').textContent=''; }, 5000);
    loadOverview();
  }catch(e){ $('saveMsg').textContent = '❌ ' + e.message; }
});

/* ───── آمار ───── */
function typeLabel(t){const m={Group:'👥 گروه',Channel:'📢 کانال',User:'👤 کاربر',unknown:'❔ نامشخص'};return m[t]||('❔ '+t)}
async function loadStats(){
  try{
    const search = $('stSearch').value.trim();
    const params = new URLSearchParams({sort: $('stSort').value});
    if(search) params.set('search', search);
    const d = await api('/stats?' + params.toString());
    $('stHint').textContent = '';
    $('stCards').innerHTML =
      '<div class="card"><div class="card-label">📨 کل پیام‌ها</div><div class="card-value">'+formatNumber(d.summary.total_messages)+'</div></div>'
      + '<div class="card"><div class="card-label">📅 امروز</div><div class="card-value green">'+formatNumber(d.summary.today_messages)+'</div></div>'
      + '<div class="card"><div class="card-label">💬 چت‌ها</div><div class="card-value purple">'+formatNumber(d.summary.total_chats)+'</div></div>';
    if(!d.chats.length){ $('stTable').innerHTML = '<div class="empty">هنوز پیامی دریافت نشده</div>'; return; }
    let h = '<table><thead><tr><th>چت</th><th>نوع</th><th>کل</th><th>امروز</th><th>آخرین پیام</th></tr></thead><tbody>';
    d.chats.forEach(x=>{
      h += '<tr><td><div style="font-weight:600">'+escapeHtml(x.title)+'</div><div class="sub" style="direction:ltr;text-align:right;font-size:11px;color:var(--dim)">'+escapeHtml(x.chat_id)+'</div></td>'
        + '<td><span class="badge">'+typeLabel(x.type)+'</span></td>'
        + '<td>'+formatNumber(x.count)+'</td><td class="green">'+formatNumber(x.today)+'</td>'
        + '<td style="font-size:11px;color:var(--dim)">'+escapeHtml(x.last_message_at || '—')+'</td></tr>';
    });
    $('stTable').innerHTML = h + '</tbody></table>';
  }catch(e){
    $('stHint').textContent = 'آمار غیرفعال است — برای فعال‌سازی enable_stats=True را در Client تنظیم کنید.';
    $('stTable').innerHTML = '<div class="empty">—</div>'; $('stCards').innerHTML = '';
  }
}
let stDebounce; $('stSearch').addEventListener('input', ()=>{ clearTimeout(stDebounce); stDebounce = setTimeout(loadStats, 300); });
$('stSort').addEventListener('change', loadStats);

/* ───── سیستم ───── */
async function loadSystem(){
  try{
    const d = await api('/system');
    $('sysHint').textContent = d.psutil ? '' : '💡 برای نمایش رم و CPU: pip install psutil';
    let cards = '<div class="card"><div class="card-label">🐍 پایتون</div><div class="card-value" style="font-size:16px">'+escapeHtml(d.python)+'</div></div>'
      + '<div class="card"><div class="card-label">⏱️ Uptime پنل</div><div class="card-value yellow" style="font-size:16px">'+formatUptime(d.uptime_seconds)+'</div></div>'
      + '<div class="card"><div class="card-label">🧵 Threadها</div><div class="card-value purple" style="font-size:16px">'+formatNumber(d.threads)+'</div></div>';
    if(d.psutil){
      cards += '<div class="card"><div class="card-label">🧠 رم پروسه</div><div class="card-value green" style="font-size:16px">'+d.ram_mb+' MB</div></div>'
        + '<div class="card"><div class="card-label">⚙️ CPU پروسه</div><div class="card-value" style="font-size:16px">'+d.cpu_percent+'٪</div></div>';
    }
    $('sysCards').innerHTML = cards;
    let t = '<table><tbody>';
    t += '<tr><td>سیستم‌عامل</td><td style="font-size:12px">'+escapeHtml(d.platform)+'</td></tr>';
    t += '<tr><td>PID</td><td><code>'+d.pid+'</code></td></tr>';
    t += '<tr><td>تسک‌های asyncio</td><td>'+formatNumber(d.asyncio_tasks)+'</td></tr>';
    t += '<tr><td>لاگ‌های در حافظه</td><td>'+formatNumber(d.log_buffer)+'</td></tr>';
    t += '</tbody></table>';
    $('sysTable').innerHTML = t;
  }catch(e){ console.error(e); }
}

/* ───── ابزارها ───── */
$('tSend').addEventListener('click', async ()=>{
  const msg = $('tSendMsg');
  try{
    const d = await api('/send', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({chat_id: $('tChatId').value.trim(), text: $('tText').value})});
    msg.textContent = '✅ ارسال شد — message_id: ' + d.message_id;
  }catch(e){ msg.textContent = '❌ ' + e.message; }
});
$('lBtn').addEventListener('click', async ()=>{
  const box = $('lResult');
  try{
    const d = await api('/lookup', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({chat_id: $('lChatId').value.trim()})});
    box.innerHTML = '<table><tbody>'
      + '<tr><td>chat_id</td><td><code>'+escapeHtml(d.chat_id)+'</code></td></tr>'
      + '<tr><td>نوع</td><td>'+typeLabel(d.type)+'</td></tr>'
      + '<tr><td>نام</td><td>'+escapeHtml(d.title || d.first_name || '—')+'</td></tr>'
      + '<tr><td>یوزرنیم</td><td>'+escapeHtml(d.username ? '@'+d.username : '—')+'</td></tr>'
      + '</tbody></table>';
  }catch(e){ box.innerHTML = '<span style="color:var(--red);font-size:13px">❌ ' + escapeHtml(e.message) + '</span>'; }
});
$('cacheBtn').addEventListener('click', async ()=>{
  try{ await api('/cache/clear', {method:'POST'}); $('cacheMsg').textContent = '✅ کش پاک شد'; }
  catch(e){ $('cacheMsg').textContent = '❌ ' + e.message; }
  setTimeout(()=>{ $('cacheMsg').textContent=''; }, 4000);
});

/* ───── شروع ───── */
loadOverview();
setInterval(()=>{ if(activeTab==='overview') loadOverview(); }, 5000);
setInterval(()=>{ if(activeTab==='system') loadSystem(); }, 10000);
</script>
</body>
</html>
"""


class AdminPanel:
    """
    پنل ادمین — لاگ لحظه‌ای، تنظیمات زنده، آمار و ابزارهای مدیریتی.

    Parameters
    ----------
    client : Client
        کلاینت FastRub
    host : str
        آدرس گوش دادن (پیش‌فرض: 127.0.0.1 — فقط لوکال)
    port : int
        پورت (پیش‌فرض: 8081)
    backend : Literal["fastapi", "flask"]
        بک‌اند سرور
    path_prefix : str
        پیشوند مسیر (پیش‌فرض: /admin)
    password : str | None
        رمز پنل — اگر None باشد رمز قوی تصادفی ساخته و در کنسول چاپ می‌شود
    session_hours : float
        مدت اعتبار نشست ورود (ساعت)
    logger : logging.Logger | None
        لاگر اختصاصی
    """

    def __init__(
        self,
        client: "Client",
        host: str = "127.0.0.1",
        port: int = 8081,
        backend: Literal["fastapi", "flask"] = "fastapi",
        path_prefix: str = "/admin",
        password: str | None = None,
        session_hours: float = 12.0,
        logger: logging.Logger | None = None,
    ) -> None:
        if backend not in ("fastapi", "flask"):
            raise ValueError(f"backend must be 'fastapi' or 'flask', not '{backend}'")

        self.client = client
        self.host = host
        self.port = port
        self.backend = backend
        self.path_prefix = path_prefix.rstrip("/")
        self.session_hours = session_hours
        self.logger = logger or logging.getLogger("fast_rub.admin")

        self._secret = secrets.token_hex(32)
        self._csrf_token = secrets.token_hex(16)
        self._password_generated = not password
        self._password: str = password if password else secrets.token_urlsafe(9)

        self._failed: dict[str, list[float]] = {}
        self._locked_until: dict[str, float] = {}
        self._logs: deque[dict[str, Any]] = deque(maxlen=1000)
        self._log_seq = 0
        self._started_at = time.time()

        self._server: Any = None
        self._app: Any = None
        self._loop: asyncio.AbstractEventLoop | None = None

        # لاگ‌های ربات را در بافر پنل هم بریز — مستقل از زنجیرهٔ on_log کلاینت
        self._log_handler = _BufferLogHandler(self._on_log_entry)
        self._log_handler.setFormatter(
            logging.Formatter("%(name)s | %(message)s")
        )
        logging.getLogger().addHandler(self._log_handler)

    # ═══════════════════════════════════
    # region 🔐 احراز هویت | Auth
    # ═══════════════════════════════════

    def _sign(self, value: str) -> str:
        return hmac.new(
            self._secret.encode(), value.encode(), hashlib.sha256
        ).hexdigest()

    def _make_session_cookie(self) -> str:
        expiry = str(int(time.time()) + int(self.session_hours * 3600))
        return f"{expiry}.{self._sign(expiry)}"

    def _check_session(self, cookie: str | None) -> bool:
        if not cookie or "." not in cookie:
            return False
        expiry, signature = cookie.split(".", 1)
        if not expiry.isdigit():
            return False
        if not hmac.compare_digest(self._sign(expiry), signature):
            return False
        return int(expiry) >= time.time()

    def _check_password(self, password: str) -> bool:
        return hmac.compare_digest(
            password.encode("utf-8"), self._password.encode("utf-8")
        )

    def _ip_locked(self, ip: str) -> bool:
        return time.time() < self._locked_until.get(ip, 0.0)

    def _record_failure(self, ip: str) -> None:
        now = time.time()
        recent = [t for t in self._failed.get(ip, []) if now - t < LOCKOUT_WINDOW]
        recent.append(now)
        self._failed[ip] = recent
        if len(recent) >= LOCKOUT_THRESHOLD:
            self._locked_until[ip] = now + LOCKOUT_TIME
            self._failed.pop(ip, None)
            self.logger.warning(f"پنل ادمین: IP {ip} به‌خاطر تلاش‌های ناموفق قفل شد ({LOCKOUT_TIME:.0f}s)")

    def _reset_failures(self, ip: str) -> None:
        self._failed.pop(ip, None)
        self._locked_until.pop(ip, None)

    def _check_csrf(self, token: str | None) -> bool:
        return bool(token) and hmac.compare_digest(token, self._csrf_token)

    # endregion

    # ═══════════════════════════════════
    # region 📜 لاگ | Log Buffer
    # ═══════════════════════════════════

    def _on_log_entry(self, entry: dict) -> None:
        self._log_seq += 1
        self._logs.append(
            {
                "id": self._log_seq,
                "level": str(entry.get("level", "INFO")),
                "message": str(entry.get("message", "")),
                "time": float(entry.get("time", time.time())),
            }
        )

    def _logs_since(self, after: int) -> list[dict[str, Any]]:
        return [log for log in self._logs if log["id"] > after]

    # endregion

    # ═══════════════════════════════════
    # region 📊 داده‌ها | Data Providers
    # ═══════════════════════════════════

    async def _overview_data(self) -> dict[str, Any]:
        c = self.client
        me = None
        try:
            me = await c.get_me()
        except Exception:
            pass
        conversations = list(c._conversation_manager._conversations.values())
        return {
            "name_session": getattr(c, "name_session", "?"),
            "running": bool(getattr(c, "_running", False)),
            "dry_run": bool(getattr(c, "dry_run", False)),
            "uptime_seconds": int(time.time() - self._started_at),
            "bot_title": getattr(me, "bot_title", None) if me else None,
            "bot_username": getattr(me, "username", None) if me else None,
            "parse_mode": c.main_parse_mode,
            "poll_interval": c.poll_interval,
            "handlers": (
                len(c._message_handlers_polling)
                + len(c._message_handlers_webhook)
                + len(c._button_handlers)
            ),
            "middlewares": c._middleware_manager.count,
            "scheduler_tasks": c.scheduler.count if hasattr(c, "scheduler") else 0,
            "background_tasks": c._background.count,
            "stats_enabled": bool(c.enable_stats and c.stats),
            "active_conversation_users": sum(
                len(conv._user_states) for conv in conversations
            ),
            "conversations": [
                {
                    "name": conv.name,
                    "timeout": conv.timeout,
                    "active_users": len(conv._user_states),
                }
                for conv in conversations
            ],
            "plugins": list(c._loaded_plugins),
        }

    def _settings_data(self) -> dict[str, Any]:
        c = self.client
        cfg = c.config
        wm = getattr(c, "wait_manager", None)
        cache = getattr(c, "cache", None)
        return {
            "main_parse_mode": c.main_parse_mode,
            "poll_interval": c.poll_interval,
            "time_out": c.time_out,
            "defult_wait": c.defult_wait,
            "ssl_verify": c.ssl_verify,
            "config": {
                "validate_chat_id": cfg.validate_chat_id,
                "optimize_text": cfg.optimize_text,
                "strip_text": cfg.strip_text,
                "max_text_length": cfg.max_text_length,
                "compress_long_text": cfg.compress_long_text,
                "auto_escape": cfg.auto_escape,
                "retry_on_timeout": cfg.retry_on_timeout,
            },
            "wait_manager": (
                {
                    "low_wait": wm.low_wait,
                    "medium_wait": wm.medium_wait,
                    "high_wait": wm.high_wait,
                    "time_window": wm.time_window,
                }
                if wm
                else None
            ),
            "cache": (
                {"ttl": cache.ttl, "max_size": cache.max_size} if cache else None
            ),
        }

    def _apply_settings(self, payload: dict[str, Any]) -> list[str]:
        """اعمال تنظیمات با اعتبارسنجی نوع/محدوده — لیست موارد اعمال‌شده برمی‌گرداند"""
        applied: list[str] = []
        c = self.client

        if "main_parse_mode" in payload:
            value = payload["main_parse_mode"]
            if value in ("Markdown", "HTML", "Null", None):
                c.main_parse_mode = value
                applied.append("main_parse_mode")

        if "poll_interval" in payload:
            value = payload["poll_interval"]
            if isinstance(value, (int, float)) and value >= 0:
                c.poll_interval = float(value)
                applied.append("poll_interval")

        if "time_out" in payload:
            value = payload["time_out"]
            if isinstance(value, (int, float)) and value > 0:
                c.time_out = float(value)
                applied.append("time_out")

        if "defult_wait" in payload:
            value = payload["defult_wait"]
            if value is None or (isinstance(value, (int, float)) and value >= 0):
                c.defult_wait = None if value is None else float(value)
                applied.append("defult_wait")

        config_payload = payload.get("config")
        if isinstance(config_payload, dict):
            cfg = c.config
            bool_flags = (
                "validate_chat_id",
                "optimize_text",
                "strip_text",
                "compress_long_text",
                "auto_escape",
                "retry_on_timeout",
            )
            for flag in bool_flags:
                if flag in config_payload and isinstance(config_payload[flag], bool):
                    setattr(cfg, flag, config_payload[flag])
                    applied.append(flag)
            if "max_text_length" in config_payload:
                value = config_payload["max_text_length"]
                if value is None or (isinstance(value, int) and value > 0):
                    cfg.max_text_length = value
                    applied.append("max_text_length")

        wm_payload = payload.get("wait_manager")
        if isinstance(wm_payload, dict):
            wm = getattr(c, "wait_manager", None)
            if wm is not None:
                for key in ("low_wait", "medium_wait", "high_wait", "time_window"):
                    if key in wm_payload:
                        value = wm_payload[key]
                        if isinstance(value, (int, float)) and value >= 0:
                            setattr(wm, key, float(value))
                            applied.append(f"wait_manager.{key}")

        cache_payload = payload.get("cache")
        if isinstance(cache_payload, dict):
            cache = getattr(c, "cache", None)
            if cache is not None:
                if "ttl" in cache_payload:
                    value = cache_payload["ttl"]
                    if isinstance(value, (int, float)) and value > 0:
                        cache.ttl = float(value)
                        applied.append("cache.ttl")
                if "max_size" in cache_payload:
                    value = cache_payload["max_size"]
                    if isinstance(value, int) and value > 0:
                        cache.max_size = value
                        applied.append("cache.max_size")

        return applied

    async def _stats_data(self, sort: str, search: str) -> dict[str, Any]:
        if not (self.client.enable_stats and self.client.stats):
            raise RuntimeError("Stats not enabled — Client(enable_stats=True) لازم است")
        stats = self.client.stats
        summary = await stats.get_summary()  # pyright: ignore[reportOptionalMemberAccess]
        chats = await stats.get_chats(sort_by=sort, search=search)  # pyright: ignore[reportOptionalMemberAccess]
        return {"summary": summary, "chats": chats}

    async def _send_message(self, chat_id: str, text: str) -> dict[str, Any]:
        if not chat_id or not text:
            raise ValueError("chat_id و text لازم است")
        result = await self.client.send_text(chat_id=chat_id, text=text)
        return {"ok": True, "message_id": getattr(result, "message_id", None)}

    async def _lookup_chat(self, chat_id: str) -> dict[str, Any]:
        from ..utils.utils import Utils

        chat = await self.client.get_chat(chat_id)
        return {
            "chat_id": chat.chat_id,
            "type": Utils.get_chat_id_type(chat.chat_id),
            "title": getattr(chat, "title", None),
            "first_name": getattr(chat, "first_name", None),
            "username": getattr(chat, "username", None),
        }

    def _system_data(self) -> dict[str, Any]:
        import platform
        import sys

        data: dict[str, Any] = {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "pid": os.getpid(),
            "uptime_seconds": int(time.time() - self._started_at),
            "threads": threading.active_count(),
            "log_buffer": len(self._logs),
            "asyncio_tasks": 0,
            "psutil": False,
        }
        try:
            data["asyncio_tasks"] = len(asyncio.all_tasks(self._loop))
        except Exception:
            try:
                data["asyncio_tasks"] = len(asyncio.all_tasks())
            except Exception:
                pass
        try:
            import psutil # pyright: ignore[reportMissingModuleSource]

            process = psutil.Process()
            data["psutil"] = True
            data["ram_mb"] = round(process.memory_info().rss / 1048576, 1)
            data["cpu_percent"] = process.cpu_percent(interval=0.1)
        except ImportError:
            pass
        except Exception:
            pass
        return data

    # endregion

    # ═══════════════════════════════════
    # region 🛣️ مسیرها | Routes
    # ═══════════════════════════════════

    def _render_admin_page(self) -> str:
        return ADMIN_PAGE.replace("__CSRF__", self._csrf_token).replace(
            "__PREFIX__", self.path_prefix
        )

    def _create_fastapi_app(self) -> Any:
        try:
            from fastapi import FastAPI, Request
            from fastapi.responses import (
                HTMLResponse,
                JSONResponse,
                RedirectResponse,
            )
        except ImportError as e:
            raise ImportError(
                "FastAPI not installed! install: pip install fast_rub[fastapi]"
            ) from e

        app = FastAPI(
            title="FastRub Admin Panel",
            docs_url=None,
            redoc_url=None,
            openapi_url=None,
        )

        def _authed(req: Request) -> bool:
            return self._check_session(req.cookies.get(COOKIE_NAME))

        def _unauthorized() -> JSONResponse:
            return JSONResponse({"error": "unauthorized"}, status_code=401)

        def _forbidden(message: str = "forbidden") -> JSONResponse:
            return JSONResponse({"error": message}, status_code=403)

        async def _json_body(req: Request) -> dict[str, Any]:
            try:
                payload = await req.json()
            except Exception:
                return {}
            return payload if isinstance(payload, dict) else {}

        @app.get(self.path_prefix, response_class=HTMLResponse)
        async def index(req: Request):
            if not _authed(req):
                return RedirectResponse(f"{self.path_prefix}/login", status_code=302)
            return HTMLResponse(self._render_admin_page())

        @app.get(f"{self.path_prefix}/login", response_class=HTMLResponse)
        async def login_page():
            return HTMLResponse(LOGIN_PAGE)

        @app.post(f"{self.path_prefix}/login")
        async def login(req: Request):
            ip = req.client.host if req.client else "?"
            if self._ip_locked(ip):
                return JSONResponse(
                    {"error": "too many attempts"}, status_code=429
                )
            body = await _json_body(req)
            password = str(body.get("password", ""))
            if self._check_password(password):
                self._reset_failures(ip)
                response = JSONResponse({"ok": True})
                response.set_cookie(
                    COOKIE_NAME,
                    self._make_session_cookie(),
                    httponly=True,
                    samesite="lax",
                )
                self.logger.info(f"پنل ادمین: ورود موفق از {ip}")
                return response
            self._record_failure(ip)
            return JSONResponse({"error": "wrong password"}, status_code=403)

        @app.get(f"{self.path_prefix}/logout")
        async def logout():
            response = RedirectResponse(f"{self.path_prefix}/login", status_code=302)
            response.delete_cookie(COOKIE_NAME)
            return response

        @app.get(f"{self.path_prefix}/api/overview")
        async def api_overview(req: Request):
            if not _authed(req):
                return _unauthorized()
            return JSONResponse(await self._overview_data())

        @app.get(f"{self.path_prefix}/api/logs")
        async def api_logs(req: Request, after: int = 0):
            if not _authed(req):
                return _unauthorized()
            return JSONResponse({"logs": self._logs_since(after)})

        @app.get(f"{self.path_prefix}/api/settings")
        async def api_settings_get(req: Request):
            if not _authed(req):
                return _unauthorized()
            return JSONResponse(self._settings_data())

        @app.post(f"{self.path_prefix}/api/settings")
        async def api_settings_post(req: Request):
            if not _authed(req):
                return _unauthorized()
            if not self._check_csrf(req.headers.get("x-csrf-token")):
                return _forbidden("csrf token invalid")
            applied = self._apply_settings(await _json_body(req))
            self.logger.info(f"پنل ادمین: تنظیمات اعمال شد — {applied}")
            return JSONResponse({"applied": applied})

        @app.get(f"{self.path_prefix}/api/stats")
        async def api_stats(req: Request, sort: str = "count", search: str = ""):
            if not _authed(req):
                return _unauthorized()
            try:
                return JSONResponse(await self._stats_data(sort, search))
            except RuntimeError as e:
                return JSONResponse({"error": str(e)}, status_code=400)

        @app.post(f"{self.path_prefix}/api/send")
        async def api_send(req: Request):
            if not _authed(req):
                return _unauthorized()
            if not self._check_csrf(req.headers.get("x-csrf-token")):
                return _forbidden("csrf token invalid")
            body = await _json_body(req)
            try:
                return JSONResponse(
                    await self._send_message(
                        str(body.get("chat_id", "")), str(body.get("text", ""))
                    )
                )
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=400)

        @app.post(f"{self.path_prefix}/api/lookup")
        async def api_lookup(req: Request):
            if not _authed(req):
                return _unauthorized()
            if not self._check_csrf(req.headers.get("x-csrf-token")):
                return _forbidden("csrf token invalid")
            body = await _json_body(req)
            try:
                return JSONResponse(await self._lookup_chat(str(body.get("chat_id", ""))))
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=400)

        @app.post(f"{self.path_prefix}/api/cache/clear")
        async def api_cache_clear(req: Request):
            if not _authed(req):
                return _unauthorized()
            if not self._check_csrf(req.headers.get("x-csrf-token")):
                return _forbidden("csrf token invalid")
            cache = getattr(self.client, "cache", None)
            if cache is None:
                return JSONResponse({"error": "cache فعال نیست"}, status_code=400)
            await cache.clear()
            return JSONResponse({"ok": True})

        @app.get(f"{self.path_prefix}/api/system")
        async def api_system(req: Request):
            if not _authed(req):
                return _unauthorized()
            return JSONResponse(self._system_data())

        return app

    def _create_flask_app(self) -> Any:
        try:
            from flask import Flask, jsonify, redirect, request
        except ImportError as e:
            raise ImportError(
                "Flask not installed! install: pip install fast_rub[flask]"
            ) from e

        app = Flask("fast_rub_admin")

        def _authed() -> bool:
            return self._check_session(request.cookies.get(COOKIE_NAME))

        def _csrf_ok() -> bool:
            return self._check_csrf(request.headers.get("X-CSRF-Token"))

        def _run(coro: Any) -> Any:
            """اجرای coroutine روی event loop اصلی ربات از داخل thread فلسک"""
            if self._loop is None or self._loop.is_closed():
                raise RuntimeError("event loop اصلی ربات در دسترس نیست")
            future = asyncio.run_coroutine_threadsafe(coro, self._loop)
            return future.result(timeout=30)

        @app.route(self.path_prefix)
        def index():  # pyright: ignore[reportUnusedFunction]
            if not _authed():
                return redirect(f"{self.path_prefix}/login")
            return self._render_admin_page()

        @app.route(f"{self.path_prefix}/login", methods=["GET", "POST"])
        def login():  # pyright: ignore[reportUnusedFunction]
            ip = request.remote_addr or "?"
            if request.method == "GET":
                return LOGIN_PAGE
            if self._ip_locked(ip):
                return jsonify({"error": "too many attempts"}), 429
            body = request.get_json(silent=True) or {}
            password = str(body.get("password", ""))
            if self._check_password(password):
                self._reset_failures(ip)
                response = jsonify({"ok": True})
                response.set_cookie(
                    COOKIE_NAME,
                    self._make_session_cookie(),
                    httponly=True,
                    samesite="Lax",
                )
                self.logger.info(f"پنل ادمین: ورود موفق از {ip}")
                return response
            self._record_failure(ip)
            return jsonify({"error": "wrong password"}), 403

        @app.route(f"{self.path_prefix}/logout")
        def logout():  # pyright: ignore[reportUnusedFunction]
            response = redirect(f"{self.path_prefix}/login")
            response.delete_cookie(COOKIE_NAME)
            return response

        @app.route(f"{self.path_prefix}/api/overview")
        def api_overview():  # pyright: ignore[reportUnusedFunction]
            if not _authed():
                return jsonify({"error": "unauthorized"}), 401
            return jsonify(_run(self._overview_data()))

        @app.route(f"{self.path_prefix}/api/logs")
        def api_logs():  # pyright: ignore[reportUnusedFunction]
            if not _authed():
                return jsonify({"error": "unauthorized"}), 401
            after = request.args.get("after", 0, type=int)
            return jsonify({"logs": self._logs_since(after)})

        @app.route(f"{self.path_prefix}/api/settings", methods=["GET", "POST"])
        def api_settings():  # pyright: ignore[reportUnusedFunction]
            if not _authed():
                return jsonify({"error": "unauthorized"}), 401
            if request.method == "GET":
                return jsonify(self._settings_data())
            if not _csrf_ok():
                return jsonify({"error": "csrf token invalid"}), 403
            body = request.get_json(silent=True) or {}
            applied = self._apply_settings(body)
            self.logger.info(f"پنل ادمین: تنظیمات اعمال شد — {applied}")
            return jsonify({"applied": applied})

        @app.route(f"{self.path_prefix}/api/stats")
        def api_stats():  # pyright: ignore[reportUnusedFunction]
            if not _authed():
                return jsonify({"error": "unauthorized"}), 401
            sort = request.args.get("sort", "count")
            search = request.args.get("search", "")
            try:
                return jsonify(_run(self._stats_data(sort, search)))
            except RuntimeError as e:
                return jsonify({"error": str(e)}), 400

        @app.route(f"{self.path_prefix}/api/send", methods=["POST"])
        def api_send():  # pyright: ignore[reportUnusedFunction]
            if not _authed():
                return jsonify({"error": "unauthorized"}), 401
            if not _csrf_ok():
                return jsonify({"error": "csrf token invalid"}), 403
            body = request.get_json(silent=True) or {}
            try:
                return jsonify(
                    _run(
                        self._send_message(
                            str(body.get("chat_id", "")), str(body.get("text", ""))
                        )
                    )
                )
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @app.route(f"{self.path_prefix}/api/lookup", methods=["POST"])
        def api_lookup():  # pyright: ignore[reportUnusedFunction]
            if not _authed():
                return jsonify({"error": "unauthorized"}), 401
            if not _csrf_ok():
                return jsonify({"error": "csrf token invalid"}), 403
            body = request.get_json(silent=True) or {}
            try:
                return jsonify(_run(self._lookup_chat(str(body.get("chat_id", "")))))
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @app.route(f"{self.path_prefix}/api/cache/clear", methods=["POST"])
        def api_cache_clear():  # pyright: ignore[reportUnusedFunction]
            if not _authed():
                return jsonify({"error": "unauthorized"}), 401
            if not _csrf_ok():
                return jsonify({"error": "csrf token invalid"}), 403
            cache = getattr(self.client, "cache", None)
            if cache is None:
                return jsonify({"error": "cache فعال نیست"}), 400
            _run(cache.clear())
            return jsonify({"ok": True})

        @app.route(f"{self.path_prefix}/api/system")
        def api_system():  # pyright: ignore[reportUnusedFunction]
            if not _authed():
                return jsonify({"error": "unauthorized"}), 401
            return jsonify(self._system_data())

        return app

    # endregion

    # ═══════════════════════════════════
    # region 🚀 شروع و توقف | Start & Stop
    # ═══════════════════════════════════

    async def start(self) -> None:
        """شروع سرور پنل ادمین"""
        self._started_at = time.time()
        self._loop = asyncio.get_running_loop()

        if self._password_generated:
            # رمز تصادفی ساخته شده — حتماً باید به کاربر نشان داده شود
            print(
                f"\n🛡️ پنل ادمین FastRub — رمز ورود: {self._password}\n"
                f"   آدرس: http://{self.host}:{self.port}{self.path_prefix}\n"
            )
            self.logger.warning(
                "رمز پنل ادمین به‌صورت تصادفی ساخته شد و در کنسول چاپ شد — "
                "برای رمز دلخواه: bot.start_admin(password='...')"
            )

        if self.backend == "fastapi":
            self._app = self._create_fastapi_app()
            import uvicorn

            config = uvicorn.Config(
                self._app,
                host=self.host,
                port=self.port,
                log_level="warning",
            )
            self._server = uvicorn.Server(config)
            self.logger.info(
                f"🛡️ Admin Panel (FastAPI) running at "
                f"http://{self.host}:{self.port}{self.path_prefix}"
            )
            await self._server.serve()
        else:
            from werkzeug.serving import make_server

            self._app = self._create_flask_app()
            self._server = make_server(
                self.host, self.port, self._app, threaded=True
            )
            self.logger.info(
                f"🛡️ Admin Panel (Flask) running at "
                f"http://{self.host}:{self.port}{self.path_prefix}"
            )
            await asyncio.to_thread(self._server.serve_forever)

    async def stop(self) -> None:
        """توقف سرور پنل ادمین"""
        logging.getLogger().removeHandler(self._log_handler)
        if self.backend == "fastapi" and self._server is not None:
            self._server.should_exit = True
        elif self.backend == "flask" and self._server is not None:
            await asyncio.to_thread(self._server.shutdown)
        self.logger.info("🛡️ Admin Panel stopped")

    # endregion
