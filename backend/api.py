from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
import os
import asyncio
from pathlib import Path
from podcast_workflow import PodcastPipeline
from typing import Optional
import tempfile
import logging
import traceback
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:2000", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the podcast pipeline
pipeline = PodcastPipeline()

# --------------------------
# SERVE FRONTEND
# --------------------------
app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")

@app.get("/")
async def serve_frontend():
    return FileResponse("dist/index.html")

# --------------------------
# UPLOAD PDF
# --------------------------
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        # Save the uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Copy file to the base directory with the expected name
        shutil.copy(tmp_path, str(pipeline.pdf_path))
        os.unlink(tmp_path)  # Clean up temp file

        return {"message": "PDF uploaded successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/generate-podcast")
async def generate_podcast(file: UploadFile = File(None)):
    """Generate podcast - accepts optional file upload for single-request flow."""
    try:
        # If a file is included in this request, save it first
        if file and file.filename:
            logger.info(f"Received file: {file.filename}")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = tmp.name
            shutil.copy(tmp_path, str(pipeline.pdf_path))
            os.unlink(tmp_path)
            logger.info(f"PDF saved to {pipeline.pdf_path}")

        if not pipeline.pdf_path.exists():
            raise HTTPException(status_code=400, detail="No PDF file found. Please upload a PDF first.")

        logger.info("Starting podcast pipeline...")
        await asyncio.to_thread(pipeline.run_pipeline)
        logger.info("Pipeline completed successfully.")

        if not pipeline.podcast_file.exists():
            raise HTTPException(status_code=500, detail="Pipeline completed but no audio file was generated.")

        return FileResponse(
            str(pipeline.podcast_file),
            media_type="audio/wav",
            filename="podcast.wav"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating podcast: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download-podcast")
async def download_podcast():
    try:
        if pipeline.podcast_file.exists():
            return FileResponse(
                str(pipeline.podcast_file),
                media_type="audio/wav",
                filename="podcast.wav"
            )
        raise HTTPException(status_code=404, detail="Podcast file not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
