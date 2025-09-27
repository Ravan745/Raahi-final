import os
from typing import List, Dict, Any

class Config:
    """Configuration class for the Avon Discord music bot"""
    
    def __init__(self):
        # Bot settings
        self.bot_token = os.getenv('BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("BOT_TOKEN environment variable must be set. Please set it in your environment variables or .env file.")
        self.prefix = "+"
        self.owners = ["973925530153910322"]  # Bot owner ID from original config
        self.color = 0xff0000  # Red color
        
        # Lavalink settings - using provided server details
        self.lavalink_nodes = [
            {
                "identifier": "Avon",
                "host": "lavalink.jirayu.net",
                "port": 13592,
                "password": "youshallnotpass",
                "secure": False,
                "region": "us"
            }
        ]
        
        # Discord settings
        self.support_server = "https://discord.gg/avonbot"
        self.vote_url = "https://top.gg/bot/904317141866647592/vote"
        self.setup_bg_link = "https://media.discordapp.net/attachments/1094179370966470666/1128356646113005688/Picsart_23-07-11_20-30-52-826.jpg"
        
        # Database
        self.database_path = "data/avon.db"
        
        # Spotify integration (optional)
        self.spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID', '579e0d88e85f403dad18a3fbd1a8f20a')
        self.spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET', '821937fdc8984880bd0efb41516a92ef')
        
        # Premium system
        self.premium_enabled = True
        
        # Music settings
        self.default_volume = 50
        self.max_queue_size = 500
        self.auto_play = False
        
        # Webhook settings - अलग-अलग webhooks के लिए
        self.webhook_port = 3001
        self.webhook_auth = os.getenv('WEBHOOK_AUTH', 'your_webhook_secret_here')
        
        # Vote webhooks
        self.topgg_webhook_auth = os.getenv('TOPGG_WEBHOOK_AUTH', '')
        self.vote_log_webhook = os.getenv('VOTE_LOG_WEBHOOK', 'https://discord.com/api/webhooks/1421027928413569045/dUCT-WlgjIsmpxX61ldbisWBDoK7OBuLy5p4Mni3Scjc6me3c-oGlv8G-tGmBSyqTkdZ')  # Vote notifications के लिए
        
        # Server join/leave webhooks  
        self.guild_join_webhook = os.getenv('GUILD_JOIN_WEBHOOK', 'https://discord.com/api/webhooks/1421027928413569045/dUCT-WlgjIsmpxX61ldbisWBDoK7OBuLy5p4Mni3Scjc6me3c-oGlv8G-tGmBSyqTkdZ')  # Server join के लिए
        self.guild_leave_webhook = os.getenv('GUILD_LEAVE_WEBHOOK', 'https://discord.com/api/webhooks/1421027928413569045/dUCT-WlgjIsmpxX61ldbisWBDoK7OBuLy5p4Mni3Scjc6me3c-oGlv8G-tGmBSyqTkdZ') # Server leave के लिए
        
        # Command usage webhook
        self.command_log_webhook = os.getenv('https://discord.com/api/webhooks/1421027928413569045/dUCT-WlgjIsmpxX61ldbisWBDoK7OBuLy5p4Mni3Scjc6me3c-oGlv8G-tGmBSyqTkdZ', '')  # Command usage के लिए
        
        # Bot stats webhook (optional)
        self.stats_webhook = os.getenv('STATS_WEBHOOK', 'https://discord.com/api/webhooks/1421027928413569045/dUCT-WlgjIsmpxX61ldbisWBDoK7OBuLy5p4Mni3Scjc6me3c-oGlv8G-tGmBSyqTkdZ')  # Daily/hourly stats के लिए
        
    @property
    def lavalink_config(self) -> List[Dict[str, Any]]:
        """Returns Lavalink configuration for wavelink"""
        return self.lavalink_nodes