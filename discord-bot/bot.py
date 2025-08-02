import discord
from discord.ext import commands
import os
import json

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Load cogs
for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")

# Run bot
with open("config/config.json") as f:
    config = json.load(f)
bot.run(config["TOKEN"])
