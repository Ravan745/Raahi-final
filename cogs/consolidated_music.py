import discord
import wavelink
import re
import asyncio
import aiohttp
from discord.ext import commands
from typing import Optional, List, Dict, Any
from dispatcher import AvonDispatcher
import urllib.parse

class ConsolidatedMusicCommands(commands.Cog):
    """Consolidated music commands with all functionality"""
    
    def __init__(self, bot):
        self.bot = bot
        self.spotify_pattern = re.compile(r'https://open\.spotify\.com/(track|album|playlist)/([a-zA-Z0-9]+)')
        
        # Spotify integration
        self.spotify_client_id = self.bot.config.spotify_client_id
        self.spotify_client_secret = self.bot.config.spotify_client_secret
        self.spotify_access_token = None

    # ============= BASIC MUSIC COMMANDS =============
    
    @commands.hybrid_command(name='play', aliases=['p'], description='Play a song or add it to the queue')
    async def play(self, ctx, *, query: str = None):
        """Advanced play command with all functionality"""
        if not query:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"`{ctx.prefix}play <search query or url>`"
            embed.title = "Play Syntax"
            return await ctx.send(embed=embed)
        
        # Check if user is in voice channel
        if not ctx.author.voice:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} You need to be in a voice channel to use this command!"
            embed.title = "Missing Voice Channel"
            return await ctx.send(embed=embed)
        
        # Check if URL
        if self.bot.utils.check_url(query):
            await self.handle_url_play(ctx, query)
        else:
            await self.handle_search_play(ctx, query)
    
    async def handle_url_play(self, ctx, url: str):
        """Handle URL-based play requests"""
        # Check if Spotify URL
        if self.spotify_pattern.match(url):
            await self.handle_spotify_url(ctx, url)
            return
        
        # Handle other URLs (YouTube, SoundCloud, etc.)
        try:
            tracks = await wavelink.Playable.search(url)
            if not tracks:
                embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
                embed.description = f"{self.bot.emoji.cross} No results found for the URL provided"
                return await ctx.send(embed=embed)
            
            # Check if playlist
            if hasattr(tracks, 'playlist_info') and tracks.playlist_info:
                await self.handle_playlist(ctx, tracks)
            else:
                # Single track
                track = tracks[0] if isinstance(tracks, list) else tracks
                await self.handle_single_track(ctx, track)
                
        except Exception as e:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} Error loading track: {str(e)}"
            await ctx.send(embed=embed)
    
    async def handle_search_play(self, ctx, query: str):
        """Handle search-based play requests"""
        play_type = await self.bot.utils.get_play_type(str(ctx.guild.id))
        
        if play_type == "direct":
            # Direct search mode
            await self.handle_direct_search(ctx, query)
        else:
            # Button search mode (default)
            await self.handle_button_search(ctx, query)
    
    async def handle_direct_search(self, ctx, query: str):
        """Handle direct YouTube search"""
        try:
            tracks = await wavelink.Playable.search(f"ytsearch:{query}")
            if not tracks:
                embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
                embed.description = f"{self.bot.emoji.cross} No results found for the given query"
                embed.title = "No Results"
                return await ctx.send(embed=embed)
            
            track = tracks[0]
            track.extras = {"requester": ctx.author}
            await self.handle_single_track(ctx, track)
            
        except Exception as e:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} Error searching: {str(e)}"
            await ctx.send(embed=embed)
    
    async def handle_button_search(self, ctx, query: str):
        """Handle button-based search engine selection"""
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.description = "Choose One of the buttons below to prefer your search type"
        embed.title = "Search Engines"
        
        view = SearchEngineView(ctx, query, self.bot)
        
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg
    
    async def handle_single_track(self, ctx, track):
        """Handle adding a single track"""
        dispatcher = await self.get_or_create_dispatcher(ctx, track)
        if not dispatcher:
            return
        
        dispatcher.queue.append(track)
        
        if not dispatcher.player.current:
            await dispatcher.play()
            # Send beautiful player UI
            await self.send_beautiful_player(dispatcher, track)
        
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.description = (
            f"{self.bot.emoji.queue} Added "
            f"[{track.title[:35]}]({self.bot.config.vote_url}) to Queue"
        )
        await ctx.send(embed=embed)
    
    async def handle_playlist(self, ctx, tracks):
        """Handle adding a playlist"""
        dispatcher = await self.get_or_create_dispatcher(ctx, tracks[0])
        if not dispatcher:
            return
        
        # Add all tracks to queue
        for track in tracks:
            track.extras = {"requester": ctx.author}
            dispatcher.queue.append(track)
        
        if not dispatcher.player.current:
            await dispatcher.play()
        
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.description = (
            f"{self.bot.emoji.queue} Added **{len(tracks)}** tracks "
            f"from playlist to queue"
        )
        await ctx.send(embed=embed)
    
    async def get_or_create_dispatcher(self, ctx, track) -> Optional[AvonDispatcher]:
        """Get existing dispatcher or create new one"""
        guild_id = str(ctx.guild.id)
        
        # Check if dispatcher already exists
        if guild_id in self.bot.dispatchers:
            return self.bot.dispatchers[guild_id]
        
        # Check bot permissions in voice channel
        voice_channel = ctx.author.voice.channel
        permissions = voice_channel.permissions_for(ctx.guild.me)
        
        if not permissions.connect or not permissions.speak:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = (
                f"{self.bot.emoji.cross} I don't have **Connect** or **Speak** "
                f"permissions in your voice channel"
            )
            embed.title = "Missing Permissions"
            await ctx.send(embed=embed)
            return None
        
        # Connect to voice channel
        try:
            player = await voice_channel.connect(cls=wavelink.Player)
            await player.set_volume(self.bot.config.default_volume)
            
            # Create dispatcher
            dispatcher = AvonDispatcher(self.bot, ctx.guild, ctx.channel, player)
            self.bot.dispatchers[guild_id] = dispatcher
            
            return dispatcher
            
        except Exception as e:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} Failed to connect: {str(e)}"
            await ctx.send(embed=embed)
            return None
    
    # ============= PLAYER CONTROLS =============
    
    @commands.hybrid_command(name='stop', aliases=['disconnect', 'dc'], description='Stop music and disconnect')
    async def stop(self, ctx):
        """Stop music and disconnect"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.bot.dispatchers:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} I'm not connected to any voice channel!"
            return await ctx.send(embed=embed)
        
        dispatcher = self.bot.dispatchers[guild_id]
        dispatcher.stopped = True
        
        await dispatcher.player.disconnect()
        del self.bot.dispatchers[guild_id]
        
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.description = "⏹️ Stopped the music and disconnected"
        await ctx.send(embed=embed)
    
    @commands.command(name='pause')
    async def pause(self, ctx):
        """Pause the current track"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.bot.dispatchers:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} Nothing is currently playing!"
            return await ctx.send(embed=embed)
        
        dispatcher = self.bot.dispatchers[guild_id]
        
        if not dispatcher.player.playing:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} Nothing is currently playing!"
            return await ctx.send(embed=embed)
        
        await dispatcher.player.pause(True)
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.description = "⏸️ Paused the current track"
        await ctx.send(embed=embed)
    
    @commands.command(name='resume')
    async def resume(self, ctx):
        """Resume the paused track"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.bot.dispatchers:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} I'm not connected to any voice channel!"
            return await ctx.send(embed=embed)
        
        dispatcher = self.bot.dispatchers[guild_id]
        
        if not dispatcher.player.paused:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} The player is not paused!"
            return await ctx.send(embed=embed)
        
        await dispatcher.player.pause(False)
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.description = "▶️ Resumed the track"
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='skip', aliases=['s'], description='Skip the current track')
    async def skip(self, ctx):
        """Skip the current track"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.bot.dispatchers:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} Nothing is currently playing!"
            return await ctx.send(embed=embed)
        
        dispatcher = self.bot.dispatchers[guild_id]
        
        if not dispatcher.player.playing:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} Nothing is currently playing!"
            return await ctx.send(embed=embed)
        
        await dispatcher.player.skip()
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.description = "⏭️ Skipped the current track"
        await ctx.send(embed=embed)
    
    @commands.command(name='volume', aliases=['vol'])
    async def volume(self, ctx, volume: int = None):
        """Change or check the player volume"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.bot.dispatchers:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} I'm not connected to any voice channel!"
            return await ctx.send(embed=embed)
        
        dispatcher = self.bot.dispatchers[guild_id]
        
        if volume is None:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"🔊 Current volume: **{dispatcher.player.volume}%**"
            return await ctx.send(embed=embed)
        
        if volume < 0 or volume > 100:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} Volume must be between 0 and 100!"
            return await ctx.send(embed=embed)
        
        await dispatcher.player.set_volume(volume)
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.description = f"🔊 Set volume to **{volume}%**"
        await ctx.send(embed=embed)
    
    @commands.command(name='queue', aliases=['q'])
    async def queue(self, ctx):
        """Show the current queue"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.bot.dispatchers:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} I'm not connected to any voice channel!"
            return await ctx.send(embed=embed)
        
        dispatcher = self.bot.dispatchers[guild_id]
        
        if not dispatcher.queue:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = "📭 The queue is empty!"
            return await ctx.send(embed=embed)
        
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.title = "📋 Current Queue"
        
        queue_list = []
        for i, track in enumerate(dispatcher.queue[:10], 1):  # Show only first 10 tracks
            queue_list.append(f"`{i}.` **{track.title[:40]}**")
        
        if len(dispatcher.queue) > 10:
            queue_list.append(f"... and {len(dispatcher.queue) - 10} more tracks")
        
        embed.description = "\n".join(queue_list)
        
        if dispatcher.player.current:
            embed.add_field(
                name="🎶 Now Playing",
                value=f"**{dispatcher.player.current.title}**",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='nowplaying', aliases=['np'])
    async def nowplaying(self, ctx):
        """Show the currently playing track"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.bot.dispatchers:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} Nothing is currently playing!"
            return await ctx.send(embed=embed)
        
        dispatcher = self.bot.dispatchers[guild_id]
        
        if not dispatcher.player.current:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} Nothing is currently playing!"
            return await ctx.send(embed=embed)
        
        track = dispatcher.player.current
        
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.title = "🎶 Now Playing"
        embed.description = f"**{track.title}**\n"
        
        if hasattr(track, 'author') and track.author:
            embed.description += f"👤 **Author:** {track.author}\n"
        
        embed.description += f"⏱️ **Duration:** {self.format_time(track.length)}"
        
        if hasattr(track, 'artwork') and track.artwork:
            embed.set_thumbnail(url=track.artwork)
        
        await ctx.send(embed=embed)
    
    # ============= AUDIO FILTERS =============
    
    async def apply_filter(self, player, filter_name: str):
        """Apply a filter to the player"""
        try:
            filters = wavelink.Filters()
            
            # Apply the specific filter
            if filter_name == "nightcore":
                filters.timescale.set(speed=1.3, pitch=1.2, rate=1.0)
            elif filter_name == "daycore":
                filters.timescale.set(speed=0.8, pitch=0.8, rate=1.0)
            elif filter_name == "bassboost":
                filters.equalizer.set(bands=[(0, 0.6), (1, 0.67), (2, 0.67)])
            elif filter_name == "8d":
                filters.rotation.set(rotation_hz=0.2)
            elif filter_name == "karaoke":
                filters.karaoke.set(level=1.0, mono_level=1.0, filter_band=220.0, filter_width=100.0)
            elif filter_name == "tremolo":
                filters.tremolo.set(frequency=2.0, depth=0.9)
            elif filter_name == "vibrato":
                filters.vibrato.set(frequency=2.0, depth=0.9)
            elif filter_name == "chipmunk":
                filters.timescale.set(speed=1.05, pitch=1.35, rate=1.25)
            elif filter_name == "vaporwave":
                filters.timescale.set(speed=0.8, pitch=0.8, rate=1.0)
                filters.equalizer.set(bands=[(0, -0.25), (1, -0.25), (2, 0.0)])
            elif filter_name == "pop":
                filters.equalizer.set(bands=[(0, -0.25), (1, 0.48), (2, 0.59), (3, 0.72), (4, 0.56), (5, 0.15), (6, -0.24), (7, -0.24), (8, -0.16), (9, -0.16)])
            elif filter_name == "soft":
                filters.low_pass.set(smoothing=20.0)
            
            await player.set_filters(filters)
            return True
            
        except Exception as e:
            print(f"Filter error: {e}")
            return False
    
    @commands.command(name='nightcore')
    async def nightcore(self, ctx):
        """Apply nightcore filter (higher pitch and speed)"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.bot.dispatchers:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} I'm not connected to any voice channel!"
            return await ctx.send(embed=embed)
        
        dispatcher = self.bot.dispatchers[guild_id]
        success = await self.apply_filter(dispatcher.player, "nightcore")
        
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        if success:
            embed.description = "🎵 **Nightcore** filter applied!"
        else:
            embed.description = f"{self.bot.emoji.cross} Failed to apply nightcore filter!"
        
        await ctx.send(embed=embed)
    
    @commands.command(name='bassboost', aliases=['bass'])
    async def bassboost(self, ctx):
        """Apply bass boost filter"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.bot.dispatchers:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} I'm not connected to any voice channel!"
            return await ctx.send(embed=embed)
        
        dispatcher = self.bot.dispatchers[guild_id]
        success = await self.apply_filter(dispatcher.player, "bassboost")
        
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        if success:
            embed.description = "🎵 **Bass Boost** filter applied!"
        else:
            embed.description = f"{self.bot.emoji.cross} Failed to apply bass boost filter!"
        
        await ctx.send(embed=embed)
    
    @commands.command(name='clearfilters', aliases=['clear'])
    async def clear_filters(self, ctx):
        """Remove all applied filters"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.bot.dispatchers:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} I'm not connected to any voice channel!"
            return await ctx.send(embed=embed)
        
        dispatcher = self.bot.dispatchers[guild_id]
        
        try:
            # Reset all filters
            filters = wavelink.Filters()
            await dispatcher.player.set_filters(filters)
            
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = "🔄 All filters have been cleared!"
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} Failed to clear filters: {str(e)}"
            await ctx.send(embed=embed)
    
    # ============= SPOTIFY INTEGRATION =============
    
    async def get_spotify_access_token(self):
        """Get Spotify API access token"""
        if not self.spotify_client_id or not self.spotify_client_secret:
            return None
        
        auth_url = "https://accounts.spotify.com/api/token"
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.spotify_client_id,
            'client_secret': self.spotify_client_secret
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(auth_url, data=auth_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.spotify_access_token = data.get('access_token')
                    return self.spotify_access_token
        return None
    
    async def handle_spotify_url(self, ctx, url: str):
        """Handle Spotify URL with full integration"""
        # Show loading message
        loading_embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        loading_embed.description = f"{self.bot.emoji.loading} Processing Spotify URL..."
        loading_msg = await ctx.send(embed=loading_embed)
        
        try:
            # Extract Spotify ID from URL
            match = self.spotify_pattern.search(url)
            if not match:
                embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
                embed.description = f"{self.bot.emoji.cross} Invalid Spotify URL"
                return await loading_msg.edit(embed=embed)
            
            url_type, spotify_id = match.groups()
            
            # Get search queries from Spotify
            search_queries = await self.get_spotify_search_queries(url_type, spotify_id)
            
            if not search_queries:
                embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
                embed.description = f"{self.bot.emoji.cross} Could not process Spotify URL"
                return await loading_msg.edit(embed=embed)
            
            # Get or create dispatcher
            dispatcher = await self.get_or_create_dispatcher(ctx, None)
            if not dispatcher:
                return
            
            added_tracks = []
            failed_tracks = []
            
            for query_data in search_queries[:20]:  # Limit to 20 tracks
                try:
                    # Search on Lavalink/YouTube
                    tracks = await wavelink.Playable.search(query_data['query'])
                    if tracks:
                        track = tracks[0]
                        track.extras = {"requester": ctx.author}
                        dispatcher.queue.append(track)
                        added_tracks.append(query_data['title'])
                    else:
                        failed_tracks.append(query_data['title'])
                except:
                    failed_tracks.append(query_data['title'])
            
            # Start playing if nothing is current
            if not dispatcher.player.current and added_tracks:
                await dispatcher.play()
            
            # Send success message
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.title = "🎵 Spotify Import Complete"
            
            if added_tracks:
                embed.add_field(
                    name=f"✅ Added ({len(added_tracks)} tracks)",
                    value="\n".join([f"`{i+1}.` {track[:40]}..." if len(track) > 40 else f"`{i+1}.` {track}" 
                                   for i, track in enumerate(added_tracks[:10])]) + 
                          (f"\n... and {len(added_tracks) - 10} more" if len(added_tracks) > 10 else ""),
                    inline=False
                )
            
            if failed_tracks:
                embed.add_field(
                    name=f"❌ Failed ({len(failed_tracks)} tracks)",
                    value=f"Could not find {len(failed_tracks)} tracks on YouTube",
                    inline=False
                )
            
            embed.color = 0x1DB954  # Spotify green
            await loading_msg.edit(embed=embed)
            
        except Exception as e:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} Error processing Spotify URL: {str(e)}"
            await loading_msg.edit(embed=embed)
    
    async def get_spotify_search_queries(self, url_type: str, spotify_id: str):
        """Get search queries from Spotify URL"""
        if not await self.get_spotify_access_token():
            return []
        
        headers = {'Authorization': f'Bearer {self.spotify_access_token}'}
        
        async with aiohttp.ClientSession() as session:
            if url_type == "track":
                url = f"https://api.spotify.com/v1/tracks/{spotify_id}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        artist = data['artists'][0]['name'] if data['artists'] else ''
                        title = data['name']
                        return [{'title': f"{artist} - {title}", 'query': f"{artist} {title}"}]
            
            elif url_type == "album":
                url = f"https://api.spotify.com/v1/albums/{spotify_id}/tracks"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        queries = []
                        for track in data['items']:
                            artist = track['artists'][0]['name'] if track['artists'] else ''
                            title = track['name']
                            queries.append({'title': f"{artist} - {title}", 'query': f"{artist} {title}"})
                        return queries
            
            elif url_type == "playlist":
                url = f"https://api.spotify.com/v1/playlists/{spotify_id}/tracks"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        queries = []
                        for item in data['items']:
                            if item['track'] and item['track']['type'] == 'track':
                                track = item['track']
                                artist = track['artists'][0]['name'] if track['artists'] else ''
                                title = track['name']
                                queries.append({'title': f"{artist} - {title}", 'query': f"{artist} {title}"})
                        return queries
        
        return []
    
    # ============= BEAUTIFUL PLAYER =============
    
    async def send_beautiful_player(self, dispatcher, track: wavelink.Playable):
        """Send the beautiful player UI"""
        embed = discord.Embed(color=0x57f287)  # Green accent color
        
        # Get track artwork
        if hasattr(track, 'artwork') and track.artwork:
            embed.set_thumbnail(url=track.artwork)
        
        # Format the title
        title_text = f"🎵 Now Playing: [{track.title[:50]}]({track.uri or 'https://youtube.com'})"
        embed.description = title_text
        
        # Add track details
        details = []
        
        if hasattr(track, 'author') and track.author:
            details.append(f"**{track.author}**")
        
        duration = self.format_time(track.length)
        details.append(f"Duration: {duration}")
        
        source = self.get_source_name(track)
        details.append(f"Source: {source}")
        
        if hasattr(track, 'extras') and track.extras.get('requester'):
            requester = track.extras['requester']
            details.append(f"Requested by: {requester.display_name}")
        
        embed.add_field(name="", value="\n".join(details), inline=False)
        embed.timestamp = discord.utils.utcnow()
        
        # Create control buttons
        view = BeautifulPlayerView(dispatcher, self.bot)
        
        try:
            await dispatcher.channel.send(embed=embed, view=view)
        except:
            pass
    
    # ============= UTILITY FUNCTIONS =============
    
    def format_time(self, milliseconds):
        """Format time from milliseconds to readable format"""
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        hours = minutes // 60
        minutes = minutes % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def get_source_name(self, track):
        """Get the source name of the track"""
        if hasattr(track, 'source') and track.source:
            return track.source.title()
        elif hasattr(track, 'uri') and track.uri:
            if 'youtube' in track.uri.lower():
                return "YouTube"
            elif 'soundcloud' in track.uri.lower():
                return "SoundCloud"
            elif 'spotify' in track.uri.lower():
                return "Spotify"
        return "Unknown"
    
    # ============= BUTTON INTERACTIONS =============
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle button interactions"""
        if interaction.type != discord.InteractionType.component:
            return
        
        custom_id = interaction.data.get('custom_id', '')
        
        # Handle player control buttons
        if custom_id.startswith('avon_'):
            await self.handle_player_buttons(interaction, custom_id)
    
    async def handle_player_buttons(self, interaction: discord.Interaction, custom_id: str):
        """Handle player control buttons"""
        guild_id = str(interaction.guild.id)
        
        # Check if bot is connected
        if guild_id not in self.bot.dispatchers:
            await interaction.response.send_message(
                f"{self.bot.emoji.cross} I'm not connected to any voice channel!",
                ephemeral=True
            )
            return
        
        dispatcher = self.bot.dispatchers[guild_id]
        
        # Handle different button actions
        if custom_id == 'avon_pause':
            if dispatcher.player.paused:
                await dispatcher.player.pause(False)
                await interaction.response.send_message("▶️ Resumed", ephemeral=True)
            else:
                await dispatcher.player.pause(True) 
                await interaction.response.send_message("⏸️ Paused", ephemeral=True)
        
        elif custom_id == 'avon_skip':
            if not dispatcher.player.playing:
                await interaction.response.send_message(
                    f"{self.bot.emoji.cross} Nothing is currently playing!",
                    ephemeral=True
                )
                return
            
            await dispatcher.player.skip()
            await interaction.response.send_message("⏭️ Skipped", ephemeral=True)
        
        elif custom_id == 'avon_stop':
            dispatcher.stopped = True
            await dispatcher.player.disconnect()
            del self.bot.dispatchers[guild_id]
            await interaction.response.send_message("⏹️ Stopped and disconnected", ephemeral=True)


class SearchEngineView(discord.ui.View):
    """Search engine selection view"""
    
    def __init__(self, ctx, query: str, bot):
        super().__init__(timeout=70.0)
        self.ctx = ctx
        self.query = query
        self.bot = bot
        self.message = None
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if user can use the interaction"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                f"{self.bot.emoji.cross} You are not the command requester",
                ephemeral=True
            )
            return False
        return True
    
    @discord.ui.button(
        emoji="🎵",
        label="YouTube Search",
        style=discord.ButtonStyle.secondary,
        custom_id="avon_default_search"
    )
    async def youtube_search(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle YouTube search"""
        await interaction.response.defer()
        
        try:
            tracks = await wavelink.Playable.search(f"ytsearch:{self.query}")
            if not tracks:
                embed = await self.bot.utils.premium_embed(str(self.ctx.guild.id))
                embed.description = f"{self.bot.emoji.cross} No results found for the given query"
                await interaction.edit_original_response(embed=embed, view=None)
                return
            
            track = tracks[0]
            track.extras = {"requester": self.ctx.author}
            
            # Get music cog to handle track
            music_cog = self.bot.get_cog('ConsolidatedMusicCommands')
            dispatcher = await music_cog.get_or_create_dispatcher(self.ctx, track)
            
            if dispatcher:
                dispatcher.queue.append(track)
                if not dispatcher.player.current:
                    await dispatcher.play()
                
                embed = await self.bot.utils.premium_embed(str(self.ctx.guild.id))
                embed.description = (
                    f"{self.bot.emoji.queue} Added "
                    f"[{track.title[:35]}]({self.bot.config.vote_url}) to Queue"
                )
                await interaction.edit_original_response(embed=embed, view=None)
            
        except Exception as e:
            embed = await self.bot.utils.premium_embed(str(self.ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} Error: {str(e)}"
            await interaction.edit_original_response(embed=embed, view=None)
    
    @discord.ui.button(
        emoji="🎧",
        label="SoundCloud Search",
        style=discord.ButtonStyle.primary,
        custom_id="avon_sound_search"
    )
    async def soundcloud_search(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle SoundCloud search"""
        await interaction.response.defer()
        
        try:
            tracks = await wavelink.Playable.search(f"scsearch:{self.query}")
            if not tracks:
                embed = await self.bot.utils.premium_embed(str(self.ctx.guild.id))
                embed.description = f"{self.bot.emoji.cross} No results found for the query"
                await interaction.edit_original_response(embed=embed, view=None)
                return
            
            track = tracks[0]
            track.extras = {"requester": self.ctx.author}
            
            # Get music cog to handle track
            music_cog = self.bot.get_cog('ConsolidatedMusicCommands')
            dispatcher = await music_cog.get_or_create_dispatcher(self.ctx, track)
            
            if dispatcher:
                dispatcher.queue.append(track)
                if not dispatcher.player.current:
                    await dispatcher.play()
                
                embed = await self.bot.utils.premium_embed(str(self.ctx.guild.id))
                embed.description = (
                    f"{self.bot.emoji.queue} Added "
                    f"[{track.title[:35]}]({self.bot.config.vote_url}) to Queue"
                )
                await interaction.edit_original_response(embed=embed, view=None)
            
        except Exception as e:
            embed = await self.bot.utils.premium_embed(str(self.ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} Error: {str(e)}"
            await interaction.edit_original_response(embed=embed, view=None)
    
    async def on_timeout(self):
        """Handle view timeout"""
        if self.message:
            try:
                embed = await self.bot.utils.premium_embed(str(self.ctx.guild.id))
                embed.description = "**You took too long to respond!**"
                await self.message.edit(embed=embed, view=None)
            except:
                pass


class BeautifulPlayerView(discord.ui.View):
    """Beautiful player control view"""
    
    def __init__(self, dispatcher, bot):
        super().__init__(timeout=None)
        self.dispatcher = dispatcher
        self.bot = bot
    
    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.secondary, custom_id="avon_pause")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Pause/Resume button"""
        if self.dispatcher.player.paused:
            await self.dispatcher.player.pause(False)
            button.emoji = "⏸️"
            await interaction.response.edit_message(view=self)
        else:
            await self.dispatcher.player.pause(True)
            button.emoji = "▶️"
            await interaction.response.edit_message(view=self)
    
    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, custom_id="avon_skip")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Skip button"""
        await self.dispatcher.player.skip()
        await interaction.response.send_message("⏭️ Skipped", ephemeral=True)
    
    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, custom_id="avon_stop")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Stop button"""
        self.dispatcher.stopped = True
        await self.dispatcher.player.disconnect()
        if str(self.dispatcher.guild.id) in self.bot.dispatchers:
            del self.bot.dispatchers[str(self.dispatcher.guild.id)]
        await interaction.response.send_message("⏹️ Stopped", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ConsolidatedMusicCommands(bot))