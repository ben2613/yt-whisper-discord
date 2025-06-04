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

    async def setup_hook(self):
        # Commands are auto-registered when using @bot.tree.command()
        await self.tree.sync()
        print("Slash commands synced globally")

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
        await interaction.response.send_message(f"Holodex channel ID set to `{channel_id}`.", ephemeral=True)

    @bot.tree.command(name="set_output_channel", description="Set the Discord channel to send transcripts to.")
    @app_commands.describe(channel="The channel to send transcripts to")
    async def set_output_channel(interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild_id
        if guild_id not in bot.guild_settings:
            bot.guild_settings[guild_id] = {}
        bot.guild_settings[guild_id]["output_channel_id"] = channel.id
        await interaction.response.send_message(f"Output channel set to {channel.mention}.", ephemeral=True) 