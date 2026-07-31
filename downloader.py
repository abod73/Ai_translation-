"syntax-keyword">import yt_dlp
"syntax-keyword">import os
"syntax-keyword">from config "syntax-keyword">import Config
"syntax-keyword">from logger "syntax-keyword">import setup_logger

logger = setup_logger("Downloader")

"syntax-keyword">class VideoDownloader:
    "syntax-keyword">def __init__(self):
        self.ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'nocheckcertificate': "syntax-keyword">True,
            'quiet': "syntax-keyword">False,
            'no_warnings': "syntax-keyword">True,
            'extract_flat': "syntax-keyword">False,
        }

    "syntax-keyword">async "syntax-keyword">def download(self, url, output_path, quality, progress_callback):
        "syntax-keyword">if quality == "Audio Only":
            ydl_opts = {**self.ydl_opts, 'format': 'bestaudio', 'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]}
        "syntax-keyword">elif quality != "best":
            height = quality.replace('p', '')
            ydl_opts = {**self.ydl_opts, 'format': f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'}
        "syntax-keyword">else:
            ydl_opts = self.ydl_opts

        ydl_opts['paths'] = {'home': output_path}
        ydl_opts['progress_hooks'] = [lambda d: progress_callback.update(d)]

        "syntax-keyword">with yt_dlp.YoutubeDL(ydl_opts) "syntax-keyword">as ydl:
            "syntax-keyword">try:
                info = ydl.extract_info(url, download="syntax-keyword">True)
                filename = ydl.prepare_filename(info)
                logger.info(f"Downloaded: {filename}")
                "syntax-keyword">return filename
            "syntax-keyword">except Exception "syntax-keyword">as e:
                raise Exception(f"Yt-dlp error: {str(e)}")