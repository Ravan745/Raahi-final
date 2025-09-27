import discord
from discord.ext import commands
import time
import secrets

class PremiumCommands(commands.Cog):
    """Premium system matching TypeScript version exactly"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Premium management user IDs - Replace with actual IDs
        self.owners = ["785708354445508649", "765841266181144596"]
    
    def generate_premium_code(self):
        """Generate premium activation code exactly like TS version"""
        prefix = "avon_"
        suffix = "_op"
        random_part = secrets.token_hex(5)
        return f"{prefix}{random_part}{suffix}"
    
    def is_owner(self, user_id: int) -> bool:
        """Check if user is bot owner"""
        return str(user_id) in self.owners
    
    async def is_management(self, user_id: str) -> bool:
        """Check if user is in management"""
        import aiosqlite
        async with aiosqlite.connect(self.bot.database.db_path) as db:
            async with db.execute("SELECT MANAGER FROM MANAGEMENT WHERE USER = ?", (user_id,)) as cursor:
                result = await cursor.fetchone()
                return bool(result and result[0])
    
    @commands.group(name='premium', aliases=['prem'], invoke_without_command=True)
    async def premium(self, ctx):
        """Premium system commands"""
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.title = f"{self.bot.emoji.premium} Avon Premium"
        embed.description = (
            "**Premium Commands:**\n"
            f"`{ctx.prefix}premium info` - View your premium status\n"
            f"`{ctx.prefix}premium activate <code>` - Activate premium with code\n"
            f"`{ctx.prefix}premium server <code>` - Activate server premium\n"
            f"`{ctx.prefix}premium embed <hex>` - Set custom embed color\n\n"
            "**Management Commands:**\n"
            f"`{ctx.prefix}premium add <user> <time> <tier>` - Add user premium\n"
            f"`{ctx.prefix}premium remove <user>` - Remove user premium\n"
            f"`{ctx.prefix}premium addserver <server> <time>` - Add server premium\n"
            f"`{ctx.prefix}premium removeserver <server>` - Remove server premium"
        )
        embed.set_footer(text=f"💘 Thanks for choosing {self.bot.user.name}")
        await ctx.send(embed=embed)
    
    @premium.command(name='info')
    async def premium_info(self, ctx, user: discord.User = None):
        """Check premium status"""
        target = user or ctx.author
        
        user_premium = await self.bot.utils.check_user_prem(str(target.id))
        server_premium = await self.bot.utils.check_server_prem(str(ctx.guild.id))
        
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.title = f"{self.bot.emoji.premium} Premium Status"
        
        if user_premium:
            embed.add_field(
                name="👤 User Premium",
                value=f"{self.bot.emoji.tick} **Active**",
                inline=True
            )
        else:
            embed.add_field(
                name="👤 User Premium", 
                value=f"{self.bot.emoji.cross} **Not Active**",
                inline=True
            )
        
        if server_premium:
            embed.add_field(
                name="🏠 Server Premium",
                value=f"{self.bot.emoji.tick} **Active**",
                inline=True
            )
        else:
            embed.add_field(
                name="🏠 Server Premium",
                value=f"{self.bot.emoji.cross} **Not Active**", 
                inline=True
            )
        
        if user_premium or server_premium:
            embed.description = "🌟 **Premium Features Unlocked!**"
        else:
            embed.description = "💎 Get premium to unlock exclusive features!"
        
        await ctx.send(embed=embed)
    
    @premium.command(name='activate')
    async def premium_activate(self, ctx, code: str = None):
        """Activate premium with code"""
        if not code:
            embed = await self.bot.utils.error_embed()
            embed.description = f"{self.bot.emoji.cross} Please provide a premium code!"
            embed.title = "Missing Code"
            return await ctx.send(embed=embed)
        
        # Check if already has premium
        if await self.bot.utils.check_user_prem(str(ctx.author.id)):
            embed = await self.bot.utils.error_embed()
            embed.description = f"{self.bot.emoji.cross} You already have premium!"
            return await ctx.send(embed=embed)
        
        # Validate code format
        if not code.startswith("avon_") or not code.endswith("_op"):
            embed = await self.bot.utils.error_embed()
            embed.description = f"{self.bot.emoji.cross} Invalid premium code!"
            return await ctx.send(embed=embed)
        
        # Activate premium (30 days)
        expire_time = int(time.time()) + (30 * 24 * 60 * 60)
        await self.bot.utils.db.add_user_premium(
            str(ctx.author.id), expire_time, 1, "premium", code, "Code Activation"
        )
        
        embed = await self.bot.utils.success_embed()
        embed.title = f"{self.bot.emoji.premium} Premium Activated!"
        embed.description = (
            f"{self.bot.emoji.tick} Premium has been activated for **{ctx.author.mention}**!\n"
            f"🎯 **Tier:** Premium\n"
            f"⏰ **Duration:** 30 days\n"
            f"🔑 **Code:** `{code}`"
        )
        await ctx.send(embed=embed)
    
    @premium.command(name='embed')
    async def premium_embed_color(self, ctx, hex_color: str = None):
        """Set custom embed color (premium only)"""
        if not await self.bot.utils.check_server_prem(str(ctx.guild.id)):
            embed = await self.bot.utils.error_embed()
            embed.description = f"{self.bot.emoji.cross} This server needs premium to use custom embed colors!"
            return await ctx.send(embed=embed)
        
        if not hex_color:
            current_hex = await self.bot.utils.db.get_hex(str(ctx.guild.id))
            if current_hex:
                embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
                embed.description = f"Current embed color: `{current_hex}`"
                embed.title = "Current Embed Color"
            else:
                embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
                embed.description = "No custom embed color set"
                embed.title = "Embed Color"
            
            embed.set_footer(text=f"Usage: {ctx.prefix}premium embed <hex_color>")
            return await ctx.send(embed=embed)
        
        # Validate hex color
        if not hex_color.startswith("#"):
            hex_color = f"#{hex_color}"
        
        try:
            int(hex_color[1:], 16)
            if len(hex_color) != 7:
                raise ValueError()
        except ValueError:
            embed = await self.bot.utils.error_embed()
            embed.description = f"{self.bot.emoji.cross} Invalid hex color! Use format: `#FF0000`"
            return await ctx.send(embed=embed)
        
        await self.bot.utils.db.add_hex(str(ctx.guild.id), hex_color)
        
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.title = "Embed Color Updated"
        embed.description = f"{self.bot.emoji.tick} Embed color set to `{hex_color}`"
        await ctx.send(embed=embed)
    
    # Management commands matching TypeScript version
    @premium.command(name='addpremium', aliases=['addprem', '+prem'])
    async def add_premium(self, ctx, user: discord.User, tier: str = "premium", days: int = 30):
        """Add premium to user (management only) - exactly like TS version"""
        if not self.is_owner(ctx.author.id) and not await self.is_management(str(ctx.author.id)):
            return
        
        # Premium tiers from TypeScript version
        valid_tiers = ["bronze-tier", "silver-tier", "gold-tier", "diamond-tier", "premium"]
        
        if tier not in valid_tiers:
            embed = await self.bot.utils.error_embed()
            embed.description = f"{self.bot.emoji.cross} Invalid tier! Valid tiers: {', '.join(valid_tiers)}"
            return await ctx.send(embed=embed)
        
        # Set tier-specific settings like TS version
        if tier in ["bronze-tier", "bronze_tier"]:
            days = 30
            count = 0
        elif tier in ["silver-tier", "silver_tier"]:
            days = 60
            count = 1
        elif tier in ["gold-tier", "gold_tier"]:
            days = 90
            count = 2
        elif tier in ["diamond-tier", "diamond_tier"]:
            days = 120
            count = 3
        else:
            count = 1
        
        expire_time = int(time.time()) + (days * 24 * 60 * 60)
        code = self.generate_premium_code()
        reason = f"{ctx.author} | Management Addition"
        
        await self.bot.utils.db.add_user_premium(
            str(user.id), expire_time, count, tier, code, reason
        )
        
        embed = await self.bot.utils.success_embed()
        embed.title = f"{self.bot.emoji.premium} Premium Added"
        embed.description = (
            f"{self.bot.emoji.tick} Premium added to **{user.mention}**!\n"
            f"⏰ **Duration:** {days} days\n"
            f"🎯 **Tier:** {tier}\n"
            f"🔑 **Code:** `{code}`\n"
            f"👤 **Added by:** {ctx.author.mention}"
        )
        await ctx.send(embed=embed)
    
    @premium.command(name='removepremium', aliases=['removeprem', '-prem'])
    async def remove_premium(self, ctx, user: discord.User):
        """Remove premium from user (management only)"""
        if not self.is_owner(ctx.author.id) and not await self.is_management(str(ctx.author.id)):
            return
        
        # Remove premium from database
        import aiosqlite
        async with aiosqlite.connect(self.bot.database.db_path) as db:
            await db.execute("DELETE FROM PREMIUM WHERE USER = ?", (str(user.id),))
            await db.commit()
        
        embed = await self.bot.utils.success_embed()
        embed.description = f"{self.bot.emoji.tick} Premium removed from **{user.mention}**!"
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PremiumCommands(bot))