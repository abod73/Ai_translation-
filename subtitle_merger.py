"""
AI Turkish Video Translator Bot - Subtitle Merger Module
Handles combining subtitle tracks and converting formats.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional

from config import config
from logger import get_logger
from utils import run_command, ensure_directory

log = get_logger("subtitle_merger")


async def embed_subtitle_to_mkv(
    video_path: str,
    subtitle_path: str,
    output_path: str,
    language: str = "ara",
    title: str = "Arabic"
) -> bool:
    """
    Embed subtitle into MKV container without re-encoding.

    Args:
        video_path: Input video path.
        subtitle_path: SRT subtitle path.
        output_path: Output MKV path.
        language: Subtitle language code.
        title: Subtitle track title.

    Returns:
        True if successful.
    """
    cmd = [
        config.FFMPEG_PATH,
        "-y",
        "-i", video_path,
        "-i", subtitle_path,
        "-c", "copy",
        "-c:s", "srt",
        "-metadata:s:s:0", f"language={language}",
        "-metadata:s:s:0", f"title={title}",
        "-disposition:s:0", "default",
        output_path
    ]

    log.info(f"Embedding subtitle into MKV: {output_path}")
    returncode, stdout, stderr = await run_command(cmd, timeout=600)

    if returncode != 0:
        log.error(f"MKV subtitle embedding failed: {stderr}")
        return False

    log.info("Subtitle embedded successfully")
    return True


async def burn_subtitle_to_video(
    video_path: str,
    subtitle_path: str,
    output_path: str,
    font_name: str = "Amiri",
    font_size: int = None,
    margin_v: int = None,
    outline: int = None,
    shadow: int = None
) -> bool:
    """
    Burn (hardcode) subtitle into video using FFmpeg.

    Args:
        video_path: Input video path.
        subtitle_path: SRT/ASS subtitle path.
        output_path: Output video path.
        font_name: Font name for subtitles.
        font_size: Font size.
        margin_v: Vertical margin.
        outline: Outline width.
        shadow: Shadow offset.

    Returns:
        True if successful.
    """
    font_size = font_size or config.FONT_SIZE
    margin_v = margin_v or config.SUBTITLE_MARGIN_V
    outline = outline or config.SUBTITLE_OUTLINE
    shadow = shadow or config.SUBTITLE_SHADOW

    # Escape paths for FFmpeg subtitle filter
    escaped_sub = _escape_ffmpeg_path(subtitle_path)

    # Build subtitle filter
    sub_filter = (
        f"subtitles={escaped_sub}:"
        f"force_style='FontName={font_name},"
        f"FontSize={font_size},"
        f"PrimaryColour=&H00FFFFFF,"
        f"OutlineColour=&H00000000,"
        f"BackColour=&H80000000,"
        f"Outline={outline},"
        f"Shadow={shadow},"
        f"MarginV={margin_v},"
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
        output_path
    ]

    log.info(f"Burning subtitle into video: {output_path}")
    returncode, stdout, stderr = await run_command(cmd, timeout=7200)

    if returncode != 0:
        log.error(f"Subtitle burning failed: {stderr}")
        return False

    log.info("Subtitle burned successfully")
    return True


async def convert_srt_to_ass(
    srt_path: str,
    ass_path: str,
    font_name: str = "Amiri",
    font_size: int = 24,
    margin_v: int = 40
) -> bool:
    """
    Convert SRT to ASS format with custom styling.

    Args:
        srt_path: Input SRT path.
        ass_path: Output ASS path.
        font_name: Font name.
        font_size: Font size.
        margin_v: Vertical margin.

    Returns:
        True if successful.
    """
    # First convert with FFmpeg
    cmd = [
        config.FFMPEG_PATH,
        "-y",
        "-i", srt_path,
        ass_path
    ]

    returncode, stdout, stderr = await run_command(cmd, timeout=120)
    if returncode != 0:
        log.error(f"SRT to ASS conversion failed: {stderr}")
        return False

    # Modify ASS style
    try:
        _modify_ass_style(ass_path, font_name, font_size, margin_v)
    except Exception as e:
        log.warning(f"Failed to modify ASS style: {e}")

    return True


def _modify_ass_style(
    ass_path: str,
    font_name: str,
    font_size: int,
    margin_v: int
):
    """Modify ASS file style section."""
    with open(ass_path, "r", encoding="utf-8-sig") as f:
        content = f.read()

    # Replace style line
    import re
    style_pattern = r"Style: Default,.*"
    new_style = (
        f"Style: Default,{font_name},{font_size},"
        f"&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
        f"-1,0,0,0,100,100,0,0,1,2,1,2,10,10,{margin_v},1"
    )
    content = re.sub(style_pattern, new_style, content)

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(content)


def _escape_ffmpeg_path(path: str) -> str:
    """Escape file path for FFmpeg filter usage."""
    # FFmpeg requires specific escaping for paths in filters
    path = path.replace("\\", "/")
    path = path.replace(":", "\\:")
    path = path.replace("'", "\\'")
    return path


async def extract_subtitle_from_video(
    video_path: str,
    output_path: str,
    stream_index: int = 0
) -> bool:
    """
    Extract subtitle stream from video file.

    Args:
        video_path: Input video path.
        output_path: Output SRT path.
        stream_index: Subtitle stream index.

    Returns:
        True if successful.
    """
    cmd = [
        config.FFMPEG_PATH,
        "-y",
        "-i", video_path,
        "-map", f"0:s:{stream_index}",
        output_path
    ]

    returncode, stdout, stderr = await run_command(cmd, timeout=300)
    if returncode != 0:
        log.error(f"Subtitle extraction failed: {stderr}")
        return False

    log.info(f"Subtitle extracted: {output_path}")
    return True
