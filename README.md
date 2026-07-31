# AI Turkish Video Translator Bot

مشروع بوت تيليجرام احترافي لترجمة الفيديوهات التركية إلى العربية باستخدام الذكاء الاصطناعي.

## المميزات
- دعم YouTube, Twitter, Dailymotion, m3u8 والمزيد عبر yt-dlp.
- استخراج الكلام بدقة عالية باستخدام Faster Whisper Large V3.
- ترجمة ذكية باستخدام NLLB و LLM (Qwen/Gemma) للحفاظ على السياق وأسماء الشخصيات.
- دمج الترجمة داخل الفيديو باستخدام FFmpeg مع خطوط عربية مخصصة.
- واجهة إدارة كاملة وإحصائيات.
- يعمل بكفاءة على Google Colab و Linux VPS.

## التثبيت والتشغيل

### 1. المتطلبات
تأكد من تثبيت Python 3.10+ و FFmpeg.

```bash
sudo apt update && sudo apt install ffmpeg git python3-pip -y
```

### 2. إعداد البيئة
```bash
git clone https://github.com/yourusername/AI_Turkish_Translator.git
cd AI_Turkish_Translator
pip install -r requirements.txt
```

### 3. الإعدادات
قم بتعديل ملف `config.py`:
- ضع الـ `BOT_TOKEN` الخاص بك.
- ضع `API_ID` و `API_HASH`.

### 4. التشغيل
```bash
python main.py
```

## هيكل المشروع
- `bot.py`: منطق البوت الأساسي.
- `downloader.py`: التعامل مع yt-dlp.
- `speech_to_text.py`: استخراج النصوص.
- `translator.py`: محرك الترجمة والذكاء الاصطناعي.
- `video_merger.py`: دمج الترجمة بالفيديو.

## المساهمة
يمكنك فتح Pull Request لإضافة ميزات جديدة.