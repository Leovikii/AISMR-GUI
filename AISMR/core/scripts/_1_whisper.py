import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import json
import re
import glob
import torch
from qwen_asr import Qwen3ASRModel
from utils import QWEN_ASR_DIR, get_cache_dir, load_asmr_dict, get_assets_context_path, PROMPTS_DIR

HALLUCINATION_BLACKLIST = ["Subtitle", "Caption", "Amara", "999999", "視聴ありがとう", "チャンネル登録", "高評価", "転載禁止", "字幕", "作成"]

# 最小字幕长度（字符数）
MIN_SUBTITLE_LENGTH = 3
# 最大时间间隔（秒），用于合并相邻字幕
MAX_TIME_GAP = 2.0
# 最大字幕长度（字符数）
MAX_SUBTITLE_LENGTH = 30

def format_timestamp(seconds):
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    return f"{seconds//3600:02d}:{(seconds%3600)//60:02d}:{seconds%60:02d},{milliseconds:03d}"

def fold_repetitions(text):
    return re.sub(r'(.+?)\1{2,}', r'\1...', text)

def is_hallucination(text):
    """Check if text is likely hallucination"""
    for bad in HALLUCINATION_BLACKLIST:
        if bad in text:
            return True

    if has_excessive_repetition(text):
        return True

    return False

def has_excessive_repetition(text):
    """Detect repetitive patterns"""
    if len(text) < 6:
        return False
    for length in [2, 3, 4]:
        for i in range(len(text) - length * 3):
            pattern = text[i:i+length]
            if text[i:i+length*4] == pattern * 4:
                return True
    return False

def is_valid_japanese_text(text):
    """Check if text contains valid Japanese characters"""
    if not text:
        return False
    japanese_chars = sum(1 for c in text if
                        '\u3040' <= c <= '\u309F' or  # Hiragana
                        '\u30A0' <= c <= '\u30FF' or  # Katakana
                        '\u4E00' <= c <= '\u9FFF' or  # Kanji
                        '\u3000' <= c <= '\u303F')    # Japanese punctuation
    ratio = japanese_chars / len(text)
    return ratio > 0.3

def is_sentence_end(text):
    """Check if text ends with sentence-ending punctuation"""
    if not text:
        return False
    return text[-1] in '。！？…、'

def merge_subtitle_segments(segments):
    """
    Merge small subtitle segments into larger, more readable chunks.
    Combines segments based on:
    - Time proximity (within MAX_TIME_GAP seconds)
    - Text length (up to MAX_SUBTITLE_LENGTH characters)
    - Sentence boundaries (prefer to break at punctuation)
    """
    if not segments:
        return []

    merged = []
    current = {
        'start': segments[0]['start'],
        'end': segments[0]['end'],
        'text': segments[0]['text']
    }

    for i in range(1, len(segments)):
        seg = segments[i]
        time_gap = seg['start'] - current['end']
        combined_text = current['text'] + seg['text']

        # Decide whether to merge or start new segment
        should_merge = (
            time_gap <= MAX_TIME_GAP and
            len(combined_text) <= MAX_SUBTITLE_LENGTH and
            not is_sentence_end(current['text'])
        )

        if should_merge:
            # Merge with current segment
            current['end'] = seg['end']
            current['text'] = combined_text
        else:
            # Save current and start new segment
            if len(current['text']) >= MIN_SUBTITLE_LENGTH:
                merged.append(current)
            current = {
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text']
            }

    # Don't forget the last segment
    if len(current['text']) >= MIN_SUBTITLE_LENGTH:
        merged.append(current)

    return merged

def split_by_sentence_punctuation(segments):
    """
    Split segments at sentence-ending punctuation marks.
    This ensures natural breaks at 。！？
    """
    result = []

    for seg in segments:
        text = seg['text']
        start_time = seg['start']
        end_time = seg['end']
        duration = end_time - start_time

        # Split by sentence-ending punctuation
        parts = re.split(r'([。！？])', text)

        # Recombine punctuation with preceding text
        sentences = []
        for i in range(0, len(parts) - 1, 2):
            if i + 1 < len(parts):
                sentences.append(parts[i] + parts[i + 1])
            else:
                sentences.append(parts[i])
        if len(parts) % 2 == 1 and parts[-1]:
            sentences.append(parts[-1])

        if len(sentences) <= 1:
            result.append(seg)
            continue

        # Distribute time proportionally
        total_len = sum(len(s) for s in sentences)
        current_time = start_time

        for sentence in sentences:
            if not sentence.strip():
                continue

            sentence_ratio = len(sentence) / total_len if total_len > 0 else 1.0 / len(sentences)
            sentence_duration = duration * sentence_ratio
            sentence_end = current_time + sentence_duration

            result.append({
                'start': current_time,
                'end': sentence_end,
                'text': sentence
            })

            current_time = sentence_end

    return result

def is_prompt_mirror(text, prompt):
    """Check if text is just echoing the prompt"""
    keywords = prompt.replace("、", " ").replace("。", " ").split()
    match_count = sum(1 for k in keywords if k in text)
    return match_count >= 3 and len(text) < sum(len(k) for k in keywords) * 2

def build_smart_prompt(input_file):
    """Build context prompt (not used by Qwen3-ASR, but kept for filtering)"""
    base_prompt = "这是、男性向けのASMR音声作品です。"
    keywords = []

    prompt_file_name = "default.txt"
    if os.path.exists(PROMPTS_DIR):
        txt_files = glob.glob(os.path.join(PROMPTS_DIR, "*.txt"))
        if txt_files:
            prompt_file_name = os.path.basename(txt_files[0])
    elif os.path.exists("ReadMe.txt"):
        prompt_file_name = "ReadMe.txt"

    context_file = get_assets_context_path(prompt_file_name)
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
    if len(sys.argv) < 2:
        sys.exit(1)
    input_file = sys.argv[1]

    if not os.path.exists(input_file):
        print(f"ERROR: Input file not found: {input_file}", flush=True)
        sys.exit(1)

    cache_dir = get_cache_dir(input_file)
    audio_path = os.path.join(cache_dir, "audio_16k_norm.wav")
    output_file = os.path.join(cache_dir, "raw.srt")

    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        sys.exit(0)

    if not os.path.exists(audio_path):
        print(f"ERROR: Audio file not found: {audio_path}", flush=True)
        sys.exit(1)

    initial_prompt = build_smart_prompt(input_file)

    # Check CUDA availability - REQUIRED
    if not torch.cuda.is_available():
        print("ERROR: CUDA is not available. This script requires GPU support.", flush=True)
        print("ERROR: Please install PyTorch with CUDA support:", flush=True)
        print("ERROR: Run fix-pytorch-cuda.bat or execute:", flush=True)
        print("ERROR: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124", flush=True)
        sys.exit(1)

    print(f"STATUS: Using GPU: {torch.cuda.get_device_name(0)}", flush=True)
    print("STATUS: Loading Qwen3-ASR Model", flush=True)

    try:
        model = Qwen3ASRModel.from_pretrained(
            "Qwen/Qwen3-ASR-1.7B",
            dtype=torch.bfloat16,
            device_map="cuda:0",
            max_inference_batch_size=16,
            max_new_tokens=512,
            forced_aligner="Qwen/Qwen3-ForcedAligner-0.6B",
            forced_aligner_kwargs=dict(
                dtype=torch.bfloat16,
                device_map="cuda:0",
            ),
            cache_dir=QWEN_ASR_DIR
        )
    except Exception as e:
        print(f"ERROR: Failed to load model: {e}", flush=True)
        sys.exit(1)

    print("STATUS: Transcribing Audio", flush=True)
    try:
        results = model.transcribe(
            audio=audio_path,
            language="Japanese",
            return_time_stamps=True,
        )
    except Exception as e:
        print(f"ERROR: Transcription failed: {e}", flush=True)
        sys.exit(1)

    # Collect all timestamp segments
    raw_segments = []

    for result in results:
        if not result.time_stamps:
            print("WARNING: No timestamps available", flush=True)
            continue

        for ts_segment in result.time_stamps:
            text = ts_segment.text.strip().replace(" ", "").replace("　", "")
            text = fold_repetitions(text)

            if len(text) < 1:
                continue

            if is_prompt_mirror(text, initial_prompt):
                continue

            if is_hallucination(text):
                continue

            if not is_valid_japanese_text(text):
                continue

            raw_segments.append({
                'start': ts_segment.start_time,
                'end': ts_segment.end_time,
                'text': text
            })

    print(f"STATUS: Collected {len(raw_segments)} raw segments", flush=True)

    # Merge small segments into readable chunks
    print("STATUS: Merging subtitle segments", flush=True)
    merged_segments = merge_subtitle_segments(raw_segments)
    print(f"STATUS: Merged into {len(merged_segments)} segments", flush=True)

    # Split at sentence boundaries
    print("STATUS: Splitting at sentence boundaries", flush=True)
    final_segments = split_by_sentence_punctuation(merged_segments)
    print(f"STATUS: Final output: {len(final_segments)} segments", flush=True)

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        for i, entry in enumerate(final_segments):
            f.write(f"{i+1}\n")
            f.write(f"{format_timestamp(entry['start'])} --> {format_timestamp(entry['end'])}\n")
            f.write(f"{entry['text']}\n\n")

    print(f"STATUS: Subtitle file saved: {output_file}", flush=True)
    os._exit(0)

if __name__ == "__main__":
    main()
