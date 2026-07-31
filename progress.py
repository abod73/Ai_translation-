"""
AI Turkish Video Translator Bot - Progress Module
Handles progress tracking and display for downloads and uploads.
"""

import time
import asyncio
from typing import Optional, Callable
from pyrogram.types import Message
from logger import get_logger
from utils import format_size, format_speed, format_eta

log = get_logger("progress")


class ProgressTracker:
    """Track and display progress for file operations."""

    def __init__(
        self,
        message: Message,
        operation: str = "Processing",
        update_interval: float = 3.0
    ):
        self.message = message
        self.operation = operation
        self.update_interval = update_interval
        self.start_time = time.time()
        self.last_update_time = 0.0
        self.last_progress = -1
        self._cancelled = False

    def _build_progress_bar(self, percentage: float, length: int = 10) -> str:
        """Build a visual progress bar."""
        filled = int(length * percentage / 100)
        empty = length - filled
        bar = "█" * filled + "░" * empty
        return f"[{bar}]"

    def _format_progress_text(
        self,
        current: int,
        total: int,
        speed: float = 0,
        eta: float = 0
    ) -> str:
        """Format the progress message text."""
        percentage = (current / total * 100) if total > 0 else 0
        bar = self._build_progress_bar(percentage)
        elapsed = time.time() - self.start_time

        text = (
            f"🔄 **{self.operation}**\n\n"
            f"{bar} **{percentage:.1f}%**\n\n"
            f"📊 **الحجم:** {format_size(current)} / {format_size(total)}\n"
            f"⚡ **السرعة:** {format_speed(speed)}\n"
            f"⏱ **الوقت المتبقي:** {format_eta(eta)}\n"
            f"⏳ **الوقت المنقضي:** {format_eta(elapsed)}"
        )
        return text

    async def update(
        self,
        current: int,
        total: int,
        speed: float = 0,
        eta: float = 0
    ):
        """Update the progress message."""
        if self._cancelled:
            return

        now = time.time()
        percentage = int(current / total * 100) if total > 0 else 0

        # Only update if enough time has passed or progress changed significantly
        if (now - self.last_update_time < self.update_interval
                and abs(percentage - self.last_progress) < 3
                and percentage < 100):
            return

        self.last_update_time = now
        self.last_progress = percentage

        try:
            text = self._format_progress_text(current, total, speed, eta)
            await self.message.edit_text(text)
        except Exception as e:
            # Ignore flood wait and message not modified errors
            if "FLOOD_WAIT" not in str(e) and "MESSAGE_NOT_MODIFIED" not in str(e):
                log.debug(f"Progress update error: {e}")

    async def complete(self, final_text: str = None):
        """Mark the operation as complete."""
        try:
            if final_text:
                await self.message.edit_text(final_text)
            else:
                elapsed = time.time() - self.start_time
                await self.message.edit_text(
                    f"✅ **{self.operation} مكتمل!**\n\n"
                    f"⏱ الوقت الإجمالي: {format_eta(elapsed)}"
                )
        except Exception as e:
            log.debug(f"Progress complete error: {e}")

    async def error(self, error_text: str):
        """Display an error message."""
        try:
            await self.message.edit_text(f"❌ **خطأ في {self.operation}:**\n\n{error_text}")
        except Exception as e:
            log.debug(f"Progress error display failed: {e}")

    def cancel(self):
        """Cancel the progress tracking."""
        self._cancelled = True


def create_ytdlp_progress_hook(tracker: ProgressTracker) -> Callable:
    """Create a yt-dlp progress hook that updates the tracker."""

    def hook(d: dict):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            current = d.get('downloaded_bytes', 0)
            speed = d.get('speed') or 0
            eta = d.get('eta') or 0

            # Use asyncio to schedule the coroutine
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        tracker.update(current, total, speed, eta),
                        loop
                    )
            except RuntimeError:
                pass

        elif d['status'] == 'finished':
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        tracker.complete("✅ اكتمل التحميل! جاري المعالجة..."),
                        loop
                    )
            except RuntimeError:
                pass

    return hook


class MultiStepProgress:
    """Track progress across multiple processing steps."""

    STEPS = [
        ("📥", "تحميل الفيديو"),
        ("🎙", "استخراج الكلام"),
        ("🌍", "الترجمة"),
        ("✍️", "إنشاء ملف الترجمة"),
        ("🎞", "دمج الترجمة مع الفيديو"),
        ("📤", "إرسال الملفات"),
    ]

    def __init__(self, message: Message):
        self.message = message
        self.current_step = 0
        self.total_steps = len(self.STEPS)

    def _build_steps_display(self) -> str:
        """Build the visual steps display."""
        lines = []
        for i, (emoji, name) in enumerate(self.STEPS):
            if i < self.current_step:
                lines.append(f"✅ {emoji} {name}")
            elif i == self.current_step:
                lines.append(f"🔄 {emoji} **{name}** ⏳")
            else:
                lines.append(f"⬜ {emoji} {name}")
        return "\n".join(lines)

    async def set_step(self, step: int, extra_info: str = ""):
        """Set the current processing step."""
        self.current_step = min(step, self.total_steps - 1)
        text = (
            f"🎬 **معالجة الفيديو**\n\n"
            f"{self._build_steps_display()}\n\n"
            f"📌 الخطوة {self.current_step + 1} من {self.total_steps}"
        )
        if extra_info:
            text += f"\n\n💡 {extra_info}"
        try:
            await self.message.edit_text(text)
        except Exception as e:
            if "MESSAGE_NOT_MODIFIED" not in str(e):
                log.debug(f"Step update error: {e}")

    async def complete_all(self, summary: str = ""):
        """Mark all steps as complete."""
        self.current_step = self.total_steps
        text = (
            f"🎉 **اكتملت المعالجة!**\n\n"
            f"{self._build_steps_display()}"
        )
        if summary:
            text += f"\n\n{summary}"
        try:
            await self.message.edit_text(text)
        except Exception as e:
            log.debug(f"Complete all error: {e}")
