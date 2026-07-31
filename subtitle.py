"""
AI Turkish Video Translator Bot - Subtitle Module
Creates SRT subtitle files from translated segments.
"""

import os
from pathlib import Path
from typing import Optional
from config import config
from logger import get_logger
from utils import ensure_directory

log = get_logger("subtitle")


def format_srt_timestamp(seconds: float) -> str:
    """
    Convert seconds to SRT timestamp format: HH:MM:SS,mmm

    Args:
        seconds: Time in seconds.

    Returns:
        Formatted timestamp string.
    """
    if seconds < 0:
        seconds = 0

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def create_srt_content(segments: list[dict], text_key: str = "translated_text") -> str:
    """
    Create SRT file content from segments.

    Args:
        segments: List of segment dicts with 'start', 'end', and text_key.
        text_key: Key to use for subtitle text.

    Returns:
        Complete SRT file content as string.
    """
    srt_lines = []

    for i, seg in enumerate(segments, 1):
        start = format_srt_timestamp(seg.get("start", 0))
        end = format_srt_timestamp(seg.get("end", 0))
        text = seg.get(text_key, seg.get("text", "")).strip()

        if not text:
            continue

        # Clean up text for SRT
        text = _clean_subtitle_text(text)

        # Split long lines
        text = _wrap_subtitle_text(text)

        srt_lines.append(f"{i}")
        srt_lines.append(f"{start} --> {end}")
        srt_lines.append(text)
        srt_lines.append("")  # Empty line between entries

    return "\n".join(srt_lines)


def _clean_subtitle_text(text: str) -> str:
    """Clean text for subtitle display."""
    # Remove excessive whitespace
    text = " ".join(text.split())
    # Remove leading/trailing punctuation artifacts
    text = text.strip(" .,;:!?-–—")
    # Fix common issues
    text = text.replace("  ", " ")
    # Ensure text is not empty after cleaning
    if not text:
        text = "..."
    return text


def _wrap_subtitle_text(text: str, max_chars: int = 42) -> str:
    """
    Wrap long subtitle text into multiple lines.

    Args:
        text: Subtitle text.
        max_chars: Maximum characters per line.

    Returns:
        Wrapped text with newlines.
    """
    if len(text) <= max_chars:
        return text

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars:
            current_line = f"{current_line} {word}".strip()
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    # Limit to 2 lines for readability
    if len(lines) > 2:
        mid = len(lines) // 2
        lines = [" ".join(lines[:mid]), " ".join(lines[mid:])]

    return "\n".join(lines)


def save_srt_file(
    segments: list[dict],
    output_path: str,
    text_key: str = "translated_text",
    encoding: str = "utf-8"
) -> str:
    """
    Save segments as an SRT file.

    Args:
        segments: List of segment dicts.
        output_path: Output file path.
        text_key: Key for subtitle text.
        encoding: File encoding.

    Returns:
        Path to the saved SRT file.
    """
    ensure_directory(os.path.dirname(output_path))
    content = create_srt_content(segments, text_key)

    # Add BOM for better compatibility
    with open(output_path, "w", encoding=f"{encoding}-sig") as f:
        f.write(content)

    log.info(f"SRT file saved: {output_path} ({len(segments)} segments)")
    return output_path


def create_dual_srt(
    segments: list[dict],
    output_path: str,
    source_key: str = "text",
    target_key: str = "translated_text"
) -> str:
    """
    Create a bilingual SRT file with both source and target text.

    Args:
        segments: List of segment dicts.
        output_path: Output file path.
        source_key: Key for source language text.
        target_key: Key for target language text.

    Returns:
        Path to the saved SRT file.
    """
    srt_lines = []

    for i, seg in enumerate(segments, 1):
        start = format_srt_timestamp(seg.get("start", 0))
        end = format_srt_timestamp(seg.get("end", 0))
        source_text = seg.get(source_key, "").strip()
        target_text = seg.get(target_key, "").strip()

        if not source_text and not target_text:
            continue

        combined = f"{target_text}\n<i>{source_text}</i>"

        srt_lines.append(f"{i}")
        srt_lines.append(f"{start} --> {end}")
        srt_lines.append(combined)
        srt_lines.append("")

    content = "\n".join(srt_lines)
    ensure_directory(os.path.dirname(output_path))

    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(content)

    log.info(f"Dual SRT file saved: {output_path}")
    return output_path


def parse_srt_file(filepath: str) -> list[dict]:
    """
    Parse an existing SRT file into segments.

    Args:
        filepath: Path to SRT file.

    Returns:
        List of segment dicts.
    """
    segments = []

    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()

        blocks = content.strip().split("\n\n")

        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue

            try:
                # Parse timestamp line
                time_line = lines[1]
                start_str, end_str = time_line.split(" --> ")
                start = _parse_timestamp(start_str.strip())
                end = _parse_timestamp(end_str.strip())
                text = "\n".join(lines[2:]).strip()

                segments.append({
                    "start": start,
                    "end": end,
                    "text": text,
                })
            except (ValueError, IndexError) as e:
                log.warning(f"Failed to parse SRT block: {e}")
                continue

    except Exception as e:
        log.error(f"Failed to parse SRT file {filepath}: {e}")

    return segments


def _parse_timestamp(ts: str) -> float:
    """Parse SRT timestamp to seconds."""
    parts = ts.replace(",", ".").split(":")
    hours = float(parts[0])
    minutes = float(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds
