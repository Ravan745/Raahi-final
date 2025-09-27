#!/usr/bin/env python3

import asyncio
import logging
import os
import aiosqlite
import discord
import wavelink
from discord.ext import commands
from config import Config
from database import AvonDatabase
from utils import AvonUtils
from emoji_config import AvonEmoji
from dispatcher import AvonDispatcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class AvonBot(commands.Bot):
    """Main bot class for Avon Discord music bot"""
    
    def __init__(self):
        # Discord intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.guilds = True
        intents.guild_messages = True
        
        # Initialize bot
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        # Load configuration and components
        self.config = Config()
        self.database = AvonDatabase()
        self.utils = AvonUtils(self)
        self.emoji = AvonEmoji()
        self.dispatchers = {}  # Guild ID -> Dispatcher
        
        # Bot stats
        self.start_time = None
        
    async def get_prefix(self, message):
        """Dynamic prefix system matching TypeScript version with no-prefix support"""
        if not message.guild:
            return self.config.prefix
        
        # Check for no-prefix access
        user_id = str(message.author.id)
        guild_id = str(message.guild.id)
        
        # Check global no-prefix
        if await self.utils.check_global_np(user_id):
            return commands.when_mentioned_or("")(self, message)
        
        # Check server-specific no-prefix
        if await self.utils.check_guild_np(guild_id, user_id):
            return commands.when_mentioned_or("")(self, message)
        
        # Get custom prefix from database
        custom_prefix = await self.utils.get_prefix(guild_id)
        return commands.when_mentioned_or(custom_prefix)(self, message)
    
    async def setup_hook(self):
        """Setup hook called when bot is starting"""
        # Initialize database
        await self.init_database()
        
        # Connect to Lavalink
        await self.connect_lavalink()
        
        # Load cogs/extensions
        await self.load_cogs()
        
        print(f"🎵 Avon Bot setup complete!")
    
    async def init_database(self):
        """Initialize database with all tables matching TypeScript version"""
        await self.database.init_all_tables()
    
    async def connect_lavalink(self):
        """Connect to Lavalink server"""
        try:
            nodes = []
            for node_config in self.config.lavalink_config:
                node = wavelink.Node(
                    identifier=node_config["identifier"],
                    uri=f"{'wss' if node_config['secure'] else 'ws'}://{node_config['host']}:{node_config['port']}",
                    password=node_config["password"]
                )
                nodes.append(node)
            
            # Connect to wavelink
            await wavelink.Pool.connect(nodes=nodes, client=self)
            print(f"🔗 Connected to Lavalink server: {self.config.lavalink_nodes[0]['host']}")
            
        except Exception as e:
            print(f"❌ Failed to connect to Lavalink: {e}")
    
    async def load_cogs(self):
        """Load all command cogs"""
        try:
            # Load consolidated music cog (replaces music, advanced_music, filters, beautiful_player, button_interactions, spotify_integration)
            await self.load_extension('cogs.consolidated_music')
            
            # Load webhooks and vote functionality
            await self.load_extension('cogs.webhooks_votes')
            
            # Load other essential cogs
            await self.load_extension('cogs.setup')
            await self.load_extension('cogs.owner')
            await self.load_extension('cogs.afk')
            await self.load_extension('cogs.utility')
            # Skip slash_commands cog as functionality is now in consolidated_music
            await self.load_extension('cogs.premium')
            await self.load_extension('cogs.dj_permissions')
            # Skip missing_controls cog due to command conflicts
            print("📁 All cogs loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load cogs: {e}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        self.start_time = discord.utils.utcnow()
        
        print(f"🤖 {self.user} is online and ready!")
        print(f"📊 Connected to {len(self.guilds)} guilds")
        total_members = sum(guild.member_count or 0 for guild in self.guilds)
        print(f"👥 Serving {total_members} users")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{self.config.prefix}help | Music for everyone!"
        )
        await self.change_presence(activity=activity, status=discord.Status.online)
    
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        """Called when Lavalink node is ready"""
        print(f"🎵 Lavalink node '{payload.node.identifier}' is ready!")
    
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        """Called when a track starts playing"""
        player = payload.player
        track = payload.track
        
        if player.guild:
            print(f"🎶 Now playing: {track.title} in {player.guild.name}")
    
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument provided")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.2f} seconds")
        else:
            print(f"Unhandled error: {error}")
            await ctx.send("❌ An unexpected error occurred. Please try again later.")

# Basic commands for testing
@commands.command(name='ping')
async def ping(ctx):
    """Check bot latency"""
    latency = round(ctx.bot.latency * 1000)
    await ctx.send(f"🏓 Pong! `{latency}ms`")

@commands.command(name='test')
async def test_lavalink(ctx):
    """Test Lavalink connection"""
    if not wavelink.Pool.nodes:
        await ctx.send("❌ No Lavalink nodes connected!")
        return
    
    node = wavelink.Pool.get_node()
    await ctx.send(f"✅ Lavalink connected: `{node.identifier}` - `{node.uri}`")

def main():
    """Main function to run the bot"""
    bot = AvonBot()
    
    # Add basic commands
    bot.add_command(ping)
    bot.add_command(test_lavalink)
    
    try:
        bot.run(bot.config.bot_token)
    except discord.LoginFailure:
        print("❌ Invalid bot token! Please check your BOT_TOKEN.")
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")

if __name__ == "__main__":
    main()