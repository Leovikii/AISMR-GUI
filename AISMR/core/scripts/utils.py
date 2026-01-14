import os
import sys
import json
import requests
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
CACHE_ROOT = os.path.join(PROJECT_ROOT, "cache")
LLM_DIR = os.path.join(MODELS_DIR, "llm")
WHISPER_DIR = os.path.join(MODELS_DIR, "whisper")
PROMPTS_DIR = os.path.join(PROJECT_ROOT, "prompts")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
BIN_DIR = os.path.join(PROJECT_ROOT, "bin")

QWEN_URL = "https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/main/Qwen3-4B-Instruct-2507-Q6_K.gguf?download=true"
SAKURA_URL = "https://huggingface.co/SakuraLLM/GalTransl-v4-4B-2512/resolve/main/GalTransl-v4-4B-2512.gguf?download=true"

def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_cache_dir(input_file):
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    cache_dir = os.path.join(CACHE_ROOT, base_name)
    ensure_directory(cache_dir)
    return cache_dir

def download_model(url, dest_path):
    if os.path.exists(dest_path):
        return dest_path
    ensure_directory(os.path.dirname(dest_path))
    print(f"Downloading model to {dest_path}...")
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 * 1024
    downloaded = 0
    with open(dest_path, 'wb') as f:
        for data in response.iter_content(1024):
            f.write(data)
            downloaded += len(data)
            if downloaded % (10 * 1024 * 1024) < 1024:
                print(f"Downloaded {downloaded // (1024*1024)} MB / {total_size // (1024*1024)} MB")
    print("Download complete.")
    return dest_path

def get_qwen_model():
    model_path = os.path.join(LLM_DIR, "Qwen3-4B-Instruct-2507-Q6_K.gguf")
    return download_model(QWEN_URL, model_path)

def get_sakura_model():
    model_path = os.path.join(LLM_DIR, "GalTransl-v4-4B-2512.gguf")
    return download_model(SAKURA_URL, model_path)

class LocalLLM:
    def __init__(self, port=8080):
        self.api_url = f"http://127.0.0.1:{port}/completion"

    def completion(self, prompt, temperature=0.1, top_p=0.9, max_tokens=1024):
        raw_prompt = f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        if "<|im_start|>" in prompt:
            raw_prompt = prompt
        return self._send_request(raw_prompt, temperature, top_p, max_tokens, ["<|im_end|>", "###", "[Input]", "[Output]", "<|im_start|>"])

    def _send_request(self, prompt, temperature, top_p, max_tokens, stop_tokens):
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "top_p": top_p,
            "n_predict": max_tokens,
            "stop": stop_tokens
        }
        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            return response.json()['content']
        except Exception as e:
            raise

def load_asmr_dict():
    dict_path = os.path.join(ASSETS_DIR, "asmr_dictionary.json")
    if not os.path.exists(dict_path):
        return []
    try:
        with open(dict_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def get_whisper_prompt_from_dict():
    data = load_asmr_dict()
    terms = [item['term'] for item in data]
    base = "これは、男性向けのASMR音声作品です。"
    if terms:
        return base + " 登場用語: " + "、".join(terms[:30]) + "。"
    return base