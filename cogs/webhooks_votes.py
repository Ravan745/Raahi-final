import discord
import asyncio
import aiohttp
from discord.ext import commands
from datetime import datetime, timedelta
import json

class WebhooksAndVotes(commands.Cog):
    """Webhook and vote functionality for the bot"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Vote tracking
        self.vote_rewards = {
            'weekend': 200,  # Weekend vote rewards (2x)
            'normal': 100    # Normal vote rewards
        }
        
        # Webhook settings
        self.webhook_auth = self.bot.config.webhook_auth if hasattr(self.bot.config, 'webhook_auth') else None
        self.topgg_webhook_auth = self.bot.config.topgg_webhook_auth if hasattr(self.bot.config, 'topgg_webhook_auth') else None
        
        # Start webhook server
        if hasattr(self.bot.config, 'webhook_port'):
            self.bot.loop.create_task(self.start_webhook_server())
    
    async def start_webhook_server(self):
        """Start the webhook server for vote handling"""
        from aiohttp import web
        
        app = web.Application()
        app.router.add_post('/webhook/vote', self.handle_vote_webhook)
        app.router.add_post('/webhook/topgg', self.handle_topgg_webhook)
        app.router.add_get('/webhook/status', self.webhook_status)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        port = getattr(self.bot.config, 'webhook_port', 3001)
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        print(f"🌐 Webhook server started on port {port}")
    
    async def handle_vote_webhook(self, request):
        """Handle generic vote webhooks"""
        try:
            # Verify authorization
            auth_header = request.headers.get('Authorization')
            if self.webhook_auth and auth_header != self.webhook_auth:
                return web.Response(status=401, text='Unauthorized')
            
            # Parse webhook data
            data = await request.json()
            
            user_id = data.get('user')
            bot_id = data.get('bot')
            vote_type = data.get('type', 'upvote')
            is_weekend = data.get('isWeekend', False)
            
            if user_id and bot_id:
                await self.process_vote(user_id, bot_id, vote_type, is_weekend)
                return web.Response(status=200, text='OK')
            
            return web.Response(status=400, text='Invalid data')
            
        except Exception as e:
            print(f"Webhook error: {e}")
            return web.Response(status=500, text='Internal server error')
    
    async def handle_topgg_webhook(self, request):
        """Handle Top.gg specific webhooks"""
        try:
            # Verify Top.gg authorization
            auth_header = request.headers.get('Authorization')
            if self.topgg_webhook_auth and auth_header != self.topgg_webhook_auth:
                return web.Response(status=401, text='Unauthorized')
            
            # Parse Top.gg webhook data
            data = await request.json()
            
            user_id = data.get('user')
            bot_id = data.get('bot')
            vote_type = data.get('type', 'upvote')
            is_weekend = data.get('isWeekend', False)
            query = data.get('query', '')
            
            if user_id and bot_id:
                await self.process_vote(user_id, bot_id, vote_type, is_weekend, 'topgg')
                return web.Response(status=200, text='Vote received')
            
            return web.Response(status=400, text='Invalid vote data')
            
        except Exception as e:
            print(f"Top.gg webhook error: {e}")
            return web.Response(status=500, text='Server error')
    
    async def webhook_status(self, request):
        """Webhook status endpoint"""
        status = {
            'status': 'online',
            'bot': self.bot.user.name if self.bot.user else 'Unknown',
            'guilds': len(self.bot.guilds),
            'timestamp': datetime.utcnow().isoformat()
        }
        return web.json_response(status)
    
    async def process_vote(self, user_id: str, bot_id: str, vote_type: str, is_weekend: bool, platform: str = 'generic'):
        """Process a vote and give rewards"""
        try:
            # Save vote to database
            await self.save_vote_to_database(user_id, vote_type, is_weekend, platform)
            
            # Calculate rewards
            reward_amount = self.vote_rewards['weekend'] if is_weekend else self.vote_rewards['normal']
            
            # Send thank you message
            await self.send_vote_thank_you(user_id, reward_amount, is_weekend, platform)
            
            # Grant rewards (if you have a currency/premium system)
            await self.grant_vote_rewards(user_id, reward_amount, is_weekend)
            
            print(f"🗳️ Vote processed: User {user_id} on {platform} ({'weekend' if is_weekend else 'normal'})")
            
        except Exception as e:
            print(f"Error processing vote: {e}")
    
    async def save_vote_to_database(self, user_id: str, vote_type: str, is_weekend: bool, platform: str):
        """Save vote to database"""
        try:
            async with self.bot.database.get_connection() as db:
                await db.execute("""
                    INSERT OR IGNORE INTO votes (user_id, vote_type, is_weekend, platform, voted_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, vote_type, is_weekend, platform, datetime.utcnow()))
                await db.commit()
        except Exception as e:
            print(f"Database error saving vote: {e}")
    
    async def send_vote_thank_you(self, user_id: str, reward_amount: int, is_weekend: bool, platform: str):
        """Send thank you message to voter"""
        try:
            user = await self.bot.fetch_user(int(user_id))
            if not user:
                return
            
            embed = discord.Embed(
                title="🗳️ Thank you for voting!",
                description=f"Thanks for voting for **{self.bot.user.name}** on **{platform.title()}**!",
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            reward_text = f"{reward_amount} coins"
            if is_weekend:
                reward_text += " (Weekend Bonus! 🎉)"
            
            embed.add_field(
                name="💰 Reward",
                value=reward_text,
                inline=True
            )
            
            embed.add_field(
                name="⏰ Next Vote",
                value="Available in 12 hours",
                inline=True
            )
            
            embed.add_field(
                name="🔗 Vote Again",
                value=f"[Vote on {platform.title()}]({self.bot.config.vote_url})",
                inline=False
            )
            
            embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
            embed.set_footer(text=f"Voted on {platform.title()}")
            
            await user.send(embed=embed)
            
        except discord.Forbidden:
            # User has DMs disabled
            pass
        except Exception as e:
            print(f"Error sending vote thank you: {e}")
    
    async def grant_vote_rewards(self, user_id: str, reward_amount: int, is_weekend: bool):
        """Grant rewards to the voter (coins, premium time, etc.)"""
        try:
            # Add coins to user's balance
            async with self.bot.database.get_connection() as db:
                # Create user balance if not exists
                await db.execute("""
                    INSERT OR IGNORE INTO user_economy (user_id, coins, total_votes)
                    VALUES (?, 0, 0)
                """, (user_id,))
                
                # Add coins and increment vote count
                await db.execute("""
                    UPDATE user_economy 
                    SET coins = coins + ?, total_votes = total_votes + 1
                    WHERE user_id = ?
                """, (reward_amount, user_id))
                
                # If weekend, give small premium time bonus
                if is_weekend:
                    premium_hours = 2  # 2 hours premium for weekend votes
                    expiry_time = datetime.utcnow() + timedelta(hours=premium_hours)
                    
                    await db.execute("""
                        INSERT OR REPLACE INTO premium_users (user_id, tier, expires_at)
                        VALUES (?, 'bronze', ?)
                    """, (user_id, expiry_time))
                
                await db.commit()
                
        except Exception as e:
            print(f"Error granting vote rewards: {e}")
    
    # ============= VOTE COMMANDS =============
    
    @commands.command(name='vote')
    async def vote_command(self, ctx):
        """Show vote information and links"""
        embed = discord.Embed(
            title="🗳️ Vote for Avon!",
            description="Vote for Avon to help us grow and get awesome rewards!",
            color=self.bot.config.color
        )
        
        # Vote links
        vote_links = []
        if hasattr(self.bot.config, 'vote_url'):
            vote_links.append(f"[🔹 Top.gg]({self.bot.config.vote_url})")
        
        if vote_links:
            embed.add_field(
                name="📋 Vote Links",
                value="\n".join(vote_links),
                inline=False
            )
        
        # Rewards info
        embed.add_field(
            name="💰 Rewards",
            value=f"• **{self.vote_rewards['normal']} coins** per vote\n"
                  f"• **{self.vote_rewards['weekend']} coins** on weekends\n"
                  f"• **2 hours premium** (weekend bonus)",
            inline=False
        )
        
        # Vote stats for this user
        user_votes = await self.get_user_vote_stats(str(ctx.author.id))
        embed.add_field(
            name="📊 Your Stats",
            value=f"Total Votes: **{user_votes.get('total_votes', 0)}**\n"
                  f"Current Coins: **{user_votes.get('coins', 0)}**",
            inline=False
        )
        
        embed.add_field(
            name="⏰ Vote Cooldown",
            value="You can vote every **12 hours**",
            inline=False
        )
        
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        embed.set_footer(text="Thank you for supporting Avon! 💜")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='voters', aliases=['topvoters'])
    async def top_voters(self, ctx):
        """Show top voters leaderboard"""
        try:
            async with self.bot.database.get_connection() as db:
                cursor = await db.execute("""
                    SELECT user_id, total_votes, coins
                    FROM user_economy
                    WHERE total_votes > 0
                    ORDER BY total_votes DESC
                    LIMIT 10
                """)
                voters = await cursor.fetchall()
            
            if not voters:
                embed = discord.Embed(
                    title="🗳️ Top Voters",
                    description="No voters yet! Be the first to vote!",
                    color=self.bot.config.color
                )
                return await ctx.send(embed=embed)
            
            embed = discord.Embed(
                title="🗳️ Top Voters Leaderboard",
                description="Thank you to our amazing voters!",
                color=self.bot.config.color
            )
            
            leaderboard = []
            for i, (user_id, votes, coins) in enumerate(voters, 1):
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    username = user.display_name if user else f"User {user_id}"
                except:
                    username = f"User {user_id}"
                
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                leaderboard.append(f"{medal} **{username}** - {votes} votes ({coins} coins)")
            
            embed.description += "\n\n" + "\n".join(leaderboard)
            embed.set_footer(text="Vote to join the leaderboard!")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description="Could not retrieve voter statistics.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    async def get_user_vote_stats(self, user_id: str) -> dict:
        """Get vote statistics for a user"""
        try:
            async with self.bot.database.get_connection() as db:
                cursor = await db.execute("""
                    SELECT total_votes, coins
                    FROM user_economy
                    WHERE user_id = ?
                """, (user_id,))
                result = await cursor.fetchone()
                
                if result:
                    return {
                        'total_votes': result[0],
                        'coins': result[1]
                    }
                
        except Exception as e:
            print(f"Error getting user vote stats: {e}")
        
        return {'total_votes': 0, 'coins': 0}
    
    # ============= SERVER JOIN/LEAVE WEBHOOKS =============
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Handle server join events"""
        await self.send_guild_log(guild, 'join')
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Handle server leave events"""
        await self.send_guild_log(guild, 'leave')
    
    # ============= COMMAND USAGE TRACKING =============
    
    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Track command usage and send webhook"""
        await self.track_command_usage(ctx)
    
    async def track_command_usage(self, ctx):
        """Track and log command usage"""
        try:
            # Save command usage to database
            await self.save_command_usage(ctx)
            
            # Send command usage webhook (optional - can be enabled/disabled)
            if hasattr(self.bot.config, 'command_log_webhook') and self.bot.config.command_log_webhook:
                await self.send_command_usage_webhook(ctx)
            
        except Exception as e:
            print(f"Error tracking command usage: {e}")
    
    async def save_command_usage(self, ctx):
        """Save command usage to database"""
        try:
            async with self.bot.database.get_connection() as db:
                await db.execute("""
                    INSERT OR IGNORE INTO command_usage 
                    (user_id, guild_id, command_name, used_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    str(ctx.author.id),
                    str(ctx.guild.id) if ctx.guild else 'DM',
                    ctx.command.name if ctx.command else 'unknown',
                    datetime.utcnow()
                ))
                await db.commit()
        except Exception as e:
            print(f"Database error saving command usage: {e}")
    
    async def send_command_usage_webhook(self, ctx):
        """Send command usage webhook (like original Avon)"""
        try:
            embed = discord.Embed(
                title="📝 Command Used",
                color=0x5865F2,
                timestamp=datetime.utcnow()
            )
            
            # Command info
            command_name = ctx.command.name if ctx.command else 'unknown'
            embed.add_field(
                name="Command",
                value=f"`{ctx.prefix}{command_name}`",
                inline=True
            )
            
            # User info
            embed.add_field(
                name="User",
                value=f"**{ctx.author}**\n`{ctx.author.id}`",
                inline=True
            )
            
            # Server info
            if ctx.guild:
                embed.add_field(
                    name="Server",
                    value=f"**{ctx.guild.name}**\n`{ctx.guild.id}`\nMembers: {ctx.guild.member_count}",
                    inline=True
                )
            else:
                embed.add_field(
                    name="Server",
                    value="Direct Message",
                    inline=True
                )
            
            # Bot stats
            embed.add_field(
                name="Bot Stats",
                value=f"**Servers:** {len(self.bot.guilds)}\n**Users:** {sum(g.member_count or 0 for g in self.bot.guilds)}",
                inline=False
            )
            
            if ctx.guild and ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)
            
            embed.set_footer(text=f"Command Usage Log • {self.bot.user.name}")
            
            # Send to webhook
            webhook_url = self.bot.config.command_log_webhook
            async with aiohttp.ClientSession() as session:
                webhook_data = {
                    'embeds': [embed.to_dict()]
                }
                async with session.post(webhook_url, json=webhook_data) as response:
                    if response.status != 204:
                        print(f"Failed to send command usage webhook: {response.status}")
            
        except Exception as e:
            print(f"Error sending command usage webhook: {e}")
    
    # ============= COMMAND STATS COMMANDS =============
    
    @commands.command(name='commandstats', aliases=['cmdstats'])
    async def command_stats(self, ctx, user: discord.Member = None):
        """Show command usage statistics"""
        target_user = user or ctx.author
        
        try:
            async with self.bot.database.get_connection() as db:
                # Get user's command usage
                cursor = await db.execute("""
                    SELECT command_name, COUNT(*) as usage_count
                    FROM command_usage 
                    WHERE user_id = ?
                    GROUP BY command_name
                    ORDER BY usage_count DESC
                    LIMIT 10
                """, (str(target_user.id),))
                user_stats = await cursor.fetchall()
                
                # Get total commands used by user
                cursor = await db.execute("""
                    SELECT COUNT(*) as total_commands
                    FROM command_usage 
                    WHERE user_id = ?
                """, (str(target_user.id),))
                total_result = await cursor.fetchone()
                total_commands = total_result[0] if total_result else 0
            
            embed = discord.Embed(
                title=f"📊 Command Statistics",
                description=f"Statistics for **{target_user.display_name}**",
                color=self.bot.config.color
            )
            
            embed.add_field(
                name="📈 Total Commands Used",
                value=f"**{total_commands:,}** commands",
                inline=False
            )
            
            if user_stats:
                stats_text = []
                for command_name, count in user_stats:
                    stats_text.append(f"`{command_name}`: **{count:,}** times")
                
                embed.add_field(
                    name="🔝 Most Used Commands",
                    value="\n".join(stats_text),
                    inline=False
                )
            else:
                embed.add_field(
                    name="🔝 Most Used Commands",
                    value="No commands used yet!",
                    inline=False
                )
            
            embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else None)
            embed.set_footer(text=f"Statistics for {target_user.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description="Could not retrieve command statistics.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='servercommands', aliases=['servercmds'])
    async def server_commands(self, ctx):
        """Show server command usage statistics"""
        if not ctx.guild:
            return await ctx.send("This command can only be used in servers!")
        
        try:
            async with self.bot.database.get_connection() as db:
                # Get server's most used commands
                cursor = await db.execute("""
                    SELECT command_name, COUNT(*) as usage_count
                    FROM command_usage 
                    WHERE guild_id = ?
                    GROUP BY command_name
                    ORDER BY usage_count DESC
                    LIMIT 10
                """, (str(ctx.guild.id),))
                server_stats = await cursor.fetchall()
                
                # Get total commands used in server
                cursor = await db.execute("""
                    SELECT COUNT(*) as total_commands
                    FROM command_usage 
                    WHERE guild_id = ?
                """, (str(ctx.guild.id),))
                total_result = await cursor.fetchone()
                total_commands = total_result[0] if total_result else 0
                
                # Get most active users
                cursor = await db.execute("""
                    SELECT user_id, COUNT(*) as usage_count
                    FROM command_usage 
                    WHERE guild_id = ?
                    GROUP BY user_id
                    ORDER BY usage_count DESC
                    LIMIT 5
                """, (str(ctx.guild.id),))
                active_users = await cursor.fetchall()
            
            embed = discord.Embed(
                title=f"📊 Server Command Statistics",
                description=f"Statistics for **{ctx.guild.name}**",
                color=self.bot.config.color
            )
            
            embed.add_field(
                name="📈 Total Commands Used",
                value=f"**{total_commands:,}** commands",
                inline=False
            )
            
            if server_stats:
                stats_text = []
                for command_name, count in server_stats:
                    stats_text.append(f"`{command_name}`: **{count:,}** times")
                
                embed.add_field(
                    name="🔝 Most Used Commands",
                    value="\n".join(stats_text),
                    inline=True
                )
            
            if active_users:
                users_text = []
                for i, (user_id, count) in enumerate(active_users, 1):
                    try:
                        user = await self.bot.fetch_user(int(user_id))
                        username = user.display_name if user else f"User {user_id}"
                    except:
                        username = f"User {user_id}"
                    
                    users_text.append(f"`{i}.` **{username}**: {count:,} commands")
                
                embed.add_field(
                    name="👑 Most Active Users",
                    value="\n".join(users_text),
                    inline=True
                )
            
            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)
            
            embed.set_footer(text=f"Statistics for {ctx.guild.name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description="Could not retrieve server command statistics.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    async def send_guild_log(self, guild, action):
        """Send guild join/leave log to webhook"""
        if not hasattr(self.bot.config, 'guild_log_webhook'):
            return
        
        try:
            embed = discord.Embed(
                title=f"📊 Server {'Joined' if action == 'join' else 'Left'}",
                color=0x00ff00 if action == 'join' else 0xff0000,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="Server Info",
                value=f"**Name:** {guild.name}\n"
                      f"**ID:** {guild.id}\n"
                      f"**Members:** {guild.member_count}\n"
                      f"**Owner:** <@{guild.owner_id}>",
                inline=True
            )
            
            embed.add_field(
                name="Bot Stats",
                value=f"**Total Servers:** {len(self.bot.guilds)}\n"
                      f"**Total Users:** {sum(g.member_count or 0 for g in self.bot.guilds)}",
                inline=True
            )
            
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            
            embed.set_footer(text=f"Action: {action.title()}")
            
            # Send to webhook
            webhook_url = self.bot.config.guild_log_webhook
            async with aiohttp.ClientSession() as session:
                webhook_data = {
                    'embeds': [embed.to_dict()]
                }
                async with session.post(webhook_url, json=webhook_data) as response:
                    if response.status != 204:
                        print(f"Failed to send guild log webhook: {response.status}")
            
        except Exception as e:
            print(f"Error sending guild log: {e}")


async def setup(bot):
    await bot.add_cog(WebhooksAndVotes(bot))