import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import subprocess
import shutil
import json
import glob
from pathlib import Path
from utils import get_cache_dir, PROMPTS_DIR, LocalLLM, load_asmr_dict

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except:
        sys.exit(1)

def run_ffmpeg_normalization(input_path, output_path):
    print("STATUS: Audio Normalization")
    sys.stdout.flush()
    
    compand_filter = "compand=attacks=0.05:decays=0.5:points=-90/-90|-60/-25|-20/-5|0/-0:gain=0"
    af_filter = f"highpass=f=80,lowpass=f=8000,{compand_filter},loudnorm=I=-14:TP=-1.0:LRA=11"
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path), "-af", af_filter,
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(output_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def read_text_file_robust(file_path):
    encodings = ['utf-8', 'shift_jis', 'cp932', 'euc-jp', 'gbk']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                content = f.read()
                if len(content) > 0: return content
        except: continue
    return ""

def analyze_context(cache_dir):
    print("STATUS: Context Analysis")
    sys.stdout.flush()

    context_file = os.path.join(cache_dir, "context.json")
    if os.path.exists(context_file) and os.path.getsize(context_file) > 0:
        return

    content = ""
    if os.path.exists(PROMPTS_DIR):
        txt_files = glob.glob(os.path.join(PROMPTS_DIR, "*.txt"))
        if txt_files: content = read_text_file_robust(txt_files[0])
    if not content and os.path.exists("ReadMe.txt"):
        content = read_text_file_robust("ReadMe.txt")

    default_data = {"summary": "ASMR剧情", "style": "沉浸式体验", "glossary": [], "whisper_keywords": ""}
    
    if not content:
        with open(context_file, "w", encoding="utf-8") as f: json.dump(default_data, f)
        return

    try:
        port = int(os.environ.get("LLM_PORT", 8080))
        llm = LocalLLM(port=port)
        system_prompt = (
            "You are an ASMR script analyzer. Extract metadata for translation and speech recognition.\n"
            "Output strictly valid JSON with keys: 'summary', 'style', 'whisper_keywords'.\n"
            "Rules for 'whisper_keywords':\n"
            "1. SEPARATE terms with ENGLISH COMMAS (,).\n"
            "2. IDENTIFY THE 'CAST' SECTION (e.g., '声の出演', 'CV', 'Voice'):\n"
            "   - IF format is 'Character : Actor', ONLY extract 'Character'. DISCARD 'Actor'.\n"
            "   - DISCARD any real-world names associated with '様', 'CV', '@', 'Circle'.\n"
            "3. INCLUDE: Fictional Character names, Pronouns (Ore, Boku, Kimi), Role names (Mama, Onee-chan), Slang.\n"
            "4. EXCLUDE: Real names, Dates, Prices, URL, 'ASMR', 'Binaural'."
        )
        full_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{content[:4000]}<|im_end|>\n<|im_start|>assistant\n"
        response = llm.completion(full_prompt, temperature=0.1, max_tokens=1024)
        
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            data = json.loads(response[start:end])
        except:
            data = default_data

        blacklist = ["CV", "Voice", "Circle", "Track", "http", "DL", "版本", "作者", "声优", "発売", "価格", "バイノーラル", "立体音響", "ASMR", "様", "出演"]
        
        common_terms = set()
        try:
            dict_data = load_asmr_dict()
            for item in dict_data:
                common_terms.add(item['term'])
        except: pass

        raw_keywords = data.get("whisper_keywords", "")
        if isinstance(raw_keywords, list): 
            raw_keywords = ", ".join(raw_keywords)
        
        raw_keywords = raw_keywords.replace("、", ",")
        keyword_list = [k.strip() for k in raw_keywords.split(',') if k.strip()]
        
        final_keywords = []
        for k in keyword_list:
            if any(b in k for b in blacklist): continue
            if k in common_terms: continue
            final_keywords.append(k)
            
        data["whisper_keywords"] = ", ".join(final_keywords)
        data["glossary"] = [] 
        
        with open(context_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    except:
        with open(context_file, "w", encoding="utf-8") as f: json.dump(default_data, f)

def process_audio(input_file):
    check_ffmpeg()
    input_path = Path(input_file)
    cache_dir = get_cache_dir(input_file)
    final_wav = Path(cache_dir) / "audio_16k_norm.wav"
    
    if not final_wav.exists() or final_wav.stat().st_size == 0:
        temp_wav = Path(cache_dir) / "temp.wav"
        shutil.copy(str(input_path), str(temp_wav))
        run_ffmpeg_normalization(temp_wav, final_wav)
        if temp_wav.exists(): os.remove(temp_wav)
    
    analyze_context(cache_dir)

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    process_audio(sys.argv[1])