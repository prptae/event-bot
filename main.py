import discord
from discord.ext import commands
import os
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)

class EventView(discord.ui.View):
    def __init__(self, title, description, time_text):
        super().__init__(timeout=None)

        self.title = title
        self.description = description
        self.time_text = time_text

        self.accepted = []

    def create_embed(self):
        embed = discord.Embed(
            title=self.title,
            description=self.description,
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📅 Time",
            value=self.time_text,
            inline=False
        )

        accepted_text = "\n".join(self.accepted) if self.accepted else "-"

        embed.add_field(
            name=f"✅ Accepted ({len(self.accepted)})",
            value=accepted_text,
            inline=False
        )

        return embed

    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):

        user = interaction.user.display_name

        if user not in self.accepted:
            self.accepted.append(user)

        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self
        )

    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):

        user = interaction.user.display_name

        if user in self.accepted:
            self.accepted.remove(user)

        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self
        )

@bot.tree.command(name="event", description="Create an event")
async def event(
    interaction: discord.Interaction,
    title: str,
    description: str,
    date_time: str
):

    dt = datetime.strptime(date_time, "%Y-%m-%d %H:%M")
    
    dt = dt.replace(tzinfo=ZoneInfo("Asia/Bangkok"))

    discord_timestamp = f"<t:{int(dt.timestamp())}:F>"
    
    view = EventView(title, description, discord_timestamp)

    await interaction.response.send_message(
        embed=view.create_embed(),
        view=view
    )

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
