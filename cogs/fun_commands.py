import discord
from discord.ext import commands
import requests

class FunCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def animal(self, ctx, *, animal_type):
        valid = {"fox", "cat", "bird", "panda", "red_panda", "racoon", "koala", "kangaroo", "whale", "dog"}
        key = animal_type.lower()
        if key not in valid:
            return await ctx.send(f"❌ Invalid type! Choose from: {', '.join(sorted(valid))}")

        url = f"https://some-random-api.com/animal/{key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            image_url = data.get("image")
            await ctx.send(image_url)
        else:
            await ctx.send("❌ Failed to fetch image.")

    @commands.command()
    async def poll(ctx, *, question):
            embed = discord.Embed(title="📊 Anketa", description=question, color=discord.Color.blue())
            message = await ctx.send(embed=embed)
            await message.add_reaction("👍")
            await message.add_reaction("👎")

async def setup(bot):
    await bot.add_cog(FunCommands(bot))