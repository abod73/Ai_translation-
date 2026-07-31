"""
AI Turkish Video Translator Bot - Video Merger Module
Handles final video processing and merging with FFmpeg.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional

from config import config
from logger import get_logger
from utils import run_command, ensure_directory, format_size

log = get_logger("video_merger")


async def merge_video_with_subtitle(
    video_path: str,
    subtitle_path: str,
    output_path: str,
    burn_subtitle: bool = True,
    font_name: str = None,
    font_size: int = None
) -> bool:
    """
    Merge video with subtitle (burn or embed).

    Args:
        video_path: Input video path.
        subtitle_path: SRT subtitle path.
        output_path: Output video path.
        burn_subtitle: If True, burn subtitle into video. If False, embed as track.
        font_name: Font name for burned subtitles.
        font_size: Font size for burned subtitles.

    Returns:
        True if successful.
    """
    ensure_directory(os.path.dirname(output_path))

    if burn_subtitle:
        return await _burn_subtitle(
            video_path, subtitle_path, output_path,
            font_name, font_size
        )
    else:
        return await _embed_subtitle(
            video_path, subtitle_path, output_path
        )


async def _burn_subtitle(
    video_path: str,
    subtitle_path: str,
    output_path: str,
    font_name: str = None,
    font_size: int = None
) -> bool:
    """Burn subtitle into video (hardcoded)."""
    font_name = font_name or "Amiri"
    font_size = font_size or config.FONT_SIZE

    # Escape subtitle path for FFmpeg
    escaped_sub = subtitle_path.replace("\\", "/").replace(":", "\\:")

    sub_filter = (
        f"subtitles='{escaped_sub}':"
        f"force_style='FontName={font_name},"
        f"FontSize={font_size},"
        f"PrimaryColour=&H00FFFFFF,"
        f"OutlineColour=&H00000000,"
        f"BackColour=&H80000000,"
        f"Outline={config.SUBTITLE_OUTLINE},"
        f"Shadow={config.SUBTITLE_SHADOW},"
        f"MarginV={config.SUBTITLE_MARGIN_V},"
        f"Alignment=2'"
    )

    cmd = [
        config.FFMPEG_PATH,
        "-y",
        "-i", video_path,
        "-vf", sub_filter,
        "-c:v", config.VIDEO_CODEC,
        "-preset", config.VIDEO_PRESET,
        "-crf", str(config.VIDEO_CRF),
        "-c:a", config.AUDIO_CODEC,
        "-b:a", "192k",
        "-movflags", "+faststart",
        "-threads", "0",
        output_path
    ]

    log.info(f"Burning subtitle: {video_path} -> {output_path}")
    returncode, stdout, stderr = await run_command(cmd, timeout=14400)

    if returncode != 0:
        log.error(f"Burn failed: {stderr[:500]}")
        # Fallback: try without force_style
        return await _burn_subtitle_simple(video_path, subtitle_path, output_path)

    file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    log.info(f"Burn complete: {output_path} ({format_size(file_size)})")
    return True


async def _burn_subtitle_simple(
    video_path: str,
    subtitle_path: str,
    output_path: str
) -> bool:
    """Fallback: burn subtitle without custom styling."""
    escaped_sub = subtitle_path.replace("\\", "/").replace(":", "\\:")

    cmd = [
        config.FFMPEG_PATH,
        "-y",
        "-i", video_path,
        "-vf", f"subtitles='{escaped_sub}'",
        "-c:v", config.VIDEO_CODEC,
        "-preset", "fast",
        "-crf", "28",
        "-c:a", "copy",
        output_path
    ]

    log.info("Trying simple subtitle burn...")
    returncode, stdout, stderr = await run_command(cmd, timeout=14400)

    if returncode != 0:
        log.error(f"Simple burn also failed: {stderr[:500]}")
        return False

    return True


async def _embed_subtitle(
    video_path: str,
    subtitle_path: str,
    output_path: str
) -> bool:
    """Embed subtitle as a soft track (MKV)."""
    # Change extension to MKV for soft subtitle support
    output_mkv = str(Path(output_path).with_suffix(".mkv"))

    cmd = [
        config.FFMPEG_PATH,
        "-y",
        "-i", video_path,
        "-i", subtitle_path,
        "-c", "copy",
        "-c:s", "srt",
        "-metadata:s:s:0", "language=ara",
        "-metadata:s:s:0", "title=Arabic",
        "-disposition:s:0", "default",
        output_mkv
    ]

    log.info(f"Embedding subtitle: {video_path} -> {output_mkv}")
    returncode, stdout, stderr = await run_command(cmd, timeout=3600)

    if returncode != 0:
        log.error(f"Embed failed: {stderr[:500]}")
        return False

    # Rename to output path if different
    if output_mkv != output_path:
        os.rename(output_mkv, output_path)

    return True


async def get_video_info_ffprobe(video_path: str) -> dict:
    """Get detailed video info using ffprobe."""
    cmd = [
        config.FFPROBE_PATH,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        video_path
    ]

    returncode, stdout, stderr = await run_command(cmd, timeout=60)
    if returncode != 0:
        return {}

    import json
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {}


async def check_video_duration(video_path: str) -> float:
    """Get video duration in seconds."""
    info = await get_video_info_ffprobe(video_path)
    try:
        return float(info.get("format", {}).get("duration", 0))
    except (ValueError, TypeError):
        return 0


async def resize_video(
    video_path: str,
    output_path: str,
    max_height: int = 720
) -> bool:
    """Resize video to fit within max height while maintaining aspect ratio."""
    cmd = [
        config.FFMPEG_PATH,
        "-y",
        "-i", video_path,
        "-vf", f"scale=-2:'min({max_height},ih)'",
        "-c:v", config.VIDEO_CODEC,
        "-preset", config.VIDEO_PRESET,
        "-crf", str(config.VIDEO_CRF),
        "-c:a", "copy",
        output_path
    ]

    returncode, stdout, stderr = await run_command(cmd, timeout=7200)
    return returncode == 0


async def split_video_for_telegram(
    video_path: str,
    output_dir: str,
    max_size_mb: int = 1950
) -> list[str]:
    """
    Split video into parts that fit Telegram's file size limit.

    Args:
        video_path: Input video path.
        output_dir: Output directory for parts.
        max_size_mb: Maximum size per part in MB.

    Returns:
        List of output file paths.
    """
    file_size = os.path.getsize(video_path)
    max_size_bytes = max_size_mb * 1024 * 1024

    if file_size <= max_size_bytes:
        return [video_path]

    duration = await check_video_duration(video_path)
    if duration <= 0:
        return [video_path]

    # Calculate number of parts
    num_parts = int(file_size / max_size_bytes) + 1
    part_duration = duration / num_parts

    ensure_directory(output_dir)
    parts = []
    base_name = Path(video_path).stem

    for i in range(num_parts):
        start = i * part_duration
        output_part = os.path.join(output_dir, f"{base_name}_part{i+1}.mp4")

        cmd = [
            config.FFMPEG_PATH,
            "-y",
            "-ss", str(start),
            "-i", video_path,
            "-t", str(part_duration),
            "-c:v", config.VIDEO_CODEC,
            "-preset", "fast",
            "-crf", "23",
            "-c:a", config.AUDIO_CODEC,
            "-movflags", "+faststart",
            output_part
        ]

        returncode, _, stderr = await run_command(cmd, timeout=3600)
        if returncode == 0 and os.path.exists(output_part):
            parts.append(output_part)
        else:
            log.error(f"Failed to split part {i+1}: {stderr[:200]}")

    return parts if parts else [video_path]
