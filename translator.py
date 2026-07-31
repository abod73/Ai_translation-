"syntax-keyword">import json
"syntax-keyword">from transformers "syntax-keyword">import pipeline
"syntax-keyword">from config "syntax-keyword">import Config
"syntax-keyword">from logger "syntax-keyword">import setup_logger
"syntax-keyword">import re

logger = setup_logger("Translator")

"syntax-keyword">with open('names_dictionary.json', 'r', encoding='utf-8') "syntax-keyword">as f:
    NAMES_DICT = json.load(f)

"syntax-keyword">class TranslatorEngine:
    "syntax-keyword">def __init__(self):
        logger.info("Loading Translation Model...")
        self.translator = pipeline("translation", model="facebook/nllb-200-distilled-600M") 
        
    "syntax-keyword">def protect_names(self, text):
        protected = text
        "syntax-keyword">for tr_name, ar_name "syntax-keyword">in NAMES_DICT.items():
            protected = protected.replace(tr_name, f"<NAME_{tr_name}>")
        "syntax-keyword">return protected

    "syntax-keyword">def restore_names(self, text):
        restored = text
        "syntax-keyword">for tr_name, ar_name "syntax-keyword">in NAMES_DICT.items():
            restored = restored.replace(f"<NAME_{tr_name}>", ar_name)
        "syntax-keyword">return restored

    "syntax-keyword">def translate_batch(self, segments):
        results = []
        
        chunk_size = 10
        "syntax-keyword">for i "syntax-keyword">in range(0, len(segments), chunk_size):
            chunk = segments[i:i+chunk_size]
            texts = [self.protect_names(seg['text']) "syntax-keyword">for seg "syntax-keyword">in chunk]
            
            "syntax-keyword">try:
                translations = self.translator(texts, src_lang="tur_Latn", tgt_lang="arb_Arab", max_length=512)
                
                "syntax-keyword">for j, t "syntax-keyword">in enumerate(translations):
                    translated_text = t[0]['translation_text']
                    final_text = self.restore_names(translated_text)
                    
                    results.append({
                        "start": chunk[j]['start'],
                        "end": chunk[j]['end'],
                        "original": chunk[j]['text'],
                        "translated": final_text
                    })
            "syntax-keyword">except Exception "syntax-keyword">as e:
                logger.error(f"Translation chunk error: {e}")
                "syntax-keyword">for seg "syntax-keyword">in chunk:
                    results.append({**seg, "translated": seg['text'] + " [ERR]"})
                    
        "syntax-keyword">return results

"syntax-keyword">async "syntax-keyword">def translate_segments(segments, video_path, message, db):
    engine = TranslatorEngine()
    translated_data = engine.translate_batch(segments)
    
    trans_file = video_path.replace('.mp4', '_translated.json')
    "syntax-keyword">with open(trans_file, 'w', encoding='utf-8') "syntax-keyword">as f:
        json.dump(translated_data, f, ensure_ascii="syntax-keyword">False)
        
    "syntax-keyword">await message.edit_text("✅ تمت الترجمة.\nجاري إنشاء ملف الترجمة...")
    
    "syntax-keyword">from subtitle "syntax-keyword">import create_srt
    srt_path = create_srt(translated_data, video_path)
    
    "syntax-keyword">await message.edit_text("✅ تم إنشاء ملف SRT.\nجاري دمج الترجمة مع الفيديو...")
    
    "syntax-keyword">from video_merger "syntax-keyword">import merge_subtitle
    "syntax-keyword">await merge_subtitle(video_path, srt_path, message)