# Overview

Avon is a Discord music bot built with Python and Discord.py, featuring advanced music playback capabilities, premium functionality, and comprehensive server management. The bot provides high-quality audio streaming with support for multiple music sources including YouTube, Spotify, SoundCloud, and Deezer. It includes a sophisticated permission system with DJ roles, premium user management, and customizable server settings.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Framework
- **Backend Language**: Python 3.x with Discord.py framework
- **Audio Engine**: Wavelink library for Lavalink integration
- **Database**: SQLite with aiosqlite for async operations
- **Command System**: Discord.py commands framework with both prefix and slash command support

## Database Design
The bot uses SQLite with multiple specialized tables:
- **DJ Table**: Manages music channel setup, player modes, and DJ role assignments
- **Premium Tables**: Separate user and server premium tracking with expiration times
- **Settings Tables**: Autoplay, 24/7 mode, and custom configurations
- **Management Table**: Bot administration and staff permissions

## Music System Architecture
- **Lavalink Integration**: External Lavalink server for audio processing at `lavalink.jirayu.net:13592`
- **Dispatcher Pattern**: Custom dispatcher class manages player state, queue, and events per guild
- **Multi-Source Support**: Spotify API integration, YouTube, SoundCloud, and Deezer search
- **Audio Filters**: Real-time audio effects including 8D, nightcore, bassboost, and karaoke

## Permission System
- **DJ Permissions**: Multi-tier system with administrator, DJ role, or voice channel isolation
- **Premium Tiers**: Bronze, Silver, Gold, Diamond with different feature access levels
- **Management Hierarchy**: Owner, developer, admin, and staff roles with specific permissions

## User Interface Components
- **Button Controls**: Interactive music player with pause, skip, shuffle, and repeat buttons
- **Setup System**: Persistent music control panels with custom embed colors
- **Help Menu**: Categorized command help with emoji-based navigation
- **Beautiful Player**: Canvas-based now playing displays with track artwork

## Command Architecture
- **Modular Cog System**: Organized into categories (Music, Filters, Premium, Setup, Utility)
- **Dual Command Support**: Both traditional prefix commands and modern slash commands
- **Dynamic Prefixes**: Server-specific prefix customization with database persistence
- **Context Validation**: Voice channel, permission, and premium status checking

## Configuration Management
- **Environment Variables**: Secure token and API key storage
- **Config Class**: Centralized settings with default values and validation
- **Emoji System**: Comprehensive custom emoji configuration for branding consistency

# External Dependencies

## Music Services
- **Lavalink Server**: Primary audio processing server (lavalink.jirayu.net:13592)
- **Spotify API**: Track metadata, playlist, and album information retrieval
- **YouTube**: Primary music source through Lavalink
- **SoundCloud**: Alternative music source
- **Deezer**: Additional music platform integration

## Discord Integration
- **Discord API**: Full Discord.py integration with voice state management
- **Webhooks**: Server join/leave logging and statistics tracking
- **Top.gg API**: Vote tracking and bot listing integration

## Database
- **SQLite**: Local database storage with async operations via aiosqlite
- **Database Files**: Separate databases for different feature sets (dj.sqlite, premium.sqlite, settings.sqlite)

## Development Tools
- **Canvas Library**: @napi-rs/canvas for image generation and now playing displays
- **Logging System**: Custom colored logging with timestamp formatting
- **Error Handling**: Comprehensive error catching and user-friendly error messages

## Optional Integrations
- **Cluster Management**: Discord-hybrid-sharding for horizontal scaling
- **Monitoring**: System information tracking and performance metrics
- **Auto-posting**: Automatic statistics posting to bot listing sites