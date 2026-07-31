"""
AI Turkish Video Translator Bot - Subtitle Editor Module
Advanced subtitle editing: timing adjustment, merging, splitting.
"""

from typing import Optional
from logger import get_logger

log = get_logger("subtitle_editor")


def adjust_timing(
    segments: list[dict],
    offset: float = 0.0,
    speed_factor: float = 1.0
) -> list[dict]:
    """
    Adjust timing of all segments.

    Args:
        segments: List of segment dicts.
        offset: Time offset in seconds (positive = delay).
        speed_factor: Speed multiplier (>1 = faster).

    Returns:
        Adjusted segments.
    """
    adjusted = []
    for seg in segments:
        new_seg = dict(seg)
        new_seg["start"] = max(0, (seg["start"] + offset) * speed_factor)
        new_seg["end"] = max(0, (seg["end"] + offset) * speed_factor)
        adjusted.append(new_seg)
    return adjusted


def merge_close_segments(
    segments: list[dict],
    max_gap: float = 0.3,
    max_duration: float = 7.0
) -> list[dict]:
    """
    Merge segments that are very close together.

    Args:
        segments: List of segment dicts.
        max_gap: Maximum gap in seconds to merge.
        max_duration: Maximum duration for merged segment.

    Returns:
        Merged segments.
    """
    if not segments:
        return []

    merged = [dict(segments[0])]

    for seg in segments[1:]:
        prev = merged[-1]
        gap = seg["start"] - prev["end"]
        combined_duration = seg["end"] - prev["start"]

        if gap <= max_gap and combined_duration <= max_duration:
            # Merge with previous
            prev["end"] = seg["end"]
            prev["text"] = f"{prev.get('text', '')} {seg.get('text', '')}".strip()
            if "translated_text" in prev or "translated_text" in seg:
                prev["translated_text"] = (
                    f"{prev.get('translated_text', '')} "
                    f"{seg.get('translated_text', '')}"
                ).strip()
        else:
            merged.append(dict(seg))

    log.debug(f"Merged {len(segments)} -> {len(merged)} segments")
    return merged


def split_long_segments(
    segments: list[dict],
    max_duration: float = 6.0,
    max_chars: int = 80
) -> list[dict]:
    """
    Split segments that are too long.

    Args:
        segments: List of segment dicts.
        max_duration: Maximum duration per segment.
        max_chars: Maximum characters per segment.

    Returns:
        Split segments.
    """
    result = []
    seg_id = 0

    for seg in segments:
        duration = seg["end"] - seg["start"]
        text = seg.get("translated_text", seg.get("text", ""))

        if duration <= max_duration and len(text) <= max_chars:
            new_seg = dict(seg)
            new_seg["id"] = seg_id
            result.append(new_seg)
            seg_id += 1
        else:
            # Split by sentences or midpoint
            parts = _split_text(text)
            if len(parts) <= 1:
                new_seg = dict(seg)
                new_seg["id"] = seg_id
                result.append(new_seg)
                seg_id += 1
            else:
                part_duration = duration / len(parts)
                for i, part in enumerate(parts):
                    new_seg = dict(seg)
                    new_seg["id"] = seg_id
                    new_seg["start"] = seg["start"] + (i * part_duration)
                    new_seg["end"] = seg["start"] + ((i + 1) * part_duration)
                    if "translated_text" in seg:
                        new_seg["translated_text"] = part
                    else:
                        new_seg["text"] = part
                    result.append(new_seg)
                    seg_id += 1

    return result


def _split_text(text: str) -> list[str]:
    """Split text at sentence boundaries."""
    import re
    # Try splitting at sentence-ending punctuation
    parts = re.split(r'(?<=[.!?،؟。])\s+', text)
    if len(parts) > 1:
        return [p.strip() for p in parts if p.strip()]

    # Try splitting at commas
    parts = re.split(r'(?<=[,،])\s+', text)
    if len(parts) > 1:
        return [p.strip() for p in parts if p.strip()]

    # Split at midpoint
    mid = len(text) // 2
    space_idx = text.rfind(' ', 0, mid)
    if space_idx == -1:
        space_idx = text.find(' ', mid)
    if space_idx != -1:
        return [text[:space_idx].strip(), text[space_idx:].strip()]

    return [text]


def fix_overlapping_segments(segments: list[dict]) -> list[dict]:
    """Fix overlapping timestamps between consecutive segments."""
    if not segments:
        return []

    fixed = [dict(segments[0])]

    for seg in segments[1:]:
        prev = fixed[-1]
        if seg["start"] < prev["end"]:
            # Overlap detected - adjust
            overlap = prev["end"] - seg["start"]
            if overlap < 0.5:
                # Small overlap: push current start
                seg = dict(seg)
                seg["start"] = prev["end"]
            else:
                # Large overlap: split the difference
                midpoint = (prev["end"] + seg["start"]) / 2
                prev["end"] = midpoint
                seg = dict(seg)
                seg["start"] = midpoint
        fixed.append(seg)

    return fixed


def ensure_minimum_duration(
    segments: list[dict],
    min_duration: float = 0.5
) -> list[dict]:
    """Ensure all segments have a minimum duration."""
    result = []
    for seg in segments:
        new_seg = dict(seg)
        if new_seg["end"] - new_seg["start"] < min_duration:
            new_seg["end"] = new_seg["start"] + min_duration
        result.append(new_seg)
    return result


def optimize_segments(segments: list[dict]) -> list[dict]:
    """
    Apply all optimizations to segments.

    Pipeline: merge close -> split long -> fix overlaps -> min duration
    """
    log.info(f"Optimizing {len(segments)} segments")

    segments = merge_close_segments(segments)
    segments = split_long_segments(segments)
    segments = fix_overlapping_segments(segments)
    segments = ensure_minimum_duration(segments)

    # Re-index
    for i, seg in enumerate(segments):
        seg["id"] = i

    log.info(f"Optimization complete: {len(segments)} segments")
    return segments
