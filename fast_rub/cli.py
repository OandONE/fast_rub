import os
import sys
import argparse
import webbrowser
from pathlib import Path


TEMPLATE = '''"""
Fast Rub Bot - {bot_name}
"""
from fast_rub import Client
from fast_rub.type import Message
import asyncio

bot = Client("{bot_name}", token="YOUR_TOKEN", run_start=False)

async def robot():

    await bot.start()

    @bot.on_message()
    async def handler(msg: Message):
        await msg.reply("سلام! ⚡")

    await bot.run()

if __name__ == "__main__":
    asyncio.run(robot())
'''

CONFIG_TEMPLATE = '''"""
Fast Rub Bot Configuration - {bot_name}
"""
BOT_TOKEN = "YOUR_TOKEN"
POLL_INTERVAL = 0.0
USE_RELOAD = False
'''

PLUGIN_EXAMPLE = '''"""
Example Plugin for Fast Rub
"""
def setup(bot):
    @bot.on_message(commands=["start"])
    async def start(msg):
        await msg.reply("سلام! به ربات من خوش اومدی ⚡")
'''

def cmd_new(args):
    """ساخت پروژه جدید"""
    bot_name = args.name
    base_dir = Path(bot_name)
    
    if base_dir.exists():
        print(f"❌ پوشه '{bot_name}' از قبل وجود داره.")
        return
    
    base_dir.mkdir(parents=True)
    plugins_dir = base_dir / "plugins"
    plugins_dir.mkdir()
    snapshots_dir = base_dir / "snapshots"
    snapshots_dir.mkdir()
    backups_dir = base_dir / "backups"
    backups_dir.mkdir()
    logs_dir = base_dir / "logs"
    logs_dir.mkdir()
    

    main_file = base_dir / "main.py"
    main_file.write_text(TEMPLATE.format(bot_name=bot_name), encoding="utf-8")
    
    config_file = base_dir / "config.py"
    config_file.write_text(CONFIG_TEMPLATE.format(bot_name=bot_name), encoding="utf-8")
    
    plugin_file = plugins_dir / "example.py"
    plugin_file.write_text(PLUGIN_EXAMPLE, encoding="utf-8")
    
    readme_file = base_dir / "README.md"
    readme_file.write_text(f"# {bot_name}\n\nFast Rub Bot\n", encoding="utf-8")
    
    gitignore_file = base_dir / ".gitignore"
    gitignore_file.write_text("venv/\n__pycache__/\n*.faru\n*.db\n.env\nlogs/\nbackups/\n", encoding="utf-8")
    
    print(f"✅ پروژه '{bot_name}' با موفقیت ساخته شد!")
    print(f"   📁 {base_dir.absolute()}")
    print(f"   📝 {main_file}")
    print(f"   🔌 {plugins_dir}")
    print(f"   ⚙️ {config_file}")
    print()
    print("🚀 برای شروع:")
    print(f"   cd {bot_name}")
    print(f"   fastrub run")

def cmd_run(args):
    """اجرای ربات"""
    main_file = Path("main.py")
    if not main_file.exists():
        print("❌ فایل main.py پیدا نشد. مطمئن شو توی پوشه پروژه هستی.")
        return
    
    import subprocess
    cmd = [sys.executable, "main.py"]
    if args.reload:
        cmd.append("--reload")
    
    subprocess.run(cmd)

def cmd_version(args):
    """نمایش نسخه"""
    try:
        from fast_rub import __version__
        print(f"Fast Rub v{__version__}")
    except ImportError:
        print("Fast Rub vunknown")

def cmd_docs(args):
    """باز کردن مستندات"""
    import socket
    
    urls = [
        "https://fast-rub.parssource.ir/",
        "https://oandone.github.io/fast_rub/"
    ]
    
    for url in urls:
        host = url.split("//")[1].split("/")[0]
        try:
            socket.create_connection((host, 443), timeout=3)
            print(f"✅ باز کردن: {url}")
            webbrowser.open(url)
            return
        except:
            continue
    
    print("❌ هیچکدوم از آدرس‌ها در دسترس نیست.")

def main():
    parser = argparse.ArgumentParser(
        prog="fastrub",
        description="Fast Rub CLI - The Fastest Rubika Bot Framework"
    )
    subparsers = parser.add_subparsers(dest="command")
    
    # new
    parser_new = subparsers.add_parser("new", help="ساخت پروژه جدید")
    parser_new.add_argument("name", help="اسم پروژه")
    parser_new.set_defaults(func=cmd_new)
    
    # run
    parser_run = subparsers.add_parser("run", help="اجرای ربات")
    parser_run.add_argument("--reload", action="store_true", help="فعال‌سازی Hot Reload")
    parser_run.set_defaults(func=cmd_run)
    
    # version
    parser_version = subparsers.add_parser("version", help="نمایش نسخه Fast Rub")
    parser_version.set_defaults(func=cmd_version)
    
    # docs
    parser_docs = subparsers.add_parser("docs", help="باز کردن مستندات")
    parser_docs.set_defaults(func=cmd_docs)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
    else:
        args.func(args)

if __name__ == "__main__":
    main()

