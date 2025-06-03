# YouTube-Whisper-Discord Live Transcription Pipeline

## 1. Requirements Recap

- **Whisper Model**: For real-time transcription (using [ufal/whisper_streaming](https://github.com/ufal/whisper_streaming)).
- **Discord Bot**: To send messages to a Discord channel.
- **Holodex API**: To detect if a channel is live and retrieve the live video (replaces YouTube Data API due to quota limits).
- **yt-dlp + ffmpeg**: To extract and stream audio from the live video.
- **Pipeline**: Stream audio → Whisper → Discord.

---

## 2. High-Level Architecture

### Components

1. **Holodex Live Monitor**
   - Polls Holodex API for live status of a channel.
2. **Audio Streamer**
   - Uses yt-dlp and ffmpeg to extract live audio stream.
3. **Whisper Streaming Transcriber**
   - Feeds audio chunks to Whisper for real-time transcription.
4. **Discord Bot**
   - Posts transcriptions to a Discord channel.

---

## 3. Detailed Plan

### A. Holodex Live Monitor
- Use Holodex API to check if a channel is live and retrieve the live video ID/URL.
- Example endpoint: `https://holodex.net/api/v2/channels/{channelId}` or `https://holodex.net/api/v2/users/{channelId}/live`.
- No Google API key or quota issues.

### B. Audio Streamer
- Use `yt-dlp` to get the live stream URL.
- Pipe the stream to `ffmpeg` to extract audio in the required format (e.g., 16kHz mono PCM).
- Stream audio in real-time (not download-then-process).

### C. Whisper Streaming Transcriber
- Use [ufal/whisper_streaming](https://github.com/ufal/whisper_streaming) as a module.
- Feed audio chunks from ffmpeg to the transcriber.
- Get partial and final transcripts.

### D. Discord Bot
- Use `discord.py` or `nextcord` to send messages.
- Post transcripts as they are produced.

---

## 4. Module/Script Structure

```
yt-whisper-discord/
│
├── main.py                # Orchestrates the workflow
├── holodex_monitor.py     # Checks for live streams using Holodex API
├── audio_streamer.py      # Handles yt-dlp + ffmpeg audio extraction
├── whisper_transcriber.py # Wraps whisper_streaming
├── discord_bot.py         # Handles Discord messaging
├── config.py              # API keys, channel IDs, etc.
├── requirements.txt
└── README.md
```

---

## 5. Data Flow

1. **main.py** starts all services.
2. **holodex_monitor.py** detects a live stream.
3. **audio_streamer.py** starts streaming audio from the live video.
4. **whisper_transcriber.py** receives audio chunks, transcribes, and emits text.
5. **discord_bot.py** posts the transcript to Discord.

---

## 6. Key Implementation Notes

- **Holodex API**: Use Holodex endpoints to check live status and get live video info. See [Holodex API Docs](https://holodex.stoplight.io/docs/holodex/).
- **yt-dlp + ffmpeg**: Use subprocess pipes to avoid saving files to disk. See [StackOverflow example](https://stackoverflow.com/questions/71187954/stream-audio-using-yt-dlp-kn-python-instead-of-downloading-the-file).
- **Whisper Streaming**: Use the `OnlineASRProcessor` as described in the [ufal/whisper_streaming README](https://github.com/ufal/whisper_streaming).
- **Concurrency**: Use asyncio or threading to handle real-time streaming and Discord messaging.
- **Error Handling**: Handle stream interruptions, API errors, and rate limits gracefully.

---

## 7. Dependencies

- `yt-dlp`
- `ffmpeg` (system binary)
- `discord.py` or `nextcord`
- `requests` (for Holodex API)
- `ufal/whisper_streaming` and its dependencies (`faster-whisper`, `torch`, etc.)

---

## 8. Next Steps

1. **Set up config.py** for API keys and settings.
2. **Implement Holodex live monitor**.
3. **Implement audio streaming pipeline**.
4. **Integrate Whisper streaming**.
5. **Build Discord bot**.
6. **Orchestrate in main.py**.

---

## References
- [ufal/whisper_streaming](https://github.com/ufal/whisper_streaming)
- [Holodex API Docs](https://holodex.stoplight.io/docs/holodex/)
- [StackOverflow: Stream audio using yt-dlp in Python instead of downloading the file](https://stackoverflow.com/questions/71187954/stream-audio-using-yt-dlp-kn-python-instead-of-downloading-the-file) 