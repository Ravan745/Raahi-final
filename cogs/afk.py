import discord
from discord.ext import commands
import time

class AFKCommands(commands.Cog):
    """AFK system matching TypeScript version exactly"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='afk')
    async def afk(self, ctx, *, reason: str = "AFK"):
        """Set AFK status (global or server-specific)"""
        user_id = str(ctx.author.id)
        
        # Check if already AFK globally
        if await self.bot.utils.check_global_afk(user_id):
            embed = await self.bot.utils.error_embed()
            embed.description = f"{self.bot.emoji.cross} You are already AFK globally!"
            embed.title = "Already AFK"
            return await ctx.send(embed=embed)
        
        # Check if already AFK in this server
        if await self.bot.utils.check_server_afk(user_id, str(ctx.guild.id)):
            embed = await self.bot.utils.error_embed()
            embed.description = f"{self.bot.emoji.cross} You are already AFK in this server!"
            embed.title = "Already AFK"
            return await ctx.send(embed=embed)
        
        # Set AFK (server-specific by default)
        await self.bot.utils.add_server_afk(user_id, reason, str(ctx.guild.id))
        
        embed = await self.bot.utils.success_embed()
        embed.title = "AFK Set"
        embed.description = f"{self.bot.emoji.tick} **{ctx.author.display_name}** is now AFK: {reason}"
        await ctx.send(embed=embed)
    
    @commands.command(name='gafk', aliases=['globalafk'])
    async def global_afk(self, ctx, *, reason: str = "AFK"):
        """Set global AFK status (management only)"""
        user_id = str(ctx.author.id)
        
        # Check if user is management or owner
        if not await self.is_management_or_owner(ctx.author.id):
            embed = await self.bot.utils.error_embed()
            embed.description = f"{self.bot.emoji.cross} You don't have permission to use global AFK!"
            return await ctx.send(embed=embed)
        
        # Check if already AFK globally
        if await self.bot.utils.check_global_afk(user_id):
            embed = await self.bot.utils.error_embed()
            embed.description = f"{self.bot.emoji.cross} You are already AFK globally!"
            return await ctx.send(embed=embed)
        
        # Set global AFK
        await self.bot.utils.add_global_afk(user_id, reason)
        
        embed = await self.bot.utils.success_embed()
        embed.title = "Global AFK Set"
        embed.description = f"{self.bot.emoji.tick} **{ctx.author.display_name}** is now globally AFK: {reason}"
        await ctx.send(embed=embed)
    
    @commands.command(name='unafk', aliases=['removeafk'])
    async def unafk(self, ctx):
        """Remove AFK status"""
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        
        # Check if AFK globally
        if await self.bot.utils.check_global_afk(user_id):
            await self.bot.utils.remove_global_afk(user_id)
            embed = await self.bot.utils.success_embed()
            embed.description = f"{self.bot.emoji.tick} **{ctx.author.display_name}** is no longer globally AFK"
            await ctx.send(embed=embed)
            return
        
        # Check if AFK in server
        if await self.bot.utils.check_server_afk(user_id, guild_id):
            await self.bot.utils.remove_server_afk(user_id, guild_id)
            embed = await self.bot.utils.success_embed()
            embed.description = f"{self.bot.emoji.tick} **{ctx.author.display_name}** is no longer AFK in this server"
            await ctx.send(embed=embed)
            return
        
        # Not AFK
        embed = await self.bot.utils.error_embed()
        embed.description = f"{self.bot.emoji.cross} You are not AFK!"
        await ctx.send(embed=embed)
    
    async def is_management_or_owner(self, user_id: int) -> bool:
        """Check if user is management or owner"""
        owners = ["785708354445508649", "765841266181144596"]  # From TS version
        if str(user_id) in owners:
            return True
        
        # Check management status
        import aiosqlite
        async with aiosqlite.connect(self.bot.database.db_path) as db:
            async with db.execute("SELECT MANAGER FROM MANAGEMENT WHERE USER = ?", (str(user_id),)) as cursor:
                result = await cursor.fetchone()
                return bool(result and result[0])
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Check for AFK mentions and auto-remove AFK on user activity"""
        if message.author.bot:
            return
        
        user_id = str(message.author.id)
        guild_id = str(message.guild.id) if message.guild else None
        
        # Auto-remove AFK when user sends a message
        if guild_id:
            if await self.bot.utils.check_global_afk(user_id):
                await self.bot.utils.remove_global_afk(user_id)
                embed = await self.bot.utils.success_embed()
                embed.description = f"Welcome back **{message.author.display_name}**! Your global AFK has been removed."
                try:
                    await message.channel.send(embed=embed, delete_after=5)
                except:
                    pass
            elif await self.bot.utils.check_server_afk(user_id, guild_id):
                await self.bot.utils.remove_server_afk(user_id, guild_id)
                embed = await self.bot.utils.success_embed()
                embed.description = f"Welcome back **{message.author.display_name}**! Your AFK has been removed."
                try:
                    await message.channel.send(embed=embed, delete_after=5)
                except:
                    pass
        
        # Check for AFK mentions
        if message.mentions:
            afk_mentions = []
            
            for mentioned_user in message.mentions:
                if mentioned_user.bot:
                    continue
                
                mentioned_id = str(mentioned_user.id)
                
                # Check global AFK
                if await self.bot.utils.check_global_afk(mentioned_id):
                    # Get AFK reason
                    import aiosqlite
                    async with aiosqlite.connect(self.bot.database.db_path) as db:
                        async with db.execute(
                            "SELECT REASON, TIME FROM AFK_NEW WHERE USER = ? AND GLOBAL = 1", 
                            (mentioned_id,)
                        ) as cursor:
                            result = await cursor.fetchone()
                            if result:
                                reason, afk_time = result
                                time_ago = self.format_time_ago(afk_time)
                                afk_mentions.append(f"**{mentioned_user.display_name}** is globally AFK: {reason} ({time_ago} ago)")
                
                # Check server AFK
                elif guild_id and await self.bot.utils.check_server_afk(mentioned_id, guild_id):
                    import aiosqlite
                    async with aiosqlite.connect(self.bot.database.db_path) as db:
                        async with db.execute(
                            "SELECT REASON, TIME FROM AFK_NEW WHERE USER = ? AND SERVER = ? AND GLOBAL = 0", 
                            (mentioned_id, guild_id)
                        ) as cursor:
                            result = await cursor.fetchone()
                            if result:
                                reason, afk_time = result
                                time_ago = self.format_time_ago(afk_time)
                                afk_mentions.append(f"**{mentioned_user.display_name}** is AFK: {reason} ({time_ago} ago)")
            
            if afk_mentions:
                embed = await self.bot.utils.premium_embed(guild_id)
                embed.title = "AFK Users Mentioned"
                embed.description = "\n".join(afk_mentions)
                try:
                    await message.channel.send(embed=embed, delete_after=10)
                except:
                    pass
    
    def format_time_ago(self, timestamp: int) -> str:
        """Format timestamp to 'time ago' string"""
        now = int(time.time())
        diff = now - timestamp
        
        if diff < 60:
            return f"{diff}s"
        elif diff < 3600:
            return f"{diff // 60}m"
        elif diff < 86400:
            return f"{diff // 3600}h"
        else:
            return f"{diff // 86400}d"

async def setup(bot):
    await bot.add_cog(AFKCommands(bot))