"""
AI Turkish Video Translator Bot - Database Module
SQLite database for user management, statistics, and settings.
"""

import aiosqlite
import time
from pathlib import Path
from typing import Optional
from config import config
from logger import get_logger

log = get_logger("database")


class Database:
    """Async SQLite database manager."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False

    async def initialize(self):
        """Create all required tables."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language_code TEXT,
                    is_admin INTEGER DEFAULT 0,
                    is_banned INTEGER DEFAULT 0,
                    join_date REAL,
                    last_active REAL,
                    total_downloads INTEGER DEFAULT 0,
                    total_translations INTEGER DEFAULT 0,
                    total_videos INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    default_quality TEXT DEFAULT '720',
                    target_language TEXT DEFAULT 'ar',
                    send_original INTEGER DEFAULT 0,
                    send_subtitle INTEGER DEFAULT 1,
                    send_translated INTEGER DEFAULT 1,
                    use_llm_refinement INTEGER DEFAULT 0,
                    auto_translate INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                CREATE TABLE IF NOT EXISTS download_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    url TEXT,
                    site_name TEXT,
                    video_title TEXT,
                    quality TEXT,
                    file_size INTEGER,
                    duration REAL,
                    status TEXT DEFAULT 'completed',
                    download_date REAL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                CREATE TABLE IF NOT EXISTS translation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    video_title TEXT,
                    source_language TEXT,
                    target_language TEXT,
                    segments_count INTEGER,
                    translation_model TEXT,
                    llm_used INTEGER DEFAULT 0,
                    processing_time REAL,
                    status TEXT DEFAULT 'completed',
                    translation_date REAL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                CREATE TABLE IF NOT EXISTS recent_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    url TEXT,
                    site_name TEXT,
                    video_title TEXT,
                    added_date REAL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
                CREATE INDEX IF NOT EXISTS idx_downloads_user_id ON download_history(user_id);
                CREATE INDEX IF NOT EXISTS idx_translations_user_id ON translation_history(user_id);
                CREATE INDEX IF NOT EXISTS idx_recent_links_user_id ON recent_links(user_id);
            """)
            await db.commit()
            self._initialized = True
            log.info("Database initialized successfully")

    async def _ensure_init(self):
        if not self._initialized:
            await self.initialize()

    # ─── User Management ────────────────────────────────────────────

    async def add_user(
        self,
        user_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None,
        language_code: str = None,
        is_admin: bool = False
    ):
        """Add or update a user in the database."""
        await self._ensure_init()
        now = time.time()
        async with aiosqlite.connect(self.db_path) as db:
            # Check if user exists
            cursor = await db.execute(
                "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
            )
            existing = await cursor.fetchone()

            if existing:
                await db.execute("""
                    UPDATE users SET
                        username = ?, first_name = ?, last_name = ?,
                        language_code = ?, last_active = ?
                    WHERE user_id = ?
                """, (username, first_name, last_name, language_code, now, user_id))
            else:
                await db.execute("""
                    INSERT INTO users
                    (user_id, username, first_name, last_name, language_code,
                     is_admin, join_date, last_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, username, first_name, last_name,
                      language_code, int(is_admin), now, now))
                # Create default settings
                await db.execute("""
                    INSERT OR IGNORE INTO user_settings (user_id)
                    VALUES (?)
                """, (user_id,))
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[dict]:
        """Get user information."""
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def is_user_banned(self, user_id: int) -> bool:
        """Check if a user is banned."""
        user = await self.get_user(user_id)
        return bool(user and user.get("is_banned"))

    async def ban_user(self, user_id: int, banned: bool = True):
        """Ban or unban a user."""
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET is_banned = ? WHERE user_id = ?",
                (int(banned), user_id)
            )
            await db.commit()

    # ─── User Settings ──────────────────────────────────────────────

    async def get_user_settings(self, user_id: int) -> dict:
        """Get user settings with defaults."""
        await self._ensure_init()
        defaults = {
            "default_quality": "720",
            "target_language": "ar",
            "send_original": 0,
            "send_subtitle": 1,
            "send_translated": 1,
            "use_llm_refinement": 0,
            "auto_translate": 1,
        }
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM user_settings WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            if row:
                settings = dict(row)
                settings.pop("user_id", None)
                return settings
            return defaults

    async def update_user_setting(self, user_id: int, key: str, value):
        """Update a single user setting."""
        await self._ensure_init()
        allowed_keys = {
            "default_quality", "target_language", "send_original",
            "send_subtitle", "send_translated", "use_llm_refinement",
            "auto_translate"
        }
        if key not in allowed_keys:
            log.warning(f"Invalid setting key: {key}")
            return
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE user_settings SET {key} = ? WHERE user_id = ?",
                (value, user_id)
            )
            await db.commit()

    # ─── Statistics ─────────────────────────────────────────────────

    async def increment_downloads(self, user_id: int):
        """Increment user's download count."""
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET total_downloads = total_downloads + 1 WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()

    async def increment_translations(self, user_id: int):
        """Increment user's translation count."""
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET total_translations = total_translations + 1 WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()

    async def increment_videos(self, user_id: int):
        """Increment user's video count."""
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET total_videos = total_videos + 1 WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()

    async def add_download_record(
        self, user_id: int, url: str, site_name: str,
        video_title: str, quality: str, file_size: int,
        duration: float, status: str = "completed"
    ):
        """Add a download record to history."""
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO download_history
                (user_id, url, site_name, video_title, quality, file_size,
                 duration, status, download_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, url, site_name, video_title, quality,
                  file_size, duration, status, time.time()))
            await db.commit()

    async def add_translation_record(
        self, user_id: int, video_title: str,
        source_language: str, target_language: str,
        segments_count: int, translation_model: str,
        llm_used: bool, processing_time: float,
        status: str = "completed"
    ):
        """Add a translation record to history."""
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO translation_history
                (user_id, video_title, source_language, target_language,
                 segments_count, translation_model, llm_used,
                 processing_time, status, translation_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, video_title, source_language, target_language,
                  segments_count, translation_model, int(llm_used),
                  processing_time, status, time.time()))
            await db.commit()

    # ─── Recent Links ───────────────────────────────────────────────

    async def add_recent_link(
        self, user_id: int, url: str, site_name: str, video_title: str
    ):
        """Add a link to user's recent links (keep last 10)."""
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO recent_links (user_id, url, site_name, video_title, added_date)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, url, site_name, video_title, time.time()))
            # Keep only last 10
            await db.execute("""
                DELETE FROM recent_links
                WHERE user_id = ? AND id NOT IN (
                    SELECT id FROM recent_links
                    WHERE user_id = ?
                    ORDER BY added_date DESC
                    LIMIT 10
                )
            """, (user_id, user_id))
            await db.commit()

    async def get_recent_links(self, user_id: int, limit: int = 10) -> list[dict]:
        """Get user's recent links."""
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM recent_links
                WHERE user_id = ?
                ORDER BY added_date DESC
                LIMIT ?
            """, (user_id, limit))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    # ─── Admin Statistics ───────────────────────────────────────────

    async def get_admin_stats(self) -> dict:
        """Get comprehensive admin statistics."""
        await self._ensure_init()
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}

            cursor = await db.execute("SELECT COUNT(*) FROM users")
            stats["total_users"] = (await cursor.fetchone())[0]

            cursor = await db.execute("SELECT COUNT(*) FROM users WHERE is_banned = 0")
            stats["active_users"] = (await cursor.fetchone())[0]

            cursor = await db.execute("SELECT SUM(total_downloads) FROM users")
            row = await cursor.fetchone()
            stats["total_downloads"] = row[0] or 0

            cursor = await db.execute("SELECT SUM(total_translations) FROM users")
            row = await cursor.fetchone()
            stats["total_translations"] = row[0] or 0

            cursor = await db.execute("SELECT SUM(total_videos) FROM users")
            row = await cursor.fetchone()
            stats["total_videos"] = row[0] or 0

            cursor = await db.execute(
                "SELECT COUNT(*) FROM users WHERE last_active > ?",
                (time.time() - 86400,)
            )
            stats["active_today"] = (await cursor.fetchone())[0]

            cursor = await db.execute(
                "SELECT COUNT(*) FROM download_history WHERE download_date > ?",
                (time.time() - 86400,)
            )
            stats["downloads_today"] = (await cursor.fetchone())[0]

            cursor = await db.execute(
                "SELECT COUNT(*) FROM translation_history WHERE translation_date > ?",
                (time.time() - 86400,)
            )
            stats["translations_today"] = (await cursor.fetchone())[0]

            return stats


# Global database instance
db = Database()
