"""
AI Turkish Video Translator Bot - Keyboards Module
All inline and reply keyboards for the bot interface.
"""

from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from quality import QUALITY_OPTIONS, get_available_qualities


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Main menu reply keyboard."""
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("🎬 تحميل فيديو"),
                KeyboardButton("🌍 ترجمة فيديو"),
            ],
            [
                KeyboardButton("📄 استخراج الترجمة"),
                KeyboardButton("🎞 دمج الترجمة"),
            ],
            [
                KeyboardButton("⚙ الإعدادات"),
                KeyboardButton("📂 آخر الملفات"),
            ],
            [
                KeyboardButton("ℹ️ المساعدة"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Start message inline keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 تحميل فيديو", callback_data="action_download"),
            InlineKeyboardButton("🌍 ترجمة فيديو", callback_data="action_translate"),
        ],
        [
            InlineKeyboardButton("📄 استخراج الترجمة", callback_data="action_extract_sub"),
            InlineKeyboardButton("🎞 دمج الترجمة", callback_data="action_merge_sub"),
        ],
        [
            InlineKeyboardButton("⚙ الإعدادات", callback_data="action_settings"),
            InlineKeyboardButton("📂 آخر الملفات", callback_data="action_recent"),
        ],
        [
            InlineKeyboardButton("ℹ️ المساعدة", callback_data="action_help"),
        ],
    ])


def get_quality_keyboard(
    available_qualities: list = None,
    video_id: str = ""
) -> InlineKeyboardMarkup:
    """Quality selection inline keyboard."""
    qualities = available_qualities or QUALITY_OPTIONS
    buttons = []
    row = []

    for q in qualities:
        btn = InlineKeyboardButton(
            f"{'🎵' if q.is_audio_only else '📺'} {q.label}",
            callback_data=f"q_{q.height}_{video_id}"
        )
        row.append(btn)
        if len(row) == 3:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    # Add cancel button
    buttons.append([
        InlineKeyboardButton("❌ إلغاء", callback_data=f"cancel_{video_id}")
    ])

    return InlineKeyboardMarkup(buttons)


def get_settings_keyboard(user_settings: dict) -> InlineKeyboardMarkup:
    """Settings inline keyboard with current values."""
    quality = user_settings.get("default_quality", "720")
    auto_translate = "✅" if user_settings.get("auto_translate") else "❌"
    send_sub = "✅" if user_settings.get("send_subtitle") else "❌"
    send_orig = "✅" if user_settings.get("send_original") else "❌"
    llm = "✅" if user_settings.get("use_llm_refinement") else "❌"

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"📺 الجودة: {quality}p",
                callback_data="setting_quality"
            ),
        ],
        [
            InlineKeyboardButton(
                f"🌍 ترجمة تلقائية: {auto_translate}",
                callback_data="setting_auto_translate"
            ),
        ],
        [
            InlineKeyboardButton(
                f"📄 إرسال الترجمة: {send_sub}",
                callback_data="setting_send_subtitle"
            ),
            InlineKeyboardButton(
                f"📹 إرسال الأصلي: {send_orig}",
                callback_data="setting_send_original"
            ),
        ],
        [
            InlineKeyboardButton(
                f"🤖 تحسين بالذكاء: {llm}",
                callback_data="setting_llm"
            ),
        ],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data="action_main"),
        ],
    ])


def get_quality_setting_keyboard() -> InlineKeyboardMarkup:
    """Quality selection for settings."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("240p", callback_data="set_q_240"),
            InlineKeyboardButton("360p", callback_data="set_q_360"),
            InlineKeyboardButton("480p", callback_data="set_q_480"),
        ],
        [
            InlineKeyboardButton("720p", callback_data="set_q_720"),
            InlineKeyboardButton("1080p", callback_data="set_q_1080"),
            InlineKeyboardButton("Best", callback_data="set_q_best"),
        ],
        [
            InlineKeyboardButton("🔙 رجوع", callback_data="action_settings"),
        ],
    ])


def get_confirm_keyboard(video_id: str) -> InlineKeyboardMarkup:
    """Confirmation keyboard."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأكيد", callback_data=f"confirm_{video_id}"),
            InlineKeyboardButton("❌ إلغاء", callback_data=f"cancel_{video_id}"),
        ],
    ])


def get_action_choice_keyboard(video_id: str) -> InlineKeyboardMarkup:
    """Choose action after download."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🌍 ترجمة تلقائية",
                callback_data=f"auto_translate_{video_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                "📥 تحميل فقط",
                callback_data=f"download_only_{video_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                "❌ إلغاء",
                callback_data=f"cancel_{video_id}"
            ),
        ],
    ])


def get_recent_links_keyboard(links: list[dict]) -> InlineKeyboardMarkup:
    """Recent links keyboard."""
    buttons = []
    for i, link in enumerate(links[:5]):
        title = link.get("video_title", "فيديو")[:30]
        site = link.get("site_name", "")
        buttons.append([
            InlineKeyboardButton(
                f"{site}: {title}",
                callback_data=f"recent_{i}"
            )
        ])
    buttons.append([
        InlineKeyboardButton("🔙 رجوع", callback_data="action_main")
    ])
    return InlineKeyboardMarkup(buttons)
