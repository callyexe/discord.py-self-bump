import os
import discord
from discord.ext import tasks
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('DISCORD_GUILD_ID'))
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

client = discord.Client(intents=intents)
#きんたま
cooldowns = {
    "dissoku up": timedelta(hours=1),
    "bump": timedelta(hours=2)
}
last_executed = {cmd: datetime.min for cmd in cooldowns}

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    execute_command.start()

@client.event
async def on_message(message: discord.Message):
    if message.guild.id != GUILD_ID or message.channel.id != CHANNEL_ID:
        return
    
    if message.content == "miaq":
        user_message = await message.channel.fetch_message(message.reference.message_id)
        payload = {
            "username": user_message.author.name,
            "display_name": user_message.author.display_name,
            "text": user_message.content,
            "avatar": user_message.author.avatar.url,
            "color": True
        }

        quote = requests.post("https://api.voids.top/quote", json=payload).json()
        await message.channel.send(quote['url'])

@tasks.loop(seconds=60)
async def execute_command():
    now = datetime.now()
    channel = client.get_channel(CHANNEL_ID)
    
    for command, cooldown in cooldowns.items():
        if now - last_executed[command] >= cooldown:
            await channel.send(f"/{command}")
            last_executed[command] = now

client.run(TOKEN)
