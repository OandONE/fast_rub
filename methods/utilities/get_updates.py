from typing import Optional

class GetUpdates:
    async def get_updates(self: "fast_rub.Client", limit: int, offset_id: Optional[str] = None):
        data = {"offset_id": offset_id, "limit": limit}
        result = await self.send_request("getUpdates", data, request_type="post")
        return result