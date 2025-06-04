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
    """Monitor a specific guild for live streams"""
    # Create or get the HolodexMonitor for this guild
    if guild_id not in monitors:
        settings = bot.get_guild_settings(guild_id)
        holodex_channel_id = settings.get("holodex_channel_id", HOLODEX_CHANNEL_ID)
        monitors[guild_id] = HolodexMonitor(holodex_channel_id)
    holodex = monitors[guild_id]
    audio_streamer = AudioStreamer()
    whisper = WhisperTranscriber()

    try:
        while True:
            # Always use the current channel_id from the monitor
            live_video_id = await holodex.get_live_video_id()
            if live_video_id:
                # Start audio streaming, transcription, and Discord posting
                # (To be implemented: stream audio, transcribe, send to Discord)
                pass
            await asyncio.sleep(POLL_INTERVAL)
    except asyncio.CancelledError:
        print(f"Monitor task for guild {guild_id} was cancelled")
        raise

async def start_guild_monitor(guild_id, bot):
    """Start monitoring for a specific guild"""
    if guild_id not in tasks:
        print(f"Starting monitor for guild {guild_id}")
        tasks[guild_id] = asyncio.create_task(monitor_guild(guild_id, bot))
    else:
        print(f"Monitor for guild {guild_id} already running")

async def stop_guild_monitor(guild_id):
    """Stop monitoring for a specific guild"""
    if guild_id in tasks:
        print(f"Stopping monitor for guild {guild_id}")
        tasks[guild_id].cancel()
        try:
            await tasks[guild_id]
        except asyncio.CancelledError:
            pass
        del tasks[guild_id]
    
    # Clean up monitor
    if guild_id in monitors:
        del monitors[guild_id]

def on_channel_update(guild_id, new_channel_id):
    """Update the HolodexMonitor for this guild when channel changes"""
    if guild_id in monitors:
        monitors[guild_id].set_channel_id(new_channel_id)
    else:
        monitors[guild_id] = HolodexMonitor(new_channel_id)
    # Optionally, you could restart the monitor task if needed

async def on_guild_join(guild_id, bot):
    """Called when bot joins a new guild - start monitoring"""
    await start_guild_monitor(guild_id, bot)

async def on_guild_remove(guild_id):
    """Called when bot leaves a guild - stop monitoring"""
    await stop_guild_monitor(guild_id)

async def main():
    discord_bot = DiscordBot(DISCORD_TOKEN)
    
    # Set up commands after creating bot instance
    setup_commands(discord_bot)
    
    # Register callbacks
    discord_bot.on_channel_update = on_channel_update
    discord_bot.on_guild_join_callback = on_guild_join
    discord_bot.on_guild_remove_callback = on_guild_remove

    # Start the Discord bot in the background
    bot_task = asyncio.create_task(discord_bot.start(discord_bot.token))

    # Wait for the bot to be ready and have guilds
    await asyncio.sleep(5)  # Placeholder: replace with proper event/wait

    # Start monitors for all existing guilds
    for guild in discord_bot.guilds:
        await start_guild_monitor(guild.id, discord_bot)

    # Keep the main task running
    await bot_task

if __name__ == "__main__":
    asyncio.run(main()) 