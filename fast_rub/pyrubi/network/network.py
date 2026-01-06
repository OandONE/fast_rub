from json import dumps, loads
from tqdm import tqdm
from typing import Any, Protocol, Optional, Union
import httpx
import aiohttp
from ..utils import Configs
from ..exceptions import *
from .helper import Helper
from ..utils import *


class MethodsProtocol(Protocol):
    sessionData: Any
    crypto: Any
    proxy: Optional[str]
    platform: str
    apiVersion: int
    timeOut: int
    showProgressBar: bool
    async def requestSendFile(
        self, fileName: str, mime: str, size: int
    ) -> dict: ...


class Network:
    def __init__(self, methods: MethodsProtocol) -> None:
        self.methods = methods
        self.sessionData = methods.sessionData
        self.crypto = methods.crypto
        
        if methods.proxy:
            import os
            if isinstance(methods.proxy, dict):
                proxy_str = methods.proxy.get("http") or methods.proxy.get("https") or list(methods.proxy.values())[0]
            else:
                proxy_str = methods.proxy
            
            os.environ['HTTP_PROXY'] = proxy_str
            os.environ['HTTPS_PROXY'] = proxy_str
            os.environ['ALL_PROXY'] = proxy_str
        
        self.httpx_client = httpx.AsyncClient(
            timeout=methods.timeOut,
            trust_env=True
        )
        
        self.proxy_str = None
        if methods.proxy:
            if isinstance(methods.proxy, dict):
                self.proxy_str = methods.proxy.get("http") or methods.proxy.get("https") or list(methods.proxy.values())[0]
            else:
                self.proxy_str = methods.proxy
        
        self.aiohttp_session = None

    async def _get_aiohttp_session(self):
        if self.aiohttp_session is None:
            connector = aiohttp.TCPConnector()
            
            if self.proxy_str:
                self.aiohttp_session = aiohttp.ClientSession(
                    connector=connector,
                    trust_env=True
                )
            else:
                self.aiohttp_session = aiohttp.ClientSession(
                    connector=connector
                )
        
        return self.aiohttp_session

    async def request(self, method: str, input: dict = {}, tmpSession: bool = False, 
                     attempt: int = 0, maxAttempt: int = 2) -> dict:
        url: str = Helper.getApiServer()
        platform: str = self.methods.platform.lower()
        apiVersion: int = self.methods.apiVersion
        configs = Configs()
        
        if platform in ["rubx", "rubikax"]:
            client: dict = configs.clients["android"]
            client["package"] = "ir.rubx.bapp"
        elif platform in ["android"]:
            client: dict = configs.clients["android"]
        else:
            client: dict = configs.clients["web"]

        auth_key = "tmp_session" if tmpSession else "auth"
        auth_value = (
            self.crypto.auth if tmpSession else
            self.crypto.changeAuthType(self.sessionData["auth"]) if apiVersion > 5 else
            self.sessionData["auth"]
        )
        
        data = {
            "api_version": str(apiVersion),
            auth_key: auth_value,
            "data_enc": self.crypto.encrypt(
                dumps({
                    "method": method,
                    "input": input,
                    "client": client
                })
            )
        }

        headers: dict = {
            "Referer": "https://web.rubika.ir/",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        if not tmpSession and apiVersion > 5:
            data["sign"] = self.crypto.makeSignFromData(data["data_enc"])

        while attempt <= maxAttempt:
            try:
                response = await self.httpx_client.post(
                    url=url,
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                
                result_data = response.json()
                decrypted_data = self.crypto.decrypt(result_data["data_enc"])
                result = loads(decrypted_data)
                
                if result["status"] == "OK":
                    if tmpSession:
                        result["data"]["tmp_session"] = self.crypto.auth
                    return result["data"]
                else:
                    raise Utils.raise_error(result)
                    
            except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as e:
                attempt += 1
                if attempt > maxAttempt:
                    raise httpx.NetworkError(f"Request failed after {maxAttempt} attempts: {str(e)}")
                continue

        raise httpx.NetworkError("Request failed")

    async def upload(
        self, 
        file: Union[str, bytes], 
        fileName: Optional[str] = None, 
        chunkSize: int = 131072
    ) -> Optional[dict]:
        if isinstance(file, str):
            if Utils.checkLink(url=file):
                response = await self.httpx_client.get(file)
                response.raise_for_status()
                file_bytes: bytes = response.content
                mime: str = Utils.getMimeFromByte(file_bytes)
                fileName = fileName or Utils.generateFileName(mime=mime)
                file = file_bytes
            else:
                fileName = fileName or file
                with open(file, "rb") as fh:
                    file = fh.read()
                mime = Utils.getMimeFromByte(file)

        elif isinstance(file, bytes):
            mime = Utils.getMimeFromByte(file)
            fileName = fileName or Utils.generateFileName(mime=mime)
        else:
            raise FileNotFoundError("Enter a valid path or url or bytes of file.")

        async def send_chunk(session: aiohttp.ClientSession, data: bytes, 
                           upload_url: str, headers: dict, maxAttempts: int = 2) -> Optional[dict]:
            for attempt in range(maxAttempts):
                try:
                    async with session.post(
                        upload_url,
                        headers=headers,
                        data=data,
                        timeout=aiohttp.ClientTimeout(total=self.methods.timeOut)
                    ) as response:
                        response.raise_for_status()
                        return await response.json()
                except Exception as e:
                    print(f"\nError uploading file! (Attempt {attempt + 1}/{maxAttempts}): {e}")
            
            print("\nFailed to upload the file!")
            return None

        requestSendFileData = await self.methods.requestSendFile(
            fileName=fileName,
            mime=mime,
            size=len(file)
        )

        session = await self._get_aiohttp_session()
        
        headers = {
            "auth": self.sessionData["auth"],
            "access-hash-send": requestSendFileData["access_hash_send"],
            "file-id": requestSendFileData["id"],
        }

        totalParts = (len(file) + chunkSize - 1) // chunkSize

        processBar: Optional[tqdm] = None

        if self.methods.showProgressBar:
            processBar = tqdm(
                desc=f"Uploading {fileName}",
                total=len(file),
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            )

        for partNumber in range(1, totalParts + 1):
            startIdx = (partNumber - 1) * chunkSize
            endIdx = min(startIdx + chunkSize, len(file))
            chunk_headers = headers.copy()
            chunk_headers["chunk-size"] = str(endIdx - startIdx)
            chunk_headers["part-number"] = str(partNumber)
            chunk_headers["total-part"] = str(totalParts)
            
            data = file[startIdx:endIdx]
            hashFileReceive = await send_chunk(
                session, 
                data, 
                requestSendFileData["upload_url"],
                chunk_headers
            )
            
            if processBar is not None:
                processBar.update(len(data))

            if not hashFileReceive:
                return None
            
            if partNumber == totalParts:
                if not hashFileReceive.get("data"):
                    return None
                
                requestSendFileData["file"] = file
                requestSendFileData["access_hash_rec"] = hashFileReceive["data"]["access_hash_rec"]
                requestSendFileData["file_name"] = fileName
                requestSendFileData["mime"] = mime
                requestSendFileData["size"] = len(file)
                return requestSendFileData
        
        return None

    async def download(self, accessHashRec: str, fileId: str, dcId: str, 
                      size: int, fileName: str, chunkSize: int = 262143, 
                      attempt: int = 0, maxAttempts: int = 2) -> Optional[bytes]:
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
            "User-Agent": "okhttp/3.12.1"
        }

        session = await self._get_aiohttp_session()
        url = f"https://messenger{dcId}.iranlms.ir/GetFile.ashx"

        processBar: Optional[tqdm] = None

        if self.methods.showProgressBar:
            processBar = tqdm(
                desc=f"Downloading {fileName}",
                total=size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            )

        for retry in range(maxAttempts):
            try:
                data: bytes = b""
                
                async with session.post(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.methods.timeOut)
                ) as response:
                    response.raise_for_status()
                    
                    async for chunk in response.content.iter_chunked(chunkSize):
                        if chunk:
                            data += chunk
                            if processBar is not None:
                                processBar.update(len(chunk))
                        
                        if len(data) >= size:
                            if processBar is not None:
                                processBar.close()
                            return data[:size]
                
            except Exception as e:
                attempt += 1
                if attempt <= maxAttempts:
                    print(f"\nError downloading file! (Attempt {attempt}/{maxAttempts}): {e}")
                    continue
                
                if processBar is not None:
                    processBar.close()
                raise TimeoutError("Failed to download the file!")
        
        if processBar is not None:
            processBar.close()
        return None

    async def close(self):
        """Close all HTTP sessions"""
        await self.httpx_client.aclose()
        
        if self.aiohttp_session:
            await self.aiohttp_session.close()
            self.aiohttp_session = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
