# VocalNote-PDF2Podcast

*Turn Any PDF Into a Private Podcast, Instantly—Offline, Secure, and Fast.*

## Project Motivation
I wanted to make AI tools and utility apps that help users like students, professors, and many more to have access to AI applications while running them offline—without any internet. My focus was on making them run fast on edge devices, while also upholding privacy and security: files uploaded never leave the user's device. Through this project, I aimed to learn how AI applications are developed and brought to market as real-world products. My goal was to understand the end-to-end process—from building the core functionality to packaging, deployment, and user experience—so I could eventually release my own AI-based solutions.

**Future plans:** Add user authentication, allow users to save audio files and transcripts to a database, and scale the app for broader use.

## Project Overview
**VocalNote-PDF2Podcast** is an AI-powered web application that converts any PDF into a podcast-style audio file, all locally on your machine. Users can:
- Upload a PDF and generate a podcast audio file (WAV)
- Listen to or download the generated podcast
- Enjoy full privacy: files and data never leave your device
- Experience fast, offline AI processing—no internet required

**Technologies Used:**
- **Python 3.11**: Backend and AI pipeline
- **FastAPI**: Backend API for file upload, processing, and download
- **llama-cpp-python**: Local LLM inference for text cleaning and transcript generation
- **Kokoro**: Local text-to-speech (TTS) for podcast audio
- **PyPDF2**: PDF text extraction
- **Pydub, NumPy, SciPy**: Audio processing
- **React + TypeScript + Vite**: Modern, responsive frontend
- **Axios**: Frontend-backend communication
- **CORS**: Secure frontend-backend integration

These technologies were chosen for their speed, privacy, and ability to run on consumer hardware without cloud dependencies.

## Setup Instructions

### 1. Backend (Python, FastAPI)
```bash
cd backend
python -m venv nbq3.11
source nbq3.11/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn api:app --reload --host 0.0.0.0 --port 9000
```

### 2. Frontend (React, Vite)
```bash
cd frontend
npm install
npm run dev
# App runs at http://localhost:2000
```

### 3. Usage
- Open [http://localhost:2000](http://localhost:2000) in your browser
- Upload a PDF and click "Generate Podcast"
- Listen to or download the generated audio

## Project Structure
```
VocalNote-PDF2Podcast/
├── backend/
│   ├── api.py                # FastAPI app (file upload, processing, download)
│   ├── main.py               # (Legacy) FastAPI endpoint for direct PDF-to-audio
│   ├── podcast_workflow.py   # Core pipeline: PDF → text → transcript → audio
│   ├── models/               # LLM and TTS model files (GGUF)
│   ├── requirements.txt      # Backend dependencies
│   └── resources/            # Sample PDFs, extracted text, etc.
├── frontend/
│   ├── src/                  # React app source code
│   ├── public/               # Static assets
│   ├── package.json          # Frontend dependencies
│   └── vite.config.ts        # Vite config
└── README.md                 # Project documentation
```

## Function-by-Function Explanation

### backend/api.py (FastAPI Backend)
- **/upload-pdf**: Accepts PDF uploads and stores them locally for processing
- **/generate-podcast**: Runs the full pipeline (PDF → podcast audio)
- **/download-podcast**: Serves the generated audio file for download
- **CORS Middleware**: Allows secure frontend-backend communication

### backend/podcast_workflow.py (Core Pipeline)
- **PodcastPipeline**: Orchestrates the full process
  - `extract_text_from_pdf`: Extracts text from PDF
  - `preprocess_text`: Cleans and deduplicates text using a local LLM
  - `generate_transcript`: Generates a podcast-style transcript with two speakers
  - `rewrite_transcript`: Refines transcript for TTS
  - `generate_podcast`: Uses Kokoro TTS to synthesize audio for each speaker
  - `run_pipeline`: Runs all steps in sequence

### backend/main.py (Legacy/Alternate API)
- **/generate-podcast**: Accepts PDF upload, runs pipeline, streams audio response

### frontend/src/App.tsx (React Frontend)
- **File Upload**: Lets user select and upload a PDF
- **Generate Podcast**: Triggers backend processing and shows status
- **Audio Player**: Plays and allows download of the generated podcast
- **Error Handling**: User-friendly error/status messages

## Repository
GitHub: [your-repo-link-here]

## Extra Details
- **Privacy-first**: All processing is local; no data leaves your device
- **Offline-ready**: No internet required after setup
- **Extensible**: Future plans for user authentication, saving podcasts/transcripts, and database integration
- **Edge-optimized**: Designed to run on consumer hardware (laptops, desktops)

## Troubleshooting
- If you encounter errors with model files, ensure the GGUF models are present in `backend/models/`
- For Llama or Kokoro errors, check that your CPU supports required instructions (AVX2, etc.)
- If the frontend cannot connect, ensure both backend (port 9000) and frontend (port 2000) are running
- For PDF extraction issues, verify your PDF is not encrypted or corrupted
- For audio playback issues, try a different browser or audio player

## Contributing
Contributions are welcome! Ideas for new features, bug fixes, or improvements can be submitted via issues or pull requests. Please follow best practices and write clear commit messages.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- [Kokoro TTS](https://huggingface.co/hexgrad/Kokoro-82M)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [PyPDF2](https://pypdf2.readthedocs.io/)
- [Pydub](https://github.com/jiaaro/pydub)
- Inspiration from open-source AI and privacy-first tools

## Contact
Created by [prathamm-k](https://github.com/prathamm-k) — Feel free to reach out via GitHub for questions, suggestions, or collaboration.

---
Enjoy using and extending VocalNote-PDF2Podcast! 