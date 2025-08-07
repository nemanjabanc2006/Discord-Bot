import discord
from discord.ext import commands
import json
import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests

XP_FILE = "data/xp_tracking.json"

def create_rank_card(username, avatar_url, level, xp, xp_needed):
    bg = Image.open("images/op_bg.png").convert("RGBA")
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
        os.makedirs(os.path.dirname(XP_FILE), exist_ok=True)  # Make sure folder exists
        with open(XP_FILE, "w") as f:
            json.dump({}, f)
    with open(XP_FILE, "r") as f:
        return json.load(f)

def save_xp(data):
    with open(XP_FILE, "w") as f:
        json.dump(data, f, indent=4)

class XP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_data = load_xp()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        self.xp_data.setdefault(user_id, {"xp": 0, "level": 1})
        self.xp_data[user_id]["xp"] += 10

        xp = self.xp_data[user_id]["xp"]
        level = self.xp_data[user_id]["level"]
        if xp >= level * 100:
            self.xp_data[user_id]["level"] += 1
            self.xp_data[user_id]["xp"] = xp - (level * 100)  # subtract XP needed to level up
            await message.channel.send(f"🎉 {message.author.mention} leveled up to {level + 1}!")

        save_xp(self.xp_data)

    @commands.command()
    async def rank(self, ctx):
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
        
    @commands.command()
    async def leaderboard(self, ctx):
        data = load_xp()
        sorted_users = sorted(data.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)

        desc = ""
        for i, (uid, info) in enumerate(sorted_users[:10], 1):
            user = await self.bot.fetch_user(int(uid))
            desc += f"{i}. {user.name} - Level {info['level']} ({info['xp']} XP)\n"

        embed = discord.Embed(title="🏆 Leaderboard", description=desc, color=discord.Color.gold())
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(XP(bot))
