"""
pyrubi network layer — completely standalone, no inheritance from Fast Rub.
Uses httpx + HTTP/2, with retry, rate limiting, and structured logging.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, TYPE_CHECKING

import aiofiles
import httpx
from tqdm import tqdm

from ..exceptions import *
from ..utils import Utils, Configs
from ...utils import Utils as UtilsFastRub
from .helper import Helper

if TYPE_CHECKING:
    from ..methods import Methods

# 
# Network
# 
class Network:
    """Replacement for the old aiohttp‑based pyrubi network."""

    def __init__(
        self,
        methods: "Methods",
        *,
        max_retries: int = 3,
        rate_limit: int = 20,
        logger: logging.Logger | None = None,
    ) -> None:
        #  pyrubi-specific state 
        self.methods = methods
        self.sessionData = methods.sessionData
        self.crypto = methods.crypto
        self.platform = methods.platform
        self.apiVersion = methods.apiVersion
        self.timeOut = methods.timeOut
        self.showProgressBar = methods.showProgressBar

        #  proxy support 
        self.proxy: str | None = None
        if methods.proxy:
            if isinstance(methods.proxy, dict):
                self.proxy = (
                    methods.proxy.get("http")
                    or methods.proxy.get("https")
                    or list(methods.proxy.values())[0]
                )
            else:
                self.proxy = methods.proxy
            # Set environment variables for other libraries
            if self.proxy:
                os.environ["HTTP_PROXY"] = self.proxy
                os.environ["HTTPS_PROXY"] = self.proxy
                os.environ["ALL_PROXY"] = self.proxy

        #  httpx client 
        self._client: httpx.AsyncClient | None = None
        self._client_lock = asyncio.Lock()

        #  retry & rate limiting 
        self.max_retries = max_retries
        self._rate_sem = asyncio.Semaphore(rate_limit)

        #  logging 
        self.logger = logger or logging.getLogger("pyrubi.network")

        #  misc 
        self._closed = False
        self._configs = Configs()

    # 
    # Client lifecycle
    # 
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            async with self._client_lock:
                if self._client is None or self._client.is_closed:
                    self._client = httpx.AsyncClient(
                        timeout=httpx.Timeout(
                            connect=10.0,
                            read=float(self.timeOut),
                            write=10.0,
                            pool=10.0,
                        ),
                        limits=httpx.Limits(
                            max_connections=100,
                            max_keepalive_connections=20,
                        ),
                        http1=True,
                        http2=True,
                        proxy=self.proxy,
                    )
        return self._client

    async def close(self) -> None:
        self._closed = True
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # 
    # pyrubi request (old signature)
    # 
    async def request(
        self,
        method: str,
        input: dict[str, Any] | None = None,
        tmpSession: bool = False,
        attempt: int = 0,
        maxAttempt: int = 2,
    ) -> dict[str, Any]:
        """
        Encrypt + send request to the Rubika API.
        Signature matches the original pyrubi network for drop‑in compatibility.
        """
        if input is None:
            input = {}

        input = UtilsFastRub.clean_dict(input)

        url = Helper.getApiServer()
        platform = self.platform.lower()
        api_version = self.apiVersion

        # Client descriptor
        if platform in ("rubx", "rubikax"):
            client = dict(self._configs.clients["android"])
            client["package"] = "ir.rubx.bapp"
        elif platform == "android":
            client = dict(self._configs.clients["android"])
        else:
            client = dict(self._configs.clients["web"])

        auth_key = "tmp_session" if tmpSession else "auth"
        auth_value = (
            self.crypto.auth
            if tmpSession
            else self.crypto.changeAuthType(self.sessionData["auth"])
            if api_version > 5
            else self.sessionData["auth"]
        )

        payload = {
            "api_version": str(api_version),
            auth_key: auth_value,
            "data_enc": self.crypto.encrypt(
                json.dumps(
                    {
                        "method": method,
                        "input": input,
                        "client": client,
                    }
                )
            ),
        }

        headers = {
            "Referer": "https://web.rubika.ir/",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko)"
            ),
        }

        if not tmpSession and api_version > 5:
            payload["sign"] = self.crypto.makeSignFromData(payload["data_enc"])

        client = await self._get_client()

        last_exc: Exception | None = None
        for retry in range(attempt, maxAttempt + 1):
            try:
                async with self._rate_sem:
                    resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()

                body = resp.json()
                decrypted = self.crypto.decrypt(body["data_enc"])
                result = json.loads(decrypted)

                if result["status"] == "OK":
                    if tmpSession:
                        result["data"]["tmp_session"] = self.crypto.auth
                    return result["data"]

                raise Utils.raise_error(result)

            except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as exc:
                last_exc = exc
                self.logger.warning(
                    "Request attempt %d/%d failed: %s", retry + 1, maxAttempt, exc
                )
                if retry >= maxAttempt:
                    break
                await asyncio.sleep(1.0)  # small back‑off

        raise httpx.NetworkError(
            f"Request failed after {maxAttempt} attempts"
        ) from last_exc

    # 
    # File upload (httpx)
    # 
    async def upload(
        self,
        file: str | bytes,
        fileName: str | None = None,
        chunkSize: int = 131_072,
    ) -> dict[str, Any] | None:
        """
        Upload a file to the Rubika CDN.  Replaces the old aiohttp‑based upload.
        """
        #  Normalise file 
        if isinstance(file, str):
            if Utils.checkLink(url=file):
                client = await self._get_client()
                resp = await client.get(file)
                resp.raise_for_status()
                file_bytes: bytes = resp.content
                mime = Utils.getMimeFromByte(file_bytes)
                fileName = fileName or Utils.generateFileName(mime=mime)
                file = file_bytes
            else:
                fileName = fileName or file
                async with aiofiles.open(file, "rb") as fh:
                    file = await fh.read()
                mime = Utils.getMimeFromByte(file)
        elif isinstance(file, bytes):
            mime = Utils.getMimeFromByte(file)
            fileName = fileName or Utils.generateFileName(mime=mime)
        else:
            raise FileNotFoundError("Enter a valid path, url, or bytes.")

        #  Request upload slot 
        slot = await self.methods.requestSendFile(
            fileName=fileName, mime=mime, size=len(file)
        )

        total_parts = (len(file) + chunkSize - 1) // chunkSize
        base_headers = {
            "auth": self.sessionData["auth"],
            "access-hash-send": slot["access_hash_send"],
            "file-id": slot["id"],
        }

        pbar: tqdm | None = None
        if self.showProgressBar:
            pbar = tqdm(
                desc=f"Uploading {fileName}",
                total=len(file),
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            )

        client = await self._get_client()
        upload_url = slot["upload_url"]

        for part_number in range(1, total_parts + 1):
            start = (part_number - 1) * chunkSize
            end = min(start + chunkSize, len(file))
            chunk = file[start:end]

            headers = base_headers.copy()
            headers["chunk-size"] = str(end - start)
            headers["part-number"] = str(part_number)
            headers["total-part"] = str(total_parts)

            resp = await client.post(upload_url, content=chunk, headers=headers)

            if pbar:
                pbar.update(len(chunk))

            if resp.status_code != 200:
                if pbar:
                    pbar.close()
                return None

            if part_number == total_parts:
                result = resp.json()
                if pbar:
                    pbar.close()

                if not result.get("data"):
                    return None

                return {
                    "file": file,
                    "access_hash_rec": result["data"]["access_hash_rec"],
                    "file_name": fileName,
                    "mime": mime,
                    "size": len(file),
                }

        if pbar:
            pbar.close()
        return None

    # 
    # File download (httpx)
    # 
    async def download(
        self,
        accessHashRec: str,
        fileId: str,
        dcId: str,
        size: int,
        fileName: str,
        chunkSize: int = 262_143,
        attempt: int = 0,
        maxAttempts: int = 2,
    ) -> bytes | None:
        """
        Download a file from the Rubika CDN.  Replaces the old aiohttp‑based download.
        """
        url = f"https://messenger{dcId}.iranlms.ir/GetFile.ashx"
        headers = {
            "auth": self.sessionData["auth"],
            "access-hash-rec": accessHashRec,
            "dc-id": dcId,
            "file-id": fileId,
            "Host": f"messenger{dcId}.iranlms.ir",
            "client-app-name": "Main",
            "client-app-version": "3.5.7",
            "client-package": "app.rbmain.a",
            "client-platform": "Android",
            "Connection": "Keep-Alive",
            "Content-Type": "application/json",
            "User-Agent": "okhttp/3.12.1",
        }

        pbar: tqdm | None = None
        if self.showProgressBar:
            pbar = tqdm(
                desc=f"Downloading {fileName}",
                total=size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            )

        client = await self._get_client()
        data = b""

        for retry in range(maxAttempts):
            try:
                async with client.stream("POST", url, headers=headers) as resp:
                    resp.raise_for_status()
                    async for chunk in resp.aiter_bytes(chunkSize):
                        if chunk:
                            data += chunk
                            if pbar:
                                pbar.update(len(chunk))
                            if len(data) >= size:
                                if pbar:
                                    pbar.close()
                                return data[:size]
                # File smaller than expected
                if pbar:
                    pbar.close()
                return data if data else None

            except Exception:
                self.logger.warning(
                    "Download attempt %d/%d failed", retry + 1, maxAttempts
                )
                if retry >= maxAttempts - 1:
                    if pbar:
                        pbar.close()
                    raise TimeoutError("Failed to download the file!")
                await asyncio.sleep(1.0)

        if pbar:
            pbar.close()
        return None
    
    

