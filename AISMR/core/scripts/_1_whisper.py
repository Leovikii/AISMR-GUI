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

# === 优化后的断句配置 ===
# ASMR通常包含长停顿，3秒太短会导致句子被切断。
# 建议调整为 10~15秒，主要依赖标点符号断句。
MAX_TIME_GAP = 12.0  
MIN_SUBTITLE_LENGTH = 2

def format_timestamp(seconds):
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    return f"{seconds//3600:02d}:{(seconds%3600)//60:02d}:{seconds%60:02d},{milliseconds:03d}"

def fold_repetitions(text):
    return re.sub(r'(.+?)\1{2,}', r'\1...', text)

def is_hallucination(text):
    for bad in HALLUCINATION_BLACKLIST:
        if bad in text:
            return True
    if has_excessive_repetition(text):
        return True
    return False

def has_excessive_repetition(text):
    if len(text) < 6:
        return False
    for length in [2, 3, 4]:
        for i in range(len(text) - length * 3):
            pattern = text[i:i+length]
            if text[i:i+length*4] == pattern * 4:
                return True
    return False

def is_valid_japanese_text(text):
    if not text:
        return False
    japanese_chars = sum(1 for c in text if
                        '\u3040' <= c <= '\u309F' or
                        '\u30A0' <= c <= '\u30FF' or
                        '\u4E00' <= c <= '\u9FFF' or
                        '\u3000' <= c <= '\u303F')
    ratio = japanese_chars / len(text)
    return ratio > 0.3

def get_punctuation_priority(char):
    if char in '。！？': return 3
    elif char in '…～': return 2
    elif char in '、，': return 1
    else: return 0

def has_strong_punctuation(text):
    return any(p in text for p in '。！？')

def semantic_merge_segments(segments):
    """
    【优化版】基于语义的智能字幕合并
    改进点：
    1. 大幅放宽时间间隔限制，避免ASMR长停顿导致断句。
    2. 严格遵循强标点（。！？）断句。
    3. 弱标点（、，）仅在停顿极长时才断句。
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
        
        # 获取上一段文字的最后一个字符
        last_char = current['text'][-1] if current['text'] else ''
        last_char_priority = get_punctuation_priority(last_char)

        should_break = False

        # === 断句规则优化 ===
        
        # 规则 1: 遇到强标点（。！？），必须断句
        # 这是保证句子自然结束的最重要规则
        if last_char_priority >= 3:
            should_break = True

        # 规则 2: 时间间隔极长（超过 MAX_TIME_GAP），强制断句
        # 防止两个不相关的句子因为没有标点而粘在一起
        elif time_gap > MAX_TIME_GAP:
            should_break = True

        # 规则 3: 弱标点（逗号、顿号），仅在长时间停顿（>3秒）时断句
        # 原来是1.5秒，容易切断慢速说话的句子
        elif last_char_priority == 1 and time_gap > 3.0:
            should_break = True
            
        # 规则 4: 省略号（...），仅在有明显停顿（>2秒）时断句
        elif last_char_priority == 2 and time_gap > 2.0:
            should_break = True

        # 规则 5: 如果没有任何标点，但停顿非常长（>5秒），也可以考虑断句
        # 兜底策略，处理模型漏标点的情况
        elif last_char_priority == 0 and time_gap > 5.0:
            should_break = True

        if should_break:
            if len(current['text']) >= MIN_SUBTITLE_LENGTH:
                merged.append(current)
            current = {
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text']
            }
        else:
            current['end'] = seg['end']
            current['text'] += seg['text']

    if len(current['text']) >= MIN_SUBTITLE_LENGTH:
        merged.append(current)

    return merged

def split_by_strong_punctuation(segments):
    # 此函数保持不变，用于处理模型将多个句子输出在一个片段里的情况
    result = []
    for seg in segments:
        text = seg['text']
        start_time = seg['start']
        end_time = seg['end']
        duration = end_time - start_time

        if not has_strong_punctuation(text):
            result.append(seg)
            continue

        parts = re.split(r'([。！？])', text)
        sentences = []
        i = 0
        while i < len(parts):
            if i + 1 < len(parts) and parts[i + 1] in '。！？':
                sentences.append(parts[i] + parts[i + 1])
                i += 2
            elif parts[i]:
                sentences.append(parts[i])
                i += 1
            else:
                i += 1

        if len(sentences) <= 1:
            result.append(seg)
            continue

        total_len = sum(len(s) for s in sentences)
        current_time = start_time

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence: continue
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
    keywords = prompt.replace("、", " ").replace("。", " ").split()
    match_count = sum(1 for k in keywords if k in text)
    return match_count >= 3 and len(text) < sum(len(k) for k in keywords) * 2

def build_smart_prompt(input_file):
    # 保持原有的 Prompt 构建逻辑
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
    print(f"STATUS: Context Prompt: {initial_prompt}", flush=True)

    if not torch.cuda.is_available():
        print("ERROR: CUDA is not available.", flush=True)
        sys.exit(1)

    print(f"STATUS: Using GPU: {torch.cuda.get_device_name(0)}", flush=True)
    print("STATUS: Loading Qwen3-ASR Model", flush=True)

    try:
        # === 优化点 1: 启用 Flash Attention 2 (如果显卡支持) ===
        # 这能显著提升长音频的推理速度和降低显存占用
        attn_impl = "sdpa" # 默认使用 PyTorch 内置加速
        try:
            import flash_attn
            attn_impl = "flash_attention_2"
            print("STATUS: Flash Attention 2 enabled", flush=True)
        except ImportError:
            print("WARNING: flash_attn not found, using default attention", flush=True)

        model = Qwen3ASRModel.from_pretrained(
            "Qwen/Qwen3-ASR-1.7B",
            dtype=torch.bfloat16,
            device_map="cuda:0",
            attn_implementation=attn_impl,  # 显式指定注意力实现
            max_inference_batch_size=32,    # 稍微调大批处理大小
            max_new_tokens=2048,            # === 优化点 2: 调大生成长度 ===
                                            # 防止长音频片段被截断（原512太小）
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
        # === 优化点 3: 传入 Context 参数 ===
        # 将我们构建好的 prompt 传给模型，提升专有名词识别率
        results = model.transcribe(
            audio=audio_path,
            language="Japanese",
            context=[initial_prompt],  # 关键修复：利用 Qwen3 的上下文偏置能力
            return_time_stamps=True,
        )
    except Exception as e:
        print(f"ERROR: Transcription failed: {e}", flush=True)
        sys.exit(1)

    raw_segments = []

    for result in results:
        if not result.time_stamps:
            print("WARNING: No timestamps available", flush=True)
            continue

        for ts_segment in result.time_stamps:
            text = ts_segment.text.strip().replace(" ", "").replace("　", "")
            text = fold_repetitions(text)

            if len(text) < 1: continue
            if is_prompt_mirror(text, initial_prompt): continue
            if is_hallucination(text): continue
            if not is_valid_japanese_text(text): continue

            raw_segments.append({
                'start': ts_segment.start_time,
                'end': ts_segment.end_time,
                'text': text
            })

    print(f"STATUS: Collected {len(raw_segments)} raw segments", flush=True)

    print("STATUS: Semantic merging based on punctuation", flush=True)
    merged_segments = semantic_merge_segments(raw_segments)
    print(f"STATUS: Merged into {len(merged_segments)} segments", flush=True)

    print("STATUS: Splitting at strong punctuation marks", flush=True)
    final_segments = split_by_strong_punctuation(merged_segments)
    print(f"STATUS: Final output: {len(final_segments)} segments", flush=True)

    with open(output_file, "w", encoding="utf-8") as f:
        for i, entry in enumerate(final_segments):
            f.write(f"{i+1}\n")
            f.write(f"{format_timestamp(entry['start'])} --> {format_timestamp(entry['end'])}\n")
            f.write(f"{entry['text']}\n\n")

    print(f"STATUS: Subtitle file saved: {output_file}", flush=True)
    os._exit(0)

if __name__ == "__main__":
    main()