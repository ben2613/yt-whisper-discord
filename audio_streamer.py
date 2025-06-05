import asyncio
import subprocess
from yt_dlp import YoutubeDL

class AudioStreamer:
    def __init__(self):
        pass

    async def get_audio_stream_url(self, video_id: str) -> str:
        # Use yt_dlp Python API to get the best audio stream URL
        video_url = video_id if video_id.startswith('http') else f'https://www.youtube.com/watch?v={video_id}'
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        loop = asyncio.get_event_loop()
        def extract():
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                # Find the best audio URL
                if 'url' in info:
                    return info['url']
                # Sometimes 'formats' is present
                if 'formats' in info:
                    for f in info['formats']:
                        if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                            return f['url']
                return None
        stream_url = await loop.run_in_executor(None, extract)
        return stream_url

    async def stream_audio(self, video_id: str, chunk_size: int = 4096):
        # 1. Get direct audio stream URL
        stream_url = await self.get_audio_stream_url(video_id)
        if not stream_url:
            raise RuntimeError('Could not get stream URL from yt-dlp')

        # 2. Start ffmpeg to transcode and pipe audio
        ffmpeg_cmd = [
            'ffmpeg', '-i', stream_url,
            '-f', 's16le', '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', '-'
        ]
        proc = await asyncio.create_subprocess_exec(
            *ffmpeg_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )

        # 3. Yield audio chunks
        try:
            while True:
                chunk = await proc.stdout.read(chunk_size)
                if not chunk:
                    break
                yield chunk
        finally:
            if proc.stdout:
                proc.stdout.close()
            await proc.wait() 