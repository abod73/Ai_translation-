"syntax-keyword">from pyrogram.types "syntax-keyword">import InlineKeyboardMarkup, InlineKeyboardButton

"syntax-keyword">def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎬 تحميل فيديو", callback_data="action_download")],
        [InlineKeyboardButton("🌍 ترجمة فيديو", callback_data="action_translate")],
        [InlineKeyboardButton("📄 استخراج الترجمة", callback_data="action_extract_sub")],
        [InlineKeyboardButton("🎞 دمج الترجمة", callback_data="action_merge_sub")],
        [InlineKeyboardButton("⚙ الإعدادات", callback_data="action_settings")],
        [InlineKeyboardButton("ℹ️ المساعدة", callback_data="action_help")]
    ]
    "syntax-keyword">return InlineKeyboardMarkup(keyboard)

"syntax-keyword">def get_quality_keyboard(formats):
    keyboard = []
    row = []
    
    qualities = ['1080p', '720p', '480p', '360p', 'Audio Only']
    
    "syntax-keyword">for q "syntax-keyword">in qualities:
        row.append(InlineKeyboardButton(q, callback_data=f"quality_{q}"))
        "syntax-keyword">if len(row) == 2:
            keyboard.append(row)
            row = []
    "syntax-keyword">if row:
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel")])
    
    "syntax-keyword">return InlineKeyboardMarkup(keyboard)