import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import json
import re
from faster_whisper import WhisperModel
from utils import WHISPER_DIR, get_cache_dir, load_asmr_dict

MODEL_SIZE = "large-v2"
COMPUTE_TYPE = "int8_float16"

HALLUCINATION_BLACKLIST = ["Subtitle", "Caption", "Amara", "999999", "視聴ありがとう", "チャンネル登録", "高評価", "転載禁止", "字幕", "作成"]

def format_timestamp(seconds):
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    return f"{seconds//3600:02d}:{(seconds%3600)//60:02d}:{seconds%60:02d},{milliseconds:03d}"

def fold_repetitions(text):
    return re.sub(r'(.+?)\1{2,}', r'\1...', text)

def is_hallucination(text, compression_ratio):
    for bad in HALLUCINATION_BLACKLIST:
        if bad in text: return True
    if compression_ratio > 2.4: return True
    return False

def split_by_sentence_end(segment):
    text = segment.text.strip().replace(" ", "").replace("　", "")
    text = fold_repetitions(text)
    if not text: return []
    
    parts = re.split(r'(?<=[。！？])', text)
    parts = [p for p in parts if p]
    if len(parts) <= 1:
        return [{'start': segment.start, 'end': segment.end, 'text': text}]
    
    results = []
    duration = segment.end - segment.start
    total_len = len(text)
    current_start = segment.start
    
    for p in parts:
        part_ratio = len(p) / total_len
        part_duration = duration * part_ratio
        results.append({'start': current_start, 'end': current_start + part_duration, 'text': p})
        current_start += part_duration
    return results

def is_prompt_mirror(text, prompt):
    keywords = prompt.replace("、", " ").replace("。", " ").split()
    match_count = sum(1 for k in keywords if k in text)
    return match_count >= 3 and len(text) < sum(len(k) for k in keywords) * 2

def build_smart_prompt(cache_dir):
    base_prompt = "这是、男性向けのASMR音声作品です。"
    keywords = []

    context_file = os.path.join(cache_dir, "context.json")
    if os.path.exists(context_file):
        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                kw = data.get("whisper_keywords", "")
                if kw:
                    keywords.extend([k.strip() for k in kw.replace("、", ",").split(",") if k.strip()])
        except: pass

    try:
        common_data = load_asmr_dict()
        for item in common_data:
            term = item.get('term')
            if term and term not in keywords:
                keywords.append(term)
    except: pass

    prompt_str = base_prompt
    if keywords:
        prompt_str += " 登場用語: " + "、".join(keywords)
    
    return prompt_str[:220]

def main():
    if len(sys.argv) < 2: sys.exit(1)
    input_file = sys.argv[1]
    cache_dir = get_cache_dir(input_file)
    audio_path = os.path.join(cache_dir, "audio_16k_norm.wav")
    output_file = os.path.join(cache_dir, "raw.srt")

    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        sys.exit(0)

    if not os.path.exists(audio_path):
        sys.exit(1)

    initial_prompt = build_smart_prompt(cache_dir)

    print("Loading Whisper Model...", flush=True)
    model = WhisperModel(MODEL_SIZE, device="cuda", compute_type=COMPUTE_TYPE, download_root=WHISPER_DIR)
    
    print("Starting Transcription...", flush=True)
    segments, info = model.transcribe(
        audio_path,
        language="ja",
        beam_size=5,
        initial_prompt=initial_prompt,
        vad_filter=False,
        no_speech_threshold=None,
        log_prob_threshold=None,
        word_timestamps=True,
        condition_on_previous_text=False,
        repetition_penalty=1.1
    )
    
    final_srt_entries = []
    
    for segment in segments:
        text = segment.text.strip().replace(" ", "").replace("　", "")
        text = fold_repetitions(text)
        
        if len(text) < 1: continue
        if is_prompt_mirror(text, initial_prompt): continue
        if is_hallucination(text, segment.compression_ratio): continue
        if segment.avg_logprob < -1.0 and len(text) < 5: continue

        print(f"Processing: {format_timestamp(segment.start)} -> {format_timestamp(segment.end)}", flush=True)

        split_results = split_by_sentence_end(segment)
        for sub in split_results:
            final_srt_entries.append(sub)
            
    with open(output_file, "w", encoding="utf-8") as f:
        for i, entry in enumerate(final_srt_entries):
            f.write(f"{i+1}\n")
            f.write(f"{format_timestamp(entry['start'])} --> {format_timestamp(entry['end'])}\n")
            f.write(f"{entry['text']}\n\n")

    os._exit(0)

if __name__ == "__main__":
    main()