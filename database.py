import sqlite3
import aiosqlite
import os
from datetime import datetime

class Database:
    def __init__(self, db_path="gacha_bot.db"):
        self.db_path = db_path
        self.conn = None
    
    async def init_db(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    draco_coins INTEGER DEFAULT 0,
                    total_rolls INTEGER DEFAULT 0,
                    total_spent INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_daily TIMESTAMP,
                    last_roll TIMESTAMP,
                    first_roll_done INTEGER DEFAULT 0
                );
                
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    fruit_name TEXT,
                    rarity TEXT,
                    obtained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );
                
                CREATE TABLE IF NOT EXISTS roll_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    fruit_name TEXT,
                    rarity TEXT,
                    rolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );
                
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user INTEGER,
                    to_user INTEGER,
                    from_fruit TEXT,
                    to_fruit TEXT,
                    trade_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(from_user) REFERENCES users(user_id),
                    FOREIGN KEY(to_user) REFERENCES users(user_id)
                );
                
                CREATE TABLE IF NOT EXISTS chat_rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    server_id INTEGER,
                    coins_earned INTEGER DEFAULT 2,
                    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                );
            """)
            await db.commit()
    
    async def get_or_create_user(self, user_id, username):
        """Get or create a user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )
            await db.commit()
            
            cursor = await db.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            return await cursor.fetchone()
    
    async def add_draco_coins(self, user_id, amount):
        """Add draco coins to user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET draco_coins = draco_coins + ? WHERE user_id = ?",
                (amount, user_id)
            )
            await db.commit()
    
    async def subtract_draco_coins(self, user_id, amount):
        """Subtract draco coins from user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET draco_coins = draco_coins - ? WHERE user_id = ?",
                (amount, user_id)
            )
            await db.commit()
    
    async def get_draco_coins(self, user_id):
        """Get user's draco coins"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT draco_coins FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def add_chat_reward(self, user_id, server_id):
        """Record chat reward earned"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO chat_rewards (user_id, server_id) VALUES (?, ?)",
                (user_id, server_id)
            )
            await db.commit()
    
    async def get_last_chat_reward(self, user_id, server_id):
        """Get last chat reward time in a server"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT earned_at FROM chat_rewards WHERE user_id = ? AND server_id = ? ORDER BY earned_at DESC LIMIT 1",
                (user_id, server_id)
            )
            result = await cursor.fetchone()
            return result[0] if result else None
    
    async def add_fruit_to_inventory(self, user_id, fruit_name, rarity):
        """Add fruit to user's inventory"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO inventory (user_id, fruit_name, rarity) VALUES (?, ?, ?)",
                (user_id, fruit_name, rarity)
            )
            await db.commit()
    
    async def get_inventory(self, user_id):
        """Get user's inventory"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT fruit_name, rarity, COUNT(*) as count FROM inventory WHERE user_id = ? GROUP BY fruit_name ORDER BY rarity DESC",
                (user_id,)
            )
            return await cursor.fetchall()
    
    async def add_roll_history(self, user_id, fruit_name, rarity):
        """Record roll in history"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO roll_history (user_id, fruit_name, rarity) VALUES (?, ?, ?)",
                (user_id, fruit_name, rarity)
            )
            await db.commit()
    
    async def get_user_stats(self, user_id):
        """Get user statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT 
                    (SELECT COUNT(*) FROM roll_history WHERE user_id = ?) as total_rolls,
                    (SELECT COUNT(DISTINCT fruit_name) FROM inventory WHERE user_id = ?) as unique_fruits,
                    (SELECT COUNT(*) FROM inventory WHERE user_id = ?) as total_fruits
                """,
                (user_id, user_id, user_id)
            )
            return await cursor.fetchone()
    
    async def get_leaderboard(self, limit=10):
        """Get top users by total rolls"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT user_id, username, COUNT(*) as rolls FROM roll_history 
                   GROUP BY user_id ORDER BY rolls DESC LIMIT ?""",
                (limit,)
            )
            return await cursor.fetchall()
    
    async def set_last_daily(self, user_id):
        """Set last daily claim time"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET last_daily = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()
    
    async def get_last_daily(self, user_id):
        """Get last daily claim time"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT last_daily FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result else None
    
    async def set_last_roll(self, user_id):
        """Set last roll time"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET last_roll = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()
    
    async def get_last_roll(self, user_id):
        """Get last roll time"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT last_roll FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result else None
    
    async def is_first_roll_done(self, user_id):
        """Check if user has done their first free roll"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT first_roll_done FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def set_first_roll_done(self, user_id):
        """Mark first roll as completed"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET first_roll_done = 1 WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()
