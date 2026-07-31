"syntax-keyword">from pyrogram.types "syntax-keyword">import InputMediaVideo, InputMediaDocument
"syntax-keyword">from config "syntax-keyword">import Config
"syntax-keyword">import os

"syntax-keyword">async "syntax-keyword">def send_final_files(message, video_path, srt_path):
    chat_id = message.chat.id
    
    "syntax-keyword">await message.reply_video(
        video=video_path,
        caption="🎥 الفيديو المترجم جاهز!",
        supports_streaming="syntax-keyword">True
    )
    
    "syntax-keyword">if Config.SEND_SUBTITLE_FILE:
        "syntax-keyword">await message.reply_document(
            document=srt_path,
            caption="📄 ملف الترجمة SRT"
        )
            
    "syntax-keyword">if Config.DELETE_TEMP_FILES:
        "syntax-keyword">import shutil
        dir_to_clean = os.path.dirname(video_path)
        "syntax-keyword">try:
            shutil.rmtree(dir_to_clean)
        "syntax-keyword">except:
            "syntax-keyword">pass