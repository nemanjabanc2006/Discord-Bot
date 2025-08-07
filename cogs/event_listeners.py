import discord
from discord.ext import commands
import json
import os
from datetime import datetime
import requests

XP_FILE = "data/xp_tracking.json"

def load_xp():
    with open(XP_FILE, "r") as f:
        return json.load(f)

def save_xp(data):
    with open(XP_FILE, "w") as f:
        json.dump(data, f, indent=4)

class EventListeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_message_log = {}

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} is online.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        # Fun messages
        responses = {
            "ping": "pong",
            "pong": "ping",
            "ko koga voli vise": "Mara voli Nemanju najvise ❤️",
            "sorry love": "Mara te voli najvise na svetu i njoj je jako zao zato sto se ponasa kao razmazena kidara, pls forgive her ❤️",
            "sorry baby": "Nemanja te voli najvise na svetu i jako mu je  zao zato sto se ponasa kao razmazena kidara, pls forgive him ❤️",
            "my baby 🥺": "Mi baby srecan svetski dan devojaka, ti si moja omiljena osoba i ulepsala si mi zivot u prteklih 456 dana i pomogla si mi da unapred i poboljsam sebe. Hvala ti na svemu love youi theeeeee moost ❤️ \n 🥺"
        }

        if message.content.lower() in responses:
            await message.channel.send(responses[message.content.lower()])

        # SPAM DETECTION
        user_id = message.author.id
        content = message.content.lower()

        if user_id not in self.user_message_log:
            self.user_message_log[user_id] = []

        self.user_message_log[user_id].append((content, message.created_at))
        self.user_message_log[user_id] = self.user_message_log[user_id][-5:]

        if len(self.user_message_log[user_id]) >= 3:
            last_msgs = [msg[0] for msg in self.user_message_log[user_id]]
            if len(set(last_msgs)) == 1:
                await message.channel.send(f"{message.author.mention} nemoj da spamujes!")
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass

        # XP SYSTEM
        def add_xp(user_id, amount):
            data = load_xp()

            user_id = str(user_id)
            if user_id not in data:
                data[user_id] = {"xp": 0, "level": 1}

            data[user_id]["xp"] += amount
            xp = data[user_id]["xp"]
            level = data[user_id]["level"]

            required_xp = level * 100
            leveled_up = False

            while xp >= required_xp:
                xp -= required_xp
                level += 1
                required_xp = level * 100
                leveled_up = True

            data[user_id]["xp"] = xp
            data[user_id]["level"] = level
            save_xp(data)

            return leveled_up, level

        # Give XP
        leveled_up, new_level = add_xp(message.author.id, 10)
        if leveled_up:
            await message.channel.send(f"{message.author.mention} se level upovao na **Level {new_level}**!")

async def setup(bot):  # REQUIRED for the cog to load
    await bot.add_cog(EventListeners(bot))