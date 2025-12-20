import httpx
import asyncio
from typing import Optional, Union, Dict, Any, List, Literal
from ..type.errors import ServerRubikaError
import os
import aiofiles
import logging

class Network:
    def __init__(
        self,
        token: str,
        logger: Optional[logging.Logger] = None,
        max_retries: int = 3,
        user_agent: Optional[str] = None,
        main_url: str = "https://botapi.rubika.ir/v3/",
        proxy: Optional[str] = None,
        rate_limit: int = 20
    ):
        self.logger = logger or logging.getLogger("fast_rub.network")
        self.token = token
        self.user_agent = user_agent
        self.main_url = main_url
        self.proxy = proxy
        self.max_retries = max_retries

        self._client: httpx.AsyncClient | None = None
        self._client_lock = asyncio.Lock()

        self._rate_sem: Optional[asyncio.Semaphore] = None
        self._queue: Optional[asyncio.Queue] = None
        self._worker_task: Optional[asyncio.Task] = None
        self._closed = False
        self._rate_limit = rate_limit

    # -------------------
    # Lifecycle: start / stop
    # -------------------
    async def start(self, *, start_worker: bool = True):
        asyncio.get_running_loop()

        if self._client_lock is None:
            self._client_lock = asyncio.Lock()
        if self._rate_sem is None:
            self._rate_sem = asyncio.Semaphore(self._rate_limit)
        if self._queue is None:
            self._queue = asyncio.Queue()

        await self._create_client()

        if start_worker:
            await self.start_worker()

    async def _create_client(self):
        self._client = httpx.AsyncClient(**self._build_client_kwargs())
        self.logger.debug("HTTP client created")

    async def close(self):
        self._closed = True

        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        if self._client and not self._client.is_closed:
            try:
                await self._client.aclose()
            except RuntimeError as e:
                if "Event loop is closed" not in str(e):
                    raise


    # -------------------
    # Worker queue
    # -------------------
    async def start_worker(self):
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._worker())
            self.logger.debug("Worker started")

    def _build_client_kwargs(self) -> dict:
        kwargs = {
            "timeout": httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0),
            "limits": httpx.Limits(max_connections=100, max_keepalive_connections=20),
            "http1": True,
            "http2": True,
            "headers": {
                "Content-Type": "application/json",
                "User-Agent": self.user_agent or "fast_rub/Network"
            }
        }

        if self.proxy:
            try:
                httpx.AsyncClient(proxy=self.proxy)
                kwargs["proxies"] = self.proxy
            except TypeError:
                kwargs["proxy"] = self.proxy

        return kwargs


    async def _worker(self):
        if self._queue is None:
            self.logger.warning("Worker started but queue is None.")
            return

        while not self._closed:
            try:
                url, method, data_, headers, overrides, fut = await self._queue.get()
            except asyncio.CancelledError:
                break
            try:
                res = await self._do_request(url, method, data_, headers, **overrides)
                if not fut.done():
                    fut.set_result(res)
            except Exception as e:
                if not fut.done():
                    fut.set_exception(e)
            finally:
                try:
                    self._queue.task_done()
                except Exception:
                    pass

    # -------------------
    # Public request
    # -------------------
    async def request(
        self,
        url: str,
        data_: Optional[Union[Dict[str, Any], List[Any]]] = None,
        type_send: Literal["POST", "GET"] = "POST",
        *,
        max_retries: Optional[int] = None,
        timeout: Optional[float] = None
    ) -> httpx.Response:
        if self._closed:
            raise RuntimeError("Network is closed")

        overrides = {
            "max_retries": max_retries or self.max_retries,
            "timeout": timeout or 30.0
        }

        return await self._do_request(url, type_send, data_, None, **overrides)

    # -------------------
    # Internal request with retry
    # -------------------
    async def _ensure_client(self):
        if self._client_lock is None:
            self._client_lock = asyncio.Lock()
        if self._rate_sem is None:
            self._rate_sem = asyncio.Semaphore(self._rate_limit)
        if self._queue is None:
            self._queue = asyncio.Queue()

        if self._client is None or (hasattr(self._client, "is_closed") and self._client.is_closed):
            async with self._client_lock:
                if self._client is None or (hasattr(self._client, "is_closed") and self._client.is_closed):
                    await self._create_client()

    async def _do_request(
        self,
        url: str,
        method: str,
        data_: Optional[Union[Dict, List]],
        headers: Optional[Dict[str, str]],
        *,
        max_retries: int,
        timeout: float
    ) -> httpx.Response:

        last_exception = None
        headers = headers.copy() if headers else {"Content-Type": "application/json"}
        if self.user_agent:
            headers["User-Agent"] = self.user_agent

        await self._ensure_client()

        for attempt in range(1, max_retries + 1):
            try:
                if self._rate_sem is None:
                    self._rate_sem = asyncio.Semaphore(self._rate_limit)

                async with self._rate_sem:
                    if method == "POST":
                        resp = await self._client.post(url, json=data_, headers=headers, timeout=timeout)
                    elif method == "GET":
                        resp = await self._client.get(url, headers=headers, timeout=timeout)
                    else:
                        raise ValueError(f"Invalid method: {method}")

                resp.raise_for_status()
                return resp

            except (httpx.ReadError, httpx.ConnectError, httpx.TimeoutException) as e:
                last_exception = e
                wait_time = attempt * 1.5
                self.logger.warning(f"Request failed attempt {attempt}/{max_retries}: {e}. Retrying in {wait_time}s...")

                if self._client_lock is None:
                    self._client_lock = asyncio.Lock()

                async with self._client_lock:
                    if self._client:
                        try:
                            await self._client.aclose()
                        except RuntimeError as re:
                            if "Event loop is closed" in str(re):
                                self.logger.debug("Event loop closed while closing client (during retry) — ignoring.")
                            else:
                                self.logger.exception("RuntimeError when closing client (during retry)")
                        except Exception:
                            pass
                        self._client = None

                try:
                    await self._ensure_client()
                except Exception as e2:
                    self.logger.exception(f"Failed to recreate client: {e2}")
                    raise e2

                await asyncio.sleep(wait_time)

            except Exception as e:
                self.logger.error(f"Unexpected error during request: {e}")
                raise e

        self.logger.error(f"All {max_retries} attempts failed for {url}")
        raise last_exception or RuntimeError("Unknown error in request")

    # -------------------
    # Rubika high-level
    # -------------------
    async def send_request(
        self,
        method: str,
        data_: Optional[Union[Dict[str, Any], List[Any]]] = None
    ) -> dict:
        self.logger.debug(f"method {method}")
        url = f"{self.main_url}{self.token}/{method}"
        resp = await self.request(url, data_, "POST")
        try:
            result = resp.json()
        except Exception:
            raise ServerRubikaError("Error converting response to JSON")

        if result.get("status", "") != "OK":
            self.logger.error(f"Server returned error: {result}")
            raise ServerRubikaError(result)
        return result["data"]

    async def download(self, url: str, path: str = "file") -> bool:
        try:
            await self._ensure_client()

            dir_path = os.path.dirname(path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            if self._rate_sem is None:
                self._rate_sem = asyncio.Semaphore(self._rate_limit)

            async with self._rate_sem:
                async with self._client.stream("GET", url) as response:
                    response.raise_for_status()
                    async with aiofiles.open(path, 'wb') as file:
                        async for chunk in response.aiter_bytes():
                            await file.write(chunk)
            return True
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            return False
    
    async def upload(self, url: str, files: dict, timeout: int = 30) -> dict:
        try:
            self.logger.info("در حال آپلود فایل ...")
            await self._ensure_client()

            response = await self._client.post(url, files=files, timeout=timeout)
            response.raise_for_status()
            result = response.json()
            if result.get("status", "") != "OK":
                self.logger.error(f"Server returned error: {result}")
                raise ServerRubikaError(result)
            self.logger.info("فایل آپلود شد")
            return result["data"]
        except httpx.TimeoutException:
            self.logger.error("زمان خروج فرا رسیده !")
            raise
        except httpx.HTTPError:
            self.logger.error("خطای HTTP")
            raise
        except Exception as e:
            self.logger.error(f"خطایی ناشناخته » {e}")
            raise