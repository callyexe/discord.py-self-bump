import os
import asyncio
import aiohttp
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import logging
import discord

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('DISCORD_GUILD_ID'))
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

# コマンドIDを定義
commands_info = {
    "dissoku up": 828002256690610256,
    "bump": 947088344167366698
}

cooldowns = {
    "dissoku up": timedelta(hours=1),
    "bump": timedelta(hours=2)
}

last_executed = {cmd: datetime.min for cmd in cooldowns}

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name}')
    execute_command.start()

@tasks.loop(seconds=60)
async def execute_command():
    now = datetime.now()
    for command, cooldown in cooldowns.items():
        if now - last_executed[command] >= cooldown:
            last_executed[command] = now
            await send_command(command)

async def send_command(command):
    command_id = commands_info[command]
    url = "https://discord.com/api/v9/interactions"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "type": 2,
        "application_id": bot.user.id,
        "guild_id": GUILD_ID,
        "channel_id": CHANNEL_ID,
        "data": {
            "id": str(command_id),
            "name": command,
            "type": 1
        }
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                if resp.status == 200:
                    logger.info(f"Sent command: {command}")
                else:
                    logger.error(f"Error sending command {command}: {resp.status}")
    except aiohttp.ClientError as e:
        logger.error(f"HTTP request failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

@bot.event
async def on_message(message):
    if message.guild.id != GUILD_ID or message.channel.id != CHANNEL_ID:
        return

    if message.content.lower() == "miaq" and message.reference:
        try:
            ref_msg = await message.channel.fetch_message(message.reference.message_id)
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "username": ref_msg.author.name,
                    "display_name": ref_msg.author.display_name,
                    "text": ref_msg.content,
                    "avatar": str(ref_msg.author.avatar.url),
                    "color": True
                }
                try:
                    async with session.post("https://api.voids.top/quote", json=payload) as resp:
                        if resp.status == 200:
                            quote_data = await resp.json()
                            await message.channel.send(quote_data['url'])
                        else:
                            logger.error(f"Error from quote API: {resp.status}")
                except aiohttp.ClientError as e:
                    logger.error(f"HTTP request failed: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error when contacting quote API: {e}")
        except discord.NotFound:
            logger.error(f"Referenced message not found: {message.reference.message_id}")
        except discord.Forbidden:
            logger.error(f"Forbidden to fetch message: {message.reference.message_id}")
        except discord.HTTPException as e:
            logger.error(f"HTTP error occurred: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing 'miaq' command: {e}")

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)
