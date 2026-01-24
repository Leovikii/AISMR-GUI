import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import get_cache_dir

def parse_time(ts):
    try:
        h, m, s = ts.split(':')
        s, ms = s.split(',')
        return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000.0
    except:
        return 0.0

def main():
    if len(sys.argv) < 2: sys.exit(1)
    print("STATUS: Generating Final Output", flush=True)

    inp = sys.argv[1]

    if not os.path.exists(inp):
        print(f"ERROR: Input file not found: {inp}", flush=True)
        sys.exit(1)

    cache_dir = get_cache_dir(inp)
    src_srt = os.path.join(cache_dir, "translated.srt")

    if not os.path.exists(src_srt):
        print(f"ERROR: Translated SRT not found: {src_srt}", flush=True)
        sys.exit(1)
    
    base = os.path.splitext(inp)[0]
    is_audio = os.path.splitext(inp)[1].lower() in ['.mp3', '.wav', '.flac', '.m4a']
    final_output = f"{base}.lrc" if is_audio else f"{base}.srt"
    
    if os.path.exists(final_output) and os.path.getsize(final_output) > 0:
        sys.exit(0)
    
    with open(src_srt, 'r', encoding='utf-8') as f:
        blocks = f.read().strip().split('\n\n')
    
    with open(final_output, 'w', encoding='utf-8') as f:
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                ts = lines[1]
                text = " ".join(lines[2:])
                if is_audio:
                    start = ts.split(' --> ')[0]
                    sec = parse_time(start)
                    mm = int(sec // 60)
                    ss = sec % 60
                    f.write(f"[{mm:02d}:{ss:05.2f}]{text}\n")
                else:
                    f.write(block + "\n\n")

if __name__ == "__main__":
    main()