"syntax-keyword">import yt_dlp
"syntax-keyword">from logger "syntax-keyword">import setup_logger

logger = setup_logger("VideoInfo")

"syntax-keyword">async "syntax-keyword">def get_video_info(url):
    ydl_opts = {
        'quiet': "syntax-keyword">True,
        'no_warnings': "syntax-keyword">True,
        'extract_flat': "syntax-keyword">False,
        'socket_timeout': 10
    }
    
    "syntax-keyword">try:
        "syntax-keyword">with yt_dlp.YoutubeDL(ydl_opts) "syntax-keyword">as ydl:
            info = ydl.extract_info(url, download="syntax-keyword">False)
            
            "syntax-keyword">if not info:
                "syntax-keyword">return "syntax-keyword">None
                
            formats = info.get('formats', [])
            
            "syntax-keyword">return {
                'id': info.get('id'),
                'title': info.get('title', 'Unknown Title'),
                'duration': info.get('duration_string', 'Unknown'),
                'thumbnail': info.get('thumbnail'),
                'extractor': info.get('extractor_key'),
                'webpage_url': info.get('webpage_url'),
                'formats': formats
            }
    "syntax-keyword">except Exception "syntax-keyword">as e:
        logger.error(f"Failed to fetch info: {e}")
        "syntax-keyword">return "syntax-keyword">None