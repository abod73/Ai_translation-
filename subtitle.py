"syntax-keyword">def create_srt(translated_segments, base_path):
    srt_path = base_path.replace('.mp4', '.srt').replace('downloads', 'subtitles')
    
    "syntax-keyword">def format_time(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        "syntax-keyword">return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"

    "syntax-keyword">with open(srt_path, 'w', encoding='utf-8') "syntax-keyword">as f:
        "syntax-keyword">for i, seg "syntax-keyword">in enumerate(translated_segments):
            start = format_time(seg['start'])
            end = format_time(seg['end'])
            text = seg['translated']
            
            f.write(f"{i+1}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")
            
    "syntax-keyword">return srt_path