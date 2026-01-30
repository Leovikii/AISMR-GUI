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

# 语义断句配置
MAX_TIME_GAP = 3.0  # 最大时间间隔（秒），超过此间隔强制断句
MIN_SUBTITLE_LENGTH = 2  # 最小字幕长度，过滤掉过短的片段

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

def get_punctuation_priority(char):
    """
    获取标点符号的断句优先级
    优先级越高，越应该在此处断句
    """
    if char in '。！？':  # 句号、感叹号、问号 - 最高优先级，必须断句
        return 3
    elif char in '…～':  # 省略号、波浪号 - 高优先级
        return 2
    elif char in '、，':  # 顿号、逗号 - 中等优先级
        return 1
    else:
        return 0

def has_strong_punctuation(text):
    """检查文本是否包含强断句标点（。！？）"""
    return any(p in text for p in '。！？')

def semantic_merge_segments(segments):
    """
    基于语义的智能字幕合并
    核心原则：
    1. 优先在句号、感叹号、问号处断句
    2. 如果没有强标点，在逗号、顿号处断句
    3. 时间间隔过大时强制断句
    4. 不使用硬性长度限制
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

        # 检查当前文本的最后一个字符
        last_char = current['text'][-1] if current['text'] else ''
        last_char_priority = get_punctuation_priority(last_char)

        # 决定是否应该断句
        should_break = False

        # 规则 1: 时间间隔过大，强制断句
        if time_gap > MAX_TIME_GAP:
            should_break = True

        # 规则 2: 遇到强断句标点（。！？），必须断句
        elif last_char_priority >= 3:
            should_break = True

        # 规则 3: 遇到省略号或波浪号，且时间间隔较大，断句
        elif last_char_priority == 2 and time_gap > 1.0:
            should_break = True

        # 规则 4: 遇到逗号或顿号，且时间间隔较大，断句
        elif last_char_priority == 1 and time_gap > 1.5:
            should_break = True

        if should_break:
            # 保存当前片段并开始新片段
            if len(current['text']) >= MIN_SUBTITLE_LENGTH:
                merged.append(current)
            current = {
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text']
            }
        else:
            # 继续合并
            current['end'] = seg['end']
            current['text'] += seg['text']

    # 保存最后一个片段
    if len(current['text']) >= MIN_SUBTITLE_LENGTH:
        merged.append(current)

    return merged

def split_by_strong_punctuation(segments):
    """
    在强标点符号（。！？）处分割字幕
    这是最后一步处理，确保每个字幕都在语义完整的位置结束
    """
    result = []

    for seg in segments:
        text = seg['text']
        start_time = seg['start']
        end_time = seg['end']
        duration = end_time - start_time

        # 如果文本中没有强标点，直接保留
        if not has_strong_punctuation(text):
            result.append(seg)
            continue

        # 在强标点处分割（保留标点）
        parts = re.split(r'([。！？])', text)

        # 重新组合：将标点符号附加到前面的文本
        sentences = []
        i = 0
        while i < len(parts):
            if i + 1 < len(parts) and parts[i + 1] in '。！？':
                # 文本 + 标点
                sentences.append(parts[i] + parts[i + 1])
                i += 2
            elif parts[i]:
                # 只有文本（最后一个片段）
                sentences.append(parts[i])
                i += 1
            else:
                i += 1

        # 如果只有一个句子，不需要分割
        if len(sentences) <= 1:
            result.append(seg)
            continue

        # 按字符长度比例分配时间
        total_len = sum(len(s) for s in sentences)
        current_time = start_time

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 计算这个句子的时间占比
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

    # Semantic merge based on punctuation
    print("STATUS: Semantic merging based on punctuation", flush=True)
    merged_segments = semantic_merge_segments(raw_segments)
    print(f"STATUS: Merged into {len(merged_segments)} segments", flush=True)

    # Split at strong punctuation marks (。！？)
    print("STATUS: Splitting at strong punctuation marks", flush=True)
    final_segments = split_by_strong_punctuation(merged_segments)
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
