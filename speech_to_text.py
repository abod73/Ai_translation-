"syntax-keyword">from faster_whisper "syntax-keyword">import WhisperModel
"syntax-keyword">import torch
"syntax-keyword">from config "syntax-keyword">import Config
"syntax-keyword">from logger "syntax-keyword">import setup_logger
"syntax-keyword">import json

logger = setup_logger("STT")

"syntax-keyword">class Transcriber:
    "syntax-keyword">def __init__(self):
        device = "cuda" "syntax-keyword">if torch.cuda.is_available() and Config.USE_GPU "syntax-keyword">else "cpu"
        compute_type = "float16" "syntax-keyword">if device == "cuda" "syntax-keyword">else "int8"
        
        logger.info(f"Loading Whisper Model({Config.WHISPER_MODEL}) on {device}...")
        self.model = WhisperModel(Config.WHISPER_MODEL, device=device, compute_type=compute_type)

    "syntax-keyword">def transcribe(self, audio_path):
        logger.info(f"Transcribing: {audio_path}")
        
        segments, info = self.model.transcribe(
            audio_path, 
            beam_size=5, 
            language="tr",
            vad_filter="syntax-keyword">True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        result = []
        "syntax-keyword">for segment "syntax-keyword">in segments:
            result.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            
        "syntax-keyword">return result

"syntax-keyword">async "syntax-keyword">def transcribe_video(video_path, message, db):
    "syntax-keyword">try:
        transcriber = Transcriber()
        segments = transcriber.transcribe(video_path)
        
        "syntax-keyword">import json
        seg_file = video_path.replace('.mp4', '_segments.json')
        "syntax-keyword">with open(seg_file, 'w', encoding='utf-8') "syntax-keyword">as f:
            json.dump(segments, f, ensure_ascii="syntax-keyword">False)
            
        "syntax-keyword">await message.edit_text(f"✅ تم استخراج النص ({len(segments)} سطر).\nجاري الترجمة...")
        
        "syntax-keyword">from translator "syntax-keyword">import translate_segments
        "syntax-keyword">await translate_segments(segments, video_path, message, db)
        
    "syntax-keyword">except Exception "syntax-keyword">as e:
        logger.error(f"Transcription error: {e}")
        "syntax-keyword">await message.edit_text(f"❌ خطأ في الاستخراج: {e}")