import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

async def load_cogs():
    await bot.load_extension("cogs.xp")
    await bot.load_extension("cogs.moderation")
    await bot.load_extension("cogs.event_listeners")
    await bot.load_extension("cogs.fun_commands")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}!")
    await load_cogs()

def run_bot():
    bot.run(TOKEN)