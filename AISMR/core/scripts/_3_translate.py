import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import json
from utils import LocalLLM, get_cache_dir, load_asmr_dict

BATCH_SIZE = 10
MAX_HISTORY = 5

def parse_srt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
    entries = []
    for block in content.strip().split('\n\n'):
        lines = block.split('\n')
        if len(lines) >= 3:
            entries.append({'index': lines[0], 'timestamp': lines[1], 'text': " ".join(lines[2:])})
    return entries

def save_srt_append(file_path, entries):
    with open(file_path, 'a' if os.path.exists(file_path) else 'w', encoding='utf-8') as f:
        for e in entries: f.write(f"{e['index']}\n{e['timestamp']}\n{e['text']}\n\n")

def load_filtered_glossary(full_text):
    relevant_glossary = []
    try:
        common_data = load_asmr_dict()
        for item in common_data:
            term = item.get('term')
            translation = item.get('trans')
            if term and translation and item.get("type") != "noise":
                if term in full_text:
                    relevant_glossary.append(f"{term}->{translation}")
    except: pass
    return "\n".join(relevant_glossary)

def load_context_info(cache_dir):
    summary = ""
    style = ""
    try:
        with open(os.path.join(cache_dir, "context.json"), "r", encoding="utf-8") as f:
            d = json.load(f)
            summary = d.get("summary", "")
            style = d.get("style", "")
    except: pass
    return summary, style

def recursive_translate(llm, items, history, context_tuple):
    summary, style, glossary = context_tuple
    
    sys_prompt = "你是一个视觉小说翻译模型，可以通顺地使用给定的术语表以指定的风格将日文翻译成简体中文。"
    if summary: sys_prompt += f"\n剧情背景：{summary}"
    if style: sys_prompt += f"\n翻译风格要求：{style}"
    if history:
        recent_context = history[-3:] 
        sys_prompt += f"\n上文回顾：{' | '.join(recent_context)}"

    user_prompt_parts = []
    if glossary:
        user_prompt_parts.append(f"参考以下术语表：\n{glossary}\n")
    
    current_text = "\n".join([i['text'] for i in items])
    user_prompt_parts.append(f"将下面的文本从日文翻译成简体中文：\n{current_text}")
    
    user_prompt = "\n".join(user_prompt_parts)
    
    prompt = f"<|im_start|>system\n{sys_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"
    
    try:
        res = llm.completion(prompt, temperature=0.3, top_p=0.8).replace("<|im_end|>", "").strip()
        lines = [l.strip() for l in res.split('\n') if l.strip()]
        if len(lines) == len(items): return lines
        if len(items) == 1 and len(lines) > 0: return [lines[0]]
    except: pass
    
    if len(items) > 1:
        mid = len(items) // 2
        res_first = recursive_translate(llm, items[:mid], history, context_tuple)
        res_second = recursive_translate(llm, items[mid:], history + res_first, context_tuple)
        return res_first + res_second
    return [items[0]['text']]

def main():
    if len(sys.argv) < 2: sys.exit(1)
    cache_dir = get_cache_dir(sys.argv[1])
    inp_srt = os.path.join(cache_dir, "corrected.srt")
    trans_srt = os.path.join(cache_dir, "translated.srt")
    
    if os.path.exists(trans_srt) and os.path.getsize(trans_srt) > 0:
        sys.exit(0)
    
    if not os.path.exists(inp_srt):
        sys.exit(1)
    
    entries = parse_srt(inp_srt)
    
    # 1. 提取全文内容用于过滤术语
    full_text = "".join([e['text'] for e in entries])
    
    # 2. 生成过滤后的精简术语表
    glossary_str = load_filtered_glossary(full_text)
    
    # 3. 加载背景信息
    summary, style = load_context_info(cache_dir)
    context_tuple = (summary, style, glossary_str)
    
    llm = LocalLLM(port=int(os.environ.get("LLM_PORT", 8080)))
    
    history = []
    total_batches = (len(entries) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for i in range(0, len(entries), BATCH_SIZE):
        batch = entries[i:i+BATCH_SIZE]
        current_batch_num = i // BATCH_SIZE + 1
        print(f"Translating batch {current_batch_num}/{total_batches}...", flush=True)
        
        results = recursive_translate(llm, batch, history, context_tuple)
        save_srt_append(trans_srt, [{'index': b['index'], 'timestamp': b['timestamp'], 'text': r} for b, r in zip(batch, results)])
        history = (history + results)[-MAX_HISTORY:]

if __name__ == "__main__":
    main()