import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import os
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)

scheduler = AsyncIOScheduler(timezone="Asia/Bangkok")

class EventView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.accepted = []

    def create_embed(self, title, description, time_text):

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📅 Time",
            value=time_text,
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

        embed = interaction.message.embeds[0]

        new_embed = discord.Embed.from_dict(embed.to_dict())

        accepted_text = "\n".join(self.accepted)

        new_embed.set_field_at(
            1,
            name=f"✅ Accepted ({len(self.accepted)})",
            value=accepted_text,
            inline=False
        )

        await interaction.response.edit_message(
            embed=new_embed,
            view=self
        )

async def send_event(channel, title, description, discord_timestamp):

    view = EventView()

    embed = view.create_embed(
        title,
        description,
        discord_timestamp
    )

    await channel.send(
        embed=embed,
        view=view
    )

@bot.tree.command(name="event", description="Schedule an event")
async def event(
    interaction: discord.Interaction,
    title: str,
    description: str,
    date_time: str,
    repeat: bool = False
):

    dt = datetime.strptime(date_time, "%Y-%m-%d %H:%M")
    dt = dt.replace(tzinfo=ZoneInfo("Asia/Bangkok"))

    discord_timestamp = f"<t:{int(dt.timestamp())}:F>"

    channel = interaction.channel

    if repeat:

        scheduler.add_job(
            send_event,
            "interval",
            weeks=1,
            next_run_time=dt,
            args=[
                channel,
                title,
                description,
                discord_timestamp
            ]
        )

    else:

        scheduler.add_job(
            send_event,
            "date",
            run_date=dt,
            args=[
                channel,
                title,
                description,
                discord_timestamp
            ]
        )

    await interaction.response.send_message(
        f"✅ Event scheduled for {discord_timestamp}",
        ephemeral=True
    )

@bot.event
async def on_ready():

    scheduler.start()

    await bot.tree.sync()

    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
