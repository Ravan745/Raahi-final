import discord
from discord.ext import commands
from typing import Optional

class SetupCommands(commands.Cog):
    """Setup commands matching TypeScript version exactly"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.group(name='setup', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx):
        """Main setup command"""
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.title = "Avon Setup Commands"
        embed.description = (
            f"`{ctx.prefix}setup dj` - Setup DJ system with dedicated music channel\n"
            f"`{ctx.prefix}setup player <mode>` - Set player mode\n"
            f"`{ctx.prefix}setup play <type>` - Set play command type\n"
            f"`{ctx.prefix}setup prefix <prefix>` - Set custom prefix\n"
            f"`{ctx.prefix}setup autoplay <enable/disable>` - Configure autoplay\n"
            f"`{ctx.prefix}setup 247 <enable/disable>` - Configure 24/7 mode"
        )
        embed.set_footer(text=f"💘 Thanks for choosing {self.bot.user.name}")
        await ctx.send(embed=embed)
    
    @setup.command(name='dj')
    @commands.has_permissions(administrator=True)
    async def setup_dj(self, ctx):
        """Setup DJ system with persistent music controls"""
        # Check if DJ setup already exists
        if await self.bot.utils.check_dj_setup(str(ctx.guild.id)):
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"{self.bot.emoji.cross} DJ Setup already exists for this server!"
            embed.title = "Setup Already Exists"
            return await ctx.send(embed=embed)
        
        # Create DJ setup embed
        embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
        embed.title = f"{self.bot.emoji.setup['nowPlaying']} Nothing Playing"
        embed.description = "Use the buttons below to control music playback"
        embed.set_image(url=self.bot.config.setup_bg_link)
        embed.set_footer(
            text=f"💘 Thanks for choosing {self.bot.user.name}",
            icon_url=self.bot.user.display_avatar.url
        )
        embed.set_author(
            name="| DJ Setup",
            icon_url=self.bot.user.display_avatar.url
        )
        
        # Create DJ control view
        view = DJControlView(self.bot)
        
        try:
            msg = await ctx.send(embed=embed, view=view)
            
            # Save DJ setup to database
            await self.bot.utils.create_dj(str(ctx.guild.id), str(ctx.channel.id), str(msg.id))
            
            # Send confirmation
            success_embed = await self.bot.utils.success_embed()
            success_embed.description = f"{self.bot.emoji.tick} DJ Setup completed successfully!"
            success_embed.title = "Setup Complete"
            await ctx.send(embed=success_embed)
            
        except Exception as e:
            embed = await self.bot.utils.error_embed()
            embed.description = f"{self.bot.emoji.cross} Failed to setup DJ system: {str(e)}"
            await ctx.send(embed=embed)
    
    @setup.command(name='player')
    @commands.has_permissions(administrator=True)
    async def setup_player(self, ctx, mode: str = None):
        """Set player mode"""
        valid_modes = [
            "avon-classic", "avon-spotify", "avon-simple", 
            "avon-special", "avon-no", "avon-old", "avon-new"
        ]
        
        if not mode:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.title = "Player Modes"
            embed.description = (
                "Available player modes:\n"
                f"`avon-classic` - Default player with all controls\n"
                f"`avon-spotify` - Spotify-style interface\n"
                f"`avon-simple` - Simplified controls\n"
                f"`avon-special` - Premium-style interface\n"
                f"`avon-no` - No buttons, filter dropdown only\n"
                f"`avon-old` - Retro style interface\n"
                f"`avon-new` - Modern clean interface"
            )
            embed.set_footer(text=f"Usage: {ctx.prefix}setup player <mode>")
            return await ctx.send(embed=embed)
        
        if mode not in valid_modes:
            embed = await self.bot.utils.error_embed()
            embed.description = f"{self.bot.emoji.cross} Invalid player mode! Use one of: {', '.join(valid_modes)}"
            return await ctx.send(embed=embed)
        
        await self.bot.utils.update_player_mode(str(ctx.guild.id), mode)
        
        embed = await self.bot.utils.success_embed()
        embed.description = f"{self.bot.emoji.tick} Player mode set to **{mode}**"
        embed.title = "Player Mode Updated"
        await ctx.send(embed=embed)
    
    @setup.command(name='play')
    @commands.has_permissions(administrator=True)
    async def setup_play(self, ctx, play_type: str = None):
        """Set play command type"""
        valid_types = ["buttons", "direct"]
        
        if not play_type:
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.title = "Play Types"
            embed.description = (
                "Available play types:\n"
                f"`buttons` - Show search engine selection buttons\n"
                f"`direct` - Search directly on YouTube"
            )
            embed.set_footer(text=f"Usage: {ctx.prefix}setup play <type>")
            return await ctx.send(embed=embed)
        
        if play_type not in valid_types:
            embed = await self.bot.utils.error_embed()
            embed.description = f"{self.bot.emoji.cross} Invalid play type! Use: {', '.join(valid_types)}"
            return await ctx.send(embed=embed)
        
        await self.bot.utils.update_play_type(str(ctx.guild.id), play_type)
        
        embed = await self.bot.utils.success_embed()
        embed.description = f"{self.bot.emoji.tick} Play type set to **{play_type}**"
        embed.title = "Play Type Updated"
        await ctx.send(embed=embed)
    
    @setup.command(name='prefix')
    @commands.has_permissions(administrator=True)
    async def setup_prefix(self, ctx, *, prefix: str = None):
        """Set custom prefix"""
        if not prefix:
            current_prefix = await self.bot.utils.get_prefix(str(ctx.guild.id))
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"Current prefix: `{current_prefix}`"
            embed.title = "Current Prefix"
            embed.set_footer(text=f"Usage: {ctx.prefix}setup prefix <new_prefix>")
            return await ctx.send(embed=embed)
        
        if len(prefix) > 5:
            embed = await self.bot.utils.error_embed()
            embed.description = f"{self.bot.emoji.cross} Prefix cannot be longer than 5 characters!"
            return await ctx.send(embed=embed)
        
        await self.bot.utils.update_prefix(str(ctx.guild.id), prefix)
        
        embed = await self.bot.utils.success_embed()
        embed.description = f"{self.bot.emoji.tick} Prefix updated to `{prefix}`"
        embed.title = "Prefix Updated"
        await ctx.send(embed=embed)
    
    @setup.command(name='autoplay')
    @commands.has_permissions(administrator=True)
    async def setup_autoplay(self, ctx, setting: str = None):
        """Configure autoplay"""
        if not setting or setting.lower() not in ['enable', 'disable']:
            current = await self.bot.utils.get_autoplay(str(ctx.guild.id))
            status = "enabled" if current else "disabled"
            
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"Autoplay is currently **{status}**"
            embed.title = "Autoplay Status"
            embed.set_footer(text=f"Usage: {ctx.prefix}setup autoplay <enable/disable>")
            return await ctx.send(embed=embed)
        
        if setting.lower() == 'enable':
            await self.bot.utils.update_autoplay(str(ctx.guild.id))
            status = "enabled"
        else:
            await self.bot.utils.update_autoplay(str(ctx.guild.id))
            status = "disabled"
        
        embed = await self.bot.utils.success_embed()
        embed.description = f"{self.bot.emoji.tick} Autoplay has been **{status}**"
        embed.title = "Autoplay Updated"
        await ctx.send(embed=embed)
    
    @setup.command(name='247')
    @commands.has_permissions(administrator=True)
    async def setup_247(self, ctx, setting: str = None):
        """Configure 24/7 mode"""
        if not setting or setting.lower() not in ['enable', 'disable']:
            current = await self.bot.utils.get_247(str(ctx.guild.id))
            status = "enabled" if current else "disabled"
            
            embed = await self.bot.utils.premium_embed(str(ctx.guild.id))
            embed.description = f"24/7 mode is currently **{status}**"
            embed.title = "24/7 Status"
            embed.set_footer(text=f"Usage: {ctx.prefix}setup 247 <enable/disable>")
            return await ctx.send(embed=embed)
        
        if setting.lower() == 'enable':
            if not ctx.author.voice:
                embed = await self.bot.utils.error_embed()
                embed.description = f"{self.bot.emoji.cross} You need to be in a voice channel to enable 24/7!"
                return await ctx.send(embed=embed)
            
            voice_channel = ctx.author.voice.channel
            await self.bot.utils.enable_247(str(ctx.guild.id), str(voice_channel.id), str(ctx.channel.id))
            status = "enabled"
        else:
            await self.bot.utils.disable_247(str(ctx.guild.id))
            status = "disabled"
        
        embed = await self.bot.utils.success_embed()
        embed.description = f"{self.bot.emoji.tick} 24/7 mode has been **{status}**"
        embed.title = "24/7 Updated"
        await ctx.send(embed=embed)

class DJControlView(discord.ui.View):
    """DJ control panel view with persistent buttons"""
    
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.button(
        emoji="<:avonpause:1129738547176419348>",
        style=discord.ButtonStyle.secondary,
        custom_id="dj_pause",
        row=0
    )
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Pause/Resume button"""
        guild_id = str(interaction.guild.id)
        
        if guild_id not in self.bot.dispatchers:
            await interaction.response.send_message(
                f"{self.bot.emoji.cross} Nothing is currently playing!",
                ephemeral=True
            )
            return
        
        dispatcher = self.bot.dispatchers[guild_id]
        
        if dispatcher.player.paused:
            await dispatcher.player.pause(False)
            await interaction.response.send_message("▶️ Resumed", ephemeral=True)
        else:
            await dispatcher.player.pause(True)
            await interaction.response.send_message("⏸️ Paused", ephemeral=True)
    
    @discord.ui.button(
        emoji="<:avonslip:1129744547644190770>",
        style=discord.ButtonStyle.secondary,
        custom_id="dj_skip",
        row=0
    )
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Skip button"""
        guild_id = str(interaction.guild.id)
        
        if guild_id not in self.bot.dispatchers:
            await interaction.response.send_message(
                f"{self.bot.emoji.cross} Nothing is currently playing!",
                ephemeral=True
            )
            return
        
        dispatcher = self.bot.dispatchers[guild_id]
        await dispatcher.player.skip()
        await interaction.response.send_message("⏭️ Skipped", ephemeral=True)
    
    @discord.ui.button(
        emoji="<:avonstop:1129747306040791180>",
        style=discord.ButtonStyle.danger,
        custom_id="dj_stop",
        row=0
    )
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Stop button"""
        guild_id = str(interaction.guild.id)
        
        if guild_id not in self.bot.dispatchers:
            await interaction.response.send_message(
                f"{self.bot.emoji.cross} I'm not connected to any voice channel!",
                ephemeral=True
            )
            return
        
        dispatcher = self.bot.dispatchers[guild_id]
        dispatcher.stopped = True
        await dispatcher.player.disconnect()
        del self.bot.dispatchers[guild_id]
        
        await interaction.response.send_message("⏹️ Stopped and disconnected", ephemeral=True)
    
    @discord.ui.button(
        emoji="<:avonsuffle:1129751417138196623>",
        style=discord.ButtonStyle.secondary,
        custom_id="dj_shuffle",
        row=0
    )
    async def shuffle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Shuffle button"""
        guild_id = str(interaction.guild.id)
        
        if guild_id not in self.bot.dispatchers:
            await interaction.response.send_message(
                f"{self.bot.emoji.cross} Nothing is currently playing!",
                ephemeral=True
            )
            return
        
        dispatcher = self.bot.dispatchers[guild_id]
        
        if not dispatcher.queue:
            await interaction.response.send_message(
                f"{self.bot.emoji.cross} No tracks in queue to shuffle!",
                ephemeral=True
            )
            return
        
        import random
        random.shuffle(dispatcher.queue)
        await interaction.response.send_message("🔀 Shuffled the queue", ephemeral=True)
    
    @discord.ui.button(
        emoji="<:avonrequest:1129747309094260837>",
        style=discord.ButtonStyle.secondary,
        custom_id="dj_loop",
        row=0
    )
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Loop button"""
        guild_id = str(interaction.guild.id)
        
        if guild_id not in self.bot.dispatchers:
            await interaction.response.send_message(
                f"{self.bot.emoji.cross} Nothing is currently playing!",
                ephemeral=True
            )
            return
        
        dispatcher = self.bot.dispatchers[guild_id]
        
        if dispatcher.repeat == "off":
            dispatcher.repeat = "one"
            await interaction.response.send_message("🔂 Loop mode: Track", ephemeral=True)
        elif dispatcher.repeat == "one":
            dispatcher.repeat = "all"
            await interaction.response.send_message("🔁 Loop mode: Queue", ephemeral=True)
        else:
            dispatcher.repeat = "off"
            await interaction.response.send_message("▶️ Loop mode: Off", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SetupCommands(bot))