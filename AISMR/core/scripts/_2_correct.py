import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import json
import re
import pykakasi
from difflib import SequenceMatcher
from utils import get_cache_dir, load_asmr_dict

def get_acoustic_fingerprint(text):
    if not text: return ""
    s = text.lower()
    s = re.sub(r'[^a-z]', '', s)
    trans_table = str.maketrans({
        'b': 'h', 'p': 'h',
        'd': 't',
        'g': 'k',
        'z': 's', 'j': 's'
    })
    s = s.translate(trans_table)
    s = re.sub(r'([a-z])\1+', r'\1', s)
    return s

def load_correction_data():
    data = load_asmr_dict()
    replace_map = {}
    phonetic_map = {}
    noise_keywords = []
    for item in data:
        term = item['term']
        if item.get('type') == 'noise':
            noise_keywords.append(term)
            if item.get('wrongs'):
                noise_keywords.extend(item['wrongs'])
            continue
        if item.get('wrongs'):
            for wrong in item['wrongs']:
                replace_map[wrong] = term
        if item.get('reading'):
            fp = get_acoustic_fingerprint(item['reading'])
            if fp and fp not in phonetic_map:
                phonetic_map[fp] = term
    return replace_map, phonetic_map, noise_keywords

def parse_srt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
    entries = []
    for block in content.strip().split('\n\n'):
        lines = block.split('\n')
        if len(lines) >= 3:
            entries.append({'index': int(lines[0]), 'timestamp': lines[1], 'text': " ".join(lines[2:])})
    return entries

def save_srt(file_path, entries):
    with open(file_path, 'w', encoding='utf-8') as f:
        for i, e in enumerate(entries):
            f.write(f"{i+1}\n{e['timestamp']}\n{e['text']}\n\n")

def batch_replace(text, replace_map):
    if not replace_map: return text
    sorted_keys = sorted(replace_map.keys(), key=len, reverse=True)
    pattern = re.compile("|".join(map(re.escape, sorted_keys)))
    return pattern.sub(lambda m: replace_map[m.group(0)], text)

def phonetic_replace(text, phonetic_map, kks_converter):
    if not text.strip(): return text
    result = []
    tokens = kks_converter.convert(text)
    for token in tokens:
        hepburn = token['hepburn']
        fp = get_acoustic_fingerprint(hepburn)
        if fp in phonetic_map:
            result.append(phonetic_map[fp])
        else:
            result.append(token['orig'])
    return "".join(result)

def compress_repetitions(text):
    return re.sub(r'([ー〜～…\.!? ])\1{2,}', r'\1\1', text)

def is_noise_line(text, noise_keywords):
    if len(text) > 20: return False
    for kw in noise_keywords:
        if kw in text: return True
    return False

def are_similar(t1, t2):
    return SequenceMatcher(None, t1, t2).ratio() > 0.6

def process_correction(input_file):
    cache_dir = get_cache_dir(input_file)
    raw_srt = os.path.join(cache_dir, "raw.srt")
    corrected_srt = os.path.join(cache_dir, "corrected.srt")
    
    if os.path.exists(corrected_srt) and os.path.getsize(corrected_srt) > 0:
        return
    
    if not os.path.exists(raw_srt):
        sys.exit(1)
        
    replace_map, phonetic_map, noise_keywords = load_correction_data()
    entries = parse_srt(raw_srt)
    kks = pykakasi.kakasi()
    
    processed_entries = []
    for entry in entries:
        t = entry['text']
        t = batch_replace(t, replace_map)
        t = phonetic_replace(t, phonetic_map, kks)
        t = compress_repetitions(t)
        entry['text'] = t
        processed_entries.append(entry)
    
    final_entries = []
    i = 0
    n = len(processed_entries)
    while i < n:
        curr = processed_entries[i]
        curr_text = curr['text']
        if i + 3 < n:
            if (processed_entries[i+1]['text'] == curr_text and 
                processed_entries[i+2]['text'] == curr_text and 
                processed_entries[i+3]['text'] == curr_text):
                j = i + 1
                while j < n and processed_entries[j]['text'] == curr_text:
                    j += 1
                i = j
                continue
        if is_noise_line(curr_text, noise_keywords):
            j = i + 1
            streak = 1
            while j < n and is_noise_line(processed_entries[j]['text'], noise_keywords) and are_similar(processed_entries[j]['text'], curr_text):
                streak += 1
                j += 1
            if streak >= 3:
                final_entries.append(curr)
                i = j
            else:
                final_entries.append(curr)
                i += 1
        else:
            final_entries.append(curr)
            i += 1
            
    save_srt(corrected_srt, final_entries)

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    process_correction(sys.argv[1])