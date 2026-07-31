from typing import Any
from pathlib import Path
from tqdm import tqdm
import aiofiles
import os

from ...network.network import Network as BaseNetwork


class Network(BaseNetwork):
    """
    pyrubi network layer — extends Fast Rub's Network with
    pyrubi-specific upload/download methods.
    Uses httpx instead of aiohttp.
    """
    
    def __init__(
        self,
        token: str,
        client: Any,
        logger: Any = None,
        max_retries: int = 3,
        user_agent: str | None = None,
        base_urls: list | None = None,
        proxy: str | None = None,
        rate_limit: int = 20,
        ssl_verify: bool = True,
        max_retries_upload: int | None = None,
        max_retries_download: int | None = None,
        session_data: dict | None = None,
        show_progress: bool = True,
    ):
        if base_urls is None:
            base_urls = [
                "https://messengerg2b1.iranlms.ir/",
            ]
        
        super().__init__(
            token=token,
            client=client,
            logger=logger,
            max_retries=max_retries,
            user_agent=user_agent,
            base_urls=base_urls,
            proxy=proxy,
            rate_limit=rate_limit,
            ssl_verify=ssl_verify,
            max_retries_upload=max_retries_upload,
            max_retries_download=max_retries_download,
        )
        
        self.session_data = session_data or {}
        self.show_progress = show_progress
    
    async def upload_file(
        self,
        file: str | Path | bytes,
        upload_url: str,
        access_hash_send: str,
        file_id: str,
        file_name: str | None = None,
        chunk_size: int = 131072,
    ) -> dict | None:
        """
        Upload a file to the given upload_url using httpx.
        Replacement for the old aiohttp-based upload.
        """
        from ..utils import Utils
        
        # Prepare file data
        if isinstance(file, str):
            if Utils.checkLink(url=file):
                response = await self._client.get(file) # pyright: ignore[reportOptionalMemberAccess]
                response.raise_for_status()
                file_bytes: bytes = response.content
                mime = Utils.getMimeFromByte(file_bytes)
                file_name = file_name or Utils.generateFileName(mime=mime)
                file = file_bytes
            else:
                file_name = file_name or file
                async with aiofiles.open(file, "rb") as fh:
                    file = await fh.read()
                mime = Utils.getMimeFromByte(file)
        elif isinstance(file, bytes):
            mime = Utils.getMimeFromByte(file)
            file_name = file_name or Utils.generateFileName(mime=mime)
        else:
            raise FileNotFoundError("Enter a valid path or url or bytes of file.")
        
        total_size = len(file)
        total_parts = (total_size + chunk_size - 1) // chunk_size
        
        headers_base = {
            "auth": self.session_data.get("auth", ""),
            "access-hash-send": access_hash_send,
            "file-id": file_id,
        }
        
        pbar = None
        if self.show_progress:
            pbar = tqdm(
                desc=f"Uploading {file_name}",
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            )
        
        for part_number in range(1, total_parts + 1):
            start_idx = (part_number - 1) * chunk_size
            end_idx = min(start_idx + chunk_size, total_size)
            chunk = file[start_idx:end_idx]
            
            headers = headers_base.copy()
            headers["chunk-size"] = str(end_idx - start_idx)
            headers["part-number"] = str(part_number)
            headers["total-part"] = str(total_parts)
            
            response = await self._client.post( # pyright: ignore[reportOptionalMemberAccess]
                upload_url,
                content=chunk,
                headers=headers,
                timeout=None,
            )
            
            if response.status_code != 200:
                if pbar:
                    pbar.close()
                return None
            
            if pbar:
                pbar.update(len(chunk))
            
            if part_number == total_parts:
                result = response.json()
                if pbar:
                    pbar.close()
                
                if not result.get("data"):
                    return None
                
                return {
                    "file": file,
                    "access_hash_rec": result["data"]["access_hash_rec"],
                    "file_name": file_name,
                    "mime": mime,
                    "size": total_size,
                }
        
        if pbar:
            pbar.close()
        return None
    
    async def download_file(
        self,
        access_hash_rec: str,
        file_id: str,
        dc_id: str,
        size: int,
        file_name: str,
        chunk_size: int = 262143,
        save_path: str | None = None,
    ) -> bytes | None:
        """
        Download a file from Rubika servers using httpx.
        Replacement for the old aiohttp-based download.
        """
        url = f"https://messenger{dc_id}.iranlms.ir/GetFile.ashx"
        
        headers = {
            "auth": self.session_data.get("auth", ""),
            "access-hash-rec": access_hash_rec,
            "dc-id": dc_id,
            "file-id": file_id,
            "Host": f"messenger{dc_id}.iranlms.ir",
            "client-app-name": "Main",
            "client-app-version": "3.5.7",
            "client-package": "app.rbmain.a",
            "client-platform": "Android",
            "Connection": "Keep-Alive",
            "User-Agent": "okhttp/3.12.1",
        }
        
        pbar = None
        if self.show_progress:
            pbar = tqdm(
                desc=f"Downloading {file_name}",
                total=size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            )
        
        data = b""
        
        async with self._client.stream("POST", url, headers=headers) as response: # pyright: ignore[reportOptionalMemberAccess]
            response.raise_for_status()
            
            async for chunk in response.aiter_bytes(chunk_size):
                if chunk:
                    data += chunk
                    if pbar:
                        pbar.update(len(chunk))
                    
                    if len(data) >= size:
                        if pbar:
                            pbar.close()
                        data = data[:size]
                        break
        
        if pbar:
            pbar.close()
        
        # Optionally save to disk
        if save_path:
            dir_path = os.path.dirname(save_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            async with aiofiles.open(save_path, "wb") as f:
                await f.write(data)
        
        return data if data else None
