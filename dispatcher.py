import discord
import wavelink
import asyncio
from typing import Optional, List, Dict, Any
from utils import AvonUtils
from emoji_config import AvonEmoji

class AvonDispatcher:
    """Advanced dispatcher matching TypeScript version exactly"""
    
    def __init__(self, bot, guild: discord.Guild, channel: discord.TextChannel, player: wavelink.Player):
        self.bot = bot
        self.guild = guild
        self.channel = channel
        self.player = player
        self.utils = AvonUtils(bot)
        self.emoji = AvonEmoji()
        
        # Player state
        self.repeat = "off"  # off, one, all
        self.current = None
        self.previous = None
        self.stopped = False
        self.queue = []
        self.data = {}
        
        # Set up player events
        self.setup_player_events()
    
    def setup_player_events(self):
        """Setup player event handlers"""
        @self.player.on_track_start
        async def on_track_start(payload: wavelink.TrackStartEventPayload):
            await self.handle_track_start(payload)
        
        @self.player.on_track_end  
        async def on_track_end(payload: wavelink.TrackEndEventPayload):
            await self.handle_track_end(payload)
    
    async def handle_track_start(self, payload):
        """Handle track start - send now playing with appropriate UI"""
        self.current = payload.track
        
        # Handle repeat logic
        if self.repeat == "one":
            if hasattr(self, 'punit') and self.punit:
                return
            else:
                self.punit = True
        elif self.repeat in ["all", "off"]:
            self.punit = False
        
        # Check if DJ setup exists and update it
        if await self.utils.check_dj_setup(self.guild.id):
            await self.update_dj_setup()
        
        # Get player mode and send appropriate UI
        mode = await self.utils.get_player_mode(self.guild.id)
        dj_setup = await self.utils.get_dj(self.guild.id)
        
        # Don't send UI if this is the DJ channel
        if dj_setup and dj_setup.get("CHANNEL") == str(self.channel.id):
            return
            
        await self.send_now_playing_ui(mode)
    
    async def update_dj_setup(self):
        """Update DJ setup message"""
        try:
            dj_setup = await self.utils.get_dj(self.guild.id)
            if not dj_setup or not dj_setup.get("CHANNEL") or not dj_setup.get("MESSAGE"):
                return
            
            channel = self.guild.get_channel(int(dj_setup["CHANNEL"]))
            if not channel:
                return
            
            try:
                message = await channel.fetch_message(int(dj_setup["MESSAGE"]))
                
                embed = discord.Embed(
                    title=f"{self.emoji.setup['nowPlaying']} {self.current.title[:40]}",
                    url=self.bot.config.vote_url,
                    color=0xff0000
                )
                
                embed.add_field(
                    name=f"{self.emoji.setup['requester']} Requester",
                    value=f"{self.current.extras.get('requester', 'Unknown')}",
                    inline=True
                )
                
                embed.add_field(
                    name=f"{self.emoji.setup['duration']} Duration", 
                    value=f"{self.utils.humanize(self.current.length)}",
                    inline=True
                )
                
                embed.add_field(
                    name=f"{self.emoji.setup['author']} Song Author",
                    value=f"[{self.current.author}]({self.bot.config.vote_url})",
                    inline=True
                )
                
                embed.set_image(url=self.bot.config.setup_bg_link)
                embed.set_footer(
                    text=f"💘 Thanks for choosing {self.bot.user.name}",
                    icon_url=self.bot.user.display_avatar.url
                )
                embed.set_author(
                    name="| Now Playing",
                    icon_url=self.bot.user.display_avatar.url
                )
                
                await message.edit(embed=embed)
                
            except (discord.NotFound, discord.Forbidden):
                pass
                
        except Exception as e:
            print(f"Error updating DJ setup: {e}")
    
    async def send_now_playing_ui(self, mode: str):
        """Send now playing UI based on mode"""
        if mode == "avon-old":
            await self.send_old_style_ui()
        elif mode == "avon-classic":
            await self.send_classic_ui()
        elif mode == "avon-no":
            await self.send_no_buttons_ui()
        elif mode == "avon-special":
            await self.send_special_ui()
        elif mode == "avon-simple":
            await self.send_simple_ui()
        elif mode == "avon-spotify":
            await self.send_spotify_ui()
        elif mode == "avon-new":
            await self.send_new_ui()
        elif mode == "avon-beautiful":
            await self.send_beautiful_ui()
        else:
            await self.send_beautiful_ui()  # Default to beautiful player
    
    async def send_old_style_ui(self):
        """Send old style UI"""
        embed = await self.utils.premium_embed(str(self.guild.id))
        embed.description = (
            f"[{self.current.title}]({self.bot.config.vote_url}) By "
            f"[{self.current.author}]({self.bot.config.vote_url}) "
            f"[{self.utils.humanize(self.current.length)}]"
        )
        embed.set_thumbnail(url=getattr(self.current.extras.get('requester'), 'display_avatar', {}).get('url', ''))
        embed.set_author(
            name="| Now Playing",
            icon_url=getattr(self.current.extras.get('requester'), 'display_avatar', {}).get('url', '')
        )
        
        # Create buttons
        view = AvonPlayerView()
        view.add_buttons([
            self.create_button("Stop", 4, "avon_stop"),
            self.create_button("Pause", 3, "avon_pause"),
            self.create_button("Loop", 1, "avon_loop"),
            self.create_button("Previous", 2, "avon_previous"),
            self.create_button("Skip", 2, "avon_skip")
        ])
        
        try:
            msg = await self.channel.send(embed=embed, view=view)
            self.data["current_message"] = msg
        except:
            pass
    
    async def send_classic_ui(self):
        """Send classic style UI"""
        embed = await self.utils.premium_embed(str(self.guild.id))
        embed.set_thumbnail(url=f"https://img.youtube.com/vi/{self.current.identifier}/maxresdefault.jpg")
        embed.title = f"{self.emoji.avonNew['nowPlaying']} {self.current.title[:30]}"
        embed.url = self.bot.config.vote_url
        embed.description = (
            f"{self.emoji.avonNew['requester']} **Requester:** {self.current.extras.get('requester', 'Unknown')}\n"
            f"{self.emoji.avonNew['duration']} **Duration:** {self.utils.humanize(self.current.length)}"
        )
        
        view = AvonPlayerView()
        view.add_buttons([
            self.create_button("Stop", 4, "avon_stop"),
            self.create_button("Pause", 3, "avon_pause"),
            self.create_button("Loop", 1, "avon_loop"),
            self.create_button("Previous", 2, "avon_previous"),
            self.create_button("Skip", 2, "avon_skip")
        ])
        
        try:
            msg = await self.channel.send(embed=embed, view=view)
            self.data["current_message"] = msg
        except:
            pass
    
    async def send_no_buttons_ui(self):
        """Send no buttons style UI with filter dropdown"""
        embed = await self.utils.premium_embed(str(self.guild.id))
        embed.set_author(name="Now Playing", icon_url=self.bot.user.display_avatar.url)
        embed.set_thumbnail(url=getattr(self.current.extras.get('requester'), 'display_avatar', {}).get('url', ''))
        embed.description = f"{self.emoji.noButtons['emote']} [{self.current.title[:35]}]({self.bot.config.vote_url})"
        
        embed.add_field(
            name=f"{self.emoji.noButtons['requester']} Requester",
            value=f"{self.current.extras.get('requester', 'Unknown')}",
            inline=True
        )
        embed.add_field(
            name=f"{self.emoji.noButtons['duration']} Duration",
            value=f"{self.utils.humanize(self.current.length)}",
            inline=True
        )
        
        # Create filter dropdown
        view = AvonFilterView()
        
        try:
            msg = await self.channel.send(embed=embed, view=view)
            self.data["current_message"] = msg
        except:
            pass
    
    async def send_special_ui(self):
        """Send special style UI with full controls"""
        embed = await self.utils.premium_embed(str(self.guild.id))
        embed.title = f"{self.current.title[:35]}"
        embed.url = self.bot.config.vote_url
        embed.set_thumbnail(url=f"https://img.youtube.com/vi/{self.current.identifier}/maxresdefault.jpg")
        
        embed.add_field(
            name=f"{self.emoji.special['requester']} Requester",
            value=f"{self.current.extras.get('requester', 'Unknown')}",
            inline=True
        )
        embed.add_field(
            name=f"{self.emoji.special['duration']} Duration",
            value=f"{self.utils.humanize(self.current.length)}",
            inline=True
        )
        
        view = AvonSpecialView()
        
        try:
            msg = await self.channel.send(embed=embed, view=view)
            self.data["current_message"] = msg
        except:
            pass
    
    async def send_simple_ui(self):
        """Send simple style UI"""
        embed = await self.utils.premium_embed(str(self.guild.id))
        embed.set_author(name="Now Playing", icon_url=self.bot.user.display_avatar.url)
        embed.description = f"[{self.current.title[:35]}]({self.bot.config.vote_url})"
        
        embed.add_field(
            name=f"{self.emoji.simple['requester']} Requester",
            value=f"{self.current.extras.get('requester', 'Unknown')}",
            inline=True
        )
        embed.add_field(
            name=f"{self.emoji.simple['duration']} Duration", 
            value=f"{self.utils.humanize(self.current.length)}",
            inline=True
        )
        embed.add_field(
            name=f"{self.emoji.simple['author']} Author",
            value=f"{self.current.author}",
            inline=True
        )
        
        view = AvonSimpleView()
        
        try:
            msg = await self.channel.send(embed=embed, view=view)
            self.data["current_message"] = msg
        except:
            pass
    
    async def send_spotify_ui(self):
        """Send Spotify style UI"""
        embed = await self.utils.premium_embed(str(self.guild.id))
        embed.set_author(name="Now Playing", icon_url=self.bot.user.display_avatar.url)
        embed.description = (
            f"{self.emoji.spotify['nowPlaying']} "
            f"[{self.current.title[:40]}]({self.bot.config.vote_url})"
        )
        
        thumbnail_url = f"https://img.youtube.com/vi/{self.current.identifier}/maxresdefault.jpg"
        if not thumbnail_url:
            thumbnail_url = getattr(self.current.extras.get('requester'), 'display_avatar', {}).get('url', '')
        embed.set_thumbnail(url=thumbnail_url)
        
        embed.add_field(
            name=f"{self.emoji.spotify['requester']} Requester",
            value=f"{self.current.extras.get('requester', 'Unknown')}",
            inline=True
        )
        embed.add_field(
            name=f"{self.emoji.spotify['duration']} Duration",
            value=f"{self.utils.humanize(self.current.length)}",
            inline=True
        )
        
        view = AvonSpotifyView()
        
        try:
            msg = await self.channel.send(embed=embed, view=view)
            self.data["current_message"] = msg
        except:
            pass
    
    async def send_new_ui(self):
        """Send new style UI"""
        embed = await self.utils.premium_embed(str(self.guild.id))
        embed.description = (
            f"{self.emoji.avonNew['nowPlaying']} "
            f"[`{self.current.title[:35]}`]({self.bot.config.vote_url})\n"
            f"{self.emoji.avonNew['requester']} **Requester:** {self.current.extras.get('requester', 'Unknown')}\n"
            f"{self.emoji.avonNew['duration']} {self.utils.humanize(self.current.length)}"
        )
        embed.set_author(
            name="Now Playing",
            icon_url=getattr(self.current.extras.get('requester'), 'display_avatar', {}).get('url', '')
        )
        
        view = AvonNewView()
        
        try:
            msg = await self.channel.send(embed=embed, view=view)
            self.data["current_message"] = msg
        except:
            pass
    
    async def send_beautiful_ui(self):
        """Send beautiful player UI matching reference image"""
        try:
            from cogs.beautiful_player import BeautifulMusicPlayer
            
            if not hasattr(self, 'beautiful_player'):
                self.beautiful_player = BeautifulMusicPlayer(self.bot, self)
            
            await self.beautiful_player.send_beautiful_player(self.current)
        except Exception as e:
            print(f"Error sending beautiful UI: {e}")
            # Fallback to classic UI
            await self.send_classic_ui()
    
    def create_button(self, label: str, style: int, custom_id: str, emoji: str = None) -> discord.ui.Button:
        """Create button with proper styling"""
        button = discord.ui.Button(
            label=label,
            style=discord.ButtonStyle(style),
            custom_id=custom_id
        )
        if emoji:
            button.emoji = emoji
        return button
    
    async def handle_track_end(self, payload):
        """Handle track end"""
        if self.repeat == "one" and not self.stopped:
            # Replay current track
            await self.player.play(self.current)
            return
        
        if self.queue and not self.stopped:
            # Play next track
            next_track = self.queue.pop(0)
            if self.repeat == "all":
                self.queue.append(self.current)
            self.previous = self.current
            await self.player.play(next_track)
        else:
            self.current = None
    
    async def play(self, track=None):
        """Play a track"""
        if track:
            await self.player.play(track)
        elif self.queue:
            next_track = self.queue.pop(0)
            await self.player.play(next_track)

# Views for different player modes
class AvonPlayerView(discord.ui.View):
    """Basic player view"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    def add_buttons(self, buttons):
        for button in buttons:
            self.add_item(button)

class AvonFilterView(discord.ui.View):
    """Filter dropdown view"""
    
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FilterSelect())

class FilterSelect(discord.ui.Select):
    """Filter selection dropdown"""
    
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Reset Filters",
                description="Resets all the filters of the player",
                value="avon_filter_reset"
            ),
            discord.SelectOption(
                label="8D",
                description="Sets Up 8d filter to the player",
                value="avon_filter_8d"
            ),
            discord.SelectOption(
                label="BassBoost",
                description="Sets bassboost filter to the player", 
                value="avon_filter_bassboost"
            ),
            discord.SelectOption(
                label="NightCore",
                description="Sets NightCore filter to the player",
                value="avon_filter_nightcore"
            ),
            discord.SelectOption(
                label="Vaporwave",
                description="Sets Vaporwave filter to the player",
                value="avon_filter_vaporwave"
            )
        ]
        
        super().__init__(
            placeholder="Choose filters",
            options=options,
            custom_id="filter_select"
        )

class AvonSpecialView(discord.ui.View):
    """Special style view with advanced controls"""
    
    def __init__(self):
        super().__init__(timeout=None)
        # Row 1: Basic controls
        # Row 2: Volume and seeking controls

class AvonSimpleView(discord.ui.View):
    """Simple style view"""
    
    def __init__(self):
        super().__init__(timeout=None)

class AvonSpotifyView(discord.ui.View):
    """Spotify style view"""
    
    def __init__(self):
        super().__init__(timeout=None)

class AvonNewView(discord.ui.View):
    """New style view"""
    
    def __init__(self):
        super().__init__(timeout=None)