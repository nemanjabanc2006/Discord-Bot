import discord
from discord.ext import commands
import aiohttp
import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

API_KEY = os.getenv("WEATHER_API_KEY")  # Store your API key in .env

def create_weather_card(city, country, temperature, condition, time):

    def get_text_size(font, text):
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    def get_hours_minutes(time_str):
        # Split date and time
        time_part = time_str.split(" ")[1]  # "HH:MM" or "HH:MM:SS"
        # Get first 5 chars = "HH:MM"
        return time_part[:5]
    
    #Background done
    #bg_sunny = Image.new(mode = "RGB", size= (500, 500), color=(78, 139, 243))
    #bg_night = Image.new(mode = "RGB", size= (500, 500), color=(31, 27, 145))
    #bg_rainy = Image.new(mode = "RGB", size= (500, 500), color=(49, 48, 84))
    #bg_cloudy = Image.new(mode = "RGB", size= (500, 500), color=(130, 129, 164))

    bg_color = (78, 139, 243)  # default sunny color
    if "clear" in condition:
        bg_color = (31, 27, 145)

    bg = Image.new("RGB", (500, 500), color=bg_color)

    draw = ImageDraw.Draw(bg)

    #Emoji
    day = Image.open("images/weather/sunny.png").convert("RGBA")
    night = Image.open("images/weather/clear.png").convert("RGBA")
    #"partly cloudy": "⛅", "cloudy": "☁️", "overcast": "☁️", "mist": "🌫️", "rain": "🌧️", "snow": "❄️", "thunder": "⛈️", fog": "🌫️", "drizzle": "🌦️"

    #Text
    temp_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 150)
    place_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
    time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)


    bg_width, bg_height = bg.size

    # Write temperature
    draw.text((20, 20), f"{temperature}°", font=temp_font, fill="white")

     # Write city and country
    draw.text((20, 440), f"{city}, {country}", font=place_font, fill="white")


    if "clear" in condition:
        emoji = night.resize((240, 240))
    else:
        emoji = day.resize((240, 240))
    # Calculate center position
    #bg_width, bg_height = bg.size
    #emoji_width, emoji_height = emoji.size
    #x = (bg_width - emoji_width) // 2
    #y = (bg_height - emoji_height) // 2

    # Paste emoji centered
    bg.paste(emoji, (20, 180), emoji)

    time_width, time_height = get_text_size(time_font, get_hours_minutes(time))
    time_x = bg_width - time_width - 20
    time_y = 440
    draw.text((time_x, time_y), get_hours_minutes(time), font=time_font, fill="white")
    
    output_path = "images/weather_card.png"
    bg.save(output_path)
    return output_path



class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def weather(self, ctx, *, location: str):
        """Get weather info for a location"""
        url = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={location}&aqi=no"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return await ctx.send("❌ Couldn't fetch weather data.")
                data = await resp.json()

        # Extract data
        city = data["location"]["name"]
        country = data["location"]["country"]
        temp_c = int(data["current"]["temp_c"])
        condition = data["current"]["condition"]["text"].lower()
        local_time = data["location"]["localtime"]

        # Emoji map
        """weather_emojis = {
            "sunny": "☀️",
            "clear": "🌙",
            "partly cloudy": "⛅",
            "cloudy": "☁️",
            "overcast": "☁️",
            "mist": "🌫️",
            "rain": "🌧️",
            "snow": "❄️",
            "thunder": "⛈️",
            "fog": "🌫️",
            "drizzle": "🌦️"
        }"""

        """emoji = "🌍"  # Default
        for key, value in weather_emojis.items():
            if key in condition:
                emoji = value
                break

        embed = discord.Embed(
            title=f"Weather in {city}, {country}",
            description=f"{emoji} {condition.capitalize()}",
            color=discord.Color.green()
        )
        embed.add_field(name="🌡 Temperature", value=f"{temp_c}°C")
        embed.add_field(name="🕒 Local Time", value=local_time)

        await ctx.send(embed=embed)"""

        card_image = create_weather_card(city, country, temp_c, condition, local_time)

        await ctx.send(file=discord.File(card_image))

async def setup(bot):
    await bot.add_cog(Weather(bot))
