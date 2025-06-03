# YouTube-Whisper-Discord Bot

## Disclaimer
- The code supports multiple Discord servers, but running live transcription (Whisper) for multiple servers on one host is not practical.
- Each transcription session is resource-intensive.
- No resource isolation per server.
- **Recommended:** Each Discord server should host its own bot instance.

## Overview
- Monitors a YouTube channel (via Holodex API).
- Streams live audio, transcribes with Whisper, posts transcript to Discord.
- Configuration via Discord slash commands and environment variables.

## Setup
1. Copy `.env.example` to `.env` and fill in your values.
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Run:
   ```sh
   python main.py
   ```

## Usage
- Use `/set_monitor_channel <holodex_channel_id>` to set the YouTube channel.
- Use `/set_output_channel <#channel>` to set the Discord output channel.

## Deployment Note
- For reliable operation, deploy a separate bot instance per Discord server.

## License
MIT 