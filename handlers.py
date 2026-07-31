"""
AI Turkish Video Translator Bot - Handlers Module
Message handlers for all bot commands and user interactions.
"""

import os
import time
import asyncio
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.types import Message

from config import config
from logger import get_logger
from database import db
from utils import (
    is_valid_url, is_m3u8_url, sanitize_filename,
    generate_unique_id, ensure_directory, format_size, format_duration
)
from video_info import extract_video_info, check_url_validity, VideoInfo
from downloader import downloader
from speech_to_text import stt
from translator import translator
from subtitle import save_srt_file
from subtitle_editor import optimize_segments
from video_merger import merge_video_with_subtitle
from telegram_sender import TelegramSender
from progress import ProgressTracker, MultiStepProgress, create_ytdlp_progress_hook
from keyboards import (
    get_main_menu_keyboard, get_start_keyboard,
    get_quality_keyboard, get_settings_keyboard,
    get_action_choice_keyboard
)

log = get_logger("handlers")

# User state tracking
user_states: dict[int, dict] = {}


def get_user_state(user_id: int) -> dict:
    """Get or create user state."""
    if user_id not in user_states:
        user_states[user_id] = {
            "action": None,
            "url": None,
            "video_info": None,
            "download_path": None,
            "task_id": None,
        }
    return user_states[user_id]


def clear_user_state(user_id: int):
    """Clear user state."""
    user_states.pop(user_id, None)


async def process_video_pipeline(
    client: Client,
    message: Message,
    url: str,
    quality: str = "720",
    auto_translate: bool = True
):
    """
    Complete video processing pipeline:
    Download -> Transcribe -> Translate -> Subtitle -> Merge -> Send
    """
    user_id = message.chat.id
    sender = TelegramSender(client)
    state = get_user_state(user_id)
    task_id = generate_unique_id()
    state["task_id"] = task_id

    # Send initial processing message
    progress_msg = await message.reply_text("⏳ جاري بدء المعالجة...")
    multi_progress = MultiStepProgress(progress_msg)

    work_dir = ensure_directory(str(Path(config.TEMP_FOLDER) / task_id))
    start_time = time.time()

    try:
        # ─── Step 1: Download ───────────────────────────────────────
        await multi_progress.set_step(0, "جاري تحميل الفيديو...")

        tracker = ProgressTracker(progress_msg, "📥 تحميل الفيديو")
        progress_hook = create_ytdlp_progress_hook(tracker)

        download_result = await downloader.download(
            url=url,
            quality=quality,
            progress_hook=progress_hook
        )

        if not download_result.success:
            await progress_msg.edit_text(
                f"❌ فشل التحميل:\n{download_result.error}"
            )
            return

        video_path = download_result.filepath
        video_title = sanitize_filename(
            Path(video_path).stem, max_length=50
        )
        state["download_path"] = video_path

        await db.increment_downloads(user_id)
        await db.increment_videos(user_id)

        if not auto_translate:
            # Send downloaded video only
            await sender.send_video(
                user_id, video_path,
                caption=f"🎬 {video_title}",
                duration=int(download_result.duration),
                progress_message=progress_msg
            )
            await multi_progress.complete_all("✅ تم تحميل الفيديو بنجاح!")
            return

        # ─── Step 2: Speech to Text ─────────────────────────────────
        await multi_progress.set_step(1, "جاري استخراج الكلام من الفيديو...")

        transcription = await stt.transcribe_video(
            video_path,
            language=config.SOURCE_LANGUAGE
        )

        if not transcription.segments:
            await progress_msg.edit_text(
                "⚠️ لم يتم العثور على كلام في الفيديو.\n"
                "سيتم إرسال الفيديو بدون ترجمة."
            )
            await sender.send_video(
                user_id, video_path,
                caption=f"🎬 {video_title}",
                duration=int(download_result.duration)
            )
            return

        await multi_progress.set_step(
            1,
            f"تم استخراج {transcription.total_segments} جملة"
        )

        # ─── Step 3: Translation ────────────────────────────────────
        await multi_progress.set_step(2, "جاري ترجمة النص إلى العربية...")

        segments_data = [seg.to_dict() for seg in transcription.segments]
        translated_segments = await translator.translate_segments(
            segments_data,
            source_lang=config.SOURCE_LANGUAGE,
            target_lang=config.TARGET_LANGUAGE
        )

        await db.increment_translations(user_id)

        # ─── Step 4: Create Subtitle ────────────────────────────────
        await multi_progress.set_step(3, "جاري إنشاء ملف الترجمة...")

        # Optimize segments
        optimized = optimize_segments(translated_segments)

        # Save SRT
        srt_path = str(work_dir / f"{video_title}_Arabic.srt")
        save_srt_file(optimized, srt_path, text_key="translated_text")

        # ─── Step 5: Merge Subtitle ─────────────────────────────────
        await multi_progress.set_step(4, "جاري دمج الترجمة مع الفيديو...")

        output_video = str(work_dir / f"{video_title}_translated.mp4")
        merge_success = await merge_video_with_subtitle(
            video_path=video_path,
            subtitle_path=srt_path,
            output_path=output_video,
            burn_subtitle=True
        )

        if not merge_success:
            await progress_msg.edit_text(
                "⚠️ فشل دمج الترجمة مع الفيديو.\n"
                "سيتم إرسال الملفات بشكل منفصل."
            )
            output_video = None

        # ─── Step 6: Send Results ───────────────────────────────────
        await multi_progress.set_step(5, "جاري إرسال الملفات...")

        await sender.send_processing_results(
            chat_id=user_id,
            video_path=output_video or video_path,
            subtitle_path=srt_path,
            original_video_path=video_path if config.SEND_ORIGINAL else None,
            video_title=video_title,
            duration=int(download_result.duration),
            progress_message=progress_msg
        )

        # Record translation
        processing_time = time.time() - start_time
        await db.add_translation_record(
            user_id=user_id,
            video_title=video_title,
            source_language=config.SOURCE_LANGUAGE,
            target_language=config.TARGET_LANGUAGE,
            segments_count=len(optimized),
            translation_model=config.TRANSLATION_MODEL,
            llm_used=config.USE_LLM_REFINEMENT,
            processing_time=processing_time
        )

        await multi_progress.complete_all(
            f"✅ تم الانتهاء بنجاح!\n"
            f"⏱ الوقت الإجمالي: {format_duration(processing_time)}\n"
            f"📝 عدد الجمل: {len(optimized)}"
        )

    except Exception as e:
        log.error(f"Pipeline error for {url}: {e}", exc_info=True)
        try:
            await progress_msg.edit_text(
                f"❌ حدث خطأ أثناء المعالجة:\n`{str(e)[:300]}`"
            )
        except Exception:
            pass

    finally:
        # Cleanup
        if config.DELETE_TEMP_FILES:
            from utils import remove_directory
            remove_directory(str(work_dir))
        clear_user_state(user_id)


# ─── Command Handlers ───────────────────────────────────────────────

async def handle_start(client: Client, message: Message):
    """Handle /start command."""
    user = message.from_user
    await db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code,
        is_admin=user.id in config.ADMIN_IDS
    )

    welcome_text = (
        f"مرحباً {user.first_name}! 👋\n\n"
        f"🎬 **بوت ترجمة الفيديوهات التركية**\n\n"
        f"أرسل رابط فيديو وسأقوم بـ:\n"
        f"1️⃣ تحميل الفيديو\n"
        f"2️⃣ استخراج الكلام التركي\n"
        f"3️⃣ ترجمته إلى العربية\n"
        f"4️⃣ دمج الترجمة مع الفيديو\n"
        f"5️⃣ إرسال النتيجة\n\n"
        f"📌 **المواقع المدعومة:**\n"
        f"YouTube, Twitter/X, Dailymotion, m3u8\n"
        f"وأي موقع يدعمه yt-dlp\n\n"
        f"اختر من القائمة أدناه أو أرسل رابطاً مباشرةً:"
    )

    await message.reply_text(
        welcome_text,
        reply_markup=get_start_keyboard()
    )


async def handle_help(client: Client, message: Message):
    """Handle /help command."""
    help_text = (
        "📖 **دليل الاستخدام**\n\n"
        "🎬 **تحميل فيديو:**\n"
        "أرسل رابط الفيديو واختر الجودة\n\n"
        "🌍 **ترجمة فيديو:**\n"
        "أرسل الرابط وسيتم التحميل والترجمة تلقائياً\n\n"
        "📄 **استخراج الترجمة:**\n"
        "استخراج النص من الفيديو كملف SRT\n\n"
        "🎞 **دمج الترجمة:**\n"
        "أرسل فيديو + ملف ترجمة لدمجهما\n\n"
        "⚙ **الإعدادات:**\n"
        "تخصيص الجودة واللغة والخيارات\n\n"
        "📌 **المواقع المدعومة:**\n"
        "• YouTube\n"
        "• Twitter/X\n"
        "• Dailymotion\n"
        "• m3u8 streams\n"
        "• وأي موقع يدعمه yt-dlp\n\n"
        "💡 **نصيحة:** يمكنك إرسال الرابط مباشرة بدون أوامر!"
    )
    await message.reply_text(help_text, reply_markup=get_main_menu_keyboard())


async def handle_admin(client: Client, message: Message):
    """Handle /admin command."""
    user_id = message.from_user.id
    if user_id not in config.ADMIN_IDS:
        await message.reply_text("❌ ليس لديك صلاحية")
        return

    stats = await db.get_admin_stats()

    from utils import get_directory_size, format_size
    downloads_size = format_size(get_directory_size(config.DOWNLOAD_FOLDER))
    temp_size = format_size(get_directory_size(config.TEMP_FOLDER))
    outputs_size = format_size(get_directory_size(config.OUTPUT_FOLDER))

    admin_text = (
        "🔧 **لوحة الإدارة**\n\n"
        f"👥 **المستخدمين:** {stats['total_users']}\n"
        f"✅ **نشط اليوم:** {stats['active_today']}\n\n"
        f"📥 **إجمالي التحميلات:** {stats['total_downloads']}\n"
        f"📥 **تحميلات اليوم:** {stats['downloads_today']}\n\n"
        f"🌍 **إجمالي الترجمات:** {stats['total_translations']}\n"
        f"🌍 **ترجمات اليوم:** {stats['translations_today']}\n\n"
        f"🎬 **إجمالي الفيديوهات:** {stats['total_videos']}\n\n"
        f"💾 **المساحة المستخدمة:**\n"
        f"  📥 التحميلات: {downloads_size}\n"
        f"  📁 المؤقتة: {temp_size}\n"
        f"  📤 المخرجات: {outputs_size}\n"
    )

    from utils import check_gpu, get_gpu_info
    if check_gpu():
        admin_text += f"\n🖥 **GPU:** {get_gpu_info()}"
    else:
        admin_text += "\n🖥 **GPU:** غير متوفر (CPU)"

    await message.reply_text(admin_text)


async def handle_text_message(client: Client, message: Message):
    """Handle incoming text messages (URLs and menu buttons)."""
    text = message.text.strip()
    user_id = message.from_user.id

    # Update user activity
    await db.add_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    # Check if banned
    if await db.is_user_banned(user_id):
        await message.reply_text("❌ تم حظرك من استخدام البوت")
        return

    # Menu buttons
    if text == "🎬 تحميل فيديو":
        state = get_user_state(user_id)
        state["action"] = "download"
        await message.reply_text(
            "📎 أرسل رابط الفيديو لتحميله:",
            reply_markup=get_main_menu_keyboard()
        )
        return

    elif text == "🌍 ترجمة فيديو":
        state = get_user_state(user_id)
        state["action"] = "translate"
        await message.reply_text(
            "📎 أرسل رابط الفيديو لترجمته:",
            reply_markup=get_main_menu_keyboard()
        )
        return

    elif text == "📄 استخراج الترجمة":
        state = get_user_state(user_id)
        state["action"] = "extract_sub"
        await message.reply_text(
            "📎 أرسل رابط الفيديو لاستخراج الترجمة:",
            reply_markup=get_main_menu_keyboard()
        )
        return

    elif text == "🎞 دمج الترجمة":
        await message.reply_text(
            "📎 أرسل ملف الفيديو أولاً، ثم أرسل ملف الترجمة SRT\n"
            "(هذه الميزة قيد التطوير)",
            reply_markup=get_main_menu_keyboard()
        )
        return

    elif text == "⚙ الإعدادات":
        settings = await db.get_user_settings(user_id)
        await message.reply_text(
            "⚙ **الإعدادات:**",
            reply_markup=get_settings_keyboard(settings)
        )
        return

    elif text == "📂 آخر الملفات":
        links = await db.get_recent_links(user_id)
        if not links:
            await message.reply_text("📭 لا توجد ملفات سابقة")
            return
        from keyboards import get_recent_links_keyboard
        await message.reply_text(
            "📂 **آخر الروابط:**",
            reply_markup=get_recent_links_keyboard(links)
        )
        return

    elif text == "ℹ️ المساعدة":
        await handle_help(client, message)
        return

    # Check if it's a URL
    if is_valid_url(text) or is_m3u8_url(text):
        state = get_user_state(user_id)
        action = state.get("action", "translate")  # Default to translate

        # Validate URL
        status_msg = await message.reply_text("🔍 جاري التحقق من الرابط...")
        is_valid, error = await check_url_validity(text)

        if not is_valid:
            await status_msg.edit_text(f"❌ {error}")
            return

        # Get video info
        await status_msg.edit_text("📊 جاري جلب معلومات الفيديو...")
        video_info = await extract_video_info(text)

        if not video_info:
            await status_msg.edit_text("❌ لم أتمكن من الحصول على معلومات الفيديو")
            return

        # Save to recent links
        await db.add_recent_link(
            user_id, text, video_info.site_name, video_info.title
        )

        # Check duration limit
        if (video_info.duration > config.MAX_VIDEO_DURATION_MIN * 60
                and config.MAX_VIDEO_DURATION_MIN > 0):
            await status_msg.edit_text(
                f"⚠️ الفيديو طويل جداً ({video_info.duration_formatted})\n"
                f"الحد الأقصى: {config.MAX_VIDEO_DURATION_MIN} دقيقة"
            )
            return

        # Display video info
        info_text = video_info.to_display_text()

        if action == "download":
            # Show quality selection
            from quality import get_available_qualities
            available = get_available_qualities(video_info.formats)
            video_id = generate_unique_id()
            state["video_info"] = video_info
            state["url"] = text

            await status_msg.edit_text(
                f"{info_text}\n\n📺 اختر الجودة:",
                reply_markup=get_quality_keyboard(available, video_id)
            )
        else:
            # Auto translate mode
            await status_msg.edit_text(
                f"{info_text}\n\n🌍 جاري بدء التحميل والترجمة التلقائية..."
            )
            settings = await db.get_user_settings(user_id)
            quality = settings.get("default_quality", "720")

            await process_video_pipeline(
                client, message, text,
                quality=quality,
                auto_translate=True
            )
    else:
        await message.reply_text(
            "🤔 لم أفهم رسالتك.\n"
            "أرسل رابط فيديو أو اختر من القائمة.",
            reply_markup=get_main_menu_keyboard()
        )
