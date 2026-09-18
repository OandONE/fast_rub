"""
داشبورد HTML برای نمایش آمار پیام‌ها.
FastRub HTML Dashboard for message statistics.
"""
import asyncio
import logging
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .client import Client


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FastRub • آمار پیام‌ها</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  :root{
    --bg:#0f172a;--card:#1e293b;--card2:#172033;--hover:#334155;
    --text:#e2e8f0;--dim:#94a3b8;--accent:#6366f1;--accent2:#8b5cf6;
    --green:#10b981;--yellow:#f59e0b;--red:#ef4444;--border:#334155;
  }
  html,body{height:100%}
  body{
    font-family:'Segoe UI',Tahoma,system-ui,sans-serif;
    background:var(--bg);color:var(--text);padding:24px;
    background-image:
      radial-gradient(at 0% 0%,rgba(99,102,241,.18),transparent 50%),
      radial-gradient(at 100% 0%,rgba(139,92,246,.15),transparent 50%);
    background-attachment:fixed;min-height:100vh;
  }
  .container{max-width:1200px;margin:0 auto}
  header{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;margin-bottom:28px;padding-bottom:20px;border-bottom:1px solid var(--border)}
  .brand{display:flex;align-items:center;gap:14px}
  .logo{width:48px;height:48px;border-radius:12px;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;font-size:24px;box-shadow:0 8px 24px rgba(99,102,241,.35)}
  h1{font-size:22px;font-weight:700;background:linear-gradient(135deg,#fff,#94a3b8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
  .subtitle{font-size:13px;color:var(--dim);margin-top:4px}
  .controls{display:flex;gap:10px;align-items:center}
  .status{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--dim);padding:8px 14px;background:rgba(255,255,255,.03);border:1px solid var(--border);border-radius:10px}
  .dot{width:8px;height:8px;border-radius:50%;background:var(--green);box-shadow:0 0 12px var(--green);animation:pulse 2s infinite}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
  .btn{background:var(--card2);color:var(--text);border:1px solid var(--border);border-radius:10px;padding:8px 14px;font-size:13px;font-family:inherit;cursor:pointer;transition:all .2s}
  .btn:hover{border-color:var(--accent);color:#c7d2fe}
  .btn.danger:hover{border-color:var(--red);color:#fca5a5}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:28px}
  .card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:20px;position:relative;overflow:hidden;transition:transform .2s,border-color .2s}
  .card::before{content:'';position:absolute;top:0;right:0;left:0;height:3px;background:linear-gradient(90deg,var(--accent),var(--accent2))}
  .card:hover{transform:translateY(-3px);border-color:var(--accent)}
  .card-label{font-size:13px;color:var(--dim);margin-bottom:10px;display:flex;align-items:center;gap:6px}
  .card-value{font-size:30px;font-weight:800;letter-spacing:-.5px;font-variant-numeric:tabular-nums}
  .card-value.green{color:var(--green)}
  .card-value.yellow{color:var(--yellow)}
  .card-value.purple{color:var(--accent2)}
  .panel{background:var(--card);border:1px solid var(--border);border-radius:16px;overflow:hidden}
  .panel-head{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;padding:18px 22px;border-bottom:1px solid var(--border)}
  .panel-title{font-size:16px;font-weight:700}
  .filters{display:flex;gap:10px;flex-wrap:wrap}
  input[type=text],select{background:var(--card2);color:var(--text);border:1px solid var(--border);border-radius:10px;padding:10px 14px;font-size:14px;font-family:inherit;outline:none;transition:border-color .2s}
  input[type=text]:focus,select:focus{border-color:var(--accent)}
  input[type=text]{min-width:200px}
  select option{background:var(--card)}
  table{width:100%;border-collapse:collapse}
  th,td{text-align:right;padding:14px 22px;font-size:14px;border-bottom:1px solid var(--border)}
  th{background:var(--card2);color:var(--dim);font-weight:600;font-size:12px;letter-spacing:.5px}
  tr:last-child td{border-bottom:none}
  tbody tr{transition:background .15s}
  tbody tr:hover{background:var(--hover)}
  .rank{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:8px;background:var(--card2);font-weight:700;font-size:12px;color:var(--dim)}
  .rank.gold{background:linear-gradient(135deg,#fbbf24,#f59e0b);color:#0f172a}
  .rank.silver{background:linear-gradient(135deg,#e5e7eb,#9ca3af);color:#0f172a}
  .rank.bronze{background:linear-gradient(135deg,#d97706,#b45309);color:#fff}
  .chat-name{font-weight:600}
  .chat-id{font-size:11px;color:var(--dim);font-family:ui-monospace,monospace;direction:ltr;text-align:right;display:inline-block;margin-top:3px}
  .badge{display:inline-block;font-size:11px;padding:3px 10px;border-radius:20px;background:rgba(99,102,241,.15);color:#a5b4fc;border:1px solid rgba(99,102,241,.3)}
  .count-num{font-weight:700;font-variant-numeric:tabular-nums;font-size:15px}
  .count-num.green{color:var(--green)}
  .empty{padding:60px 20px;text-align:center;color:var(--dim)}
  .empty-icon{font-size:48px;margin-bottom:12px;opacity:.4}
  .footer{text-align:center;padding:24px 0 8px;color:var(--dim);font-size:12px}
  .footer a{color:var(--accent);text-decoration:none}
  @media(max-width:640px){
    body{padding:14px}
    h1{font-size:18px}
    .card-value{font-size:24px}
    th,td{padding:12px 14px;font-size:13px}
    .hide-mobile{display:none}
  }
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="brand">
      <div class="logo">⚡</div>
      <div>
        <h1>داشبورد آمار FastRub</h1>
        <div class="subtitle">آمار لحظه‌ای پیام‌های دریافت‌شده از گروه‌ها و چت‌ها</div>
      </div>
    </div>
    <div class="controls">
      <div class="status"><span class="dot"></span><span id="statusText">در حال اتصال…</span></div>
      <button class="btn danger" id="resetBtn">🗑️ ریست</button>
    </div>
  </header>

  <div class="cards">
    <div class="card"><div class="card-label">📨 کل پیام‌ها</div><div class="card-value" id="totalMessages">0</div></div>
    <div class="card"><div class="card-label">📅 پیام‌های امروز</div><div class="card-value green" id="todayMessages">0</div></div>
    <div class="card"><div class="card-label">💬 چت‌های فعال</div><div class="card-value purple" id="activeChats">0</div></div>
    <div class="card"><div class="card-label">⏱️ زمان فعالیت</div><div class="card-value yellow" id="uptime">—</div></div>
  </div>

  <div class="panel">
    <div class="panel-head">
      <div class="panel-title">📊 رتبه‌بندی چت‌ها</div>
      <div class="filters">
        <input type="text" id="search" placeholder="🔍 جستجوی نام یا آیدی…">
        <select id="sortBy">
          <option value="count">بیشترین پیام</option>
          <option value="today">بیشترین امروز</option>
          <option value="title">نام (الفبا)</option>
        </select>
      </div>
    </div>
    <div id="tableContainer">
      <div class="empty"><div class="empty-icon">📭</div><div>در حال بارگذاری…</div></div>
    </div>
  </div>

  <div class="footer">
    ساخته‌شده با ❤️ توسط
    <a href="https://github.com/OandONE/fast_rub" target="_blank">FastRub</a>
    • آخرین به‌روزرسانی: <span id="lastUpdate">—</span>
  </div>
</div>

<script>
const $=id=>document.getElementById(id);
const BASE = location.pathname.replace(/\/+$/, '');
const API  = BASE + '/api';

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
function escapeHtml(s){
  return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function typeLabel(t){
  const m={Group:'👥 گروه',Channel:'📢 کانال',User:'👤 کاربر',Bot:'🤖 ربات',unknown:'❔ نامشخص'};
  return m[t]||('❔ '+t);
}

function renderTable(chats){
  const c=$('tableContainer');
  if(!chats.length){
    c.innerHTML=`<div class="empty"><div class="empty-icon">📭</div>
      <div>هنوز پیامی دریافت نشده یا نتیجه‌ای یافت نشد</div></div>`;
    return;
  }
  let h='<table><thead><tr><th style="width:70px">رتبه</th><th>چت</th>'+
    '<th class="hide-mobile">نوع</th><th>کل پیام</th><th>امروز</th></tr></thead><tbody>';
  chats.forEach((x,i)=>{
    let rc='';
    if(i===0)rc='gold'; else if(i===1)rc='silver'; else if(i===2)rc='bronze';
    h+=`<tr><td><span class="rank ${rc}">${i+1}</span></td>
      <td><div class="chat-name">${escapeHtml(x.title)}</div>
          <div class="chat-id">${escapeHtml(x.chat_id)}</div></td>
      <td class="hide-mobile"><span class="badge">${typeLabel(x.type)}</span></td>
      <td><span class="count-num">${formatNumber(x.count)}</span></td>
      <td><span class="count-num green">${formatNumber(x.today)}</span></td>
    </tr>`;
  });
  c.innerHTML=h+'</tbody></table>';
}

async function loadData(){
  try{
    const search=$('search').value.trim();
    const sortBy=$('sortBy').value;
    const params=new URLSearchParams({sort:sortBy});
    if(search)params.set('search',search);
    const r=await fetch(API + '/stats?' + params.toString());
    if(!r.ok)throw new Error('HTTP '+r.status);
    const data=await r.json();
    $('totalMessages').textContent=formatNumber(data.summary.total_messages);
    $('todayMessages').textContent=formatNumber(data.summary.today_messages);
    $('activeChats').textContent=formatNumber(data.summary.total_chats);
    $('uptime').textContent=formatUptime(data.summary.uptime_seconds);
    $('lastUpdate').textContent=new Date(data.summary.now).toLocaleTimeString('fa-IR');
    $('statusText').textContent='متصل';
    renderTable(data.chats);
  }catch(e){
    $('statusText').textContent='خطا در اتصال';
    console.error(e);
  }
}

async function resetStats(){
  if(!confirm('آیا از پاک کردن تمام آمار مطمئن هستید؟'))return;
  try{
    await fetch(API + '/reset',{method:'POST'});
    loadData();
  }catch(e){alert('خطا در ریست کردن آمار');}
}

function debounce(fn,ms){let t;return(...a)=>{clearTimeout(t);t=setTimeout(()=>fn(...a),ms)}}

$('search').addEventListener('input',debounce(loadData,300));
$('sortBy').addEventListener('change',loadData);
$('resetBtn').addEventListener('click',resetStats);

loadData();
setInterval(loadData,5000);
</script>
</body>
</html>
"""


class Dashboard:
    """
    داشبورد HTML برای نمایش آمار پیام‌ها.

    از هر دو بک‌اند FastAPI و Flask پشتیبانی می‌کند.

    Parameters
    ----------
    client : Client
        کلاینت FastRub
    host : str
        آدرس گوش دادن (پیش‌فرض: 127.0.0.1)
    port : int
        پورت (پیش‌فرض: 8080)
    backend : Literal["fastapi", "flask"]
        بک‌اند سرور (پیش‌فرض: fastapi)
    path_prefix : str
        پیشوند مسیر (پیش‌فرض: /dashboard)
    logger : logging.Logger | None
        لاگر اختصاصی
    """

    def __init__(
        self,
        client: "Client",
        host: str = "127.0.0.1",
        port: int = 8080,
        backend: Literal["fastapi", "flask"] = "fastapi",
        path_prefix: str = "/dashboard",
        logger: logging.Logger | None = None,
    ) -> None:
        self.client = client
        self.host = host
        self.port = port
        self.backend = backend
        self.path_prefix = path_prefix
        self.logger = logger or logging.getLogger("fast_rub.dashboard")
        self._server = None
        self._app = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def _get_or_create_loop(self) -> asyncio.AbstractEventLoop:
        """ایجاد یا دریافت event loop برای Flask"""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop

    def _create_fastapi_app(self):
        """ساخت اپلیکیشن FastAPI"""
        try:
            from fastapi import FastAPI
            from fastapi.responses import HTMLResponse, JSONResponse
        except ImportError:
            raise ImportError(
                "FastAPI not installed !",
                "install: pip install fast_rub[fastapi]"
            )
        app = FastAPI(title="FastRub Dashboard")

        @app.get(self.path_prefix, response_class=HTMLResponse)
        async def index():
            return HTML_PAGE

        @app.get(f"{self.path_prefix}/api/stats")
        async def api_stats(sort: str = "count", search: str = ""):
            if not self.client.stats:
                return JSONResponse(
                    {"error": "Stats not enabled"}, status_code=400
                )
            summary = await self.client.stats.get_summary()
            chats = await self.client.stats.get_chats(
                sort_by=sort, search=search
            )
            return {"summary": summary, "chats": chats}

        @app.post(f"{self.path_prefix}/api/reset")
        async def api_reset():
            if not self.client.stats:
                return JSONResponse(
                    {"error": "Stats not enabled"}, status_code=400
                )
            await self.client.stats.reset()
            return {"ok": True}

        return app

    def _create_flask_app(self):
        """ساخت اپلیکیشن Flask"""
        try:
            from flask import Flask, jsonify, request
        except ImportError:
            raise ImportError(
                "Flask not installed !",
                "install: pip install fast_rub[flask]"
            )

        app = Flask(__name__)

        @app.route(self.path_prefix)
        def index():
            return HTML_PAGE

        @app.route(f"{self.path_prefix}/api/stats")
        def api_stats():
            sort = request.args.get("sort", "count")
            search = request.args.get("search", "")
            if not self.client.stats:
                return jsonify({"error": "Stats not enabled"}), 400
            loop = self._get_or_create_loop()
            summary = loop.run_until_complete(
                self.client.stats.get_summary()
            )
            chats = loop.run_until_complete(
                self.client.stats.get_chats(sort_by=sort, search=search)
            )
            return jsonify({"summary": summary, "chats": chats})

        @app.route(f"{self.path_prefix}/api/reset", methods=["POST"])
        def api_reset():
            if not self.client.stats:
                return jsonify({"error": "Stats not enabled"}), 400
            loop = self._get_or_create_loop()
            loop.run_until_complete(self.client.stats.reset())
            return jsonify({"ok": True})

        return app

    async def start(self) -> None:
        """شروع سرور داشبورد"""
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
                f"🌐 Dashboard (FastAPI) running at "
                f"http://{self.host}:{self.port}{self.path_prefix}"
            )
            await self._server.serve()
        elif self.backend == "flask":
            self._app = self._create_flask_app()
            self.logger.info(
                f"🌐 Dashboard (Flask) running at "
                f"http://{self.host}:{self.port}{self.path_prefix}"
            )
            # app.run بلاک‌کننده است — در thread جدا اجرا شود تا event loop ربات فریز نشود
            await asyncio.to_thread(
                self._app.run,
                host=self.host,
                port=self.port,
                threaded=True,
            )
        else:
            raise ValueError(
                f"backend must be 'fastapi' or 'flask', not '{self.backend}'"
            )

    async def stop(self) -> None:
        """توقف سرور"""
        if self.backend == "fastapi" and self._server:
            self._server.should_exit = True
        self.logger.info("🌐 Dashboard stopped")