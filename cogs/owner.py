import discord
from discord.ext import commands
import ast
import inspect
import traceback
from typing import Optional

class OwnerCommands(commands.Cog):
    """Owner commands matching TypeScript version exactly"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Owner IDs - Replace with actual owner IDs
        self.owners = ["785708354445508649", "973925530153910322"]  # From TS version
    
    def is_owner(self, user_id: int) -> bool:
        """Check if user is bot owner"""
        return str(user_id) in self.owners
    
    async def is_management(self, user_id: str) -> bool:
        """Check if user is in management"""
        # Check database for management status
        import aiosqlite
        async with aiosqlite.connect(self.bot.database.db_path) as db:
            async with db.execute("SELECT MANAGER FROM MANAGEMENT WHERE USER = ?", (user_id,)) as cursor:
                result = await cursor.fetchone()
                return bool(result and result[0])
    
    @commands.command(name='eval', aliases=['jadu', 'exe', 'puni'])
    async def eval_command(self, ctx, *, code: str = None):
        """Evaluate Python code (owner only)"""
        if not self.is_owner(ctx.author.id):
            return
        
        if not code:
            return await ctx.reply(f"{self.bot.emoji.cross} Please provide me some code to evaluate")
        
        # Remove code blocks if present
        if code.startswith('```py\n'):
            code = code[6:-3]
        elif code.startswith('```python\n'):
            code = code[10:-3]
        elif code.startswith('```\n'):
            code = code[4:-3]
        elif code.startswith('```'):
            code = code[3:-3]
        
        # Prepare local variables
        local_vars = {
            'ctx': ctx,
            'bot': self.bot,
            'discord': discord,
            'commands': commands,
            'guild': ctx.guild,
            'channel': ctx.channel,
            'author': ctx.author,
            'message': ctx.message
        }
        
        try:
            # Try to evaluate as expression first
            try:
                compiled = compile(code, '<eval>', 'eval')
                result = eval(compiled, globals(), local_vars)
            except SyntaxError:
                # If it fails, try as statement
                compiled = compile(code, '<eval>', 'exec')
                exec(compiled, globals(), local_vars)
                result = None
            
            if inspect.iscoroutine(result):
                result = await result
            
            result_str = str(result) if result is not None else "None"
            
            if len(result_str) > 2000:
                result_str = result_str[:1997] + "..."
            
            embed = discord.Embed(
                title="Evaluation Result",
                color=0x00ff00
            )
            embed.add_field(
                name="📥 Input",
                value=f"```py\n{code[:1000]}\n```",
                inline=False
            )
            embed.add_field(
                name="📤 Output", 
                value=f"```py\n{result_str}\n```",
                inline=False
            )
            
            view = EvalView()
            await ctx.reply(embed=embed, view=view)
            
        except Exception as e:
            error_str = str(e)
            if len(error_str) > 1800:
                error_str = error_str[:1797] + "..."
            
            embed = discord.Embed(
                title="Evaluation Error",
                color=0xff0000
            )
            embed.add_field(
                name="📥 Input",
                value=f"```py\n{code[:1000]}\n```",
                inline=False
            )
            embed.add_field(
                name="❌ Error",
                value=f"```py\n{error_str}\n```",
                inline=False
            )
            
            view = EvalView()
            await ctx.reply(embed=embed, view=view)
    
    @commands.group(name='management', aliases=['manage'], invoke_without_command=True)
    async def management(self, ctx):
        """Management system commands (owner only)"""
        if not self.is_owner(ctx.author.id):
            return
        
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.title = "Management"
        embed.description = (
            f"`{ctx.prefix}management add` - Adds a user to the bot's management\n"
            f"`{ctx.prefix}management remove` - Removes a user from bot's management\n"
            f"`{ctx.prefix}management list` - Shows the list of the current management of the bot"
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
    
    @management.command(name='add')
    async def management_add(self, ctx, user: discord.User = None):
        """Add user to management"""
        if not self.is_owner(ctx.author.id):
            return
        
        if not user:
            return await ctx.reply(f"{self.bot.emoji.cross} Please provide me a valid user")
        
        # Check if already in management
        if await self.is_management(str(user.id)):
            return await ctx.reply(
                f"{self.bot.emoji.cross} This User {user} is already in my Management List"
            )
        
        # Add to management
        import aiosqlite
        async with aiosqlite.connect(self.bot.database.db_path) as db:
            await db.execute("INSERT INTO MANAGEMENT(USER, MANAGER) VALUES(?, 1)", (str(user.id),))
            await db.commit()
        
        await ctx.reply(
            f"{self.bot.emoji.tick} Successfully **Added** {user} to my Management List"
        )
    
    @management.command(name='remove')
    async def management_remove(self, ctx, user: discord.User = None):
        """Remove user from management"""
        if not self.is_owner(ctx.author.id):
            return
        
        if not user:
            return await ctx.reply(f"{self.bot.emoji.cross} Please provide me a valid user")
        
        # Check if in management
        if not await self.is_management(str(user.id)):
            return await ctx.reply(
                f"{self.bot.emoji.cross} This User {user} is not in my Management List"
            )
        
        # Remove from management
        import aiosqlite
        async with aiosqlite.connect(self.bot.database.db_path) as db:
            await db.execute("DELETE FROM MANAGEMENT WHERE USER = ? AND MANAGER = 1", (str(user.id),))
            await db.commit()
        
        await ctx.reply(
            f"{self.bot.emoji.tick} Successfully **Removed** {user} from my Management List"
        )
    
    @management.command(name='list')
    async def management_list(self, ctx):
        """List all management users"""
        if not self.is_owner(ctx.author.id):
            return
        
        # Get all management users
        import aiosqlite
        async with aiosqlite.connect(self.bot.database.db_path) as db:
            async with db.execute("SELECT USER FROM MANAGEMENT WHERE MANAGER = 1") as cursor:
                results = await cursor.fetchall()
        
        if not results:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = "No users found in management list"
            embed.title = "Management List"
            return await ctx.send(embed=embed)
        
        management_list = []
        for row in results:
            try:
                user = await self.bot.fetch_user(int(row[0]))
                management_list.append(f"{user} ({user.id})")
            except:
                management_list.append(f"Unknown User ({row[0]})")
        
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.title = "Management List"
        embed.description = "\n".join(management_list)
        await ctx.send(embed=embed)
    
    @commands.group(name='noprefix', aliases=['nopre'], invoke_without_command=True)
    async def noprefix(self, ctx):
        """No prefix system commands"""
        if not self.is_owner(ctx.author.id) and not await self.is_management(str(ctx.author.id)):
            return
        
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.title = "No Prefix Commands"
        embed.description = (
            f"`{ctx.prefix}noprefix add <user> [reason]` - Add global no-prefix access\n"
            f"`{ctx.prefix}noprefix remove <user>` - Remove global no-prefix access\n"
            f"`{ctx.prefix}noprefix server add <user> [reason]` - Add server no-prefix access\n"
            f"`{ctx.prefix}noprefix server remove <user>` - Remove server no-prefix access\n"
            f"`{ctx.prefix}noprefix list` - Show global no-prefix users\n"
            f"`{ctx.prefix}noprefix server list` - Show server no-prefix users"
        )
        await ctx.send(embed=embed)
    
    @noprefix.command(name='add')
    async def noprefix_add(self, ctx, user: discord.User, *, reason: str = "No reason provided"):
        """Add global no-prefix access"""
        if not self.is_owner(ctx.author.id) and not await self.is_management(str(ctx.author.id)):
            return
        
        # Check if already has global no-prefix
        if await self.bot.utils.check_global_np(str(user.id)):
            return await ctx.reply(f"{self.bot.emoji.cross} {user} already has global no-prefix access")
        
        await self.bot.utils.add_global_np(str(user.id), reason)
        await ctx.reply(f"{self.bot.emoji.tick} Added global no-prefix access for {user}")
    
    @noprefix.command(name='remove')
    async def noprefix_remove(self, ctx, user: discord.User):
        """Remove global no-prefix access"""
        if not self.is_owner(ctx.author.id) and not await self.is_management(str(ctx.author.id)):
            return
        
        if not await self.bot.utils.check_global_np(str(user.id)):
            return await ctx.reply(f"{self.bot.emoji.cross} {user} doesn't have global no-prefix access")
        
        await self.bot.utils.remove_global_np(str(user.id))
        await ctx.reply(f"{self.bot.emoji.tick} Removed global no-prefix access for {user}")
    
    @noprefix.group(name='server', invoke_without_command=True)
    async def noprefix_server(self, ctx):
        """Server no-prefix commands"""
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.title = "Server No Prefix Commands"
        embed.description = (
            f"`{ctx.prefix}noprefix server add <user> [reason]` - Add server no-prefix access\n"
            f"`{ctx.prefix}noprefix server remove <user>` - Remove server no-prefix access\n"
            f"`{ctx.prefix}noprefix server list` - Show server no-prefix users"
        )
        await ctx.send(embed=embed)
    
    @noprefix_server.command(name='add')
    async def noprefix_server_add(self, ctx, user: discord.User, *, reason: str = "No reason provided"):
        """Add server no-prefix access"""
        if not self.is_owner(ctx.author.id) and not await self.is_management(str(ctx.author.id)):
            return
        
        if await self.bot.utils.check_guild_np(str(ctx.guild.id), str(user.id)):
            return await ctx.reply(f"{self.bot.emoji.cross} {user} already has server no-prefix access")
        
        await self.bot.utils.add_guild_np(str(ctx.guild.id), str(user.id), reason)
        await ctx.reply(f"{self.bot.emoji.tick} Added server no-prefix access for {user}")
    
    @noprefix_server.command(name='remove')
    async def noprefix_server_remove(self, ctx, user: discord.User):
        """Remove server no-prefix access"""
        if not self.is_owner(ctx.author.id) and not await self.is_management(str(ctx.author.id)):
            return
        
        if not await self.bot.utils.check_guild_np(str(ctx.guild.id), str(user.id)):
            return await ctx.reply(f"{self.bot.emoji.cross} {user} doesn't have server no-prefix access")
        
        await self.bot.utils.remove_guild_np(str(user.id), str(ctx.guild.id))
        await ctx.reply(f"{self.bot.emoji.tick} Removed server no-prefix access for {user}")

class EvalView(discord.ui.View):
    """Delete button for eval command"""
    
    def __init__(self):
        super().__init__(timeout=300)
    
    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, custom_id="dev_del")
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Delete the eval result"""
        try:
            await interaction.response.defer()
            await interaction.delete_original_response()
        except:
            pass

async def setup(bot):
    await bot.add_cog(OwnerCommands(bot))