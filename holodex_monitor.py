import asyncio
import requests

class HolodexMonitor:
    def __init__(self, channel_id):
        self.channel_id = channel_id

    def set_channel_id(self, channel_id):
        self.channel_id = channel_id

    async def get_live_video_id(self):
        # Always use the current channel_id
        await asyncio.sleep(0)  # Simulate async
        return None 