"syntax-keyword">import ffmpeg
"syntax-keyword">from config "syntax-keyword">import Config
"syntax-keyword">from logger "syntax-keyword">import setup_logger
"syntax-keyword">import os

logger = setup_logger("Merger")

"syntax-keyword">async "syntax-keyword">def merge_subtitle(video_path, srt_path, message):
    output_path = video_path.replace('.mp4', '_translated.mp4').replace('downloads', 'outputs')
    
    font_path = Config.ARABIC_FONT
    "syntax-keyword">if not os.path.exists(font_path):
        logger.warning("Font not found, using default.")
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    "syntax-keyword">try:
        safe_srt = srt_path.replace(':', '\\:')
        
        stream = ffmpeg.input(video_path)
        stream = ffmpeg.output(
            stream, 
            output_path, 
            vf=f"subtitles='{safe_srt}':force_style='FontName=DejaVu Sans,FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Bold=1,Shadow=1'",
            acodec='copy'
        )
        
        ffmpeg.run(stream, overwrite_output="syntax-keyword">True)
        
        "syntax-keyword">await message.edit_text("✅ اكتمل الدمج!\nجاري الإرسال...")
        
        "syntax-keyword">from telegram_sender "syntax-keyword">import send_final_files
        "syntax-keyword">await send_final_files(message, output_path, srt_path)
        
    "syntax-keyword">except Exception "syntax-keyword">as e:
        logger.error(f"FFmpeg Error: {e}")
        "syntax-keyword">await message.edit_text(f"❌ فشل دمج الفيديو: {e}")