from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from podcast_workflow import PodcastPipeline
from pathlib import Path
import io
import os
import asyncio
import tempfile
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])

@app.post("/generate-podcast")
async def generate_podcast(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        return {"error": "Invalid file type. Please upload a PDF."}

    temp_dir = Path(tempfile.gettempdir())
    temp_pdf_path = temp_dir / file.filename
    try:
        with open(temp_pdf_path, "wb") as f_temp:
            content = await file.read()
            f_temp.write(content)

        pipeline = PodcastPipeline()
        pipeline.pdf_path = temp_pdf_path
        await asyncio.to_thread(pipeline.run_pipeline)

        podcast_file = pipeline.podcast_file
        if not podcast_file.exists():
            return {"error": "Podcast generation failed."}

        with open(podcast_file, "rb") as f:
            audio_content = f.read()

        os.remove(temp_pdf_path)
        if podcast_file.exists():
            os.remove(podcast_file)

        return StreamingResponse(
            io.BytesIO(audio_content),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=podcast.wav"}
        )
    except Exception as e:
        if temp_pdf_path.exists():
            os.remove(temp_pdf_path)
        return {"error": f"Error processing file: {str(e)}"}