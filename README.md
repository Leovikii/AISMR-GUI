# AISMR-GUI

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-ff69b4.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-blue.svg)

**An automated, AI-powered subtitle generation and translation tool tailored for Japanese ASMR content.**

</div>

## ✨ Features

**AISMR-GUI** automates the entire workflow of creating localized subtitles for Japanese audio tracks using a modern, aesthetic interface.

* **🌸 Sakura Dark UI:** A refined, user-friendly interface featuring a frameless window, mica material effects, and a "Sakura Dark" color scheme.
* **🤖 Full AI Pipeline:**
    * **Pre-process:** Audio normalization and context extraction using **Qwen**.
    * **Transcribe:** High-accuracy Japanese speech recognition via **Faster-Whisper**.
    * **Correct:** Acoustic fingerprinting and term correction to fix common recognition errors.
    * **Translate:** Context-aware translation using **SakuraLLM**, specialized for Japanese ACG/ASMR content.
* **📂 Smart Management:**
    * Drag-and-drop support for files and folders.
    * Recursive directory scanning.
    * Smart caching system (resume from interruption).
    * Auto-cleanup strategies for storage management.
* **🚀 Export:** Generates standard `.srt` or `.lrc` files automatically.

## 🛠️ Tech Stack

* **Frontend:** Vue, TypeScript, TailwindCSS
* **Backend:** Go (Wails v2)
* **Core Logic:** Python (Embedded)
* **Inference:** `llama.cpp`, `faster-whisper`

## 🚀 Getting Started

### Prerequisites
* Windows 10/11 (x64) with NVIDIA GPU (CUDA recommended for performance).
* [Go](https://go.dev/) (for building from source).
* [Node.js](https://nodejs.org/) (for frontend).

### Development

1.  Clone the repository:
    ```bash
    git clone [https://github.com/YourUsername/AISMR-GUI.git](https://github.com/YourUsername/AISMR-GUI.git)
    cd AISMR-GUI
    ```

2.  Install frontend dependencies:
    ```bash
    cd frontend
    npm install
    ```

3.  Run in development mode:
    ```bash
    wails dev
    ```

### Build

To build the production binary:

```bash
wails build
