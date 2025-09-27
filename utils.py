import discord
from discord.ext import commands
import re
from typing import Optional, Union, List, Dict, Any
from datetime import datetime
import aiosqlite
from database import DatabaseFunctions
from emoji_config import AvonEmoji

class AvonUtils:
    """Utility class matching TypeScript version exactly"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseFunctions()
        self.emoji = AvonEmoji()
    
    def embed(self, color: int = 0xff0000) -> discord.Embed:
        """Create basic embed"""
        return discord.Embed(color=color)
    
    def success_embed(self) -> discord.Embed:
        """Create success embed"""
        return discord.Embed(color=0x33ff00)
    
    def error_embed(self) -> discord.Embed:
        """Create error embed"""
        return discord.Embed(color=0xff0e00)
    
    async def premium_embed(self, guild_id: str) -> discord.Embed:
        """Create premium embed with custom color if premium"""
        if not await self.check_server_prem(guild_id) and not await self.check_server_prem_status(guild_id):
            await self.db.remove_hex(guild_id)
            return discord.Embed(color=0xff0000)
        
        try:
            hex_code = await self.db.get_hex(guild_id)
            if hex_code:
                return discord.Embed(color=int(hex_code.replace("#", ""), 16))
            else:
                return discord.Embed(color=0xff0000)
        except:
            await self.db.remove_hex(guild_id)
            return discord.Embed(color=0xff0000)
    
    async def check_user_prem(self, user_id: str) -> bool:
        """Check if user has premium"""
        return await self.db.get_user_premium_status(user_id)
    
    async def check_server_prem_status(self, guild_id: str) -> bool:
        """Check server premium status"""
        return await self.db.get_server_premium_status(guild_id)
    
    async def check_server_prem(self, guild_id: str) -> bool:
        """Check if server has premium"""
        return await self.db.get_server_premium_status(guild_id)
    
    def button(self, style: int, custom_id: str, label: str = None, emoji: str = None, url: str = None) -> discord.ui.Button:
        """Create button matching TypeScript structure"""
        if url:
            button = discord.ui.Button(style=discord.ButtonStyle.link, url=url)
        else:
            button = discord.ui.Button(style=discord.ButtonStyle(style), custom_id=custom_id)
        
        if label:
            button.label = label
        if emoji:
            try:
                button.emoji = emoji
            except:
                pass
        
        return button
    
    def menu_option(self, label: str, description: str, value: str, emoji: str = None) -> discord.SelectOption:
        """Create select menu option"""
        option = discord.SelectOption(
            label=label,
            description=description,
            value=value
        )
        if emoji:
            try:
                option.emoji = emoji
            except:
                pass
        return option
    
    async def get_player_mode(self, guild_id: str) -> str:
        """Get player mode for guild"""
        mode = await self.db.get_player_mode(guild_id)
        return mode or "avon-classic"
    
    async def update_player_mode(self, guild_id: str, mode: str):
        """Update player mode"""
        await self.db.update_player_mode(guild_id, mode)
    
    async def check_dj_setup(self, guild_id: str) -> bool:
        """Check if DJ setup exists"""
        return await self.db.check_dj_setup(guild_id)
    
    async def get_dj_setup_channel(self, guild_id: str) -> Optional[str]:
        """Get DJ setup channel"""
        setup = await self.db.get_dj_setup(guild_id)
        return setup.get("CHANNEL")
    
    async def create_dj(self, guild_id: str, channel_id: str, message_id: str):
        """Create DJ setup"""
        await self.db.create_dj_setup(guild_id, channel_id, message_id)
    
    async def delete_dj(self, guild_id: str):
        """Delete DJ setup"""
        await self.db.delete_dj_setup(guild_id)
    
    async def get_dj(self, guild_id: str) -> Dict[str, Optional[str]]:
        """Get DJ setup details"""
        return await self.db.get_dj_setup(guild_id)
    
    async def get_dj_role(self, guild_id: str) -> Optional[str]:
        """Get DJ role"""
        return await self.db.get_dj_role(guild_id)
    
    async def add_dj_role(self, guild_id: str, role_id: str):
        """Add DJ role"""
        await self.db.add_dj_role(guild_id, role_id)
    
    async def delete_dj_role(self, guild_id: str):
        """Delete DJ role"""
        await self.db.remove_dj_role(guild_id)
    
    async def get_play_type(self, guild_id: str) -> str:
        """Get play command type"""
        play_type = await self.db.get_play_type(guild_id)
        if not play_type:
            await self.db.update_play_type(guild_id, "buttons")
            return "buttons"
        return play_type
    
    async def update_play_type(self, guild_id: str, play_type: str):
        """Update play command type"""
        await self.db.update_play_type(guild_id, play_type)
    
    def check_url(self, url: str) -> bool:
        """Check if string is valid URL"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    async def get_autoplay(self, guild_id: str) -> bool:
        """Get autoplay setting"""
        return await self.db.get_autoplay(guild_id)
    
    async def update_autoplay(self, guild_id: str) -> bool:
        """Toggle autoplay setting"""
        current = await self.db.get_autoplay(guild_id)
        if current:
            await self.db.disable_autoplay(guild_id)
            return False
        else:
            await self.db.enable_autoplay(guild_id)
            return True
    
    async def get_247(self, guild_id: str) -> bool:
        """Get 24/7 setting"""
        return await self.db.get_247(guild_id)
    
    async def enable_247(self, guild_id: str, voice_id: str, text_id: str):
        """Enable 24/7 mode"""
        await self.db.enable_247(guild_id, voice_id, text_id)
    
    async def disable_247(self, guild_id: str):
        """Disable 24/7 mode"""
        await self.db.disable_247(guild_id)
    
    def humanize(self, milliseconds: int) -> str:
        """Convert milliseconds to human readable time"""
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        hours = minutes // 60
        minutes = minutes % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    async def check_global_afk(self, user_id: str) -> bool:
        """Check if user has global AFK"""
        return await self.db.check_global_afk(user_id)
    
    async def check_server_afk(self, user_id: str, guild_id: str) -> bool:
        """Check if user has server AFK"""
        return await self.db.check_server_afk(user_id, guild_id)
    
    async def add_global_afk(self, user_id: str, reason: str):
        """Add global AFK"""
        timestamp = int(datetime.now().timestamp())
        await self.db.add_global_afk(user_id, reason, timestamp)
    
    async def add_server_afk(self, user_id: str, reason: str, guild_id: str):
        """Add server AFK"""
        timestamp = int(datetime.now().timestamp())
        await self.db.add_server_afk(user_id, reason, timestamp, guild_id)
    
    async def remove_global_afk(self, user_id: str):
        """Remove global AFK"""
        await self.db.remove_global_afk(user_id)
    
    async def remove_server_afk(self, user_id: str, guild_id: str):
        """Remove server AFK"""
        await self.db.remove_server_afk(user_id, guild_id)
    
    def format_time(self, timestamp: int) -> str:
        """Format timestamp to readable format"""
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    async def update_prefix(self, guild_id: str, prefix: str):
        """Update guild prefix"""
        await self.db.update_prefix(guild_id, prefix)
    
    async def get_prefix(self, guild_id: str) -> str:
        """Get guild prefix"""
        prefix = await self.db.get_prefix(guild_id)
        return prefix or "+"
    
    # No Prefix System Functions
    async def check_global_np(self, user_id: str) -> bool:
        """Check if user has global no-prefix"""
        async with aiosqlite.connect(self.db.db_path) as db:
            async with db.execute("SELECT USER FROM NOPREFIX WHERE USER = ? AND GLOBAL = 1", (user_id,)) as cursor:
                return bool(await cursor.fetchone())
    
    async def check_guild_np(self, guild_id: str, user_id: str) -> bool:
        """Check if user has server no-prefix"""
        async with aiosqlite.connect(self.db.db_path) as db:
            async with db.execute("SELECT USER FROM NOPREFIX WHERE USER = ? AND SERVER = ? AND GLOBAL = 0", (user_id, guild_id)) as cursor:
                return bool(await cursor.fetchone())
    
    async def add_global_np(self, user_id: str, reason: str):
        """Add global no-prefix access"""
        async with aiosqlite.connect(self.db.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO NOPREFIX(USER, GLOBAL, REASON) VALUES(?, 1, ?)", (user_id, reason))
            await db.commit()
    
    async def remove_global_np(self, user_id: str):
        """Remove global no-prefix access"""
        async with aiosqlite.connect(self.db.db_path) as db:
            await db.execute("DELETE FROM NOPREFIX WHERE USER = ? AND GLOBAL = 1", (user_id,))
            await db.commit()
    
    async def add_guild_np(self, guild_id: str, user_id: str, reason: str):
        """Add server no-prefix access"""
        async with aiosqlite.connect(self.db.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO NOPREFIX(USER, GLOBAL, SERVER, REASON) VALUES(?, 0, ?, ?)", (user_id, guild_id, reason))
            await db.commit()
    
    async def remove_guild_np(self, user_id: str, guild_id: str):
        """Remove server no-prefix access"""
        async with aiosqlite.connect(self.db.db_path) as db:
            await db.execute("DELETE FROM NOPREFIX WHERE USER = ? AND SERVER = ? AND GLOBAL = 0", (user_id, guild_id))
            await db.commit()