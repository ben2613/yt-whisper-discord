import asyncio

class DiartProcessor:
    def __init__(self, enabled=True):
        self.enabled = enabled

    async def process_audio_stream(self, audio_stream):
        """
        Process an async audio stream and yield (start_time, end_time, audio_chunk, speaker_label) tuples.
        If disabled, yield the raw audio stream as a single segment with no speaker label.
        """
        if not self.enabled:
            # Pass through the audio stream as a single segment
            async for chunk in audio_stream:
                yield (None, None, chunk, None)
            return
        # Placeholder: integrate diart for VAD/diarization
        # Example: for each detected speech segment, yield (start, end, audio_chunk, speaker_label)
        await asyncio.sleep(0)  # Simulate async
        # yield (start_time, end_time, audio_chunk, speaker_label)
        return 