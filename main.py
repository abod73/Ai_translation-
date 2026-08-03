"""
AI Turkish Video Translator Bot - Main Entry Point
Initializes and runs the bot application (Google Colab Compatible).
"""

import asyncio
import signal
import sys
from pathlib import Path

# تطبيق إصلاح asyncio الخاص بـ Colab تلقائياً
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import config
from logger import setup_logger, get_logger
from bot import TurkishTranslatorBot
from utils import check_ffmpeg, check_gpu, get_gpu_info, clean_temp_directory


def check_dependencies():
    """Check all required dependencies are available."""
    log = get_logger("main")

    # Check FFmpeg
    if not check_ffmpeg():
        log.error("❌ FFmpeg is not installed!")
        log.error("Install it with: apt install ffmpeg / brew install ffmpeg")
        sys.exit(1)
    log.info("✅ FFmpeg found")

    # Check GPU
    if check_gpu():
        log.info(f"✅ GPU available: {get_gpu_info()}")
    else:
        log.warning("⚠️ No GPU found. Using CPU (slower processing)")

    # Check Python version
    if sys.version_info < (3, 10):
        log.warning(f"⚠️ Python {sys.version_info.major}.{sys.version_info.minor} "
                     f"detected. Recommended: 3.10+")

    # Clean old temp files
    clean_temp_directory(config.TEMP_FOLDER, max_age_hours=48)
    log.info("✅ Temp directory cleaned")


async def async_main():
    """Async Main entry point for Colab/Async environment."""
    log = get_logger("main")
    log.info("🚀 Starting AI Turkish Video Translator Bot...")

    # Check dependencies
    check_dependencies()

    # Validate configuration
    errors = config.validate()
    if errors:
        log.error("❌ Configuration errors:")
        for err in errors:
            log.error(f"   • {err}")
        log.error("\nSet the required environment variables:")
        log.error("  export BOT_TOKEN='your_bot_token'")
        log.error("  export API_ID='your_api_id'")
        log.error("  export API_HASH='your_api_hash'")
        sys.exit(1)

    # Create and run bot
    bot = TurkishTranslatorBot()

    try:
        await bot.run()
    except KeyboardInterrupt:
        log.info("Keyboard interrupt received")
    except Exception as e:
        log.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await bot.stop()
        log.info("👋 Bot shutdown complete")


def main():
    """Main entry point wrapper."""
    setup_logger("turkish_bot")
    try:
        # إذا كنا في Colab أو بيئة بها event loop يعمل مسبقاً
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(async_main())
        else:
            loop.run_until_complete(async_main())
    except Exception:
        asyncio.run(async_main())


if __name__ == "__main__":
    main()
