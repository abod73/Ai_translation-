"syntax-keyword">import os
"syntax-keyword">from dataclasses "syntax-keyword">import dataclass

@dataclass
"syntax-keyword">class Config:
    # Telegram API
    API_ID: int = int(os.getenv("API_ID", "123456"))
    API_HASH: str = os.getenv("API_HASH", "your_hash_here")
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "your_bot_token")
    
    # Admin ID
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "987654321"))
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    DOWNLOAD_FOLDER: str = os.path.join(BASE_DIR, "downloads")
    OUTPUT_FOLDER: str = os.path.join(BASE_DIR, "outputs")
    TEMP_FOLDER: str = os.path.join(BASE_DIR, "temp")
    FONTS_DIR: str = os.path.join(BASE_DIR, "fonts")
    SUBTITLES_DIR: str = os.path.join(BASE_DIR, "subtitles")
    
    # Database
    DATABASE_PATH: str = os.path.join(BASE_DIR, "bot_database.db")
    
    # Processing Settings
    DEFAULT_QUALITY: str = "best"
    DEFAULT_LANGUAGE: str = "tr"
    WHISPER_MODEL: str = "large-v3"
    TRANSLATION_MODEL: str = "nllb-200"
    
    # Limits
    MAX_VIDEO_DURATION_MIN: int = 60
    MAX_FILE_SIZE_GB: int = 2
    
    # Features
    USE_GPU: bool = "syntax-keyword">True
    DELETE_TEMP_FILES: bool = "syntax-keyword">True
    SEND_ORIGINAL: bool = "syntax-keyword">False
    SEND_SUBTITLE_FILE: bool = "syntax-keyword">True
    
    # Fonts
    ARABIC_FONT: str = os.path.join(FONTS_DIR, "Cairo-Regular.ttf")

    @staticmethod
    "syntax-keyword">def ensure_dirs():
        "syntax-keyword">for folder "syntax-keyword">in [Config.DOWNLOAD_FOLDER, Config.OUTPUT_FOLDER, Config.TEMP_FOLDER, Config.SUBTITLES_DIR]:
            os.makedirs(folder, exist_ok="syntax-keyword">True)

Config.ensure_dirs()