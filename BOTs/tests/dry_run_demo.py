"""
تست حالت شبیه‌سازی (Dry Run) — بدون توکن واقعی و بدون اینترنت
اجرا: python dry_run_demo.py
"""
import asyncio

from fast_rub import Client, filters, inline_filters


async def main():
    bot = Client("dry_run_demo", dry_run=True)

    @bot.on_message(filters.text("سلام"))
    async def hello(msg):
        await msg.reply("سلام! این پاسخ ربات در حالت Dry Run است ⚡")

    @bot.on_message(filters.commands(["help"]))
    async def help_cmd(msg):
        await msg.reply("راهنما:\n- سلام\n- /help")

    @bot.on_button(inline_filters.button_id("like"))
    async def like(msg):
        await msg.send_text("لایک شد 👍")

    await bot.start()

    # ─── شبیه‌سازی ورودی‌ها ───
    chat_id = "b" + "a" * 31
    upd1 = await bot.mock.receive_text(chat_id=chat_id, text="سلام")
    upd2 = await bot.mock.receive_text(chat_id=chat_id, text="/help")
    await bot.mock.receive_text(chat_id=chat_id, text="چیزی که هندلر نداره")
    btn = await bot.mock.receive_button(chat_id=chat_id, button_id="like")

    # ─── بررسی خروجی‌ها ───
    print(f"\n=== نتایج ===")
    print(f"get_me: {await bot.get_me()}")

    chat_info = await bot.get_chat(chat_id)
    print(f"get_chat title: {chat_info.title}")

    print(f"\nتعداد درخواست‌های ثبت‌شده: {len(bot.mock.requests)}")
    print(f"تعداد پیام‌های ارسال‌شده: {len(bot.mock.sent)}")
    for s in bot.mock.sent:
        print(f"  → {s['method']}: {s['data'].get('text', '')!r}")

    # ─── assert ها ───
    texts = [s["data"].get("text", "") for s in bot.mock.get_sent("sendMessage")]
    assert "سلام! این پاسخ ربات در حالت Dry Run است ⚡" in texts, "پاسخ سلام نیامد!"
    assert any("راهنما" in t for t in texts), "پاسخ /help نیامد!"
    assert "لایک شد 👍" in texts, "پاسخ دکمه نیامد!"
    assert upd1.chat_id == chat_id and upd1.text == "سلام"
    assert btn.button_id == "like"
    assert bot.mock.last_sent is not None

    # ─── تست صف و get_updates ───
    bot.mock.clear()
    bot.mock.enqueue_text(chat_id=chat_id, text="سلام")
    updates = await bot.get_updates()
    assert len(updates["updates"]) == 1, "صف get_updates کار نمی‌کند!"
    print(f"\nصف get_updates: {len(updates['updates'])} آپدیت ✓")

    # ─── تست ویرایش و حذف ───
    received_edits = []
    received_deletes = []

    @bot.on_edit()
    async def on_edit_handler(msg):
        received_edits.append(msg)

    @bot.on_delete()
    async def on_delete_handler(msg):
        received_deletes.append(msg)

    await bot.mock.receive_edit(chat_id=chat_id, message_id=upd1.new_message.message_id, new_text="متن جدید")
    await bot.mock.receive_deleted(chat_id=chat_id, message_id=upd1.new_message.message_id)
    assert len(received_edits) == 1 and received_edits[0].text == "متن جدید", "ویرایش دریافت نشد!"
    assert len(received_deletes) == 1, "حذف دریافت نشد!"
    print("ویرایش/حذف شبیه‌سازی شد ✓")

    print("\n✅ Dry Run همه‌چیز درست کار می‌کند")
    await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
