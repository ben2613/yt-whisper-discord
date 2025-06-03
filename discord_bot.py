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
        self.tree.add_command(self.set_monitor_channel)
        self.tree.add_command(self.set_output_channel)

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

    @app_commands.command(name="set_monitor_channel", description="Set the Holodex channel ID to monitor.")
    @app_commands.describe(channel_id="Holodex channel ID (YouTube channel ID)")
    async def set_monitor_channel(self, interaction: discord.Interaction, channel_id: str):
        guild_id = interaction.guild_id
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {}
        self.guild_settings[guild_id]["holodex_channel_id"] = channel_id
        # Notify main.py of the channel update
        if self.on_channel_update:
            self.on_channel_update(guild_id, channel_id)
        await interaction.response.send_message(f"Holodex channel ID set to `{channel_id}`.", ephemeral=True)

    @app_commands.command(name="set_output_channel", description="Set the Discord channel to send transcripts to.")
    @app_commands.describe(channel="The channel to send transcripts to")
    async def set_output_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild_id
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {}
        self.guild_settings[guild_id]["output_channel_id"] = channel.id
        await interaction.response.send_message(f"Output channel set to {channel.mention}.", ephemeral=True)

    def run_bot(self):
        super().run(self.token) 