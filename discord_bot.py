import asyncio
import discord
from discord.ext import commands
from discord import app_commands

class DiscordBot(commands.Bot):
    def __init__(self, token):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.token = token
        # {guild_id: {"holodex_channel_id": str, "output_channel_id": int}}
        self.guild_settings = {}
        self.on_channel_update = None  # Callback for channel updates
        self.on_guild_join_callback = None  # Callback for when bot joins a guild
        self.on_guild_remove_callback = None  # Callback for when bot leaves a guild
        self.on_settings_update_callback = None  # Callback when any setting is updated
        self.on_manual_start_callback = None  # Callback for manual start
        self.on_manual_stop_callback = None  # Callback for manual stop
        self.get_monitor_status_callback = None  # Callback to get current monitor status

    async def setup_hook(self):
        # Commands are auto-registered when using @bot.tree.command()
        await self.tree.sync()
        print("Slash commands synced globally")

    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild"""
        print(f"Bot joined guild: {guild.name} (ID: {guild.id})")
        if self.on_guild_join_callback:
            await self.on_guild_join_callback(guild.id, self)

    async def on_guild_remove(self, guild):
        """Called when the bot leaves a guild"""
        print(f"Bot left guild: {guild.name} (ID: {guild.id})")
        # Clean up guild settings
        if guild.id in self.guild_settings:
            del self.guild_settings[guild.id]
        if self.on_guild_remove_callback:
            await self.on_guild_remove_callback(guild.id)

    # Add error handler for slash command errors
    async def on_app_command_error(self, interaction, error):
        print(f"Slash command error: {error}")
        try:
            await interaction.response.send_message("An error occurred.", ephemeral=True)
        except:
            pass

    async def send_message(self, guild_id, message):
        channel_id = self.guild_settings.get(guild_id, {}).get("output_channel_id")
        if not channel_id:
            # No output channel set for this guild
            return
        channel = self.get_channel(channel_id)
        if channel:
            await channel.send(message)

    def get_guild_settings(self, guild_id):
        return self.guild_settings.get(guild_id, {})

    def run_bot(self):
        super().run(self.token)

# Create a function to set up commands after bot instance is created
def setup_commands(bot):
    @bot.tree.command(name="set_monitor_channel", description="Set the Holodex channel ID to monitor.")
    @app_commands.describe(channel_id="Holodex channel ID (YouTube channel ID)")
    async def set_monitor_channel(interaction: discord.Interaction, channel_id: str):
        guild_id = interaction.guild_id
        if guild_id not in bot.guild_settings:
            bot.guild_settings[guild_id] = {}
        bot.guild_settings[guild_id]["holodex_channel_id"] = channel_id
        
        # Notify main.py of the channel update
        if bot.on_channel_update:
            bot.on_channel_update(guild_id, channel_id)
        
        # Check if monitoring should start/stop
        if bot.on_settings_update_callback:
            await bot.on_settings_update_callback(guild_id, bot)
            
        await interaction.response.send_message(f"Holodex channel ID set to `{channel_id}`.", ephemeral=True)

    @bot.tree.command(name="set_output_channel", description="Set the Discord channel to send transcripts to.")
    @app_commands.describe(channel="The channel to send transcripts to")
    async def set_output_channel(interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild_id
        if guild_id not in bot.guild_settings:
            bot.guild_settings[guild_id] = {}
        bot.guild_settings[guild_id]["output_channel_id"] = channel.id
        
        # Check if monitoring should start/stop
        if bot.on_settings_update_callback:
            await bot.on_settings_update_callback(guild_id, bot)
            
        await interaction.response.send_message(f"Output channel set to {channel.mention}.", ephemeral=True)

    @bot.tree.command(name="start", description="Manually start the transcript monitoring service.")
    async def start_monitoring(interaction: discord.Interaction):
        guild_id = interaction.guild_id
        
        # Check if properly configured
        settings = bot.get_guild_settings(guild_id)
        has_holodex = bool(settings.get("holodex_channel_id"))
        has_output = bool(settings.get("output_channel_id"))
        
        if not (has_holodex and has_output):
            missing = []
            if not has_holodex:
                missing.append("Holodex channel ID (`/set_monitor_channel`)")
            if not has_output:
                missing.append("Output channel (`/set_output_channel`)")
            
            await interaction.response.send_message(
                f"❌ Cannot start monitoring. Missing configuration:\n• " + "\n• ".join(missing), 
                ephemeral=True
            )
            return
        
        if bot.on_manual_start_callback:
            success = await bot.on_manual_start_callback(guild_id, bot)
            if success:
                await interaction.response.send_message("✅ Transcript monitoring started!", ephemeral=True)
            else:
                await interaction.response.send_message("⚠️ Monitoring is already running.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Service not available.", ephemeral=True)

    @bot.tree.command(name="stop", description="Manually stop the transcript monitoring service.")
    async def stop_monitoring(interaction: discord.Interaction):
        guild_id = interaction.guild_id
        
        if bot.on_manual_stop_callback:
            success = await bot.on_manual_stop_callback(guild_id)
            if success:
                await interaction.response.send_message("⏹️ Transcript monitoring stopped.", ephemeral=True)
            else:
                await interaction.response.send_message("⚠️ Monitoring is not currently running.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Service not available.", ephemeral=True)

    @bot.tree.command(name="status", description="Check the current configuration and monitoring status.")
    async def status(interaction: discord.Interaction):
        guild_id = interaction.guild_id
        settings = bot.get_guild_settings(guild_id)
        
        holodex_id = settings.get("holodex_channel_id", "Not set")
        output_id = settings.get("output_channel_id")
        output_channel = f"<#{output_id}>" if output_id else "Not set"
        
        # Get current monitoring status
        is_monitoring = False
        if bot.get_monitor_status_callback:
            is_monitoring = bot.get_monitor_status_callback(guild_id)
        
        status_text = "📊 **Bot Status:**\n"
        status_text += f"**Holodex Channel ID:** {holodex_id}\n"
        status_text += f"**Output Channel:** {output_channel}\n\n"
        
        # Configuration status
        config_complete = holodex_id != "Not set" and output_id
        if config_complete:
            status_text += "✅ **Configuration:** Complete\n"
        else:
            status_text += "❌ **Configuration:** Incomplete\n"
        
        # Monitoring status
        if is_monitoring:
            status_text += "🟢 **Monitoring:** Active\n"
        else:
            status_text += "🔴 **Monitoring:** Inactive\n"
        
        # Instructions
        if not config_complete:
            status_text += "\n**⚙️ Setup Required:**"
            if holodex_id == "Not set":
                status_text += "\n• Set Holodex channel ID with `/set_monitor_channel`"
            if not output_id:
                status_text += "\n• Set output channel with `/set_output_channel`"
        elif not is_monitoring:
            status_text += "\n**🚀 Ready to start:** Use `/start` to begin monitoring"
        else:
            status_text += "\n**⏹️ Manual control:** Use `/stop` to pause monitoring"
        
        await interaction.response.send_message(status_text, ephemeral=True) 