"syntax-keyword">from pyrogram.types "syntax-keyword">import CallbackQuery
"syntax-keyword">from downloader "syntax-keyword">import VideoDownloader
"syntax-keyword">from progress "syntax-keyword">import ProgressCallback
"syntax-keyword">from logger "syntax-keyword">import setup_logger

logger = setup_logger("Callbacks")

"syntax-keyword">async "syntax-keyword">def handle_callback(client, callback_query: CallbackQuery, db):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    "syntax-keyword">if data.startswith("quality_"):
        quality = data.split("_")[1]
        "syntax-keyword">await callback_query.answer(f"جاري التحميل بجودة {quality}...")
        
        video_info = db.get_temp_video(user_id)
        "syntax-keyword">if not video_info:
            "syntax-keyword">await callback_query.message.edit_text("❌ انتهت صلاحية الجلسة. أرسل الرابط مجدداً.")
            "syntax-keyword">return
            
        "syntax-keyword">await process_download(callback_query, video_info, quality, db)

    "syntax-keyword">elif data == "cancel":
        "syntax-keyword">await callback_query.message.delete()
        "syntax-keyword">await callback_query.answer("تم الإلغاء.")

"syntax-keyword">async "syntax-keyword">def process_download(cb, info, quality, db):
    "syntax-keyword">await cb.message.edit_text("⬇️ جاري بدء التحميل...")
    
    downloader = VideoDownloader()
    progress = ProgressCallback(cb.message)
    
    "syntax-keyword">try:
        file_path = "syntax-keyword">await downloader.download(
            url=info['webpage_url'],
            output_path=f"downloads/{info['id']}",
            quality=quality,
            progress_callback=progress
        )
        
        "syntax-keyword">await cb.message.edit_text("✅ تم التحميل بنجاح!\nجاري بدء عملية استخراج الكلام...")
        
        "syntax-keyword">from speech_to_text "syntax-keyword">import transcribe_video
        "syntax-keyword">await transcribe_video(file_path, cb.message, db)
        
    "syntax-keyword">except Exception "syntax-keyword">as e:
        logger.error(f"Download failed: {e}")
        "syntax-keyword">await cb.message.edit_text(f"❌ فشل التحميل: {e}")