import discord
from discord.ext import commands

class InfoCog(commands.Cog):
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
    
    @commands.hybrid_command(name="info", description="View all bot commands and information")
    async def info(self, ctx):
        """Show bot information and commands"""
        
        embed = discord.Embed(
            title="🎲 Blox Fruits Gacha Bot - Commands",
            description="Complete guide to all available commands",
            color=discord.Color.blurple()
        )
        
        # Gacha Commands
        embed.add_field(
            name="🎲 **GACHA COMMANDS**",
            value="`/roll` - Roll for a fruit! (First FREE, then 50 💰)\n`/daily` - Claim daily reward (500 💰)",
            inline=False
        )
        
        # User Commands
        embed.add_field(
            name="📱 **USER COMMANDS**",
            value="`/inventory` - View your fruits\n"
                  "`/inventory @user` - View someone's fruits\n"
                  "`/profile` - View your stats\n"
                  "`/profile @user` - View someone's stats\n"
                  "`/balance` - Check your Draco Coins\n"
                  "`/balance @user` - Check someone's coins\n"
                  "`/leaderboard` - View top 10 rollers",
            inline=False
        )
        
        # Admin Commands
        embed.add_field(
            name="👑 **ADMIN COMMANDS** (Owner Only)",
            value="`/spawnfruit @user fruitname` - Spawn any fruit\n"
                  "`/addcurrency @user amount` - Add Draco Coins",
            inline=False
        )
        
        # Currency System
        embed.add_field(
            name="💰 **CURRENCY SYSTEM**",
            value="**Chat Reward:** +2 Draco Coins per message (1 min cooldown/server)\n"
                  "**First Roll:** FREE 🎁\n"
                  "**Rolls:** 50 Draco Coins each\n"
                  "**Daily:** 500 Draco Coins\n"
                  "**Roll Cooldown:** 1 hour between rolls",
            inline=False
        )
        
        # Fruits Info
        embed.add_field(
            name="🍎 **FRUIT RARITIES**",
            value="⚪ **Common** (47%) - Bomb, Spike, Chop, Spin, Smoke, Flame\n"
                  "🟢 **Uncommon** (30%) - Gum, Mushroom, Kilo, Stone, Chill, Spring\n"
                  "🔵 **Rare** (15%) - Sand, Ice, Rubber, Light, Venom, Control\n"
                  "🟣 **Epic** (7%) - Magma, Quake, Shadow, Human, Portal, String\n"
                  "🟡 **Legendary** (0.8%) - Dragon, Phoenix, Buddha, Leopard, Dough\n"
                  "🟣 **Mythic** (0.2%) - Mythic Dragon",
            inline=False
        )
        
        # Tips
        embed.add_field(
            name="💡 **TIPS**",
            value="✅ Chat in any channel to earn coins passively\n"
                  "✅ Claim daily reward for 500 coins\n"
                  "✅ First roll is free - use it wisely!\n"
                  "✅ Higher rarity = lower drop rate\n"
                  "✅ Check leaderboard to compete with friends",
            inline=False
        )
        
        embed.set_footer(text="Use the commands above to start playing! 🚀")
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(InfoCog(bot, None))
