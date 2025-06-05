import asyncio

class WhisperStreamStub:
    def __init__(self):
        self._buffer = []
        self._transcripts = []
        self._running = True

    async def feed(self, audio_chunk):
        # Simulate processing
        await asyncio.sleep(0.01)
        # For stub, just append a dummy transcript for every chunk
        self._transcripts.append("[transcript for chunk]")

    async def get_transcripts(self):
        # Simulate streaming transcripts
        while self._running or self._transcripts:
            if self._transcripts:
                yield self._transcripts.pop(0)
            else:
                await asyncio.sleep(0.05)

    async def stop(self):
        self._running = False

class WhisperTranscriber:
    def __init__(self):
        pass

    async def transcribe(self, audio_chunk):
        # Placeholder: implement whisper_streaming transcription
        await asyncio.sleep(0)  # Simulate async
        return None

    async def start_streaming(self):
        # Async context manager for streaming
        class _StreamContext:
            async def __aenter__(self_):
                self_._stream = WhisperStreamStub()
                return self_._stream
            async def __aexit__(self_, exc_type, exc, tb):
                await self_._stream.stop()
        return _StreamContext() 