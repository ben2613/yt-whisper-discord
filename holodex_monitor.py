import asyncio
import os
import httpx

class HolodexMonitor:
    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.api_key = os.getenv("HOLODEX_API_KEY", "YOUR_HOLODEX_API_KEY")

    def set_channel_id(self, channel_id):
        self.channel_id = channel_id

    async def get_live_video_id(self):
        # Query Holodex API for live videos for this channel
        url = f"https://holodex.net/api/v2/live"
        headers = {"X-APIKEY": self.api_key}
        params = {"channel_id": self.channel_id, "status": "live", "type": "stream", "limit": 1}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, headers=headers, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list) and data:
                    return data[0]["id"]
                elif isinstance(data, dict) and "items" in data and data["items"]:
                    return data["items"][0]["id"]
            except Exception as e:
                print(f"Holodex API error: {e}")
        return None 