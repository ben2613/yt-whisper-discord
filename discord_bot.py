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

    @bot.tree.command(name="status", description="Check the current configuration and monitoring status.")
    async def status(interaction: discord.Interaction):
        guild_id = interaction.guild_id
        settings = bot.get_guild_settings(guild_id)
        
        holodex_id = settings.get("holodex_channel_id", "Not set")
        output_id = settings.get("output_channel_id")
        output_channel = f"<#{output_id}>" if output_id else "Not set"
        
        # Check if monitoring is active (this would need to be passed from main.py)
        status_text = "✅ **Configuration Status:**\n"
        status_text += f"**Holodex Channel ID:** {holodex_id}\n"
        status_text += f"**Output Channel:** {output_channel}\n"
        
        if holodex_id != "Not set" and output_id:
            status_text += "\n🟢 **Status:** Monitoring active"
        else:
            status_text += "\n🔴 **Status:** Monitoring inactive (incomplete configuration)"
            status_text += "\n\n**To start monitoring:**"
            if holodex_id == "Not set":
                status_text += "\n• Set Holodex channel ID with `/set_monitor_channel`"
            if not output_id:
                status_text += "\n• Set output channel with `/set_output_channel`"
        
        await interaction.response.send_message(status_text, ephemeral=True) 