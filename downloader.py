"""
AI Turkish Video Translator Bot - Downloader Module
Handles video downloading using yt-dlp with progress tracking.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass

from config import config
from logger import get_logger
from quality import get_format_string, get_merge_format
from utils import sanitize_filename, generate_unique_id, ensure_directory

log = get_logger("downloader")


@dataclass
class DownloadResult:
    """Result of a download operation."""
    success: bool
    filepath: str = ""
    filename: str = ""
    file_size: int = 0
    duration: float = 0
    error: str = ""
    thumbnail_path: str = ""


class VideoDownloader:
    """Async video downloader using yt-dlp."""

    def __init__(self):
        self.download_dir = ensure_directory(config.DOWNLOAD_FOLDER)
        self.temp_dir = ensure_directory(config.TEMP_FOLDER)
        self._active_downloads: dict[str, bool] = {}

    def _build_ydl_opts(
        self,
        output_path: str,
        quality: str = "720",
        progress_hook: Optional[Callable] = None,
        audio_only: bool = False
    ) -> dict:
        """Build yt-dlp options dictionary."""
        format_string = get_format_string(quality)

        opts = {
            'format': format_string,
            'outtmpl': output_path,
            'merge_output_format': 'mp4' if not audio_only else 'mp3',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'socket_timeout': 60,
            'retries': 5,
            'fragment_retries': 5,
            'extractor_retries': 3,
            'file_access_retries': 3,
            'http_chunk_size': 10485760,  # 10 MB
            'buffersize': 1024 * 1024,    # 1 MB
            'consoletitle': False,
            'writethumbnail': True,
            'postprocessors': [],
            'keepvideo': False,
            'overwrites': True,
        }

        # Add cookies if available
        if config.COOKIES_FILE and os.path.exists(config.COOKIES_FILE):
            opts['cookiefile'] = config.COOKIES_FILE

        # Audio-only postprocessor
        if audio_only:
            opts['postprocessors'].append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            })

        # Add progress hook
        if progress_hook:
            opts['progress_hooks'] = [progress_hook]

        return opts

    async def download(
        self,
        url: str,
        quality: str = "720",
        progress_hook: Optional[Callable] = None,
        custom_filename: str = None
    ) -> DownloadResult:
        """
        Download a video from URL.

        Args:
            url: Video URL.
            quality: Quality string ('240', '360', '720', '1080', 'best', 'audio').
            progress_hook: Optional progress callback function.
            custom_filename: Optional custom filename.

        Returns:
            DownloadResult with file path and metadata.
        """
        unique_id = generate_unique_id()
        self._active_downloads[unique_id] = True

        try:
            log.info(f"Starting download: {url} (quality: {quality})")

            # Determine filename
            if custom_filename:
                safe_name = sanitize_filename(custom_filename)
            else:
                safe_name = f"video_{unique_id}"

            audio_only = quality.lower() in ("audio", "audio only")
            ext = "mp3" if audio_only else "mp4"
            output_template = str(self.download_dir / f"{safe_name}.%(ext)s")
            final_path = str(self.download_dir / f"{safe_name}.{ext}")

            # Build options
            ydl_opts = self._build_ydl_opts(
                output_path=output_template,
                quality=quality,
                progress_hook=progress_hook,
                audio_only=audio_only
            )

            # Download in executor
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                self._download_sync,
                url,
                ydl_opts
            )

            if not info:
                return DownloadResult(
                    success=False,
                    error="فشل التحميل - لم يتم الحصول على معلومات الفيديو"
                )

            # Find the actual downloaded file
            downloaded_file = self._find_downloaded_file(safe_name, ext)
            if not downloaded_file:
                return DownloadResult(
                    success=False,
                    error="فشل التحميل - الملف غير موجود"
                )

            file_size = os.path.getsize(downloaded_file)
            duration = info.get('duration', 0) or 0

            # Find thumbnail
            thumbnail = self._find_thumbnail(safe_name)

            log.info(
                f"Download complete: {downloaded_file} "
                f"({file_size / 1024 / 1024:.1f} MB, {duration}s)"
            )

            return DownloadResult(
                success=True,
                filepath=downloaded_file,
                filename=os.path.basename(downloaded_file),
                file_size=file_size,
                duration=duration,
                thumbnail_path=thumbnail
            )

        except Exception as e:
            log.error(f"Download failed: {e}", exc_info=True)
            return DownloadResult(
                success=False,
                error=f"خطأ في التحميل: {str(e)[:200]}"
            )
        finally:
            self._active_downloads.pop(unique_id, None)

    def _download_sync(self, url: str, ydl_opts: dict) -> Optional[dict]:
        """Synchronous download for executor."""
        import yt_dlp
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info
        except Exception as e:
            log.error(f"yt-dlp download error: {e}")
            return None

    def _find_downloaded_file(self, base_name: str, ext: str) -> Optional[str]:
        """Find the downloaded file in the download directory."""
        # Try exact match first
        exact = self.download_dir / f"{base_name}.{ext}"
        if exact.exists():
            return str(exact)

        # Search for any matching file
        for f in self.download_dir.glob(f"{base_name}*"):
            if f.suffix.lower() in (f'.{ext}', '.mp4', '.mkv', '.webm', '.mp3', '.m4a'):
                return str(f)

        # Search more broadly
        for f in self.download_dir.glob("*"):
            if f.is_file() and f.stat().st_mtime > (
                asyncio.get_event_loop().time() - 300
            ):
                return str(f)

        return None

    def _find_thumbnail(self, base_name: str) -> str:
        """Find the thumbnail file for a download."""
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            thumb = self.download_dir / f"{base_name}{ext}"
            if thumb.exists():
                return str(thumb)
        # Search broadly
        for f in self.download_dir.glob(f"{base_name}*.jpg"):
            return str(f)
        return ""

    def cancel_download(self, download_id: str):
        """Cancel an active download."""
        if download_id in self._active_downloads:
            self._active_downloads[download_id] = False
            log.info(f"Download cancelled: {download_id}")

    def cleanup_download(self, filepath: str):
        """Remove a downloaded file."""
        if config.DELETE_TEMP_FILES:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    log.debug(f"Cleaned up: {filepath}")
            except Exception as e:
                log.warning(f"Failed to cleanup {filepath}: {e}")


# Global downloader instance
downloader = VideoDownloader()
