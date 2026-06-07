import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
from cogs.gacha import GachaCog
from cogs.chat_rewards import ChatRewardsCog
from cogs.inventory import InventoryCog
from cogs.profile import ProfileCog
from cogs.info import InfoCog
from database import Database

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
db = Database()

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    await db.init_db()
    print("Database initialized")
    await sync_commands()

async def sync_commands():
    try:
        await bot.tree.sync()
        print("Slash commands synced")
    except Exception as e:
        print(f"Error syncing commands: {e}")

async def load_cogs():
    cogs = [
        GachaCog(bot, db),
        ChatRewardsCog(bot, db),
        InventoryCog(bot, db),
        ProfileCog(bot, db),
        InfoCog(bot, db),
    ]
    
    for cog in cogs:
        await bot.add_cog(cog)
        print(f"Loaded {cog.__class__.__name__}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())
