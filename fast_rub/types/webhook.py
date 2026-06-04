from dataclasses import dataclass
from typing import Literal


@dataclass
class WebhookConfig:
    """تنظیمات وب‌هوک"""
    url: str = ""                        # آدرس بیس (https://user.pythonanywhere.com)
    host: str = "0.0.0.0"               # آدرس گوش دادن
    port: int = 443                      # پورت (پیش‌فرض ۴۴۳)
    path_prefix: str = "/webhook"        # پیشوند مسیر
    backend: Literal["fastapi", "flask"] = "fastapi" # بک اند
    use_token_in_url: bool = False      # استفاده توکن در آدرس
