# 🎬 AI Turkish Video Translator Bot

بوت تيليجرام احترافي لتحميل الفيديوهات التركية وترجمتها تلقائياً إلى العربية باستخدام الذكاء الاصطناعي.

## ✨ المميزات

- 📥 تحميل من YouTube, Twitter/X, Dailymotion, m3u8 وأي موقع يدعمه yt-dlp
- 🎙 استخراج الكلام التركي بدقة باستخدام Faster Whisper Large V3
- 🌍 ترجمة عالية الجودة باستخدام NLLB-200
- 🤖 تحسين الترجمة بالذكاء الاصطناعي (Qwen/Gemma) - اختياري
- 📝 إنشاء ملفات ترجمة SRT عربية
- 🎞 دمج الترجمة مع الفيديو باستخدام FFmpeg
- 📤 إرسال الفيديو المترجم تلقائياً عبر تيليجرام
- ⚙️ إعدادات مخصصة لكل مستخدم
- 📊 لوحة إدارة بإحصائيات شاملة
- 🗃 قاعدة بيانات SQLite

---

## 📋 المتطلبات

- Python 3.10+
- FFmpeg
- 8GB RAM minimum (16GB+ recommended)
- GPU with CUDA (optional but recommended)

---

## 🚀 طريقة التشغيل على Google Colab

### 1. افتح Colab وأنشئ notebook جديد

### 2. ثبّت المتطلبات:
```python
!apt-get update
!apt-get install -y ffmpeg
!pip install pyrogram tgcrypto yt-dlp faster-whisper transformers \
    torch accelerate sentencepiece aiosqlite aiohttp aiofiles
```

### 3. أنشئ ملف `.env` أو عيّن المتغيرات:
```python
import os
os.environ["BOT_TOKEN"] = "YOUR_BOT_TOKEN"
os.environ["API_ID"] = "YOUR_API_ID"
os.environ["API_HASH"] = "YOUR_API_HASH"
os.environ["ADMIN_IDS"] = "YOUR_TELEGRAM_ID"
os.environ["USE_GPU"] = "true"
```

### 4. انسخ ملفات المشروع وشغّل:
```python
!python main.py
```

> **ملاحظة:** Colab session ينتهي بعد فترة. استخدم `ngrok` أو `cloudflared` للحفاظ على الاتصال.

---

## 🐧 طريقة التشغيل على Linux

### 1. ثبّت المتطلبات:
```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip ffmpeg git

# Clone المشروع
git clone <repository-url>
cd AI_Turkish_Translator
```

### 2. أنشئ بيئة افتراضية:
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. عيّن المتغيرات:
```bash
export BOT_TOKEN="your_bot_token"
export API_ID="your_api_id"
export API_HASH="your_api_hash"
export ADMIN_IDS="your_telegram_id"
```

### 4. شغّل البوت:
```bash
python main.py
```

### 5. (اختياري) شغّل كخدمة:
```bash
# أنشئ ملف systemd
sudo nano /etc/systemd/system/turkish-bot.service
```

```ini
[Unit]
Description=Turkish Translator Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/AI_Turkish_Translator
Environment=BOT_TOKEN=your_token
Environment=API_ID=your_id
Environment=API_HASH=your_hash
ExecStart=/path/to/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable turkish-bot
sudo systemctl start turkish-bot
```

---

## 🖥 طريقة التشغيل على VPS

اتبع نفس خطوات Linux أعلاه. المتطلبات الموصى بها:
- **RAM:** 8GB+ (16GB للترجمة بالـ LLM)
- **Storage:** 50GB+ SSD
- **CPU:** 4 cores+
- **GPU:** NVIDIA مع CUDA (اختياري)

---

## 🔑 طريقة إنشاء BOT TOKEN

1. افتح تيليجرام وابحث عن `@BotFather`
2. أرسل `/newbot`
3. اختر اسماً للبوت
4. اختر username للبوت (ينتهي بـ `bot`)
5. انسخ الـ Token الذي سيظهر

---

## 🔑 طريقة إنشاء API_ID و API_HASH

1. اذهب إلى [my.telegram.org](https://my.telegram.org)
2. سجّل الدخول برقم هاتفك
3. اضغط على "API development tools"
4. أنشئ تطبيقاً جديداً
5. انسخ `api_id` و `api_hash`

---

## 🔄 طريقة تحديث المشروع

```bash
cd AI_Turkish_Translator
git pull origin main
pip install -r requirements.txt --upgrade
sudo systemctl restart turkish-bot  # إذا كان خدمة
```

---

## 🔧 طريقة تغيير نموذج الترجمة

### تغيير نموذج NLLB:
```bash
# في .env أو config.py
export TRANSLATION_MODEL="facebook/nllb-200-3.3B"  # نموذج أكبر وأدق
# أو
export TRANSLATION_MODEL="facebook/nllb-200-distilled-600M"  # أسرع وأخف
```

### تفعيل تحسين LLM:
```bash
export USE_LLM_REFINEMENT="true"
export LLM_MODEL="Qwen/Qwen2.5-1.5B-Instruct"  # أو أي نموذج آخر
```

### النماذج المدعومة للـ LLM:
- `Qwen/Qwen2.5-1.5B-Instruct` (سريع)
- `Qwen/Qwen2.5-7B-Instruct` (أدق)
- `google/gemma-2-2b-it` (سريع)
- `google/gemma-2-9b-it` (أدق)

---

## ➕ طريقة إضافة مواقع جديدة

البوت يستخدم `yt-dlp` الذي يدعم أكثر من 1000 موقع تلقائياً. لإضافة دعم مخصص:

1. افتح `video_info.py`
2. أضف الموقع في دالة `get_site_name()`
3. إذا كان الموقع يحتاج cookies:
```bash
   export COOKIES_FILE="/path/to/cookies.txt"
```

---

## 📁 هيكل المشروع
