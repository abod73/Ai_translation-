"""
AI Turkish Video Translator Bot - Utilities Module
Common helper functions used across the project.
"""

import os
import re
import json
import shutil
import asyncio
import hashlib
import unicodedata
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

from logger import get_logger

log = get_logger("utils")


def format_duration(seconds: float) -> str:
    """Convert seconds to HH:MM:SS or MM:SS format."""
    if seconds is None or seconds < 0:
        return "00:00"
    td = timedelta(seconds=int(seconds))
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_size(size_bytes: float) -> str:
    """Convert bytes to human-readable size string."""
    if size_bytes is None or size_bytes <= 0:
        return "Unknown"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_speed(speed_bytes: float) -> str:
    """Convert bytes/sec to human-readable speed string."""
    if speed_bytes is None or speed_bytes <= 0:
        return "-- KB/s"
    return f"{format_size(speed_bytes)}/s"


def format_eta(eta_seconds: float) -> str:
    """Convert ETA seconds to human-readable string."""
    if eta_seconds is None or eta_seconds <= 0:
        return "--:--"
    return format_duration(eta_seconds)


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """Sanitize a string to be safe for use as a filename."""
    if not name:
        return "untitled"
    # Remove or replace invalid characters
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    # Remove leading/trailing dots and spaces
    name = name.strip('. ')
    # Limit length
    if len(name) > max_length:
        name = name[:max_length]
    return name or "untitled"


def generate_unique_id() -> str:
    """Generate a unique ID based on timestamp and random hash."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_hash = hashlib.md5(os.urandom(16)).hexdigest()[:8]
    return f"{timestamp}_{random_hash}"


def get_file_extension(url: str, default: str = ".mp4") -> str:
    """Extract file extension from URL or return default."""
    from urllib.parse import urlparse, unquote
    parsed = urlparse(url)
    path = unquote(parsed.path)
    ext = Path(path).suffix.lower()
    if ext in ['.mp4', '.mkv', '.avi', '.webm', '.flv', '.mov', '.m4a', '.mp3', '.ogg']:
        return ext
    return default


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL."""
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )
    return bool(url_pattern.match(url.strip()))


def is_m3u8_url(url: str) -> bool:
    """Check if URL is an m3u8 stream."""
    return '.m3u8' in url.lower()


def get_site_name(url: str) -> str:
    """Extract website name from URL."""
    from urllib.parse import urlparse
    parsed = urlparse(url.strip())
    domain = parsed.netloc.lower()
    domain = domain.replace('www.', '')

    site_map = {
        'youtube.com': 'YouTube',
        'youtu.be': 'YouTube',
        'twitter.com': 'Twitter/X',
        'x.com': 'Twitter/X',
        'dailymotion.com': 'Dailymotion',
        'facebook.com': 'Facebook',
        'instagram.com': 'Instagram',
        'tiktok.com': 'TikTok',
        'vimeo.com': 'Vimeo',
        'twitch.tv': 'Twitch',
        'reddit.com': 'Reddit',
    }

    for key, name in site_map.items():
        if key in domain:
            return name
    return domain.split('.')[0].capitalize()


def clean_temp_directory(temp_dir: str, max_age_hours: int = 24):
    """Remove files older than max_age_hours from temp directory."""
    try:
        temp_path = Path(temp_dir)
        if not temp_path.exists():
            return
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        removed = 0
        for item in temp_path.rglob("*"):
            if item.is_file() and item.stat().st_mtime < cutoff:
                item.unlink()
                removed += 1
            elif item.is_dir() and not any(item.iterdir()):
                item.rmdir()
        if removed > 0:
            log.info(f"Cleaned {removed} old temp files")
    except Exception as e:
        log.error(f"Error cleaning temp directory: {e}")


def get_directory_size(directory: str) -> int:
    """Get total size of a directory in bytes."""
    total = 0
    dir_path = Path(directory)
    if not dir_path.exists():
        return 0
    for entry in dir_path.rglob("*"):
        if entry.is_file():
            total += entry.stat().st_size
    return total


async def run_command(cmd: list[str], timeout: int = 3600) -> tuple[int, str, str]:
    """
    Run a shell command asynchronously.

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    log.debug(f"Running command: {' '.join(cmd)}")
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
        return (
            process.returncode or 0,
            stdout.decode('utf-8', errors='replace'),
            stderr.decode('utf-8', errors='replace')
        )
    except asyncio.TimeoutError:
        log.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
        try:
            process.kill()
        except Exception:
            pass
        return (-1, "", "Command timed out")
    except Exception as e:
        log.error(f"Command failed: {e}")
        return (-1, "", str(e))


def load_json_file(filepath: str) -> dict:
    """Load and parse a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        log.warning(f"JSON file not found: {filepath}")
        return {}
    except json.JSONDecodeError as e:
        log.error(f"Invalid JSON in {filepath}: {e}")
        return {}


def save_json_file(filepath: str, data: dict, indent: int = 2):
    """Save data to a JSON file."""
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
    except Exception as e:
        log.error(f"Failed to save JSON to {filepath}: {e}")


def ensure_directory(path: str) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def remove_file(filepath: str) -> bool:
    """Safely remove a file."""
    try:
        p = Path(filepath)
        if p.exists() and p.is_file():
            p.unlink()
            return True
        return False
    except Exception as e:
        log.error(f"Failed to remove file {filepath}: {e}")
        return False


def remove_directory(dirpath: str) -> bool:
    """Safely remove a directory and its contents."""
    try:
        p = Path(dirpath)
        if p.exists() and p.is_dir():
            shutil.rmtree(p)
            return True
        return False
    except Exception as e:
        log.error(f"Failed to remove directory {dirpath}: {e}")
        return False


def check_ffmpeg() -> bool:
    """Check if FFmpeg is installed and accessible."""
    try:
        result = shutil.which("ffmpeg")
        return result is not None
    except Exception:
        return False


def check_gpu() -> bool:
    """Check if GPU (CUDA) is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def get_gpu_info() -> str:
    """Get GPU information string."""
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            props = torch.cuda.get_device_properties(0)
            
            # حساب حجم الذاكرة بالتوافق مع التسميات المختلفة لخاصية total_memory / total_mem
            total_bytes = getattr(props, 'total_memory', getattr(props, 'total_mem', 0))
            mem = total_bytes / (1024**3)
            return f"{name} ({mem:.1f} GB)"
        return "No GPU"
    except Exception as e:
        log.error(f"Error fetching GPU info: {e}")
        return "GPU Info Unavailable"


def normalize_arabic_text(text: str) -> str:
    """Normalize Arabic text for consistent display."""
    if not text:
        return text
    # Normalize Unicode
    text = unicodedata.normalize('NFC', text)
    # Common Arabic normalizations
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ة', 'ه')
    text = text.replace('ى', 'ي')
    return text


def chunk_list(lst: list, chunk_size: int) -> list[list]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def retry_async(max_retries: int = 3, delay: float = 2.0, backoff: float = 2.0):
    """Decorator for retrying async functions with exponential backoff."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        log.warning(
                            f"Attempt {attempt}/{max_retries} failed for "
                            f"{func.__name__}: {e}. Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        log.error(
                            f"All {max_retries} attempts failed for "
                            f"{func.__name__}: {e}"
                        )
            raise last_exception
        return wrapper
    return decorator
