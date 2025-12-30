from json import dumps, loads
from tqdm import tqdm
from urllib3 import PoolManager, ProxyManager
from ..utils import Configs
from ..exceptions import *
from .helper import Helper
from typing import Any, Protocol, Optional, Union
import asyncio
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
    def __init__(self, methods:MethodsProtocol) -> None:
        self.methods = methods
        self.sessionData = methods.sessionData
        self.crypto = methods.crypto
        self.http = ProxyManager(methods.proxy) if methods.proxy else PoolManager()

    async def request(self, method:str, input:dict={}, tmpSession:bool=False, attempt:int = 0, maxAttempt:int=2) -> dict:
        url:str = Helper.getApiServer()
        platform:str = self.methods.platform.lower()
        apiVersion:int = self.methods.apiVersion
        configs = Configs()
        if platform in ["rubx", "rubikax"]:
            client: dict = configs.clients["android"]
            client["package"] = "ir.rubx.bapp"
        
        elif platform in ["android"]:
            client: dict = configs.clients["android"]

        else:
            client: dict = configs.clients["web"]

        data = {
            "api_version": str(apiVersion),
            "tmp_session" if tmpSession else
            "auth": self.crypto.auth if tmpSession else
            self.crypto.changeAuthType(self.sessionData["auth"]) if apiVersion > 5 else
            self.sessionData["auth"],
            "data_enc": self.crypto.encrypt(
                dumps({
                    "method": method,
                    "input": input,
                    "client": client
                })
            )
        }

        headers:dict = {
            "Referer": "https://web.rubika.ir/",
            "Content-Type": "application/json; charset=utf-8"
        }

        if not tmpSession and apiVersion > 5:
            data["sign"] = self.crypto.makeSignFromData(data["data_enc"])

        while True:
            result = self.http.request(
                method="POST",
                url=url,
                headers=headers,
                body = dumps(data).encode(),
                timeout=self.methods.timeOut
            )

            try:
                result = loads(self.crypto.decrypt(loads(result.data.decode("UTF-8"))["data_enc"]))
            except:
                attempt += 1

                if attempt > maxAttempt:
                    raise
                
                continue

            if result["status"] == "OK":
                if tmpSession:
                    result["data"]["tmp_session"] = self.crypto.auth

                return result["data"]
            
            else:
                raise {
                    "INVALID_AUTH": InvalidAuth(),
                    "NOT_REGISTERED": NotRegistered(),
                    "INVALID_INPUT": InvalidInput(),
                    "TOO_REQUESTS": TooRequests()
                }[result["status_det"]]

    def upload(
        self, 
        file: Union[str, bytes], 
        fileName: Optional[str] = None, 
        chunkSize: int = 131072
    ):
        if isinstance(file, str):
            if Utils.checkLink(url=file):
                file_bytes: bytes = self.http.request(method="GET", url=file).data
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

        def send_chunk(data, maxAttempts=2):
            for attempt in range(maxAttempts):
                try:
                    response = self.http.request(
                        "POST",
                        url=requestSendFileData["upload_url"],
                        headers=header,
                        body=data
                    )
                    return loads(response.data.decode("UTF-8"))
                except Exception:
                    print(f"\nError uploading file! (Attempt {attempt + 1}/{maxAttempts})")
            
            print("\nFailed to upload the file!")

        try:
            loop = asyncio.get_running_loop()
            requestSendFileData = asyncio.run_coroutine_threadsafe(
                self.methods.requestSendFile(
                    fileName=fileName,
                    mime=mime, 
                    size=len(file)
                ), loop
            ).result()
        except RuntimeError:
            requestSendFileData = asyncio.run(self.methods.requestSendFile(
                fileName=fileName,
                mime=mime,
                size=len(file)
            ))

        header = {
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
            header["chunk-size"] = str(endIdx - startIdx)
            header["part-number"] = str(partNumber)
            header["total-part"] = str(totalParts)
            data = file[startIdx:endIdx]
            hashFileReceive = send_chunk(data)
            
            if processBar is not None:
                processBar.update(len(data))

            if not hashFileReceive:
                return
            
            if partNumber == totalParts:

                if not hashFileReceive["data"]:
                    return
                
                requestSendFileData["file"] = file
                requestSendFileData["access_hash_rec"] = hashFileReceive["data"]["access_hash_rec"]
                requestSendFileData["file_name"] = fileName
                requestSendFileData["mime"] = mime
                requestSendFileData["size"] = len(file)
                return requestSendFileData
            
    def download(self, accessHashRec:str, fileId:str, dcId:str, size:int, fileName:str, chunkSize:int=262143, attempt:int=0, maxAttempts:int=2):
        headers:dict = {
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


        response = self.http.request(
            "POST",
            url=f"https://messenger{dcId}.iranlms.ir/GetFile.ashx",
            headers=headers,
            preload_content=False
        )

        data:bytes = b""

        processBar: Optional[tqdm] = None

        if self.methods.showProgressBar:
            processBar = tqdm(
                desc=f"Downloading {fileName}",
                total=size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            )

        for downloadedData in response.stream(chunkSize):
            try:
                if downloadedData:
                    data += downloadedData
                    if processBar is not None:
                        processBar.update(len(downloadedData))

                if len(data) >= size:
                    return data
            except Exception:
                if attempt <= maxAttempts:
                    attempt += 1
                    print(f"\nError downloading file! (Attempt {attempt}/{maxAttempts})")
                    continue

                raise TimeoutError("Failed to download the file!")