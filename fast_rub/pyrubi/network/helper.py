import httpx
from random import randint, choice


class Helper:
    _client: httpx.AsyncClient | None = None
    _client_lock = None

    @classmethod
    async def _get_client(cls) -> httpx.AsyncClient:
        """ایجاد یا بازگرداندن AsyncClient مشترک."""
        if cls._client is None or cls._client.is_closed:
            if cls._client_lock is None:
                import asyncio
                cls._client_lock = asyncio.Lock()
            async with cls._client_lock:
                if cls._client is None or cls._client.is_closed:
                    cls._client = httpx.AsyncClient(
                        timeout=httpx.Timeout(10.0),
                        limits=httpx.Limits(max_connections=20),
                    )
        return cls._client

    @classmethod
    async def get_dcmess(cls) -> dict:
        """دریافت اطلاعات سرورهای DC به صورت async."""
        client = await cls._get_client()
        response = await client.get("https://getdcmess.iranlms.ir/")
        response.raise_for_status()
        return response.json()["data"]

    @classmethod
    def get_api_server(cls) -> str:
        return f"https://messengerg2c{randint(2, 3)}.iranlms.ir"

    @classmethod
    async def get_socket_server(cls) -> str:
        """انتخاب تصادفی یک socket server با دریافت اطلاعات از get_dcmess."""
        data = await cls.get_dcmess()
        return choice(list(data["socket"].values()))

    @classmethod
    async def close(cls) -> None:
        """بستن client در صورت نیاز."""
        if cls._client and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None