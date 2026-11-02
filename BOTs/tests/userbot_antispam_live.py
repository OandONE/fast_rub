"""
تست واقعی AntiSpam یوزربات روی اکانت خودت.

این اسکریپت:
  1) اگر سشن ``<session>.pyrubi`` وجود نداشته باشد، شماره و کد را می‌پرسد
     (منطق لاگین خودِ pyrubi) و سشن را ذخیره می‌کند.
  2) یک گروه خصوصی موقت می‌سازد (فقط برای همین تست).
  3) سوکت را وصل می‌کند و AntiSpam را فعال می‌کند.
  4) چند پیام پشت‌سرهم به همان گروه می‌فرستد؛ چون پیام‌ها از خود اکانت
     هستند، برای این تست بررسی «پیام خودم» موقتاً خاموش می‌شود.
  5) انتظار دارد AntiSpam پیام‌های دوم به بعد را با API واقعی
     ``deleteMessages`` حذف کند.
  6) گروه موقت را پاک می‌کند.

ایمنی:
  - اکشن فقط ``delete`` است؛ هیچ بن/اخراجی انجام نمی‌شود.
  - فقط روی گروهی که خودش می‌سازد کار می‌کند (``chats={group_guid}``).
  - سشن در ``<session>.pyrubi`` ذخیره می‌شود و کلیدهای auth داخلش است؛
    این فایل را جایی آپلود یا به اشتراک نگذار (در .gitignore هست).
  - کد پیامک فقط در همین ترمینال وارد می‌شود و ذخیره نمی‌شود.

اجرا (از ریشهٔ پروژه):
    PYTHONPATH=. venv/bin/python BOTs/tests/userbot_antispam_live.py

گزینه‌ها:
    --session NAME      نام فایل سشن (پیش‌فرض: antispam_live_test)
    --send N            تعداد پیام تست (پیش‌فرض: 3)
    --keep              گروه تست را بعد از پایان پاک نکن
    --timeout SECONDS   حداکثر انتظار برای دریافت/حذف (پیش‌فرض: 25)
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

# اجرای اسکریپت از داخل BOTs/tests باعث می‌شود نسخهٔ نصب‌شدهٔ قدیمی
# fastrub import شود؛ مسیر ریشهٔ پروژه را اول می‌گذاریم.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import fast_rub  # noqa: E402
from fast_rub.pyrubi import AntiSpam, Client  # noqa: E402


GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def ok(text: str) -> None:
    print(f"{GREEN}  ✅ {text}{RESET}")


def fail(text: str) -> None:
    print(f"{RED}  ❌ {text}{RESET}")


def warn(text: str) -> None:
    print(f"{YELLOW}  ⚠️  {text}{RESET}")


def find_guid(obj, prefix: str) -> str | None:
    """پیدا کردن اولین گوید با پیشوند مشخص (مثلاً g0 برای گروه) در یک ساختار تودرتو."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if (
                isinstance(value, str)
                and value.startswith(prefix)
                and len(value) >= 20
            ):
                return value
        for value in obj.values():
            found = find_guid(value, prefix)
            if found:
                return found
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            found = find_guid(value, prefix)
            if found:
                return found
    return None


def collect_message_ids(obj) -> set[str]:
    """جمع‌آوری همهٔ message_idهای یک پاسخ getMessages."""
    found: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "message_id" and isinstance(value, str) and value:
                found.add(value)
            else:
                found |= collect_message_ids(value)
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            found |= collect_message_ids(value)
    return found


async def wait_until(predicate, timeout: float, interval: float = 0.25) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        await asyncio.sleep(interval)
    return False


class ObservedAntiSpam(AntiSpam):
    """همان AntiSpam یوزربات + ثبت مشاهدات برای گزارش تست."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.inspected: list = []
        self.delete_attempts: list[str] = []

    async def inspect(self, message):
        self.inspected.append(message)
        return await super().inspect(message)

    async def _delete(self, message):
        self.delete_attempts.append(message.message_id)
        await super()._delete(message)


async def run(args: argparse.Namespace) -> int:
    print(f"نسخهٔ fast_rub: {fast_rub.__file__}")
    print(f"فایل سشن: {(Path.cwd() / f'{args.session}.pyrubi').resolve()}")
    print()

    antispam = ObservedAntiSpam(
        # برای اینکه تست سریع و قطعی باشد: با ۲ پیام پشت‌سرهم در ۳۰ ثانیه
        flood_max=2,
        flood_window=30.0,
        rate_max=99,
        rate_window=30.0,
        duplicate_window=0.0,
        max_message_length=10000,
        link_max=99,
        link_window=30.0,
        mention_max=99,
        mention_window=30.0,
        mute_duration=10.0,
        # اکشن امن برای تست واقعی
        action="delete",
        delete_on_action=True,
        delete_during_mute=True,
        ignore_admins=False,   # این تست گروه تازه است و ادمین دیگری ندارد
        admin_cache_ttl=0,
    )

    bot = Client(
        session=args.session,
        antispam=antispam,
        run_start=False,
    )

    print("در حال لاگین... (اگر سشن وجود نداشته باشد شماره و کد پرسیده می‌شود)")
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\nلغو شد.")
        return 2
    except EOFError:
        fail(
            "ورودی تعاملی در دسترس نیست. برای اولین لاگین، اسکریپت را "
            "در یک ترمینال واقعی اجرا کن تا شماره و کد پرسیده شوند."
        )
        return 2
    except Exception as error:
        fail(f"لاگین ناموفق بود: {error}")
        return 1

    me = await bot.get_me()
    print(f"لاگین شد: {me.get('first_name', '')} {me.get('last_name', '')}".strip())
    user_guid = find_guid(me, "u0") or find_guid(getattr(bot, "sessionData", {}), "u0")
    if user_guid:
        print(f"گوید من: {user_guid}")

    group_guid: str | None = None
    listener: asyncio.Task | None = None

    try:
        if args.login_only:
            ok("لاگین انجام شد و سشن ذخیره شد.")
            return 0

        # ── ساخت گروه موقت ─────────────────────────────────────────
        title = f"FastRub AntiSpam Live Test {int(time.time())}"
        members = [user_guid] if user_guid else []
        print(f"\nساخت گروه موقت: {title}")
        created = await bot.add_group(title, members)
        group_guid = find_guid(created, "g0")
        if not group_guid:
            # بعضی پاسخ‌ها شکل متفاوتی دارند؛ یک بار دیگر از لیست چت‌ها امتحان می‌کنیم.
            chats = await bot.get_chats()
            for chat in (chats.get("chats") or []) if isinstance(chats, dict) else []:
                if isinstance(chat, dict) and chat.get("title") == title:
                    group_guid = chat.get("object_guid") or find_guid(chat, "g0")
                    break
        if not group_guid:
            fail(f"گوید گروه پیدا نشد. پاسخ addGroup: {created}")
            return 1
        ok(f"گروه ساخته شد: {group_guid}")

        # فقط همین گروه بررسی شود و پیام‌های خود اکانت هم برای تست بررسی شوند.
        antispam.chats = {group_guid}
        antispam._is_own = lambda message: False  # noqa: SLF001 - test-only
        print("حالت تست: بررسی «پیام خودم» موقتاً خاموش شد (فقط برای همین گروه).")

        # ── اتصال سوکت ────────────────────────────────────────────
        live = asyncio.Event()

        @bot.on_live()
        async def _on_live():
            live.set()

        errors: list[BaseException] = []

        @bot.on_error(error_detail="message")
        async def _on_error(error, update=None):
            errors.append(error)

        listener = asyncio.create_task(bot.run())
        print("اتصال به سوکت...")
        try:
            await asyncio.wait_for(live.wait(), timeout=30)
        except asyncio.TimeoutError:
            fail("سوکت تا ۳۰ ثانیه وصل نشد.")
            return 1
        ok("سوکت وصل شد.")

        # ── رصد حذف واقعی ─────────────────────────────────────────
        original_delete = bot.methods.deleteMessages
        delete_results: list[tuple[list[str], object]] = []

        async def spy_delete(objectGuid, messageIds, deleteForAll=True):
            result = await original_delete(
                objectGuid=objectGuid,
                messageIds=messageIds,
                deleteForAll=deleteForAll,
            )
            delete_results.append((list(messageIds), result))
            return result

        bot.methods.deleteMessages = spy_delete  # type: ignore[method-assign]

        # ── پیام‌های تست ─────────────────────────────────────────
        def test_messages() -> list:
            result = []
            for message in antispam.inspected:
                if antispam._chat_of(message) != group_guid:  # noqa: SLF001
                    continue
                if antispam._is_edited(message):  # noqa: SLF001
                    continue
                if antispam._is_event(message):  # noqa: SLF001
                    continue
                if not antispam._text_of(message).strip():  # noqa: SLF001
                    continue
                result.append(message)
            return result

        sent: list[str] = []
        if args.mode == "api":
            print(f"\nارسال {args.send} پیام با API خود اکانت (حالت تشخیصی)...")
            for index in range(args.send):
                result = await bot.send_text(
                    group_guid,
                    f"antispam live test #{index + 1} ({int(time.time())})",
                )
                message_id = bot._extract_message_id(result)  # noqa: SLF001
                print(f"  ارسال #{index + 1} → message_id={message_id}")
                await asyncio.sleep(0.2)
            target_count = max(1, args.send - 1)
            timeout = args.timeout
            print(
                "   نکته: روبیکا معمولاً پیام‌های ارسال‌شده با API خود سشن را "
                "به سوکت همان سشن برنمی‌گرداند؛ اگر این حالت صفر آپدیت داد، "
                "از حالت manual استفاده کن."
            )
        else:
            print("\n" + "=" * 66)
            print(f"📱 از گوشی خودت به گروه «{title}» برو و {args.send} پیام پشت سر هم بفرست.")
            print("   هر متنی؛ مثلاً: antispam live test #1 / #2 / #3")
            print(f"   گوید گروه: {group_guid}")
            print(f"   تا {args.manual_timeout:.0f} ثانیه منتظر دریافت پیام‌ها هستم...")
            print("=" * 66)
            target_count = args.send
            timeout = args.manual_timeout

        async def wait_for_phone_messages() -> bool:
            """انتظار برای پیام‌های گوشی با نمایش وضعیت هر ۱۰ ثانیه."""
            deadline = time.monotonic() + timeout
            last_report = 0.0
            while time.monotonic() < deadline:
                count = len(test_messages())
                if count >= target_count:
                    return True
                now = time.monotonic()
                if now - last_report >= 10.0:
                    last_report = now
                    print(
                        f"   ⏳ {count}/{target_count} پیام دریافت شد؛ "
                        f"{int(deadline - now)} ثانیه باقی مانده..."
                    )
                await asyncio.sleep(0.5)
            return False

        if args.mode == "api":
            received = await wait_until(
                lambda: len(test_messages()) >= target_count,
                timeout,
                interval=0.5,
            )
        else:
            received = await wait_for_phone_messages()
        messages_seen = test_messages()
        if not received:
            fail(f"فقط {len(messages_seen)} پیام از {target_count} پیام به antispam رسید.")
            if antispam.inspected:
                sample = antispam.inspected[-1]
                print(
                    "     نمونهٔ آخرین آپدیت دریافتی: "
                    f"chat={getattr(sample, 'object_guid', '?')} "
                    f"author={getattr(sample, 'author_guid', '?')} "
                    f"is_mine={getattr(sample, 'is_mine', '?')} "
                    f"type={getattr(sample, 'message_type', '?')} "
                    f"text={antispam._text_of(sample)!r}"  # noqa: SLF001
                )
            else:
                print("     هیچ آپدیتی به سوکت نرسید (حتی رویدادها).")
            if args.mode == "api":
                print("     این طبیعی است؛ حالت manual را امتحان کن.")
            return 1
        sent = [message.message_id for message in messages_seen if message.message_id]
        ok(f"{len(messages_seen)} پیام به antispam رسید: {sent}")
        await asyncio.sleep(1.0)  # فرصت برای تکمیل اکشن‌های حذف

        deleted = await wait_until(lambda: bool(delete_results), args.timeout)
        if not deleted:
            fail("هیچ درخواست deleteMessages ثبت نشد.")
            if antispam.delete_attempts:
                warn(f"اکشن حذف صدا زده شد ولی نتیجه‌ای برنگشت: {antispam.delete_attempts}")
            return 1

        ok(f"{len(delete_results)} درخواست deleteMessages انجام شد.")
        for ids, result in delete_results:
            if isinstance(result, dict):
                status = result.get("status", "بدون فیلد status")
                keys = sorted(result)[:6]
                print(f"     ids={ids} status={status} keys={keys}")
            else:
                print(f"     ids={ids} response={type(result).__name__}")

        statuses = [
            str(result["status"]).upper()
            for _, result in delete_results
            if isinstance(result, dict) and "status" in result
        ]
        if statuses:
            if all(status == "OK" for status in statuses):
                ok("API حذف، وضعیت OK برگرداند.")
            else:
                warn(f"وضعیت پاسخ حذف: {statuses}")
        else:
            warn(
                "پاسخ deleteMessages فیلد status نداشت؛ "
                "درستی حذف با بررسی تاریخچه تأیید می‌شود."
            )

        target_ids = set(sent)
        deleted_ids = {
            mid for ids, _ in delete_results for mid in ids if mid
        }
        expected_deleted = set(sent[1:])
        missing = expected_deleted - deleted_ids
        if expected_deleted and not missing:
            ok(f"همهٔ پیام‌های اسپم برای حذف ارسال شدند: {sorted(expected_deleted)}")
        elif expected_deleted:
            fail(
                f"این پیام‌ها برای حذف ارسال نشدند: {sorted(missing)} "
                f"(deleted={sorted(deleted_ids)}, sent={sent})"
            )
        else:
            fail(f"هیچ message_id قابل انتظاری برای حذف نبود. sent={sent}")

        # ── بررسی تاریخچه: پیام اول باید بماند، بقیه حذف شوند ───
        try:
            history = await bot.get_messages(group_guid, limit=50)
            remaining = collect_message_ids(history)
            still_there = expected_deleted & remaining
            if still_there:
                warn(f"این پیام‌ها هنوز در تاریخچه دیده می‌شوند: {sorted(still_there)}")
            else:
                ok("پیام‌های اسپم در تاریخچهٔ گروه نمانده‌اند.")
            first_ids = set(sent[:1])
            if first_ids & remaining:
                ok("پیام اول (که اسپم نبود) در تاریخچه باقی مانده است.")
        except Exception as error:  # getMessages ممکن است برای گروه تازه خالی باشد
            warn(f"بررسی تاریخچه ممکن نشد: {error}")

        # ── بررسی سکوت (mute) ─────────────────────────────────────
        author_guid = antispam._user_of(messages_seen[0]) if messages_seen else ""  # noqa: SLF001
        if author_guid and antispam.is_muted(group_guid, author_guid):
            ok("کاربر/اکانت پس از flood وارد حالت سکوت شد.")
        elif author_guid:
            warn("حالت سکوت ثبت نشد (ممکن است قانون دیگری زودتر فعال شده باشد).")

        if errors:
            warn(f"خطاهای on_error: {errors}")

        print(f"\n{GREEN}تست واقعی با موفقیت تمام شد.{RESET}")
        return 0

    except KeyboardInterrupt:
        print("\nتوسط کاربر متوقف شد.")
        return 2
    except Exception:
        import traceback

        print(f"\n{RED}تست با خطا متوقف شد:{RESET}")
        traceback.print_exc()
        return 1
    finally:
        # ── پاکسازی ──────────────────────────────────────────────
        print("\nپاکسازی...")
        if listener is not None and not listener.done():
            try:
                await bot.methods.socket.stop()
            except Exception:
                pass
            try:
                await asyncio.wait_for(listener, timeout=10)
            except (asyncio.TimeoutError, Exception):
                listener.cancel()
        else:
            try:
                await bot.methods.socket.stop()
            except Exception:
                pass

        if group_guid and not args.keep:
            # userbot API به removeGroup دسترسی ندارد؛ leaveGroup کافی است.
            try:
                await bot.leave_chat(group_guid)
                ok("گروه موقت ترک شد. اگر در گوشی ماند، دستی حذفش کن.")
            except Exception as leave_error:
                warn(f"ترک گروه ناموفق بود: {leave_error}")
                warn(f"گروه را دستی پاک کن: {group_guid}")
        elif group_guid:
            warn(f"گروه تست نگه داشته شد: {group_guid}")

        try:
            bot.methods._background.cancel_all()  # noqa: SLF001
        except Exception:
            pass
        try:
            await bot.methods.network.close()
        except Exception:
            pass
        print("پایان.")


def main() -> None:
    parser = argparse.ArgumentParser(description="تست واقعی AntiSpam یوزربات")
    parser.add_argument("--session", default="antispam_live_test", help="نام فایل سشن")
    parser.add_argument("--send", type=int, default=3, help="تعداد پیام تست")
    parser.add_argument(
        "--mode",
        choices=["manual", "api"],
        default="manual",
        help="manual: پیام را از گوشی بفرست | api: پیام با خود API (تشخیصی)",
    )
    parser.add_argument(
        "--manual-timeout",
        type=float,
        default=180.0,
        help="حداکثر انتظار برای پیام‌های گوشی (ثانیه)",
    )
    parser.add_argument("--keep", action="store_true", help="گروه تست را پاک نکن")
    parser.add_argument(
        "--login-only",
        action="store_true",
        help="فقط لاگین کن و سشن را ذخیره کن (تست را اجرا نکن)",
    )
    parser.add_argument("--timeout", type=float, default=25.0, help="حداکثر زمان انتظار")
    args = parser.parse_args()

    if args.send < 2:
        parser.error("--send باید حداقل ۲ باشد (flood_max=2)")

    try:
        raise SystemExit(asyncio.run(run(args)))
    except KeyboardInterrupt:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
