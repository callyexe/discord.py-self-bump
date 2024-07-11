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

# 環境変数の取得と検証
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('DISCORD_GUILD_ID')
CHANNEL_ID = os.getenv('DISCORD_CHANNEL_ID')

if not all([TOKEN, GUILD_ID, CHANNEL_ID]):
    raise ValueError("必要な環境変数が設定されていません。")

GUILD_ID = int(GUILD_ID)
CHANNEL_ID = int(CHANNEL_ID)

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

bot = commands.Bot(command_prefix='!', self_bot=True)

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
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send(f"/{command}")
            logger.info(f"Sent command: {command}")
        except Exception as e:
            logger.error(f"Error sending command {command}: {e}")
    else:
        logger.error(f"Channel not found for command: {command}")

@bot.event
async def on_message(message):
    if message.guild.id != GUILD_ID or message.channel.id != CHANNEL_ID:
        return

    if message.content.lower() == "miaq" and message.reference:
        await quote(message)

    await bot.process_commands(message)

async def quote(message):
    try:
        ref_msg = await message.channel.fetch_message(message.reference.message_id)
        
        payload = {
            "username": ref_msg.author.name,
            "display_name": ref_msg.author.display_name,
            "text": ref_msg.content,
            "avatar": str(ref_msg.author.avatar.url if ref_msg.author.avatar else None),
            "color": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.voids.top/quote", json=payload) as resp:
                if resp.status == 200:
                    quote_data = await resp.json()
                    await message.channel.send(quote_data['url'])
                else:
                    logger.error(f"Error from quote API: {resp.status}")
                    await message.channel.send("引用画像の生成に失敗しました。")
    except Exception as e:
        logger.error(f"Error in quote command: {e}")
        await message.channel.send("エラーが発生しました。")

if __name__ == "__main__":
    bot.run(TOKEN)
