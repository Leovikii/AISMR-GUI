import subprocess
import sys
import os

current_script_dir = os.path.dirname(os.path.abspath(__file__))
if current_script_dir not in sys.path:
    sys.path.insert(0, current_script_dir)
os.environ["PYTHONPATH"] = current_script_dir + os.pathsep + os.environ.get("PYTHONPATH", "")

os.environ["TQDM_DISABLE"] = "1"

from utils import MODELS_DIR, get_qwen_model, get_sakura_model, get_cache_dir
from server_manager import ServerManager

DEFAULT_INPUT = "test.flac"
PORT = 8080

os.environ["HF_HOME"] = os.path.join(MODELS_DIR, "huggingface")
os.environ["LLM_PORT"] = str(PORT)

def run_script(script_name, args=[]):
    print(f"--- RUNNING: {script_name} ---")
    cmd = [sys.executable, script_name] + args
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        sys.exit(1)

def file_valid(path):
    return os.path.exists(path) and os.path.getsize(path) > 0

def main():
    target_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT
    if not os.path.exists(target_file):
        sys.exit(1)

    abs_input_path = os.path.abspath(target_file)
    cache_dir = get_cache_dir(abs_input_path)

    # Step 0: Prepare
    path_context = os.path.join(cache_dir, "context.json")
    if not file_valid(path_context):
        server = ServerManager(PORT)
        qwen_path = get_qwen_model()
        server.start(qwen_path)
        try:
            run_script("_0_prepare.py", [abs_input_path])
        finally:
            server.stop()
    
    # Step 1: Whisper
    path_raw = os.path.join(cache_dir, "raw.srt")
    if not file_valid(path_raw):
        run_script("_1_whisper.py", [abs_input_path])

    # Step 2: Correct
    path_corrected = os.path.join(cache_dir, "corrected.srt")
    if not file_valid(path_corrected):
        run_script("_2_correct.py", [abs_input_path])

    # Step 3: Translate
    path_trans = os.path.join(cache_dir, "translated.srt")
    if not file_valid(path_trans):
        server = ServerManager(PORT)
        sakura_path = get_sakura_model()
        server.start(sakura_path)
        try:
            run_script("_3_translate.py", [abs_input_path])
        finally:
            server.stop()

    # Step 4: Output
    run_script("_4_output.py", [abs_input_path])
    print("All Done.")

if __name__ == "__main__":
    main()