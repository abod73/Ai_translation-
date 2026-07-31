"syntax-keyword">from pyrogram.types "syntax-keyword">import Message, InlineKeyboardMarkup, InlineKeyboardButton
"syntax-keyword">from keyboards "syntax-keyword">import get_main_keyboard
"syntax-keyword">from logger "syntax-keyword">import setup_logger
"syntax-keyword">import re

logger = setup_logger("Handlers")

"syntax-keyword">async "syntax-keyword">def start_handler(client, message: Message, db):
    user_id = message.from_user.id
    db.add_user(user_id, message.from_user.first_name)
    
    "syntax-keyword">await message.reply_text(
        f"أهلاً بك {message.from_user.first_name}! 👋\n\n"
        "أنا بوت ترجمة الفيديوهات التركية الذكي.\n"
        "أرسل لي رابط فيديو من YouTube أو Twitter أو غيره وسأقوم بترجمته للعربية.",
        reply_markup=get_main_keyboard()
    )

"syntax-keyword">async "syntax-keyword">def link_handler(client, message: Message, db):
    url = message.text.strip()
    
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    
    "syntax-keyword">if not url_pattern.match(url):
        "syntax-keyword">await message.reply_text("❌ الرابط غير صالح. يرجى إرسال رابط صحيح.")
        "syntax-keyword">return

    status_msg = "syntax-keyword">await message.reply_text("🔍 جاري تحليل الرابط...")
    
    "syntax-keyword">try:
        "syntax-keyword">from video_info "syntax-keyword">import get_video_info
        info = "syntax-keyword">await get_video_info(url)
        
        "syntax-keyword">if not info:
            "syntax-keyword">await status_msg.edit_text("❌ فشل في جلب معلومات الفيديو. تأكد أن الرابط عام.")
            "syntax-keyword">return
            
        "syntax-keyword">from keyboards "syntax-keyword">import get_quality_keyboard
        keyboard = get_quality_keyboard(info['formats'])
        
        db.set_temp_video(user_id=message.from_user.id, info=info)
        
        caption = (
            f"🎬 **{info['title']}**\n"
            f"⏱ المدة: {info['duration']}\n"
            f"📺 الموقع: {info['extractor']}\n\n"
            "اختر الجودة المطلوبة:"
        )
        
        "syntax-keyword">await status_msg.edit_text(caption, reply_markup=keyboard)
        
    "syntax-keyword">except Exception "syntax-keyword">as e:
        logger.error(f"Error handling link: {e}")
        "syntax-keyword">await status_msg.edit_text(f"❌ حدث خطأ: {str(e)}")

"syntax-keyword">async "syntax-keyword">def settings_handler(client, message: Message, db):
    "syntax-keyword">await message.reply_text("⚙️ لوحة الإعدادات قيد التطوير...")