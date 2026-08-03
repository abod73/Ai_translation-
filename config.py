"""
AI Turkish Video Translator Bot - Configuration Module
All bot settings and environment variables are managed here.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# ─── Base Directories ───────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
OUTPUTS_DIR = BASE_DIR / "outputs"
SUBTITLES_DIR = BASE_DIR / "subtitles"
SESSIONS_DIR = BASE_DIR / "sessions"
TEMP_DIR = BASE_DIR / "temp"
FONTS_DIR = BASE_DIR / "fonts"
LOGS_DIR = BASE_DIR / "logs"
DB_DIR = BASE_DIR / "database"

# Create all directories
for d in [DOWNLOADS_DIR, OUTPUTS_DIR, SUBTITLES_DIR, SESSIONS_DIR,
          TEMP_DIR, FONTS_DIR, LOGS_DIR, DB_DIR]:
    d.mkdir(parents=True, exist_ok=True)


@dataclass
class BotConfig:
    """Main bot configuration loaded from environment variables."""

    # ─── Base Paths ─────────────────────────────────────────────────
    BASE_DIR: Path = BASE_DIR
    SESSIONS_DIR: str = str(SESSIONS_DIR)

    # ─── Telegram Credentials ───────────────────────────────────────
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    API_ID: int = int(os.getenv("API_ID", "0"))
    API_HASH: str = os.getenv("API_HASH", "")
    ADMIN_IDS: list[int] = field(default_factory=lambda: [
        int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
    ])

    # ─── Session ────────────────────────────────────────────────────
    SESSION_NAME: str = os.getenv("SESSION_NAME", "turkish_translator_bot")
    SESSION_PATH: str = str(SESSIONS_DIR / "bot_session")

    # ─── Download Settings ──────────────────────────────────────────
    DEFAULT_QUALITY: str = os.getenv("DEFAULT_QUALITY", "720")
    MAX_DOWNLOAD_SIZE_GB: float = float(os.getenv("MAX_DOWNLOAD_SIZE_GB", "2.0"))
    MAX_VIDEO_DURATION_MIN: int = int(os.getenv("MAX_VIDEO_DURATION_MIN", "180"))
    DOWNLOAD_FOLDER: str = str(DOWNLOADS_DIR)
    OUTPUT_FOLDER: str = str(OUTPUTS_DIR)
    TEMP_FOLDER: str = str(TEMP_DIR)
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "3"))

    # ─── Language Settings ──────────────────────────────────────────
    SOURCE_LANGUAGE: str = os.getenv("SOURCE_LANGUAGE", "tr")  # Turkish
    TARGET_LANGUAGE: str = os.getenv("TARGET_LANGUAGE", "ar")  # Arabic
    DEFAULT_LANGUAGE: str = TARGET_LANGUAGE

    # ─── Whisper Settings ───────────────────────────────────────────
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "large-v3")
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "auto")  # auto, cuda, cpu
    WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "auto")
    WHISPER_BEAM_SIZE: int = int(os.getenv("WHISPER_BEAM_SIZE", "5"))
    WHISPER_VAD_FILTER: bool = os.getenv("WHISPER_VAD_FILTER", "true").lower() == "true"
    WHISPER_VAD_MIN_SILENCE_MS: int = int(os.getenv("WHISPER_VAD_MIN_SILENCE_MS", "500"))
    WHISPER_VAD_MIN_SPEECH_MS: int = int(os.getenv("WHISPER_VAD_MIN_SPEECH_MS", "250"))
    WHISPER_WORD_TIMESTAMPS: bool = os.getenv("WHISPER_WORD_TIMESTAMPS", "true").lower() == "true"

    # ─── Translation Settings ───────────────────────────────────────
    TRANSLATION_MODEL: str = os.getenv("TRANSLATION_MODEL", "facebook/nllb-200-1.3B")
    TRANSLATION_DEVICE: str = os.getenv("TRANSLATION_DEVICE", "auto")
    TRANSLATION_MAX_LENGTH: int = int(os.getenv("TRANSLATION_MAX_LENGTH", "512"))
    TRANSLATION_BATCH_SIZE: int = int(os.getenv("TRANSLATION_BATCH_SIZE", "8"))

    # ─── LLM Refinement Settings ────────────────────────────────────
    USE_LLM_REFINEMENT: bool = os.getenv("USE_LLM_REFINEMENT", "false").lower() == "true"
    LLM_MODEL: str = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
    LLM_DEVICE: str = os.getenv("LLM_DEVICE", "auto")
    LLM_MAX_NEW_TOKENS: int = int(os.getenv("LLM_MAX_NEW_TOKENS", "512"))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))

    # ─── FFmpeg Settings ────────────────────────────────────────────
    FFMPEG_PATH: str = os.getenv("FFMPEG_PATH", "ffmpeg")
    FFPROBE_PATH: str = os.getenv("FFPROBE_PATH", "ffprobe")
    FONT_PATH: str = os.getenv("FONT_PATH", str(FONTS_DIR / "Amiri-Regular.ttf"))
    FONT_SIZE: int = int(os.getenv("FONT_SIZE", "24"))
    SUBTITLE_MARGIN_V: int = int(os.getenv("SUBTITLE_MARGIN_V", "40"))
    SUBTITLE_OUTLINE: int = int(os.getenv("SUBTITLE_OUTLINE", "2"))
    SUBTITLE_SHADOW: int = int(os.getenv("SUBTITLE_SHADOW", "1"))
    VIDEO_CODEC: str = os.getenv("VIDEO_CODEC", "libx264")
    AUDIO_CODEC: str = os.getenv("AUDIO_CODEC", "aac")
    VIDEO_PRESET: str = os.getenv("VIDEO_PRESET", "medium")
    VIDEO_CRF: int = int(os.getenv("VIDEO_CRF", "23"))

    # ─── Telegram Upload Settings ───────────────────────────────────
    DELETE_TEMP_FILES: bool = os.getenv("DELETE_TEMP_FILES", "true").lower() == "true"
    SEND_ORIGINAL: bool = os.getenv("SEND_ORIGINAL", "false").lower() == "true"
    SEND_SUBTITLE: bool = os.getenv("SEND_SUBTITLE", "true").lower() == "true"
    SEND_TRANSLATED: bool = os.getenv("SEND_TRANSLATED", "true").lower() == "true"
    MAX_TELEGRAM_FILE_SIZE_MB: int = 2000  # Telegram limit for bots

    # ─── GPU Settings ───────────────────────────────────────────────
    USE_GPU: bool = os.getenv("USE_GPU", "true").lower() == "true"

    # ─── Database ───────────────────────────────────────────────────
    DATABASE_PATH: str = str(DB_DIR / "bot_database.db")

    # ─── Logging ────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = str(LOGS_DIR / "bot.log")
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT: int = 5

    # ─── Names Dictionary ───────────────────────────────────────────
    NAMES_DICT_PATH: str = str(BASE_DIR / "names_dictionary.json")

    # ─── yt-dlp Cookie ─────────────────────────────────────────────
    COOKIES_FILE: Optional[str] = os.getenv("COOKIES_FILE", None)

    def validate(self) -> list[str]:
        """Validate required configuration values."""
        errors = []
        if not self.BOT_TOKEN:
            errors.append("BOT_TOKEN is required")
        if not self.API_ID or self.API_ID == 0:
            errors.append("API_ID is required")
        if not self.API_HASH:
            errors.append("API_HASH is required")
        return errors

    def get_device(self, preference: str = "auto") -> str:
        """Determine the best available device."""
        if preference != "auto":
            return preference
        if self.USE_GPU:
            try:
                import torch
                if torch.cuda.is_available():
                    return "cuda"
            except ImportError:
                pass
        return "cpu"

    def get_whisper_compute_type(self, device: str) -> str:
        """Determine the best compute type for Whisper."""
        if self.WHISPER_COMPUTE_TYPE != "auto":
            return self.WHISPER_COMPUTE_TYPE
        if device == "cuda":
            return "float16"
        return "int8"


# Global config instance
config = BotConfig()
