import aiosqlite
import os
from typing import Optional, Dict, Any, List

class AvonDatabase:
    """Database manager that exactly matches TypeScript bot structure"""
    
    def __init__(self, db_path: str = "data/avon.db"):
        self.db_path = db_path
        os.makedirs("data", exist_ok=True)
    
    async def init_all_tables(self):
        """Initialize all database tables matching TypeScript structure"""
        async with aiosqlite.connect(self.db_path) as db:
            # DJ table - manages player modes, setup, roles
            await db.execute("""
                CREATE TABLE IF NOT EXISTS DJ(
                    GUILD TEXT PRIMARY KEY,
                    CHANNEL TEXT,
                    MESSAGE TEXT,
                    ROLE TEXT,
                    MODE TEXT,
                    TYPE TEXT
                )
            """)
            
            # EMBEDS table - custom embed colors
            await db.execute("""
                CREATE TABLE IF NOT EXISTS EMBEDS(
                    GUILD TEXT PRIMARY KEY,
                    HEXCODE TEXT
                )
            """)
            
            # PREMIUM table - user premium details
            await db.execute("""
                CREATE TABLE IF NOT EXISTS PREMIUM(
                    USER TEXT PRIMARY KEY,
                    TIME INTEGER,
                    COUNT INTEGER,
                    TIER TEXT,
                    CODE TEXT,
                    REASON TEXT
                )
            """)
            
            # PREM_SERVER table - server premium details
            await db.execute("""
                CREATE TABLE IF NOT EXISTS PREM_SERVER(
                    SERVER TEXT PRIMARY KEY,
                    TIME INTEGER,
                    USER TEXT,
                    STATUS BOOLEAN,
                    CODE TEXT
                )
            """)
            
            # PREFIXDB table - custom prefixes
            await db.execute("""
                CREATE TABLE IF NOT EXISTS PREFIXDB(
                    GUILD TEXT PRIMARY KEY,
                    PREFIX TEXT
                )
            """)
            
            # NOPREFIX table - users exempt from prefix
            await db.execute("""
                CREATE TABLE IF NOT EXISTS NOPREFIX(
                    USER TEXT,
                    GLOBAL BOOLEAN,
                    SERVER TEXT,
                    REASON TEXT
                )
            """)
            
            # AUTOPLAY table - autoplay settings
            await db.execute("""
                CREATE TABLE IF NOT EXISTS AUTOPLAY(
                    GUILD TEXT PRIMARY KEY,
                    SETTING BOOLEAN
                )
            """)
            
            # RECONNECT table - 24/7 mode settings
            await db.execute("""
                CREATE TABLE IF NOT EXISTS RECONNECT(
                    GUILD TEXT PRIMARY KEY,
                    SETTING BOOLEAN,
                    CHANNELID TEXT,
                    TEXTID TEXT
                )
            """)
            
            # IGNORE table - ignored channels and bypass settings
            await db.execute("""
                CREATE TABLE IF NOT EXISTS IGNORE(
                    GUILD TEXT,
                    CHANNEL TEXT,
                    BYPASS_ADMINS BOOLEAN,
                    BYPASS_MODS BOOLEAN
                )
            """)
            
            # AFK table - server AFK system
            await db.execute("""
                CREATE TABLE IF NOT EXISTS AFK(
                    USER TEXT,
                    GUILD TEXT,
                    REASON TEXT,
                    TIME INTEGER
                )
            """)
            
            # AFK_NEW table - global AFK system
            await db.execute("""
                CREATE TABLE IF NOT EXISTS AFK_NEW(
                    USER TEXT,
                    REASON TEXT,
                    TIME INTEGER,
                    GLOBAL BOOLEAN,
                    SERVER TEXT
                )
            """)
            
            # FAVS table - user favorite tracks
            await db.execute("""
                CREATE TABLE IF NOT EXISTS FAVS(
                    USER TEXT,
                    TRACK TEXT,
                    LINK TEXT
                )
            """)
            
            # MANAGEMENT table - bot management
            await db.execute("""
                CREATE TABLE IF NOT EXISTS MANAGEMENT(
                    USER TEXT PRIMARY KEY,
                    MANAGER BOOLEAN
                )
            """)
            
            # RIHAN table - special command access
            await db.execute("""
                CREATE TABLE IF NOT EXISTS RIHAN(
                    USER TEXT
                )
            """)
            
            await db.commit()

# Database helper functions matching TypeScript structure
class DatabaseFunctions:
    """Database functions that exactly match TypeScript bot functions"""
    
    def __init__(self, db_path: str = "data/avon.db"):
        self.db_path = db_path
    
    # DJ Functions
    async def get_dj_exists(self, guild: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT GUILD FROM DJ WHERE GUILD = ?", (guild,)) as cursor:
                return bool(await cursor.fetchone())
    
    async def add_dj_role(self, guild: str, role: str):
        async with aiosqlite.connect(self.db_path) as db:
            if await self.get_dj_exists(guild):
                await db.execute("UPDATE DJ SET ROLE = ? WHERE GUILD = ?", (role, guild))
            else:
                await db.execute("INSERT INTO DJ(GUILD, ROLE) VALUES(?, ?)", (guild, role))
            await db.commit()
    
    async def get_dj_role(self, guild: str) -> Optional[str]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT ROLE FROM DJ WHERE GUILD = ?", (guild,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    async def remove_dj_role(self, guild: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE DJ SET ROLE = NULL WHERE GUILD = ?", (guild,))
            await db.commit()
    
    async def get_player_mode(self, guild: str) -> Optional[str]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT MODE FROM DJ WHERE GUILD = ?", (guild,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    async def update_player_mode(self, guild: str, mode: str):
        async with aiosqlite.connect(self.db_path) as db:
            if await self.get_dj_exists(guild):
                await db.execute("UPDATE DJ SET MODE = ? WHERE GUILD = ?", (mode, guild))
            else:
                await db.execute("INSERT INTO DJ(GUILD, MODE) VALUES(?, ?)", (guild, mode))
            await db.commit()
    
    async def get_play_type(self, guild: str) -> Optional[str]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT TYPE FROM DJ WHERE GUILD = ?", (guild,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    async def update_play_type(self, guild: str, play_type: str):
        async with aiosqlite.connect(self.db_path) as db:
            if await self.get_dj_exists(guild):
                await db.execute("UPDATE DJ SET TYPE = ? WHERE GUILD = ?", (play_type, guild))
            else:
                await db.execute("INSERT INTO DJ(GUILD, TYPE) VALUES(?, ?)", (guild, play_type))
            await db.commit()
    
    async def create_dj_setup(self, guild: str, channel: str, message: str):
        async with aiosqlite.connect(self.db_path) as db:
            if await self.get_dj_exists(guild):
                await db.execute("UPDATE DJ SET CHANNEL = ?, MESSAGE = ? WHERE GUILD = ?", (channel, message, guild))
            else:
                await db.execute("INSERT INTO DJ(GUILD, CHANNEL, MESSAGE) VALUES(?, ?, ?)", (guild, channel, message))
            await db.commit()
    
    async def get_dj_setup(self, guild: str) -> Dict[str, Optional[str]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT CHANNEL, MESSAGE FROM DJ WHERE GUILD = ?", (guild,)) as cursor:
                result = await cursor.fetchone()
                if result:
                    return {"CHANNEL": result[0], "MESSAGE": result[1]}
                return {"CHANNEL": None, "MESSAGE": None}
    
    async def check_dj_setup(self, guild: str) -> bool:
        setup = await self.get_dj_setup(guild)
        return setup["CHANNEL"] is not None and setup["MESSAGE"] is not None
    
    async def delete_dj_setup(self, guild: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE DJ SET CHANNEL = NULL, MESSAGE = NULL WHERE GUILD = ?", (guild,))
            await db.commit()
    
    # Premium Functions
    async def get_user_premium_status(self, user: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT USER FROM PREMIUM WHERE USER = ?", (user,)) as cursor:
                return bool(await cursor.fetchone())
    
    async def get_server_premium_status(self, server: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT STATUS FROM PREM_SERVER WHERE SERVER = ? AND STATUS = 1", (server,)) as cursor:
                return bool(await cursor.fetchone())
    
    async def add_user_premium(self, user: str, time: int, count: int, tier: str, code: str, reason: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO PREMIUM(USER, TIME, COUNT, TIER, CODE, REASON)
                VALUES(?, ?, ?, ?, ?, ?)
            """, (user, time, count, tier, code, reason))
            await db.commit()
    
    async def add_server_premium(self, server: str, time: int, user: str, code: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO PREM_SERVER(SERVER, TIME, USER, STATUS, CODE)
                VALUES(?, ?, ?, 1, ?)
            """, (server, time, user, code))
            await db.commit()
    
    # Embed Functions
    async def get_hex(self, guild: str) -> Optional[str]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT HEXCODE FROM EMBEDS WHERE GUILD = ?", (guild,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    async def add_hex(self, guild: str, hex_code: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO EMBEDS(GUILD, HEXCODE) VALUES(?, ?)", (guild, hex_code))
            await db.commit()
    
    async def remove_hex(self, guild: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM EMBEDS WHERE GUILD = ?", (guild,))
            await db.commit()
    
    # Prefix Functions
    async def get_prefix(self, guild: str) -> Optional[str]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT PREFIX FROM PREFIXDB WHERE GUILD = ?", (guild,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    async def update_prefix(self, guild: str, prefix: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO PREFIXDB(GUILD, PREFIX) VALUES(?, ?)", (guild, prefix))
            await db.commit()
    
    # Settings Functions
    async def get_autoplay(self, guild: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT SETTING FROM AUTOPLAY WHERE GUILD = ?", (guild,)) as cursor:
                result = await cursor.fetchone()
                return bool(result[0]) if result else False
    
    async def enable_autoplay(self, guild: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO AUTOPLAY(GUILD, SETTING) VALUES(?, 1)", (guild,))
            await db.commit()
    
    async def disable_autoplay(self, guild: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR REPLACE INTO AUTOPLAY(GUILD, SETTING) VALUES(?, 0)", (guild,))
            await db.commit()
    
    async def get_247(self, guild: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT SETTING FROM RECONNECT WHERE GUILD = ?", (guild,)) as cursor:
                result = await cursor.fetchone()
                return bool(result[0]) if result else False
    
    async def enable_247(self, guild: str, voice_id: str, text_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO RECONNECT(GUILD, SETTING, CHANNELID, TEXTID)
                VALUES(?, 1, ?, ?)
            """, (guild, voice_id, text_id))
            await db.commit()
    
    async def disable_247(self, guild: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE RECONNECT SET SETTING = 0 WHERE GUILD = ?", (guild,))
            await db.commit()
    
    # AFK Functions
    async def add_global_afk(self, user: str, reason: str, time: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO AFK_NEW(USER, REASON, TIME, GLOBAL, SERVER)
                VALUES(?, ?, ?, 1, NULL)
            """, (user, reason, time))
            await db.commit()
    
    async def add_server_afk(self, user: str, reason: str, time: int, server: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO AFK_NEW(USER, REASON, TIME, GLOBAL, SERVER)
                VALUES(?, ?, ?, 0, ?)
            """, (user, reason, time, server))
            await db.commit()
    
    async def check_global_afk(self, user: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT USER FROM AFK_NEW WHERE USER = ? AND GLOBAL = 1", (user,)) as cursor:
                return bool(await cursor.fetchone())
    
    async def check_server_afk(self, user: str, server: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT USER FROM AFK_NEW WHERE USER = ? AND SERVER = ? AND GLOBAL = 0", (user, server)) as cursor:
                return bool(await cursor.fetchone())
    
    async def remove_global_afk(self, user: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM AFK_NEW WHERE USER = ? AND GLOBAL = 1", (user,))
            await db.commit()
    
    async def remove_server_afk(self, user: str, server: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM AFK_NEW WHERE USER = ? AND SERVER = ? AND GLOBAL = 0", (user, server))
            await db.commit()