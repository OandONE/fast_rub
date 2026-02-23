from ..type.errors import ServerRubikaError
from ..utils.utils import Utils
from pathlib import Path
from typing import Optional, Union, Dict, Any, List, Literal
from tqdm.asyncio import tqdm
import os
import aiofiles
import asyncio
import httpx
import tempfile
import logging


class Network:
    def __init__(
        self,
        token: str,
        logger: Optional[logging.Logger] = None,
        max_retries: int = 3,
        user_agent: Optional[str] = None,
        base_urls: list = [
            "https://botapi.rubika.ir/",
            "https://messengerg2b1.iranlms.ir/"
        ],
        proxy: Optional[str] = None,
        rate_limit: int = 20
    ):
        self.logger = logger or logging.getLogger("fast_rub.network")
        self.token = token
        self.user_agent = user_agent
        self.base_urls = base_urls
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
                        resp = await self._client.post(url, json=data_, headers=headers, timeout=timeout) # pyright: ignore[reportOptionalMemberAccess]
                    elif method == "GET":
                        resp = await self._client.get(url, headers=headers, timeout=timeout) # pyright: ignore[reportOptionalMemberAccess]
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
        data: Optional[Union[Dict[str, Any], List[Any]]] = None
    ) -> dict:
        self.logger.debug(f"method {method}")
        for base_url in self.base_urls:
            self.logger.debug(f"Base Url » {base_url}")
            url = f"{base_url}v3/{self.token}/{method}"
            try:
                response = await self.request(url, data, "POST")
            except:
                continue
            try:
                result = response.json()
            except:
                self.logger.error("Error Converting Response To JSON")
                raise ServerRubikaError("Error Converting Response To JSON")

            if not Utils.check_data(result):
                self.logger.error(f"Server Response Error: {result}")
                raise ServerRubikaError(result)

            return result["data"]
        raise httpx.TimeoutException("All Base Urls Sending Requests and Can't Get Response .")

    async def download(self, url: str, path: str = "file", show_progress: bool = True) -> bool:
        try:
            await self._ensure_client()

            dir_path = os.path.dirname(path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            if self._rate_sem is None:
                self._rate_sem = asyncio.Semaphore(self._rate_limit)

            async with self._rate_sem:
                async with self._client.stream("GET", url) as response: # pyright: ignore[reportOptionalMemberAccess]
                    response.raise_for_status()
                    total = int(response.headers.get("content-length", 0))
                    if show_progress and total:
                        pbar = tqdm(total=total, unit="B", unit_scale=True, desc="Downloading")
                    else:
                        pbar = None
                    async with aiofiles.open(path, 'wb') as file:
                        async for chunk in response.aiter_bytes():
                            await file.write(chunk)
                            if pbar:
                                pbar.update(len(chunk))
                    if pbar:
                        pbar.close()
            return True
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            return False
    
    async def upload_httpx(self, url: str, files: dict) -> dict:
        try:
            self.logger.info("در حال آپلود فایل ...")
            await self._ensure_client()

            from ..utils.utils import Utils
            response = await self._client.post(url, files=files, timeout=None) # pyright: ignore[reportOptionalMemberAccess]
            response.raise_for_status()
            result = response.json()
            if not Utils.check_data(result):
                self.logger.error(f"Server returned error: {result}")
                raise ServerRubikaError(result)
            self.logger.info("فایل آپلود شد")
            return result["data"]
        except httpx.HTTPError:
            self.logger.error("خطای HTTP")
            raise
        except Exception as e:
            self.logger.error(f"خطایی ناشناخته » {e}")
            raise

    async def upload(
        self,
        url: str,
        file_path: Union[str, Path, bytes],
        file_name: str,
        show_progress: bool = True,
        chunk_size: int = 64 * 1024
    ) -> dict:
        self.logger.info("در حال آپلود فایل (aiohttp stream)...")
        try:
            import aiohttp
        except ImportError:
            raise ImportError("ابتدا کتابخانه aiohttp را برای آپلود نصب کنید !")
        is_temp = False
        if isinstance(file_path, (bytes, bytearray)):
            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp.write(file_path)
            tmp.close()
            file_path = tmp.name
            is_temp = True
        try:
            total_size = None
            if isinstance(file_path, (str, Path)):
                total_size = os.path.getsize(file_path)
            timeout = aiohttp.ClientTimeout(total=None)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                form = aiohttp.FormData()
                async def file_gen():
                    async with aiofiles.open(file_path, "rb") as f:
                        if show_progress and total_size:
                            pbar = tqdm(total=total_size, unit="B", unit_scale=True, desc="Uploading")
                        else:
                            pbar = None
                        while True:
                            chunk = await f.read(chunk_size)
                            if not chunk:
                                break
                            if pbar:
                                pbar.update(len(chunk))
                            yield chunk
                        if pbar:
                            pbar.close()
                form.add_field(
                    "file",
                    file_gen(),
                    filename=file_name,
                    content_type="application/octet-stream"
                )
                async with session.post(url, data=form) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        raise ServerRubikaError(
                            {"status": "ERROR", "detail": text}
                        )
                    result = await resp.json()
                    from ..utils.utils import Utils
                    if not Utils.check_data(result):
                        self.logger.error(f"Server returned error: {result}")
                        raise ServerRubikaError(result)
                    self.logger.info("آپلود با موفقیت انجام شد")
                    return result["data"]
        finally:
            if is_temp:
                os.remove(file_path)
