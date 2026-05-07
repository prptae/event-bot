import discord
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

class SignupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.players = []

    @discord.ui.button(label="✅ Join", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user.name

        if user not in self.players:
            self.players.append(user)

        await interaction.response.edit_message(
            content=f"Players ({len(self.players)}):\n" + "\n".join(self.players),
            view=self
        )

    @discord.ui.button(label="❌ Leave", style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user.name

        if user in self.players:
            self.players.remove(user)

        await interaction.response.edit_message(
            content=f"Players ({len(self.players)}):\n" + "\n".join(self.players),
            view=self
        )

@bot.command()
async def event(ctx):
    await ctx.send(
        "Players (0):",
        view=SignupView()
    )

bot.run(TOKEN)
