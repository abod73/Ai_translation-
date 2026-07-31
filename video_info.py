"""
AI Turkish Video Translator Bot - Video Info Module
Extracts video metadata using yt-dlp.
"""

import asyncio
from typing import Optional
from dataclasses import dataclass, field
from logger import get_logger
from config import config
from utils import format_duration, format_size, get_site_name

log = get_logger("video_info")


@dataclass
class VideoInfo:
    """Container for video metadata."""
    url: str
    title: str
    duration: float
    thumbnail: Optional[str]
    uploader: str
    site_name: str
    description: str
    view_count: Optional[int]
    like_count: Optional[int]
    upload_date: Optional[str]
    formats: list[dict] = field(default_factory=list)
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    language: Optional[str] = None
    is_live: bool = False
    age_limit: int = 0
    chapters: list[dict] = field(default_factory=list)
    subtitles: dict = field(default_factory=dict)
    automatic_captions: dict = field(default_factory=dict)

    @property
    def duration_formatted(self) -> str:
        return format_duration(self.duration)

    @property
    def file_size_formatted(self) -> str:
        return format_size(self.file_size) if self.file_size else "غير معروف"

    @property
    def resolution(self) -> str:
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        if self.height:
            return f"{self.height}p"
        return "غير معروف"

    def to_display_text(self) -> str:
        """Format video info for display in Telegram."""
        lines = [
            f"🎬 **{self.title}**\n",
            f"🌐 **الموقع:** {self.site_name}",
            f"⏱ **المدة:** {self.duration_formatted}",
            f"📺 **الدقة:** {self.resolution}",
            f"📦 **الحجم التقريبي:** {self.file_size_formatted}",
        ]
        if self.uploader:
            lines.append(f"👤 **الناشر:** {self.uploader}")
        if self.view_count:
            lines.append(f"👁 **المشاهدات:** {self.view_count:,}")
        if self.language:
            lines.append(f"🗣 **اللغة:** {self.language}")
        if self.is_live:
            lines.append("🔴 **بث مباشر**")
        return "\n".join(lines)


async def extract_video_info(url: str, cookies_file: str = None) -> Optional[VideoInfo]:
    """
    Extract video information from a URL using yt-dlp.

    Args:
        url: Video URL to extract info from.
        cookies_file: Optional path to cookies file.

    Returns:
        VideoInfo object or None if extraction fails.
    """
    log.info(f"Extracting video info from: {url}")

    try:
        import yt_dlp

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'ignoreerrors': True,
            'nocheckcertificate': True,
            'socket_timeout': 30,
            'retries': 3,
            'extractor_retries': 3,
        }

        if cookies_file:
            ydl_opts['cookiefile'] = cookies_file
        elif config.COOKIES_FILE:
            ydl_opts['cookiefile'] = config.COOKIES_FILE

        # Run in executor to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, _extract_sync, url, ydl_opts)

        if not info:
            log.error(f"Failed to extract info from: {url}")
            return None

        # Estimate file size from best format
        file_size = None
        formats = info.get('formats', [])
        for fmt in reversed(formats):
            if fmt.get('filesize'):
                file_size = fmt['filesize']
                break
            elif fmt.get('filesize_approx'):
                file_size = fmt['filesize_approx']
                break

        video_info = VideoInfo(
            url=url,
            title=info.get('title', 'Untitled'),
            duration=info.get('duration', 0) or 0,
            thumbnail=info.get('thumbnail'),
            uploader=info.get('uploader', ''),
            site_name=get_site_name(url),
            description=info.get('description', '')[:500],
            view_count=info.get('view_count'),
            like_count=info.get('like_count'),
            upload_date=info.get('upload_date'),
            formats=formats,
            file_size=file_size,
            width=info.get('width'),
            height=info.get('height'),
            fps=info.get('fps'),
            language=info.get('language'),
            is_live=info.get('is_live', False),
            age_limit=info.get('age_limit', 0),
            chapters=info.get('chapters', []),
            subtitles=info.get('subtitles', {}),
            automatic_captions=info.get('automatic_captions', {}),
        )

        log.info(
            f"Extracted info: {video_info.title} "
            f"({video_info.duration_formatted}, {video_info.resolution})"
        )
        return video_info

    except Exception as e:
        log.error(f"Error extracting video info: {e}", exc_info=True)
        return None


def _extract_sync(url: str, ydl_opts: dict) -> Optional[dict]:
    """Synchronous extraction for use with executor."""
    import yt_dlp
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as e:
        log.error(f"yt-dlp extraction error: {e}")
        return None


async def check_url_validity(url: str) -> tuple[bool, str]:
    """
    Quick check if a URL is valid and supported.

    Returns:
        Tuple of (is_valid, error_message)
    """
    from utils import is_valid_url, is_m3u8_url

    url = url.strip()

    if not url:
        return False, "الرابط فارغ"

    if is_m3u8_url(url):
        return True, ""

    if not is_valid_url(url):
        return False, "الرابط غير صالح"

    try:
        import yt_dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'ignoreerrors': True,
            'socket_timeout': 15,
        }
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, _extract_sync, url, ydl_opts)
        if info:
            return True, ""
        return False, "لا يمكن الوصول إلى هذا الرابط"
    except Exception as e:
        return False, f"خطأ في التحقق من الرابط: {str(e)[:100]}"
