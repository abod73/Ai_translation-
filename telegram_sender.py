"""
AI Turkish Video Translator Bot - Telegram Sender Module
Handles sending files to Telegram with progress and error handling.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional

from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import (
    FloodWait,
    FilePartMissing,
    FileReferenceExpired,
    RPCError,
)

from config import config
from logger import get_logger
from progress import ProgressTracker
from utils import format_size, format_duration, retry_async

log = get_logger("telegram_sender")


class TelegramSender:
    """Handles sending files to Telegram users."""

    def __init__(self, client: Client):
        self.client = client

    async def send_video(
        self,
        chat_id: int,
        video_path: str,
        caption: str = "",
        duration: int = 0,
        width: int = 0,
        height: int = 0,
        thumb: str = None,
        reply_to: int = None,
        progress_message: Message = None
    ) -> Optional[Message]:
        """
        Send a video file to a chat.

        Args:
            chat_id: Target chat ID.
            video_path: Path to video file.
            caption: Video caption.
            duration: Video duration in seconds.
            width: Video width.
            height: Video height.
            thumb: Thumbnail path.
            reply_to: Message ID to reply to.
            progress_message: Message to update with progress.

        Returns:
            Sent Message or None on failure.
        """
        if not os.path.exists(video_path):
            log.error(f"Video file not found: {video_path}")
            return None

        file_size = os.path.getsize(video_path)
        log.info(f"Sending video: {video_path} ({format_size(file_size)})")

        tracker = None
        if progress_message:
            tracker = ProgressTracker(progress_message, "📤 رفع الفيديو")

        try:
            progress_callback = None
            if tracker:
                async def _progress(current, total):
                    speed = current / max(1, asyncio.get_event_loop().time() - tracker.start_time)
                    eta = (total - current) / max(1, speed) if speed > 0 else 0
                    await tracker.update(current, total, speed, eta)
                progress_callback = _progress

            message = await self.client.send_video(
                chat_id=chat_id,
                video=video_path,
                caption=caption,
                duration=duration,
                width=width,
                height=height,
                thumb=thumb,
                reply_to_message_id=reply_to,
                supports_streaming=True,
                progress=progress_callback,
            )

            if tracker:
                await tracker.complete("✅ تم إرسال الفيديو بنجاح!")

            log.info(f"Video sent successfully to {chat_id}")
            return message

        except FloodWait as e:
            log.warning(f"Flood wait: {e.value}s")
            await asyncio.sleep(e.value)
            return await self.send_video(
                chat_id, video_path, caption, duration,
                width, height, thumb, reply_to
            )
        except Exception as e:
            log.error(f"Failed to send video: {e}", exc_info=True)
            if tracker:
                await tracker.error(str(e)[:200])
            return None

    async def send_document(
        self,
        chat_id: int,
        file_path: str,
        caption: str = "",
        reply_to: int = None,
        progress_message: Message = None
    ) -> Optional[Message]:
        """Send a document/file to a chat."""
        if not os.path.exists(file_path):
            log.error(f"File not found: {file_path}")
            return None

        log.info(f"Sending document: {file_path}")

        tracker = None
        if progress_message:
            tracker = ProgressTracker(progress_message, "📤 رفع الملف")

        try:
            progress_callback = None
            if tracker:
                async def _progress(current, total):
                    speed = current / max(1, asyncio.get_event_loop().time() - tracker.start_time)
                    eta = (total - current) / max(1, speed) if speed > 0 else 0
                    await tracker.update(current, total, speed, eta)
                progress_callback = _progress

            message = await self.client.send_document(
                chat_id=chat_id,
                document=file_path,
                caption=caption,
                reply_to_message_id=reply_to,
                progress=progress_callback,
            )

            if tracker:
                await tracker.complete("✅ تم إرسال الملف بنجاح!")

            return message

        except FloodWait as e:
            await asyncio.sleep(e.value)
            return await self.send_document(
                chat_id, file_path, caption, reply_to
            )
        except Exception as e:
            log.error(f"Failed to send document: {e}")
            if tracker:
                await tracker.error(str(e)[:200])
            return None

    async def send_subtitle(
        self,
        chat_id: int,
        srt_path: str,
        video_title: str = "",
        reply_to: int = None
    ) -> Optional[Message]:
        """Send an SRT subtitle file."""
        caption = f"📄 ملف الترجمة\n🎬 {video_title}" if video_title else "📄 ملف الترجمة"
        return await self.send_document(
            chat_id, srt_path, caption, reply_to
        )

    async def send_photo(
        self,
        chat_id: int,
        photo_path: str,
        caption: str = "",
        reply_to: int = None
    ) -> Optional[Message]:
        """Send a photo."""
        if not os.path.exists(photo_path):
            return None
        try:
            return await self.client.send_photo(
                chat_id=chat_id,
                photo=photo_path,
                caption=caption,
                reply_to_message_id=reply_to,
            )
        except Exception as e:
            log.error(f"Failed to send photo: {e}")
            return None

    async def send_text(
        self,
        chat_id: int,
        text: str,
        reply_to: int = None,
        parse_mode: str = "Markdown"
    ) -> Optional[Message]:
        """Send a text message."""
        try:
            return await self.client.send_message(
                chat_id=chat_id,
                text=text,
                reply_to_message_id=reply_to,
                parse_mode=parse_mode,
            )
        except Exception as e:
            log.error(f"Failed to send message: {e}")
            return None

    async def send_processing_results(
        self,
        chat_id: int,
        video_path: str,
        subtitle_path: str,
        original_video_path: str = None,
        video_title: str = "",
        duration: int = 0,
        reply_to: int = None,
        progress_message: Message = None
    ):
        """
        Send all processing results to the user.

        Sends in order:
        1. Translated video
        2. SRT subtitle file
        3. Original video (optional)
        """
        results = []

        # 1. Send translated video
        if config.SEND_TRANSLATED and video_path and os.path.exists(video_path):
            caption = (
                f"🎬 **{video_title}**\n"
                f"🌍 مترجم إلى العربية\n"
                f"⏱ المدة: {format_duration(duration)}"
            )
            msg = await self.send_video(
                chat_id, video_path, caption,
                duration=duration,
                reply_to=reply_to,
                progress_message=progress_message
            )
            if msg:
                results.append(msg)

        # 2. Send subtitle file
        if config.SEND_SUBTITLE and subtitle_path and os.path.exists(subtitle_path):
            msg = await self.send_subtitle(
                chat_id, subtitle_path, video_title, reply_to
            )
            if msg:
                results.append(msg)

        # 3. Send original video (optional)
        if (config.SEND_ORIGINAL
                and original_video_path
                and os.path.exists(original_video_path)):
            caption = f"🎬 **{video_title}**\n📹 الفيديو الأصلي"
            msg = await self.send_video(
                chat_id, original_video_path, caption,
                duration=duration,
                reply_to=reply_to
            )
            if msg:
                results.append(msg)

        return results
