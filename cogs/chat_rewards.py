import discord
from discord.ext import commands
from datetime import datetime, timedelta

class ChatRewardsCog(commands.Cog):
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.CHAT_REWARD_COOLDOWN = timedelta(minutes=1)  # Can earn once per minute per server
        self.CHAT_REWARD_AMOUNT = 2  # Draco coins per message
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Reward users for chatting"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Ignore DMs
        if not message.guild:
            return
        
        # Create/get user
        await self.db.get_or_create_user(message.author.id, message.author.name)
        
        # Check last reward time in this server
        last_reward = await self.db.get_last_chat_reward(message.author.id, message.guild.id)
        
        if last_reward:
            last_reward_dt = datetime.fromisoformat(last_reward)
            now = datetime.now()
            time_diff = now - last_reward_dt
            
            # If cooldown not expired, don't give reward
            if time_diff < self.CHAT_REWARD_COOLDOWN:
                return
        
        # Give reward
        await self.db.add_draco_coins(message.author.id, self.CHAT_REWARD_AMOUNT)
        await self.db.add_chat_reward(message.author.id, message.guild.id)
        
        # Send reward notification (optional - comment out if spam)
        # await message.reply(f"💰 +{self.CHAT_REWARD_AMOUNT} Draco Coins!", delete_after=3)
    
    @commands.hybrid_command(name="balance", description="Check your Draco Coins balance")
    async def balance(self, ctx, user: discord.User = None):
        """Check balance"""
        if user is None:
            user = ctx.author
        
        await self.db.get_or_create_user(user.id, user.name)
        coins = await self.db.get_draco_coins(user.id)
        
        embed = discord.Embed(
            title=f"💰 {user.name}'s Balance",
            description=f"**Draco Coins:** {coins}",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ChatRewardsCog(bot, None))
