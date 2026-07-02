# MS Auto Captions 🎬 | AI-Driven Social Video Automation Engine

A commercial, production-ready Windows desktop application that automates localized speech-to-text transcription, word-by-word animated subtitle synchronization, and video matrix rendering in a single click.

Launched publicly on **Gumroad** and featured on **Product Hunt**, this software was built independently using Python to replace tedious manual timeline-syncing workflows with a sleek, low-latency automated pipeline.

🔗 **Live Product Links:**
* [View on Gumroad](https://mswalihofficial.gumroad.com/l/ms_auto_captions)
* [View on Product Hunt](https://www.producthunt.com/products/ms-auto-captions?launch=ms-auto-captions)

---

## 🛠️ Tech Stack & Engineering Core

* **Core Language:** Python 3
* **User Interface:** CustomTkinter (Modern, optimized dark-mode desktop GUI framework)
* **AI & Speech Recognition:** Whisper AI Architecture (Local inference engine & optional cloud API pipelines)
* **Video & Graphics Processing:** OpenCV & MoviePy (For frame-by-frame rendering, font masking, and matrix manipulation)
* **Licensing Security:** Integrated dynamic HTTPS license verification connected to the Gumroad API

---

## 🚀 Key Technical Challenges Solved

### 1. Multi-Threaded Video Processing & Non-Blocking GUI
Executing heavy AI speech-to-text inference and frame-by-frame video rendering on a single thread causes desktop applications to freeze, crash, or stop responding.
* Engineered an asynchronous, multi-threaded worker architecture. The core rendering and AI transcription workloads run completely isolated in the background, keeping the CustomTkinter UI completely smooth and responsive during long processing cycles.

### 2. Local vs. Cloud Inference Optimization
To ensure maximum user privacy and system accessibility, the software supports two distinct processing modes:
* **Offline Edge Processing:** Runs optimized local AI models directly on the user's CPU, eliminating the need for expensive dedicated GPUs or external internet connectivity.
* **Cloud API Integration:** Implemented a secure, low-latency alternative pipeline to accelerate processing speeds for lower-spec hardware configurations.

### 3. Precision Subtitle Synchronization & Multi-Style Canvas Rendering
Creating "viral-style" word-by-word captions requires matching audio timestamps exactly to the pixel coordinates on screen.
* Developed custom parsing logic to translate Whisper AI timestamp arrays into precise frame-interval intervals.
* Designed **11 distinct trending subtitle animation configurations**, dynamically managing font scaling, color matrices, and relative positioning (Top/Center/Bottom) natively inside the video stream.

### 4. Commercial Security & Licensing Pipeline
* Implemented a robust local-to-cloud license validation network. On initial boot, the app executes an automated API handshake with the digital marketplace to activate the software, securely tracking system-specific IDs to eliminate unverified redistributions.

---

## 📐 System Workflow Architecture

```text
 [ Video Input ] ──> [ Audio Extraction Pipeline ] ──> [ Whisper AI Transcription Engine ]
                                                                     │
 [ Dynamic Video Output ] <── [ Custom Frame-by-Frame Canvas ] <── [ Timestamp Sync Logic ]
```

### ⚙️ Core Workflow Architecture

* **Ingestion:** The user selects a video file via the responsive GUI.
* **Analysis:** The pipeline extracts the audio stream, handling noise reduction and isolating vocal frequencies.
* **Transcription:** The AI engine processes the audio, outputting high-accuracy strings paired with exact millisecond timestamps.
* **Rendering:** The processing engine dynamically burns custom-styled animated fonts onto the video matrices, exporting a finished video file.

### 🧑‍💻 Business Impact & Validation

* **Fully Solved Use-Case:** Completely eliminates manual video timeline editing, turning a 2-hour editing chore into a simple, 1-click automated background routine.
* **Privacy-Centric Architecture:** By prioritizing local processing loops, user video files remain completely secure on their local machines.
* **Target Audience Alignment:** Actively engineered for content creators, educators, presenters, social media managers, and freelance video editors seeking workflow optimization.

---

> 🔒 **Note on Source Code Protection:** To protect commercial intellectual property and license verification mechanisms, core compilation configurations and security endpoints have been restricted. The codebase visible in this repository demonstrates UI architecture, media pipelines, and algorithmic state coordination.
