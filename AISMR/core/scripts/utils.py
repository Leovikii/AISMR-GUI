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

MODELS_CONFIG = [
    {"url": QWEN_URL, "path": os.path.join(LLM_DIR, "Qwen3-4B-Instruct-2507-Q6_K.gguf"), "name": "Context AI (Qwen)"},
    {"url": SAKURA_URL, "path": os.path.join(LLM_DIR, "GalTransl-v4-4B-2512.gguf"), "name": "Translator AI (Sakura)"}
]

def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_cache_dir(input_file):
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    cache_dir = os.path.join(CACHE_ROOT, base_name)
    ensure_directory(cache_dir)
    return cache_dir

def get_qwen_model():
    return MODELS_CONFIG[0]["path"]

def get_sakura_model():
    return MODELS_CONFIG[1]["path"]

def scan_models():
    missing = []
    for m in MODELS_CONFIG:
        if not os.path.exists(m["path"]):
            missing.append(m["name"])
    print(json.dumps(missing))

def download_file_with_progress(url, dest_path, label):
    if os.path.exists(dest_path):
        return True
    
    ensure_directory(os.path.dirname(dest_path))
    
    print(f"STATUS: Downloading {label}...")
    sys.stdout.flush()
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        print(f"PROGRESS: {percent}")
                        sys.stdout.flush()
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.stdout.flush()
        return False
    return True

def download_models():
    for m in MODELS_CONFIG:
        if not os.path.exists(m["path"]):
            if not download_file_with_progress(m["url"], m["path"], m["name"]):
                sys.exit(1)
    print("DONE")

def load_asmr_dict():
    dict_path = os.path.join(ASSETS_DIR, "asmr_dictionary.json")
    if not os.path.exists(dict_path):
        return []
    try:
        with open(dict_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

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

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--scan":
            scan_models()
        elif sys.argv[1] == "--download":
            download_models()