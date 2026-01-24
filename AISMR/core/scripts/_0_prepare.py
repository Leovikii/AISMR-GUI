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
from utils import get_cache_dir, PROMPTS_DIR, ASSETS_DIR, LocalLLM, load_asmr_dict, get_assets_context_path, get_assets_terms_path
import pykakasi

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

def analyze_context(content, prompt_file_name):
    print("STATUS: Context Analysis")
    sys.stdout.flush()

    context_file = get_assets_context_path(prompt_file_name)
    if os.path.exists(context_file) and os.path.getsize(context_file) > 0:
        return

    default_data = {"summary": "ASMR剧情", "style": "沉浸式体验", "whisper_keywords": ""}
    
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
            "2. ONLY extract RARE, UNCOMMON terms specific to adult-oriented content:\n"
            "   - Character names (fictional only, from CAST section)\n"
            "   - Pronouns used as names (俺, 僕, お前, あなた, きみ)\n"
            "   - Role names (ママ, お姉ちゃん, 先生, お兄さん, パパ, おじさん)\n"
            "   - Adult content gameplay terms (罵倒, 煽り, 耳責め, お仕置き, 寸止め, etc.)\n"
            "   - Rare slang and specialized terminology\n"
            "3. STRICTLY EXCLUDE common Japanese words:\n"
            "   - Common verbs/nouns (対話, 選択, ループ, 尺寸, 動作, プレイ, 内容, 音声, etc.)\n"
            "   - Setting descriptions (ループ用音声, プレイ内容, etc.)\n"
            "   - Real names, Dates, Prices, URL, 'ASMR', 'Binaural', CV names, Circle names\n"
            "4. Focus on terms that are RARE in everyday Japanese but important for this content."
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

        # Common Japanese words to exclude
        common_words = ["対話", "選択", "ループ", "尺寸", "動作", "プレイ", "内容", "音声", "用", "作品", "収録", "時間", "分", "秒", "トラック", "ファイル", "形式", "サイズ", "再生", "停止", "開始", "終了", "前", "後", "左", "右", "上", "下", "中", "外", "内", "全", "半", "大", "小", "長", "短", "高", "低", "多", "少", "新", "旧", "良", "悪", "正", "誤", "有", "無", "可", "不可"]

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

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for k in keyword_list:
            if k not in seen:
                seen.add(k)
                unique_keywords.append(k)

        final_keywords = []
        for k in unique_keywords:
            if any(b in k for b in blacklist): continue
            if k in common_terms: continue
            if k in common_words: continue
            final_keywords.append(k)

        data["whisper_keywords"] = ", ".join(final_keywords)

        with open(context_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    except:
        with open(context_file, "w", encoding="utf-8") as f: json.dump(default_data, f)

def extract_terms(content, prompt_file_name):
    """Extract terms for temporary dictionary"""
    print("STATUS: Extracting Terms")
    sys.stdout.flush()

    terms_path = get_assets_terms_path(prompt_file_name)

    # Skip if already exists
    if os.path.exists(terms_path) and os.path.getsize(terms_path) > 0:
        return

    # Load existing global dictionary for deduplication
    existing_terms = set()
    try:
        dict_data = load_asmr_dict()
        for item in dict_data:
            existing_terms.add(item['term'])
    except:
        pass

    # Default empty array
    default_terms = []

    if not content:
        with open(terms_path, "w", encoding="utf-8") as f:
            json.dump(default_terms, f, ensure_ascii=False, indent=2)
        return

    try:
        port = int(os.environ.get("LLM_PORT", 8080))
        llm = LocalLLM(port=port)
        system_prompt = (
            "你是日语成人向ASMR术语提取专家。只提取在日常日语中罕见但在成人向内容中重要的专有术语。\n"
            "输出格式：JSON数组 [{\"term\": \"日文术语\", \"type\": \"词性\"}]\n"
            "\n必须提取（仅限罕见词）：\n"
            "1. 虚构角色名（先輩、僕ちゃん、ダーリン）\n"
            "2. 作为称呼的人称代词（俺、僕、お前、あなた、きみ、パパ、おじさん）\n"
            "3. 角色关系称呼（ママ、お姉ちゃん、先生、お兄さん）\n"
            "4. 成人向玩法术语（罵倒、煽り、耳責め、お仕置き、寸止め、甘やかし等）\n"
            "5. 成人向特有黑话和专业术语\n"
            "\n严格排除（常见词和无关词）：\n"
            "- 日常常见词（対話、選択、ループ、尺寸、動作、プレイ、内容、音声、用、等）\n"
            "- 设定说明词（ループ用音声、プレイ内容等组合词）\n"
            "- 声优真名（带CV、様、@的）、公司/社团名、作品标题\n"
            "- 现实人名、日期、价格、网址\n"
            "\n判断标准：该词在日常对话中是否罕见？如果是常见词就不要提取。\n"
            "\n示例输出：\n"
            "[{\"term\":\"先輩\",\"type\":\"noun\"},"
            "{\"term\":\"僕ちゃん\",\"type\":\"noun\"},"
            "{\"term\":\"耳責め\",\"type\":\"noun\"},"
            "{\"term\":\"お仕置き\",\"type\":\"noun\"}]\n"
            "\n注意：type只需填noun/verb/adj其中之一，大部分是noun"
        )

        full_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{content[:4000]}<|im_end|>\n<|im_start|>assistant\n"
        response = llm.completion(full_prompt, temperature=0.1, max_tokens=2048)

        # Parse JSON array
        try:
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                extracted_terms = json.loads(response[start:end])
            else:
                extracted_terms = []
        except:
            extracted_terms = []

        # Filter and validate
        blacklist = ["CV", "Voice", "Circle", "Track", "http", "DL", "版本", "作者",
                     "声优", "発売", "価格", "バイノーラル", "立体音響", "ASMR", "様", "出演"]

        # Common Japanese words to exclude
        common_words = ["対話", "選択", "ループ", "尺寸", "動作", "プレイ", "内容", "音声", "用", "作品", "収録", "時間", "分", "秒", "トラック", "ファイル", "形式", "サイズ", "再生", "停止", "開始", "終了", "前", "後", "左", "右", "上", "下", "中", "外", "内", "全", "半", "大", "小", "長", "短", "高", "低", "多", "少", "新", "旧", "良", "悪", "正", "誤", "有", "無", "可", "不可"]

        filtered_terms = []
        for term_obj in extracted_terms:
            if not isinstance(term_obj, dict):
                continue
            term = term_obj.get('term', '')
            if not term:
                continue
            # Check blacklist
            if any(b in term for b in blacklist):
                continue
            # Check if already in global dictionary
            if term in existing_terms:
                continue
            # Check if common word
            if term in common_words:
                continue

            # Generate reading using pykakasi
            try:
                kks = pykakasi.kakasi()
                result = kks.convert(term)
                reading = ''.join([item['hepburn'] for item in result])
                term_obj['reading'] = reading.lower()
            except:
                term_obj['reading'] = ""

            # Ensure type field exists
            if not term_obj.get('type'):
                term_obj['type'] = 'noun'

            # Only keep term, reading, type fields
            filtered_term = {
                'term': term_obj['term'],
                'reading': term_obj['reading'],
                'type': term_obj['type']
            }

            filtered_terms.append(filtered_term)

        # Save to file
        with open(terms_path, "w", encoding="utf-8") as f:
            json.dump(filtered_terms, f, ensure_ascii=False, indent=2)

    except Exception as e:
        # Save empty array on error
        with open(terms_path, "w", encoding="utf-8") as f:
            json.dump(default_terms, f, ensure_ascii=False, indent=2)

def process_audio(input_file):
    check_ffmpeg()

    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}", flush=True)
        sys.exit(1)

    input_path = Path(input_file)
    cache_dir = get_cache_dir(input_file)
    final_wav = Path(cache_dir) / "audio_16k_norm.wav"

    if not final_wav.exists() or final_wav.stat().st_size == 0:
        temp_wav = Path(cache_dir) / "temp.wav"
        try:
            shutil.copy(input_path, temp_wav)
            run_ffmpeg_normalization(temp_wav, final_wav)
        except Exception as e:
            print(f"ERROR: Audio processing failed: {e}", flush=True)
            sys.exit(1)
        finally:
            if temp_wav.exists():
                os.remove(temp_wav)

    content = ""
    prompt_file_name = "default"
    if os.path.exists(PROMPTS_DIR):
        txt_files = glob.glob(os.path.join(PROMPTS_DIR, "*.txt"))
        if txt_files:
            content = read_text_file_robust(txt_files[0])
            prompt_file_name = os.path.basename(txt_files[0])
    if not content and os.path.exists("ReadMe.txt"):
        content = read_text_file_robust("ReadMe.txt")
        prompt_file_name = "ReadMe.txt"

    context_path = get_assets_context_path(prompt_file_name)
    terms_path = get_assets_terms_path(prompt_file_name)

    if os.path.exists(context_path) and os.path.exists(terms_path):
        print("STATUS: Using existing context and terms", flush=True)
    else:
        analyze_context(content, prompt_file_name)
        extract_terms(content, prompt_file_name)

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    process_audio(sys.argv[1])