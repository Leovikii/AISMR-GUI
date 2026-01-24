import subprocess
import sys
import os

current_script_dir = os.path.dirname(os.path.abspath(__file__))
if current_script_dir not in sys.path:
    sys.path.insert(0, current_script_dir)
os.environ["PYTHONPATH"] = current_script_dir + os.pathsep + os.environ.get("PYTHONPATH", "")

os.environ["TQDM_DISABLE"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

from utils import MODELS_DIR, get_qwen_model, get_sakura_model, get_cache_dir, get_assets_context_path, get_assets_terms_path, get_final_output_path, PROMPTS_DIR
from server_manager import ServerManager
import glob

DEFAULT_INPUT = "test.flac"
PORT = 8080

os.environ["HF_HOME"] = os.path.join(MODELS_DIR, "huggingface")
os.environ["LLM_PORT"] = str(PORT)

def get_prompt_file_name():
    """Get the prompt file name from prompts directory"""
    if os.path.exists(PROMPTS_DIR):
        txt_files = glob.glob(os.path.join(PROMPTS_DIR, "*.txt"))
        if txt_files:
            return os.path.basename(txt_files[0])
    if os.path.exists("ReadMe.txt"):
        return "ReadMe.txt"
    return "default.txt"

def run_script(script_name, args=[]):
    print(f"--- RUNNING: {script_name} ---")
    cmd = [sys.executable, script_name] + args
    try:
        subprocess.run(cmd, check=True, env=os.environ.copy())
    except subprocess.CalledProcessError:
        sys.exit(1)

def file_valid(path):
    return os.path.exists(path) and os.path.getsize(path) > 0

def main():
    target_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT

    if not os.path.exists(target_file):
        print(f"ERROR: Input file not found: {target_file}")
        sys.exit(1)

    abs_input_path = os.path.abspath(target_file)
    print(f"Processing file: {abs_input_path}")
    sys.stdout.flush()

    final_output = get_final_output_path(abs_input_path)
    if file_valid(final_output):
        print(f"Final output already exists: {final_output}")
        print("Skipping all processing.")
        sys.exit(0)

    cache_dir = get_cache_dir(abs_input_path)
    print(f"Cache directory: {cache_dir}")
    sys.stdout.flush()

    prompt_file_name = get_prompt_file_name()
    path_context = get_assets_context_path(prompt_file_name)
    path_terms = get_assets_terms_path(prompt_file_name)

    need_llm = not (file_valid(path_context) and file_valid(path_terms))

    if need_llm:
        server = ServerManager(PORT)
        qwen_path = get_qwen_model()
        server.start(qwen_path)
        try:
            run_script("_0_prepare.py", [abs_input_path])
        finally:
            server.stop()
    else:
        print("Using existing context and terms from assets folder")
        run_script("_0_prepare.py", [abs_input_path])
    
    path_raw = os.path.join(cache_dir, "raw.srt")
    if not file_valid(path_raw):
        audio_path = os.path.join(cache_dir, "audio_16k_norm.wav")
        if not file_valid(audio_path):
            print(f"ERROR: Audio file not generated: {audio_path}")
            sys.exit(1)
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