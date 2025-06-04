# Main orchestrator for YouTube-Whisper-Discord pipeline
# This script coordinates the Holodex monitor, audio streamer, whisper transcriber, and Discord bot

import asyncio
import os
from holodex_monitor import HolodexMonitor
from audio_streamer import AudioStreamer
from whisper_transcriber import WhisperTranscriber
from discord_bot import DiscordBot, setup_commands
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

HOLODEX_CHANNEL_ID = os.getenv("HOLODEX_CHANNEL_ID", "YOUR_HOLODEX_CHANNEL_ID")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))

# Global dicts to manage monitors and tasks per guild
monitors = {}
tasks = {}

async def monitor_guild(guild_id, bot):
    # Create or get the HolodexMonitor for this guild
    if guild_id not in monitors:
        settings = bot.get_guild_settings(guild_id)
        holodex_channel_id = settings.get("holodex_channel_id", HOLODEX_CHANNEL_ID)
        monitors[guild_id] = HolodexMonitor(holodex_channel_id)
    holodex = monitors[guild_id]
    audio_streamer = AudioStreamer()
    whisper = WhisperTranscriber()

    while True:
        # Always use the current channel_id from the monitor
        live_video_id = await holodex.get_live_video_id()
        if live_video_id:
            # Start audio streaming, transcription, and Discord posting
            # (To be implemented: stream audio, transcribe, send to Discord)
            pass
        await asyncio.sleep(POLL_INTERVAL)

def on_channel_update(guild_id, new_channel_id):
    # Update the HolodexMonitor for this guild
    if guild_id in monitors:
        monitors[guild_id].set_channel_id(new_channel_id)
    else:
        monitors[guild_id] = HolodexMonitor(new_channel_id)
    # Optionally, you could restart the monitor task if needed

async def main():
    discord_bot = DiscordBot(DISCORD_TOKEN)
    
    # Set up commands after creating bot instance
    setup_commands(discord_bot)
    
    # Register callback for channel updates
    discord_bot.on_channel_update = on_channel_update

    # Start the Discord bot in the background
    bot_task = asyncio.create_task(discord_bot.start(discord_bot.token))

    # Wait for the bot to be ready and have guilds
    await asyncio.sleep(5)  # Placeholder: replace with proper event/wait

    # For each guild, start a monitor task
    for guild in discord_bot.guilds:
        tasks[guild.id] = asyncio.create_task(monitor_guild(guild.id, discord_bot))

    await asyncio.gather(bot_task, *tasks.values())

if __name__ == "__main__":
    asyncio.run(main()) 