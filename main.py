# Main orchestrator for YouTube-Whisper-Discord pipeline
# This script coordinates the Holodex monitor, audio streamer, whisper transcriber, and Discord bot

import asyncio
import os
from holodex_monitor import HolodexMonitor
from audio_streamer import AudioStreamer
from whisper_transcriber import WhisperTranscriber
from discord_bot import DiscordBot, setup_commands
from dotenv import load_dotenv
from typing import Dict

# Load environment variables from .env file
load_dotenv()

HOLODEX_CHANNEL_ID = os.getenv("HOLODEX_CHANNEL_ID", "YOUR_HOLODEX_CHANNEL_ID")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))

# Global dicts to manage monitors and tasks per guild
monitors: Dict[int, HolodexMonitor] = {}
tasks: Dict[int, asyncio.Task] = {}
manually_stopped: Dict[int, bool] = {}  # Track which guilds have been manually stopped

def is_guild_configured(bot, guild_id):
    """Check if guild has both holodex_channel_id and output_channel_id configured"""
    settings = bot.get_guild_settings(guild_id)
    has_holodex_channel = bool(settings.get("holodex_channel_id"))
    has_output_channel = bool(settings.get("output_channel_id"))
    
    print(f"Guild {guild_id} config check - Holodex: {has_holodex_channel}, Output: {has_output_channel}")
    return has_holodex_channel and has_output_channel

def is_monitoring_active(guild_id):
    """Check if monitoring is currently active for a guild"""
    return guild_id in tasks and not tasks[guild_id].done()

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

async def start_guild_monitor(guild_id, bot, force=False):
    """Start monitoring for a specific guild if properly configured and not manually stopped"""
    if not is_guild_configured(bot, guild_id):
        print(f"Guild {guild_id} not fully configured - skipping monitor start")
        return False
    
    # Check if manually stopped (unless forced)
    if not force and manually_stopped.get(guild_id, False):
        print(f"Guild {guild_id} manually stopped - skipping auto-start")
        return False
    
    if guild_id not in tasks or tasks[guild_id].done():
        print(f"Starting monitor for guild {guild_id}")
        tasks[guild_id] = asyncio.create_task(monitor_guild(guild_id, bot))
        manually_stopped[guild_id] = False  # Clear manual stop flag
        return True
    else:
        print(f"Monitor for guild {guild_id} already running")
        return False

async def stop_guild_monitor(guild_id, manual=False):
    """Stop monitoring for a specific guild"""
    if guild_id in tasks and not tasks[guild_id].done():
        print(f"Stopping monitor for guild {guild_id}" + (" (manual)" if manual else ""))
        tasks[guild_id].cancel()
        try:
            await tasks[guild_id]
        except asyncio.CancelledError:
            pass
        
        if manual:
            manually_stopped[guild_id] = True
        
        return True
    else:
        print(f"Monitor for guild {guild_id} not running")
        return False

async def check_and_start_monitor(guild_id, bot):
    """Check if guild is configured and start/stop monitor accordingly (respects manual stop)"""
    if is_guild_configured(bot, guild_id):
        # If not already running and not manually stopped, start it
        if guild_id not in tasks or tasks[guild_id].done():
            if not manually_stopped.get(guild_id, False):
                started = await start_guild_monitor(guild_id, bot)
                if started:
                    print(f"✅ Monitor started for guild {guild_id} - configuration complete!")
    else:
        # If running but no longer configured, stop it
        if guild_id in tasks and not tasks[guild_id].done():
            await stop_guild_monitor(guild_id)
            print(f"⚠️ Monitor stopped for guild {guild_id} - configuration incomplete")

def on_channel_update(guild_id, new_channel_id):
    """Update the HolodexMonitor for this guild when channel changes"""
    if guild_id in monitors:
        monitors[guild_id].set_channel_id(new_channel_id)
    else:
        monitors[guild_id] = HolodexMonitor(new_channel_id)

async def on_guild_join(guild_id, bot):
    """Called when bot joins a new guild - start monitoring if configured"""
    await start_guild_monitor(guild_id, bot)

async def on_guild_remove(guild_id):
    """Called when bot leaves a guild - stop monitoring and cleanup"""
    await stop_guild_monitor(guild_id)
    # Clean up manual stop tracking
    if guild_id in manually_stopped:
        del manually_stopped[guild_id]
    # Clean up monitor
    if guild_id in monitors:
        del monitors[guild_id]

async def on_settings_update(guild_id, bot):
    """Called when guild settings are updated - check if monitoring should start/stop"""
    await check_and_start_monitor(guild_id, bot)

async def on_manual_start(guild_id, bot):
    """Handle manual start command"""
    if not is_guild_configured(bot, guild_id):
        return False
    
    return await start_guild_monitor(guild_id, bot, force=True)

async def on_manual_stop(guild_id):
    """Handle manual stop command"""
    return await stop_guild_monitor(guild_id, manual=True)

def get_monitor_status(guild_id):
    """Get current monitoring status for a guild"""
    return is_monitoring_active(guild_id)

async def main():
    discord_bot = DiscordBot(DISCORD_TOKEN)
    
    # Set up commands after creating bot instance
    setup_commands(discord_bot)
    
    # Register callbacks
    discord_bot.on_channel_update = on_channel_update
    discord_bot.on_guild_join_callback = on_guild_join
    discord_bot.on_guild_remove_callback = on_guild_remove
    discord_bot.on_settings_update_callback = on_settings_update
    discord_bot.on_manual_start_callback = on_manual_start
    discord_bot.on_manual_stop_callback = on_manual_stop
    discord_bot.get_monitor_status_callback = get_monitor_status

    # Start the Discord bot in the background
    bot_task = asyncio.create_task(discord_bot.start(discord_bot.token))

    # Wait for the bot to be ready and have guilds
    await asyncio.sleep(5)  # Placeholder: replace with proper event/wait

    # Start monitors for all existing guilds (only if properly configured)
    for guild in discord_bot.guilds:
        await start_guild_monitor(guild.id, discord_bot)

    # Keep the main task running
    await bot_task

if __name__ == "__main__":
    asyncio.run(main()) 