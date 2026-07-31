"""
AI Turkish Video Translator Bot - Callback Module
Handles all inline keyboard callback queries.
"""

import asyncio
from pyrogram import Client
from pyrogram.types import CallbackQuery

from config import config
from logger import get_logger
from database import db
from handlers import (
    get_user_state, process_video_pipeline,
    handle_start, handle_help
)
from keyboards import (
    get_start_keyboard, get_main_menu_keyboard,
    get_settings_keyboard, get_quality_setting_keyboard
)
from utils import generate_unique_id

log = get_logger("callback")


async def handle_callback(client: Client, callback: CallbackQuery):
    """Main callback router."""
    data = callback.data
    user_id = callback.from_user.id

    try:
        # ─── Action Callbacks ───────────────────────────────────────
        if data == "action_download":
            state = get_user_state(user_id)
            state["action"] = "download"
            await callback.answer("أرسل رابط الفيديو")
            await callback.message.edit_text(
                "📎 أرسل رابط الفيديو لتحميله:",
                reply_markup=None
            )

        elif data == "action_translate":
            state = get_user_state(user_id)
            state["action"] = "translate"
            await callback.answer("أرسل رابط الفيديو")
            await callback.message.edit_text(
                "📎 أرسل رابط الفيديو لترجمته:",
                reply_markup=None
            )

        elif data == "action_extract_sub":
            state = get_user_state(user_id)
            state["action"] = "extract_sub"
            await callback.answer("أرسل رابط الفيديو")
            await callback.message.edit_text(
                "📎 أرسل رابط الفيديو لاستخراج الترجمة:",
                reply_markup=None
            )

        elif data == "action_merge_sub":
            await callback.answer("قيد التطوير", show_alert=True)

        elif data == "action_settings":
            settings = await db.get_user_settings(user_id)
            await callback.message.edit_text(
                "⚙ **الإعدادات:**",
                reply_markup=get_settings_keyboard(settings)
            )

        elif data == "action_recent":
            links = await db.get_recent_links(user_id)
            if not links:
                await callback.answer("لا توجد ملفات سابقة", show_alert=True)
                return
            from keyboards import get_recent_links_keyboard
            await callback.message.edit_text(
                "📂 **آخر الروابط:**",
                reply_markup=get_recent_links_keyboard(links)
            )

        elif data == "action_help":
            await callback.message.edit_text(
                "📖 **دليل الاستخدام**\n\n"
                "أرسل رابط فيديو وسأقوم بتحميله وترجمته تلقائياً.\n\n"
                "المواقع المدعومة: YouTube, Twitter, Dailymotion, m3u8",
                reply_markup=get_start_keyboard()
            )

        elif data == "action_main":
            await callback.message.edit_text(
                "🎬 **القائمة الرئيسية**",
                reply_markup=get_start_keyboard()
            )

        # ─── Quality Selection ──────────────────────────────────────
        elif data.startswith("q_"):
            parts = data.split("_")
            if len(parts) >= 3:
                height = int(parts[1])
                video_id = parts[2]

                from quality import get_quality_by_height
                quality = get_quality_by_height(height)
                quality_label = quality.label if quality else f"{height}p"

                await callback.answer(f"تم اختيار {quality_label}")

                state = get_user_state(user_id)
                url = state.get("url")

                if not url:
                    await callback.message.edit_text(
                        "❌ انتهت صلاحية الرابط. أرسل الرابط مرة أخرى."
                    )
                    return

                quality_str = str(height) if height < 9999 else "best"
                if height == 0:
                    quality_str = "audio"

                await callback.message.edit_text(
                    f"📥 جاري التحميل بجودة {quality_label}..."
                )

                await process_video_pipeline(
                    client,
                    callback.message,
                    url,
                    quality=quality_str,
                    auto_translate=(state.get("action") == "translate")
                )

        # ─── Settings Callbacks ─────────────────────────────────────
        elif data == "setting_quality":
            await callback.message.edit_text(
                "📺 اختر الجودة الافتراضية:",
                reply_markup=get_quality_setting_keyboard()
            )

        elif data.startswith("set_q_"):
            quality = data.replace("set_q_", "")
            await db.update_user_setting(user_id, "default_quality", quality)
            await callback.answer(f"تم تعيين الجودة: {quality}p")
            settings = await db.get_user_settings(user_id)
            await callback.message.edit_text(
                "⚙ **الإعدادات:**",
                reply_markup=get_settings_keyboard(settings)
            )

        elif data == "setting_auto_translate":
            settings = await db.get_user_settings(user_id)
            new_val = 0 if settings.get("auto_translate") else 1
            await db.update_user_setting(user_id, "auto_translate", new_val)
            await callback.answer("تم تحديث الإعداد")
            settings = await db.get_user_settings(user_id)
            await callback.message.edit_text(
                "⚙ **الإعدادات:**",
                reply_markup=get_settings_keyboard(settings)
            )

        elif data == "setting_send_subtitle":
            settings = await db.get_user_settings(user_id)
            new_val = 0 if settings.get("send_subtitle") else 1
            await db.update_user_setting(user_id, "send_subtitle", new_val)
            await callback.answer("تم تحديث الإعداد")
            settings = await db.get_user_settings(user_id)
            await callback.message.edit_text(
                "⚙ **الإعدادات:**",
                reply_markup=get_settings_keyboard(settings)
            )

        elif data == "setting_send_original":
            settings = await db.get_user_settings(user_id)
            new_val = 0 if settings.get("send_original") else 1
            await db.update_user_setting(user_id, "send_original", new_val)
            await callback.answer("تم تحديث الإعداد")
            settings = await db.get_user_settings(user_id)
            await callback.message.edit_text(
                "⚙ **الإعدادات:**",
                reply_markup=get_settings_keyboard(settings)
            )

        elif data == "setting_llm":
            settings = await db.get_user_settings(user_id)
            new_val = 0 if settings.get("use_llm_refinement") else 1
            await db.update_user_setting(user_id, "use_llm_refinement", new_val)
            await callback.answer("تم تحديث الإعداد")
            settings = await db.get_user_settings(user_id)
            await callback.message.edit_text(
                "⚙ **الإعدادات:**",
                reply_markup=get_settings_keyboard(settings)
            )

        # ─── Cancel ─────────────────────────────────────────────────
        elif data.startswith("cancel_"):
            await callback.answer("تم الإلغاء")
            await callback.message.edit_text("❌ تم إلغاء العملية")

        # ─── Auto Translate / Download Only ─────────────────────────
        elif data.startswith("auto_translate_"):
            state = get_user_state(user_id)
            url = state.get("url")
            if url:
                await callback.message.edit_text("🌍 جاري التحميل والترجمة...")
                settings = await db.get_user_settings(user_id)
                await process_video_pipeline(
                    client, callback.message, url,
                    quality=settings.get("default_quality", "720"),
                    auto_translate=True
                )

        elif data.startswith("download_only_"):
            state = get_user_state(user_id)
            url = state.get("url")
            if url:
                await callback.message.edit_text("📥 جاري التحميل...")
                settings = await db.get_user_settings(user_id)
                await process_video_pipeline(
                    client, callback.message, url,
                    quality=settings.get("default_quality", "720"),
                    auto_translate=False
                )

        else:
            await callback.answer("غير معروف", show_alert=True)

    except Exception as e:
        log.error(f"Callback error: {e}", exc_info=True)
        try:
            await callback.answer("حدث خطأ", show_alert=True)
        except Exception:
            pass
