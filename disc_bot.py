import discord
from discord.ext import commands
import json
import os
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from discord.utils import get
import datetime

XP_FILE = "xp_tracking.json"

def create_rank_card(username, avatar_url, level, xp, xp_needed):
    bg = Image.open("op_bg.png").convert("RGBA")
    draw = ImageDraw.Draw(bg)

    avatar_response = requests.get(avatar_url)
    avatar = Image.open(BytesIO(avatar_response.content)).convert("RGBA").resize((160, 160))
    mask = Image.new("L", avatar.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0) + avatar.size, fill=255)
    bg.paste(avatar, (60, 60), mask)

    username_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    level_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)

    draw.text((250, 70), f"{username}", font=username_font, fill="white")
    draw.text((250, 140), f"Level: {level}", font=level_font, fill="white")
    draw.text((250, 190), f"XP: {xp}/{xp_needed}", font=level_font, fill="white")

    bar_x = 250
    bar_y = 250
    bar_width = 400
    bar_height = 35
    fill_width = int((xp / xp_needed) * bar_width)

    draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], fill=(80, 80, 80))
    draw.rectangle([bar_x, bar_y, bar_x + fill_width, bar_y + bar_height], fill=(0, 200, 255))

    output_path = "rank_card.png"
    bg.save(output_path)
    return output_path

def load_xp():
    if not os.path.exists(XP_FILE):
        return {}
    with open(XP_FILE, "r") as f:
        return json.load(f)

def save_xp(data):
    with open(XP_FILE, "w") as f:
        json.dump(data, f, indent=4)

class DiscordBot:
    def __init__(self, token):
        self.token = token
        self.user_message_log = {}

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        self.bot = commands.Bot(command_prefix='!', intents=intents)

        self.register_commands()
        self.register_events()

    def register_commands(self):

        @self.bot.command()
        @commands.has_permissions(kick_members=True)
        async def kick(ctx, member: discord.Member, *, reason=None):
            await member.kick(reason=reason)
            await ctx.send(f"👢 {member.mention} has been kicked. Reason: {reason or 'No reason provided.'}")

        @self.bot.command()
        @commands.has_permissions(ban_members=True)
        async def ban(ctx, member: discord.Member, *, reason=None):
            await member.ban(reason=reason)
            await ctx.send(f"🔨 {member.mention} has been banned. Reason: {reason or 'No reason provided.'}")

        @self.bot.command()
        @commands.has_permissions(ban_members=True)
        async def unban(ctx, *, user_info):
            banned_users = await ctx.guild.bans()
            name, discriminator = user_info.split("#")

            for ban_entry in banned_users:
                user = ban_entry.user
                if user.name == name and user.discriminator == discriminator:
                    await ctx.guild.unban(user)
                    await ctx.send(f"♻️ Unbanned {user.name}#{user.discriminator}")
                    return
            await ctx.send("❌ User not found in ban list.")

        @self.bot.command()
        @commands.has_permissions(moderate_members=True)
        async def mute(ctx, member: discord.Member, duration: int = 10):
            duration_seconds = duration * 60
            until = discord.utils.utcnow() + datetime.timedelta(seconds=duration_seconds)
            await member.timeout(until)
            await ctx.send(f"🔇 {member.mention} has been muted for {duration} minutes.")


        @self.bot.command()
        @commands.has_permissions(moderate_members=True) 
        async def unmute(ctx, member: discord.Member):
            await member.timeout(None)
            await ctx.send(f"🔊 {member.mention} has been unmuted.")

        @self.bot.command()
        async def rank(ctx):
            user = ctx.author
            user_id = str(user.id)
            data = load_xp()

            if user_id not in data:
                await ctx.send("Nemaš XP još uvek.")
                return

            xp = data[user_id]["xp"]
            level = data[user_id]["level"]
            xp_needed = level * 100

            avatar_url = user.display_avatar.url
            username = str(user.name)

            image_path = create_rank_card(username, avatar_url, level, xp, xp_needed)
            await ctx.send(file=discord.File(image_path))

        @self.bot.command()
        async def leaderboard(ctx):
            data = load_xp()
            sorted_users = sorted(data.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)

            desc = ""

            for i, (uid, info) in enumerate(sorted_users[:10], 1):
                user = await self.bot.fetch_user(int(uid))
                desc += f"{i} {user.name} - Level {info['level']} ({info['xp']} XP)\n"

            embed = discord.Embed(title="🏆 Leaderboard", description=desc, color=discord.Color.gold())
            await ctx.send(embed=embed)

        @self.bot.command()
        async def poll(ctx, *, question):
            embed = discord.Embed(title="📊 Anketa", description=question, color=discord.Color.blue())
            message = await ctx.send(embed=embed)
            await message.add_reaction("👍")
            await message.add_reaction("👎")

        @self.bot.command()
        async def animal(ctx, *, animal_type):
            valid = {"fox", "cat", "bird", "panda", "red_panda", "racoon", "koala", "kangaroo", "whale", "dog"}
            key = animal_type.lower()
            if key not in valid:
                return await ctx.send(f"❌ Invalid type! Choose from: {', '.join(sorted(valid))}")

            url = f"https://some-random-api.com/animal/{key}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                image_url = data.get("image")
                await ctx.send(f"{image_url}")
            else:
                await ctx.send("❌ Failed to fetch image.")

    def register_events(self):
        @self.bot.event
        async def on_ready():
            print(f"✅ Logged in as {self.bot.user}")

        @self.bot.event
        async def on_message(message):
            if message.author == self.bot.user:
                return

            # Simple text responses
            if message.content == "ping":
                await message.channel.send("pong")
            elif message.content == "pong":
                await message.channel.send("ping")
            elif message.content == "ko koga voli vise":
                await message.channel.send("Mara voli Nemanju najvise ❤️")
            elif message.content == "sorry love":
                await message.channel.send("Mara te voli najvise na svetu i njoj je jako zao zato sto se ponasa kao razmazena kidara, pls forgive her ❤️")
            elif message.content == "sorry baby":
                await message.channel.send("Nemanja te voli najvise na svetu i jako mu je  zao zato sto se ponasa kao razmazena kidara, pls forgive him ❤️")
            elif message.content == "my baby 🥺":
                await message.channel.send("Mi baby srecan svetski dan devojaka, ti si moja omiljena osoba i ulepsala si mi zivot u prteklih 456 dana i pomogla si mi da unapred i poboljsam sebe. Hvala ti na svemu love youi theeeeee moost ❤️ \n 🥺")

            # Spam detection
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
                    await message.delete()

            # XP system
            if not os.path.exists(XP_FILE):
                with open(XP_FILE, "w") as f:
                    json.dump({}, f)

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

            if message.author != self.bot.user:
                leveled_up, new_level = add_xp(message.author.id, 10)
                if leveled_up:
                    await message.channel.send(f"{message.author.mention} se level upovao na **Level {new_level}**!")

            # Important: allow commands to be processed
            await self.bot.process_commands(message)

    def run(self):
        self.bot.run(self.token)
