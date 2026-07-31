"""
AI Turkish Video Translator Bot - Quality Module
Handles video quality selection and format mapping for yt-dlp.
"""

from dataclasses import dataclass
from typing import Optional
from logger import get_logger

log = get_logger("quality")


@dataclass
class QualityOption:
    """Represents a video quality option."""
    label: str
    height: int
    format_id: str
    description: str
    is_audio_only: bool = False

    @property
    def callback_data(self) -> str:
        return f"quality_{self.height}"


# Predefined quality options
QUALITY_OPTIONS = [
    QualityOption("240p", 240, "bestvideo[height<=240]+bestaudio/best[height<=240]", "جودة منخفضة جداً"),
    QualityOption("360p", 360, "bestvideo[height<=360]+bestaudio/best[height<=360]", "جودة منخفضة"),
    QualityOption("480p", 480, "bestvideo[height<=480]+bestaudio/best[height<=480]", "جودة متوسطة"),
    QualityOption("720p", 720, "bestvideo[height<=720]+bestaudio/best[height<=720]", "جودة عالية HD"),
    QualityOption("1080p", 1080, "bestvideo[height<=1080]+bestaudio/best[height<=1080]", "جودة عالية جداً FHD"),
    QualityOption("Best", 9999, "bestvideo+bestaudio/best", "أفضل جودة متاحة"),
    QualityOption("Audio Only", 0, "bestaudio", "صوت فقط MP3", is_audio_only=True),
]


def get_quality_by_height(height: int) -> Optional[QualityOption]:
    """Get quality option by height value."""
    for q in QUALITY_OPTIONS:
        if q.height == height:
            return q
    return None


def get_quality_by_label(label: str) -> Optional[QualityOption]:
    """Get quality option by display label."""
    label_lower = label.lower().strip()
    for q in QUALITY_OPTIONS:
        if q.label.lower() == label_lower:
            return q
    return None


def get_format_string(quality: str) -> str:
    """
    Get yt-dlp format string for a given quality.

    Args:
        quality: Quality string like '720', '1080', 'best', 'audio'

    Returns:
        yt-dlp format string
    """
    quality = quality.lower().strip()

    quality_map = {
        "240": "bestvideo[height<=240]+bestaudio/best[height<=240]",
        "360": "bestvideo[height<=360]+bestaudio/best[height<=360]",
        "480": "bestvideo[height<=480]+bestaudio/best[height<=480]",
        "720": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "1080": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "1440": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
        "2160": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
        "best": "bestvideo+bestaudio/best",
        "audio": "bestaudio",
        "worst": "worstvideo+worstaudio/worst",
    }

    return quality_map.get(quality, quality_map["720"])


def get_available_qualities(formats: list[dict]) -> list[QualityOption]:
    """
    Filter available qualities based on actual video formats.

    Args:
        formats: List of format dicts from yt-dlp info.

    Returns:
        List of available QualityOptions.
    """
    available_heights = set()
    has_audio = False

    for fmt in formats:
        height = fmt.get('height')
        if height:
            available_heights.add(height)
        if fmt.get('acodec') != 'none' or fmt.get('vcodec') == 'none':
            has_audio = True

    available = []
    for q in QUALITY_OPTIONS:
        if q.is_audio_only:
            if has_audio:
                available.append(q)
        elif q.height == 9999:  # Best
            available.append(q)
        else:
            # Include if there's a format with this height or lower
            if any(h <= q.height for h in available_heights):
                available.append(q)

    return available if available else QUALITY_OPTIONS


def get_merge_format(quality: str) -> str:
    """Get the merge format for FFmpeg merging."""
    if quality.lower() in ("audio", "audio only"):
        return "mp3"
    return "mp4"
