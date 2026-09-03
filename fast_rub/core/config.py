class BotConfig:
    """
    BotConfig allows fine-tuning bot behaviour without modifying core code.

    کلاس BotConfig به شما اجازه می‌دهد تنظیمات جزئی و پیشرفته ربات را
    بدون تغییر در کد اصلی فریم‌ورک، به دلخواه خود تنظیم کنید.

    مسئولیت‌های اصلی:
    - کنترل اعتبارسنجی شناسه‌های چت
    - بهینه‌سازی خودکار متن پیش از ارسال
    - مدیریت طول مجاز پیام‌ها
    - جلوگیری از حملات XSS با escape خودکار
    - تنظیم رفتار تلاش مجدد در خطاهای شبکه

    Parameters
    ----------
    validate_chat_id: bool = True
        اعتبارسنجی chat_id پیش از هر درخواست.
        اگر از صحت chat_idهای ورودی اطمینان دارید،
        می‌توانید برای افزایش سرعت، این گزینه را غیرفعال کنید.

    optimize_text: bool = False
        بهینه‌سازی متن پیش از ارسال.
        فاصله‌های تکراری (بیش از یک space) را به یک فاصله کاهش می‌دهد.
        برای تمیزسازی محتوای تولیدشده توسط کاربر مفید است.

    strip_text: bool = True
        حذف فاصله‌های خالی (whitespace) از ابتدا و انتهای پیام.
        پیام‌هایی مانند "   سلام   " را به "سلام" تبدیل می‌کند.

    max_text_length: int = None
        حداکثر طول مجاز برای متن پیام (به کاراکتر).
        پیام‌های بلندتر از این مقدار بریده می‌شوند.

    compress_long_text: bool = False
        افزودن "..." به انتهای پیام‌های بلند هنگام برش.
        فقط زمانی اعمال می‌شود که max_text_length رد شده باشد.

    auto_escape: bool = True
        فرار خودکار کاراکترهای HTML و Markdown برای جلوگیری از حملات XSS.
        توصیه می‌شود همیشه روشن باشد مگر در شرایط خاص.

    retry_on_timeout: bool = True
        تلاش مجدد خودکار در صورت timeout شدن درخواست.
        برای شبکه‌های ناپایدار یا سرورهای شلوغ مفید است.

    Examples
    --------
    >>> config = BotConfig(
    ...     validate_chat_id=False,
    ...     optimize_text=True,
    ...     strip_text=True,
    ...     max_text_length=2048,
    ... )
    >>> bot = Client("my_bot", config=config)
    """

    def __init__(
        self,
        validate_chat_id: bool = True,
        optimize_text: bool = False,
        strip_text: bool = True,
        max_text_length: int | None = None,
        compress_long_text: bool = False,
        auto_escape: bool = True,
        retry_on_timeout: bool = True,
    ):
        self.validate_chat_id = validate_chat_id
        self.optimize_text = optimize_text
        self.strip_text = strip_text
        self.max_text_length = max_text_length
        self.compress_long_text = compress_long_text
        self.auto_escape = auto_escape
        self.retry_on_timeout = retry_on_timeout
