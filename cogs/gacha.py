import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta
from data.fruits import FRUITS, RARITY_RATES

class GachaCog(commands.Cog):
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        # Admin user IDs (add your user ID here)
        self.admin_ids = [1234567890]  # Replace with your Discord user ID
    
    def calculate_drop_rate(self):
        """Calculate which fruit to drop based on rarity rates"""
        roll = random.random() * 100
        cumulative = 0
        
        for rarity, rate in RARITY_RATES.items():
            cumulative += rate
            if roll <= cumulative:
                # Get random fruit of this rarity
                fruits_of_rarity = [f for f in FRUITS if f['rarity'] == rarity]
                return random.choice(fruits_of_rarity)
        
        # Fallback to common
        common_fruits = [f for f in FRUITS if f['rarity'] == 'Common']
        return random.choice(common_fruits)
    
    def get_rarity_color(self, rarity):
        """Get color for rarity tier"""
        colors = {
            'Common': discord.Color.greyple(),
            'Uncommon': discord.Color.green(),
            'Rare': discord.Color.blue(),
            'Epic': discord.Color.purple(),
            'Legendary': discord.Color.gold(),
            'Mythic': discord.Color.from_rgb(255, 0, 255)
        }
        return colors.get(rarity, discord.Color.greyple())
    
    @commands.hybrid_command(name="roll", description="Roll for a fruit! First roll is FREE, then 50 Draco Coins")
    async def roll(self, ctx):
        """Roll for a fruit"""
        user = await self.db.get_or_create_user(ctx.author.id, ctx.author.name)
        coins = await self.db.get_draco_coins(ctx.author.id)
        
        # Check if first roll
        is_first_roll = not await self.db.is_first_roll_done(ctx.author.id)
        roll_cost = 0 if is_first_roll else 50
        
        # Check cooldown (1 hour)
        last_roll = await self.db.get_last_roll(ctx.author.id)
        if last_roll:
            last_roll_dt = datetime.fromisoformat(last_roll)
            now = datetime.now()
            time_diff = now - last_roll_dt
            
            if time_diff < timedelta(hours=1):
                time_remaining = timedelta(hours=1) - time_diff
                minutes = int(time_remaining.total_seconds() // 60)
                seconds = int(time_remaining.total_seconds() % 60)
                
                embed = discord.Embed(
                    title="⏳ Roll on Cooldown",
                    description=f"You can roll again in {minutes}m {seconds}s",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
                return
        
        # Check currency if not first roll
        if not is_first_roll and coins < roll_cost:
            embed = discord.Embed(
                title="❌ Insufficient Draco Coins",
                description=f"You need {roll_cost} Draco Coins to roll, but you only have {coins}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Subtract coins if not first roll
        if not is_first_roll:
            await self.db.subtract_draco_coins(ctx.author.id, roll_cost)
        else:
            await self.db.set_first_roll_done(ctx.author.id)
        
        # Roll for fruit
        fruit = self.calculate_drop_rate()
        
        # Add to inventory and history
        await self.db.add_fruit_to_inventory(ctx.author.id, fruit['name'], fruit['rarity'])
        await self.db.add_roll_history(ctx.author.id, fruit['name'], fruit['rarity'])
        await self.db.set_last_roll(ctx.author.id)
        
        # Create embed with image
        roll_type = "FREE 🎁" if is_first_roll else "50 💰"
        embed = discord.Embed(
            title=f"🎲 You rolled: {fruit['name']}!",
            description=f"**Rarity:** {fruit['rarity']}\n**Description:** {fruit['description']}",
            color=self.get_rarity_color(fruit['rarity'])
        )
        embed.set_image(url=fruit.get('image', ''))
        embed.add_field(name="Drop Rate", value=f"{fruit['drop_rate']}%", inline=True)
        embed.add_field(name="Roll Cost", value=f"{roll_type}", inline=True)
        embed.add_field(name="Draco Coins Remaining", value=f"{coins - roll_cost} 💰", inline=True)
        embed.set_footer(text=f"Rolling: {ctx.author.name} | Next roll in 1 hour")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="spawnfruit", description="[ADMIN] Spawn any fruit to a user")
    async def spawnfruit(self, ctx, user: discord.User, fruit_name: str):
        """Spawn a fruit (Admin only)"""
        if ctx.author.id not in self.admin_ids:
            embed = discord.Embed(
                title="❌ Admin Only",
                description="You don't have permission to use this command",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Find the fruit
        fruit = None
        for f in FRUITS:
            if f['name'].lower() == fruit_name.lower():
                fruit = f
                break
        
        if not fruit:
            fruit_list = ", ".join([f['name'] for f in FRUITS])
            embed = discord.Embed(
                title="❌ Fruit Not Found",
                description=f"Available fruits:\n{fruit_list}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Add to inventory
        await self.db.get_or_create_user(user.id, user.name)
        await self.db.add_fruit_to_inventory(user.id, fruit['name'], fruit['rarity'])
        
        # Create confirmation embed
        embed = discord.Embed(
            title="✅ Fruit Spawned",
            description=f"Spawned **{fruit['name']}** ({fruit['rarity']}) for {user.mention}",
            color=self.get_rarity_color(fruit['rarity'])
        )
        embed.set_image(url=fruit.get('image', ''))
        embed.set_footer(text=f"Admin: {ctx.author.name}")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="addcurrency", description="[ADMIN] Add Draco Coins to a user")
    async def addcurrency(self, ctx, user: discord.User, amount: int):
        """Add Draco Coins to a user (Admin only)"""
        if ctx.author.id not in self.admin_ids:
            embed = discord.Embed(
                title="❌ Admin Only",
                description="You don't have permission to use this command",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        await self.db.get_or_create_user(user.id, user.name)
        await self.db.add_draco_coins(user.id, amount)
        
        embed = discord.Embed(
            title="✅ Draco Coins Added",
            description=f"Added **{amount}** Draco Coins to {user.mention}",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Admin: {ctx.author.name}")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="daily", description="Claim your daily reward (500 Draco Coins)")
    async def daily(self, ctx):
        """Claim daily reward"""
        await self.db.get_or_create_user(ctx.author.id, ctx.author.name)
        
        last_daily = await self.db.get_last_daily(ctx.author.id)
        
        if last_daily:
            last_daily_dt = datetime.fromisoformat(last_daily)
            now = datetime.now()
            time_diff = now - last_daily_dt
            
            if time_diff < timedelta(hours=24):
                time_remaining = timedelta(hours=24) - time_diff
                hours = int(time_remaining.total_seconds() // 3600)
                minutes = int((time_remaining.total_seconds() % 3600) // 60)
                
                embed = discord.Embed(
                    title="⏰ Daily Already Claimed",
                    description=f"Come back in {hours}h {minutes}m to claim your daily reward",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
                return
        
        # Award coins
        reward = 500
        await self.db.add_draco_coins(ctx.author.id, reward)
        await self.db.set_last_daily(ctx.author.id)
        
        embed = discord.Embed(
            title="✅ Daily Reward Claimed!",
            description=f"You received {reward} Draco Coins 💰",
            color=discord.Color.green()
        )
        embed.set_footer(text="Come back tomorrow for another reward!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GachaCog(bot, None))
