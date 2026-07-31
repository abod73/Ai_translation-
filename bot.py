"""
AI Turkish Video Translator Bot - Bot Module
Pyrogram client setup and handler registration.
"""

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery

from config import config
from logger import get_logger, setup_logger
from database import db
from handlers import (
    handle_start, handle_help, handle_admin,
    handle_text_message
)
from callback import handle_callback

log = get_logger("bot")


class TurkishTranslatorBot:
    """Main bot class managing the Pyrogram client."""

    def __init__(self):
        self.client = Client(
            name=config.SESSION_NAME,
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            workdir=config.SESSIONS_DIR,
            sleep_threshold=60,
            max_concurrent_transmissions=5,
        )
        self._register_handlers()

    def _register_handlers(self):
        """Register all message and callback handlers."""

        # ─── Commands ───────────────────────────────────────────────
        @self.client.on_message(filters.command("start") & filters.private)
        async def on_start(client, message):
            await handle_start(client, message)

        @self.client.on_message(filters.command("help") & filters.private)
        async def on_help(client, message):
            await handle_help(client, message)

        @self.client.on_message(filters.command("admin") & filters.private)
        async def on_admin(client, message):
            await handle_admin(client, message)

        # ─── Text Messages ──────────────────────────────────────────
        @self.client.on_message(
            filters.text & filters.private & ~filters.command(["start", "help", "admin"])
        )
        async def on_text(client, message):
            await handle_text_message(client, message)

        # ─── Callback Queries ───────────────────────────────────────
        @self.client.on_callback_query()
        async def on_callback(client, callback):
            await handle_callback(client, callback)

        # ─── Document Messages (for subtitle merging) ───────────────
        @self.client.on_message(filters.document & filters.private)
        async def on_document(client, message):
            doc = message.document
            if doc.file_name and doc.file_name.endswith('.srt'):
                await message.reply_text(
                    "📄 تم استلام ملف الترجمة.\n"
                    "ميزة دمج الترجمة مع الفيديو قيد التطوير."
                )
            else:
                await message.reply_text(
                    "📎 تم استلام الملف.\n"
                    "حالياً أدعم فقط روابط الفيديو."
                )

    async def start(self):
        """Start the bot."""
        # Validate config
        errors = config.validate()
        if errors:
            for err in errors:
                log.error(f"Config error: {err}")
            raise ValueError("Invalid configuration. Check environment variables.")

        # Initialize database
        await db.initialize()

        # Log startup info
        log.info("=" * 60)
        log.info("🎬 AI Turkish Video Translator Bot")
        log.info("=" * 60)
        log.info(f"📱 Session: {config.SESSION_NAME}")
        log.info(f"🗣 Source: {config.SOURCE_LANGUAGE} -> Target: {config.TARGET_LANGUAGE}")
        log.info(f"🎙 Whisper: {config.WHISPER_MODEL}")
        log.info(f"🌍 Translation: {config.TRANSLATION_MODEL}")
        log.info(f"🤖 LLM Refinement: {'ON' if config.USE_LLM_REFINEMENT else 'OFF'}")
        log.info(f"🖥 Device: {config.get_device()}")
        log.info("=" * 60)

        # Start client
        await self.client.start()
        me = await self.client.get_me()
        log.info(f"✅ Bot started: @{me.username} ({me.id})")

    async def stop(self):
        """Stop the bot gracefully."""
        log.info("Stopping bot...")
        await self.client.stop()
        log.info("Bot stopped")

    async def run(self):
        """Run the bot (blocking)."""
        await self.start()
        log.info("🚀 Bot is running! Press Ctrl+C to stop.")
        await self.client.idle()
        await self.stop()
