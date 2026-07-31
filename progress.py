"syntax-keyword">from logger "syntax-keyword">import setup_logger
"syntax-keyword">import time

logger = setup_logger("Progress")

"syntax-keyword">class ProgressCallback:
    "syntax-keyword">def __init__(self, message):
        self.message = message
        self.start_time = time.time()
        self.last_update = 0

    "syntax-keyword">def update(self, d):
        "syntax-keyword">if d['status'] == 'downloading':
            now = time.time()
            "syntax-keyword">if now - self.last_update > 2:
                self.last_update = now
                
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                speed = d.get('speed', 0)
                percentage = (downloaded / total) * 100 "syntax-keyword">if total "syntax-keyword">else 0
                
                speed_mb = (speed / 1024 / 1024) "syntax-keyword">if speed "syntax-keyword">else 0
                
                text = (
                    f"⬇️ جاري التحميل...\n"
                    f"📊 النسبة: {percentage:.1f}%\n"
                    f"🚀 السرعة: {speed_mb:.2f} MB/s\n"
                    f"📦 الحجم: {downloaded/1024/1024:.1f} MB"
                )
                
                "syntax-keyword">try:
                    "syntax-keyword">pass
                "syntax-keyword">except:
                    "syntax-keyword">pass