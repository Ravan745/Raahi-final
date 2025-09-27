import discord
from discord.ext import commands
from typing import Union
import functools

def requires_dj():
    """Decorator to check DJ permissions for music commands"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            # Check if user has DJ permissions
            if not await check_dj_permissions(ctx, self.bot):
                embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
                embed.description = f"{self.bot.emoji.cross} You need DJ permissions to use this command!"
                embed.title = "Missing DJ Permissions"
                embed.add_field(
                    name="How to get DJ access:",
                    value="• Be the server administrator\n"
                          "• Have the DJ role (if set)\n" 
                          "• Be alone with the bot in voice channel\n"
                          "• Be the track requester (for skip/remove)",
                    inline=False
                )
                return await ctx.send(embed=embed)
            
            return await func(self, ctx, *args, **kwargs)
        return wrapper
    return decorator

async def check_dj_permissions(ctx, bot, user: discord.Member = None, track_requester: discord.Member = None) -> bool:
    """Check if user has DJ permissions"""
    if user is None:
        user = ctx.author
    
    # Bot owners always have access
    if str(user.id) in bot.config.owners:
        return True
    
    # Administrator permission
    if user.guild_permissions.administrator:
        return True
    
    # Check DJ role
    try:
        dj_role_id = await bot.utils.get_dj_role(str(ctx.guild.id))
        if dj_role_id:
            role = ctx.guild.get_role(int(dj_role_id))
            if role in user.roles:
                return True
    except:
        pass
    
    # Check if user is track requester (for skip/remove commands)
    if track_requester and user.id == track_requester.id:
        return True
    
    # Voice channel permissions
    if user.voice:
        voice_channel = user.voice.channel
        # If user is alone with bot or channel owner
        human_members = [m for m in voice_channel.members if not m.bot]
        if len(human_members) <= 1:
            return True
        
        # Check if user has voice channel permissions
        if voice_channel.permissions_for(user).manage_channels:
            return True
    
    # Check if user is premium
    try:
        if await bot.utils.is_premium_user(str(user.id)):
            return True
    except:
        pass
    
    return False

class DJPermissionsCog(commands.Cog):
    """DJ permissions management system"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.group(name='dj', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def dj_command(self, ctx):
        """DJ role management"""
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.title = "🎧 DJ Role Management"
        embed.description = (
            f"`{ctx.prefix}dj set <@role>` - Set DJ role\n"
            f"`{ctx.prefix}dj remove` - Remove DJ role\n"
            f"`{ctx.prefix}dj info` - Show current DJ settings"
        )
        await ctx.send(embed=embed)
    
    @dj_command.command(name='set')
    @commands.has_permissions(administrator=True)
    async def dj_set(self, ctx, role: discord.Role):
        """Set DJ role"""
        await self.bot.utils.add_dj_role(str(ctx.guild.id), str(role.id))
        
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.description = f"✅ DJ role set to {role.mention}"
        embed.title = "DJ Role Updated"
        await ctx.send(embed=embed)
    
    @dj_command.command(name='remove')
    @commands.has_permissions(administrator=True)
    async def dj_remove(self, ctx):
        """Remove DJ role"""
        await self.bot.utils.delete_dj_role(str(ctx.guild.id))
        
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.description = "✅ DJ role has been removed"
        embed.title = "DJ Role Removed"
        await ctx.send(embed=embed)
    
    @dj_command.command(name='info')
    async def dj_info(self, ctx):
        """Show DJ role information"""
        dj_role_id = await self.bot.utils.get_dj_role(str(ctx.guild.id))
        
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.title = "🎧 DJ Settings"
        
        if dj_role_id:
            role = ctx.guild.get_role(int(dj_role_id))
            if role:
                embed.add_field(
                    name="DJ Role",
                    value=role.mention,
                    inline=False
                )
                embed.add_field(
                    name="Members with DJ Role",
                    value=f"{len(role.members)} members",
                    inline=True
                )
            else:
                embed.add_field(
                    name="DJ Role",
                    value="❌ Role not found (deleted)",
                    inline=False
                )
        else:
            embed.add_field(
                name="DJ Role",
                value="❌ No DJ role set",
                inline=False
            )
        
        embed.add_field(
            name="Who can use music commands:",
            value="• Server administrators\n"
                  "• Users with DJ role\n"
                  "• Premium users\n"
                  "• Users alone in voice channel\n"
                  "• Track requesters (for skip/remove)",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DJPermissionsCog(bot))