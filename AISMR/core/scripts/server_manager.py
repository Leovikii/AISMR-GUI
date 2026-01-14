import os
import sys
import subprocess
import time
import requests
import psutil
from utils import BIN_DIR

class ServerManager:
    def __init__(self, port=8080):
        self.port = port
        self.process = None
        self.server_exe = os.path.join(BIN_DIR, "llama", "llama-server.exe")

    def _kill_existing_servers(self):
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and 'llama-server.exe' in proc.info['name'].lower():
                    proc.kill()
            except:
                pass
        time.sleep(1)

    def start(self, model_path):
        self._kill_existing_servers()
        
        if not os.path.exists(self.server_exe):
            print(f"Error: Server binary not found at {self.server_exe}")
            sys.exit(1)

        cmd = [
            self.server_exe,
            "-m", model_path,
            "--port", str(self.port),
            "-ngl", "99",
            "-c", "8192"
        ]

        print(f"Starting Engine: {os.path.basename(model_path)} on port {self.port}...")
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = subprocess.CREATE_NO_WINDOW

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=startupinfo,
            creationflags=creationflags
        )

        self._wait_for_healthy()

    def _wait_for_healthy(self):
        url = f"http://127.0.0.1:{self.port}/health"
        print("Waiting for engine to load...", flush=True)
        for i in range(60): 
            try:
                res = requests.get(url, timeout=1)
                if res.status_code == 200:
                    status = res.json().get('status', '')
                    if status == 'ok' or status == 'loading model':
                        print("Engine Ready.", flush=True)
                        time.sleep(1)
                        return
            except:
                pass
            time.sleep(1)
        
        print("\nServer failed to start.")
        self.stop()
        sys.exit(1)

    def stop(self):
        if self.process:
            print("Stopping Engine...")
            self.process.kill()
            self.process = None
        self._kill_existing_servers()