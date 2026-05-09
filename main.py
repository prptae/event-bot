import sqlite3
import uuid
from myserver import server_on
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

conn = sqlite3.connect("events.db")

cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    date_time TEXT,
    channel_id INTEGER,
    repeat_type TEXT,
    max_players INTEGER
)
""")

conn.commit()


class EventView(discord.ui.View):
    def __init__(self, max_players):
        super().__init__(timeout=None)

        self.accepted = []
        self.max_players = max_players

    def create_embed(self, title, description, time_text):

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📅 Time",
            value=f"{time_text}\n\u200b",
            inline=False
        )

        accepted_text = "\n".join(
            f"> {user}" for user in self.accepted
        ) if self.accepted else "-"

        embed.add_field(
            name=f"✅ Accepted ({len(self.accepted)}/{self.max_players})",
            value=accepted_text,
            inline=False
        )

        return embed

    @discord.ui.button(
        label="✅ Accept",
        style=discord.ButtonStyle.green,
        custom_id="accept_button"
    )

    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):

        user = interaction.user.display_name

        if user not in self.accepted:
        
            if len(self.accepted) >= self.max_players:
        
                await interaction.response.send_message(
                    "❌ Event is full",
                    ephemeral=True
                )
                return
        
            self.accepted.append(user)

        embed = interaction.message.embeds[0]

        new_embed = discord.Embed.from_dict(embed.to_dict())

        accepted_text = "\n".join(
            f"> {user}" for user in self.accepted
        )

        new_embed.set_field_at(
            1,
            name=f"✅ Accepted ({len(self.accepted)}/{self.max_players})",
            value=accepted_text,
            inline=False
        )

        await interaction.response.edit_message(
            embed=new_embed,
            view=self
        )

    @discord.ui.button(
        label="❌ Decline",
        style=discord.ButtonStyle.red,
        custom_id="decline_button"
    )

    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):

        user = interaction.user.display_name

        if user in self.accepted:
            self.accepted.remove(user)

        embed = interaction.message.embeds[0]

        new_embed = discord.Embed.from_dict(embed.to_dict())

        accepted_text = "\n".join(
            f"> {user}" for user in self.accepted
        ) if self.accepted else "-"

        new_embed.set_field_at(
            1,
            name=f"✅ Accepted ({len(self.accepted)}/{self.max_players})",
            value=accepted_text,
            inline=False
        )

        await interaction.response.edit_message(
            embed=new_embed,
            view=self
        )









async def send_event(
    channel,
    title,
    description,
    discord_timestamp,
    max_players,
    event_id,
    repeat
):

    view = EventView(max_players)

    embed = view.create_embed(
        title,
        description,
        discord_timestamp
    )

    await channel.send(
        embed=embed,
        view=view
    )

    if repeat == "none":

        cursor.execute(
            "DELETE FROM events WHERE id = ?",
            (event_id,)
        )

        conn.commit()



@bot.tree.command(name="event", description="Schedule an event")
async def event(
    interaction: discord.Interaction,
    title: str,
    description: str,
    date_time: str,
    channel: discord.TextChannel,
    repeat: str = "none",
    max_players: int = 10
):

    dt = datetime.strptime(date_time, "%Y-%m-%d %H:%M")

    dt = dt.replace(tzinfo=ZoneInfo("Asia/Bangkok"))

    discord_timestamp = f"<t:{int(dt.timestamp())}:F>"
    event_id = str(uuid.uuid4())

    cursor.execute("""
    INSERT OR REPLACE INTO events
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        event_id,
        title,
        description,
        date_time,
        channel.id,
        repeat,
        max_players
    ))

    conn.commit()


    if repeat == "minute":

        scheduler.add_job(
            send_event,
            "interval",
            minutes=1,
            next_run_time=dt,
            id=event_id,
            replace_existing=True,
            args=[
                channel,
                title,
                description,
                discord_timestamp,
                max_players,
                event_id,
                repeat
            ]       
        )

    elif repeat == "daily":

        scheduler.add_job(
            send_event,
            "interval",
            days=1,
            next_run_time=dt,
            id=event_id,
            replace_existing=True,
            args=[
                channel,
                title,
                description,
                discord_timestamp,
                max_players,
                event_id,
                repeat
            ]       
        )

    elif repeat == "weekly":

        scheduler.add_job(
            send_event,
            "interval",
            weeks=1,
            next_run_time=dt,
            id=event_id,
            replace_existing=True,
            args=[
                channel,
                title,
                description,
                discord_timestamp,
                max_players,
                event_id,
                repeat
            ]       
        )

    elif repeat == "monthly":

        scheduler.add_job(
            send_event,
            "interval",
            days=30,
            next_run_time=dt,
            id=event_id,
            replace_existing=True,
            args=[
                channel,
                title,
                description,
                discord_timestamp,
                max_players,
                event_id,
                repeat
            ]       
        )

    else:

        scheduler.add_job(
            send_event,
            "date",
            run_date=dt,
            id=event_id,
            replace_existing=True,
            args=[
                channel,
                title,
                description,
                discord_timestamp,
                max_players,
                event_id,
                repeat
            ]
        )

    await interaction.response.send_message(
        f"✅ Event scheduled for {discord_timestamp}",
        ephemeral=True
    )

@bot.tree.command(name="list_events", description="List all events")
async def list_events(interaction: discord.Interaction):

    cursor.execute("SELECT * FROM events")

    events = cursor.fetchall()

    if not events:

        await interaction.response.send_message(
            "❌ No events found",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="📅 Scheduled Events",
        color=discord.Color.blue()
    )

    for event in events:

        event_id = event[0]
        title = event[1]
        description = event[2]
        date_time = event[3]
        repeat = event[5]
        max_players = event[6]

        embed.add_field(
            name=title,
            value=(
                f"🆔 `{event_id}`\n"
                f"📅 {date_time}\n"
                f"🔁 {repeat}\n"
                f"👥 {max_players}"
            ),
            inline=False
        )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )









@bot.tree.command(name="cancel_event", description="Cancel an event")
async def cancel_event(
    interaction: discord.Interaction,
    event_id: str
):

    try:

        scheduler.remove_job(event_id)

        cursor.execute(
            "DELETE FROM events WHERE id = ?",
            (event_id,)
        )

        conn.commit()

        await interaction.response.send_message(
            f"🗑️ Cancelled event: {event_id}",
            ephemeral=True
        )

    except:

        await interaction.response.send_message(
            "❌ Event not found",
            ephemeral=True
        )

async def recover_events():

    cursor.execute("SELECT * FROM events")

    events = cursor.fetchall()

    for event in events:

        event_id = event[0]
        title = event[1]
        description = event[2]
        date_time = event[3]
        channel_id = event[4]
        repeat = event[5]
        max_players = event[6]

        dt = datetime.strptime(date_time, "%Y-%m-%d %H:%M")

        dt = dt.replace(tzinfo=ZoneInfo("Asia/Bangkok"))

        discord_timestamp = f"<t:{int(dt.timestamp())}:F>"

        channel = bot.get_channel(channel_id)

        if channel is None:
            continue

        if repeat == "minute":

            scheduler.add_job(
                send_event,
                "interval",
                minutes=1,
                next_run_time=dt,
                id=event_id,
                replace_existing=True,
                args=[
                    channel,
                    title,
                    description,
                    discord_timestamp,
                    max_players,
                    event_id,
                    repeat
                ]
            )

        elif repeat == "daily":

            scheduler.add_job(
                send_event,
                "interval",
                days=1,
                next_run_time=dt,
                id=event_id,
                replace_existing=True,
                args=[
                    channel,
                    title,
                    description,
                    discord_timestamp,
                    max_players,
                    event_id,
                    repeat
                ]
            )

        elif repeat == "weekly":

            scheduler.add_job(
                send_event,
                "interval",
                weeks=1,
                next_run_time=dt,
                id=event_id,
                replace_existing=True,
                args=[
                    channel,
                    title,
                    description,
                    discord_timestamp,
                    max_players,
                    event_id,
                    repeat
                ]
            )

        elif repeat == "monthly":

            scheduler.add_job(
                send_event,
                "interval",
                days=30,
                next_run_time=dt,
                id=event_id,
                replace_existing=True,
                args=[
                    channel,
                    title,
                    description,
                    discord_timestamp,
                    max_players,
                    event_id,
                    repeat
                ]
            )



@bot.event
async def on_ready():

    if not scheduler.running:
        scheduler.start()

    scheduler.remove_all_jobs()

    bot.add_view(EventView(999))

    await recover_events()

    await bot.tree.sync()

    print(f"Logged in as {bot.user}")


server_on()

bot.run(TOKEN)
