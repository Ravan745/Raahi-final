import discord
import wavelink
from discord.ext import commands
import time
import aiosqlite

class UtilityCommands(commands.Cog):
    """Utility commands for the bot"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help')
    async def help_command(self, ctx, command: str = None):
        """Show help information"""
        if command:
            # Show help for specific command
            cmd = self.bot.get_command(command)
            if not cmd:
                embed = discord.Embed(
                    description=f"❌ Command `{command}` not found!",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)
            
            embed = discord.Embed(
                title=f"Help: {cmd.name}",
                description=cmd.help or "No description available",
                color=self.bot.config.color
            )
            
            if cmd.aliases:
                embed.add_field(
                    name="Aliases",
                    value=", ".join(f"`{alias}`" for alias in cmd.aliases),
                    inline=False
                )
            
            embed.add_field(
                name="Usage",
                value=f"`{ctx.prefix}{cmd.name} {cmd.signature}`",
                inline=False
            )
            
            return await ctx.send(embed=embed)
        
        # Show general help
        embed = discord.Embed(
            title="🎵 Avon Music Bot - Help",
            description=f"Prefix: `{ctx.prefix}`\n"
                       f"Use `{ctx.prefix}help <command>` for detailed help",
            color=self.bot.config.color
        )
        
        # Music commands
        music_commands = [
            "`play` - Play a song",
            "`pause` - Pause current track",
            "`resume` - Resume paused track",
            "`skip` - Skip current track",
            "`stop` - Stop and disconnect",
            "`queue` - Show current queue",
            "`volume` - Change volume",
            "`nowplaying` - Show current track"
        ]
        
        embed.add_field(
            name="🎶 Music Commands",
            value="\n".join(music_commands),
            inline=True
        )
        
        # Filter commands
        filter_commands = [
            "`nightcore` - Speed + pitch up",
            "`daycore` - Speed + pitch down", 
            "`bassboost` - Enhance bass",
            "`8d` - 8D audio effect",
            "`karaoke` - Remove vocals",
            "`clearfilters` - Remove all filters"
        ]
        
        embed.add_field(
            name="🎛️ Audio Filters",
            value="\n".join(filter_commands),
            inline=True
        )
        
        # Utility commands
        utility_commands = [
            "`help` - Show this help",
            "`ping` - Check bot latency",
            "`stats` - Show bot statistics",
            "`prefix` - Change server prefix"
        ]
        
        embed.add_field(
            name="🔧 Utility Commands",
            value="\n".join(utility_commands),
            inline=True
        )
        
        embed.set_footer(text=f"Avon Music Bot | {len(self.bot.guilds)} servers")
        
        await ctx.send(embed=embed)

    @commands.command(name='stats')
    async def stats(self, ctx):
        """Show bot statistics"""
        embed = discord.Embed(
            title="📊 Bot Statistics",
            color=self.bot.config.color
        )
        
        # Basic stats
        total_members = sum(guild.member_count or 0 for guild in self.bot.guilds)
        embed.add_field(
            name="📈 General",
            value=f"**Servers:** {len(self.bot.guilds)}\n"
                  f"**Users:** {total_members}\n"
                  f"**Commands:** {len(self.bot.commands)}",
            inline=True
        )
        
        # Lavalink stats
        if wavelink.Pool.nodes:
            node = wavelink.Pool.get_node()
            embed.add_field(
                name="🎵 Lavalink",
                value=f"**Node:** {node.identifier}\n"
                      f"**Players:** {len(node.players)}\n"
                      f"**Status:** Connected",
                inline=True
            )
        else:
            embed.add_field(
                name="🎵 Lavalink",
                value="**Status:** Disconnected",
                inline=True
            )
        
        # Uptime
        if self.bot.start_time:
            uptime = discord.utils.utcnow() - self.bot.start_time
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{hours}h {minutes}m {seconds}s"
        else:
            uptime_str = "Unknown"
        
        embed.add_field(
            name="⏰ Uptime",
            value=uptime_str,
            inline=True
        )
        
        # Latency
        embed.add_field(
            name="🏓 Latency",
            value=f"{round(self.bot.latency * 1000)}ms",
            inline=True
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='prefix')
    @commands.has_permissions(manage_guild=True)
    async def prefix(self, ctx, new_prefix: str = None):
        """Change the bot prefix for this server"""
        if not new_prefix:
            current_prefix = await self.bot.get_prefix(self.bot, ctx.message)
            if isinstance(current_prefix, list):
                current_prefix = current_prefix[0]
            
            embed = discord.Embed(
                title="Server Prefix",
                description=f"Current prefix: `{current_prefix}`\n"
                           f"Usage: `{current_prefix}prefix <new_prefix>`",
                color=self.bot.config.color
            )
            return await ctx.send(embed=embed)
        
        if len(new_prefix) > 5:
            embed = discord.Embed(
                description="❌ Prefix cannot be longer than 5 characters!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Update prefix in database
        try:
            async with aiosqlite.connect(self.bot.config.database_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO guild_settings (guild_id, prefix)
                    VALUES (?, ?)
                """, (ctx.guild.id, new_prefix))
                await db.commit()
            
            embed = discord.Embed(
                description=f"✅ Server prefix changed to `{new_prefix}`",
                color=self.bot.config.color
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                description=f"❌ Failed to update prefix: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name='invite')
    async def invite(self, ctx):
        """Get the bot invite link"""
        embed = discord.Embed(
            title="📨 Invite Avon Music Bot",
            description="Thanks for using Avon! Invite me to other servers:",
            color=self.bot.config.color
        )
        
        # Generate invite link
        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=discord.Permissions(
                read_messages=True,
                send_messages=True,
                embed_links=True,
                connect=True,
                speak=True,
                use_voice_activation=True,
                manage_messages=True
            )
        )
        
        embed.add_field(
            name="🔗 Invite Link",
            value=f"[Click here to invite me!]({invite_url})",
            inline=False
        )
        
        embed.add_field(
            name="🆘 Support Server",
            value=f"[Join our support server]({self.bot.config.support_server})",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @prefix.error
    async def prefix_error(self, ctx, error):
        """Handle prefix command errors"""
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                description="❌ You need the **Manage Server** permission to change the prefix!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))