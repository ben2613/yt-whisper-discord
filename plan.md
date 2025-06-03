# YouTube-Whisper-Discord Live Transcription Pipeline

## 1. Requirements Recap

- **Whisper Model**: For real-time transcription (using [faster-whisper](https://github.com/SYSTRAN/faster-whisper)).
- **Speaker Diarization & VAD (Optional)**: Use [diart](https://github.com/juanmc2005/diart) for real-time speaker segmentation and voice activity detection. Can be toggled on/off via config or environment variable (`USE_DIART`).
- **Discord Bot**: To send messages to a Discord channel.
- **Holodex API**: To detect if a channel is live and retrieve the live video (replaces YouTube Data API due to quota limits).
- **yt-dlp + ffmpeg**: To extract and stream audio from the live video.
- **Pipeline**: Stream audio → (Optional: Diart) → Whisper (transcription) → Discord.

---

## 2. High-Level Architecture

### Components

1. **Holodex Live Monitor**
   - Polls Holodex API for live status of a channel.
2. **Audio Streamer**
   - Uses yt-dlp and ffmpeg to extract live audio stream.
3. **Diart Processor (Optional)**
   - Performs real-time voice activity detection and speaker diarization on the audio stream if enabled.
   - Segments audio into speech regions and (optionally) identifies speakers.
4. **Whisper Streaming Transcriber**
   - Feeds audio (or speech segments from Diart) to Whisper for real-time transcription.
5. **Discord Bot**
   - Posts transcriptions to a Discord channel.

---

## 3. Detailed Plan

### A. Holodex Live Monitor
- Use Holodex API to check if a channel is live and retrieve the live video ID/URL.
- Example endpoint: `https://holodex.net/api/v2/channels/{channelId}` or `https://holodex.net/api/v2/users/{channelId}/live`.

### B. Audio Streamer
- Use `yt-dlp` to get the live stream URL.
- Pipe the stream to `ffmpeg` to extract audio in the required format (e.g., 16kHz mono PCM).
- Stream audio in real-time (not download-then-process).

### C. Diart Processor (Optional)
- Use [diart](https://github.com/juanmc2005/diart) to process the audio stream if enabled (`USE_DIART=true`).
- Perform VAD and speaker diarization in real time.
- Output speech segments (with timestamps and speaker labels if available).
- Reference: [Medium article on Diart + Whisper integration](https://medium.com/better-programming/color-your-captions-streamlining-live-transcriptions-with-diart-and-openais-whisper-6203350234ef)

### D. Whisper Streaming Transcriber
- Use [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for efficient local transcription.
- Feed audio (or speech segments from Diart) to Whisper.
- Get partial and final transcripts.

### E. Discord Bot
- Use `discord.py` or `nextcord` to send messages.
- Post transcripts as they are produced.
- Optionally, color or tag captions by speaker.

---

## 4. Module/Script Structure

```
yt-whisper-discord/
│
├── main.py                # Orchestrates the workflow
├── holodex_monitor.py     # Checks for live streams using Holodex API
├── audio_streamer.py      # Handles yt-dlp + ffmpeg audio extraction
├── diart_processor.py     # Handles VAD and diarization with diart (optional)
├── whisper_transcriber.py # Wraps faster-whisper
├── discord_bot.py         # Handles Discord messaging
├── .env                   # API keys, channel IDs, etc.
├── requirements.txt
└── README.md
```

---

## 5. Data Flow

1. **main.py** starts all services.
2. **holodex_monitor.py** detects a live stream.
3. **audio_streamer.py** starts streaming audio from the live video.
4. **diart_processor.py** (optional) receives audio, performs VAD/diarization, and emits speech segments.
5. **whisper_transcriber.py** transcribes each speech segment (or raw audio if Diart is disabled).
6. **discord_bot.py** posts the transcript (optionally with speaker info) to Discord.

---

## 6. Key Implementation Notes

- **diart**: Use for real-time VAD and diarization if enabled. Integrate as a streaming processor between audio extraction and transcription.
- **faster-whisper**: Use for efficient, local transcription of speech segments or raw audio.
- **yt-dlp + ffmpeg**: Use subprocess pipes to avoid saving files to disk.
- **Concurrency**: Use asyncio or threading to handle real-time streaming and Discord messaging.
- **Error Handling**: Handle stream interruptions, API errors, and rate limits gracefully.
- **Speaker Tagging**: Optionally, color or tag captions by speaker in Discord (see [Medium article](https://medium.com/better-programming/color-your-captions-streamlining-live-transcriptions-with-diart-and-openais-whisper-6203350234ef)).
- **Config**: Add `USE_DIART` to `.env` to control whether Diart is used.

---

## 7. Dependencies

- `yt-dlp`
- `ffmpeg` (system binary)
- `discord.py` or `nextcord`
- `requests` (for Holodex API)
- `diart` (optional)
- `faster-whisper`
- `torch`
- `python-dotenv`

---

## 8. Next Steps

1. **Set up .env for API keys and settings, including `USE_DIART`.**
2. **Implement Holodex live monitor.**
3. **Implement audio streaming pipeline.**
4. **Integrate Diart for VAD/diarization (optional).**
5. **Integrate faster-whisper for transcription.**
6. **Build Discord bot.**
7. **Orchestrate in main.py.**

---

## References
- [diart](https://github.com/juanmc2005/diart)
- [Medium: Color Your Captions - Streamlining Live Transcriptions with Diart and OpenAI's Whisper](https://medium.com/better-programming/color-your-captions-streamlining-live-transcriptions-with-diart-and-openais-whisper-6203350234ef)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [ufal/whisper_streaming](https://github.com/ufal/whisper_streaming)
- [Holodex API Docs](https://holodex.stoplight.io/docs/holodex/)
- [StackOverflow: Stream audio using yt-dlp in Python instead of downloading the file](https://stackoverflow.com/questions/71187954/stream-audio-using-yt-dlp-kn-python-instead-of-downloading-the-file) 