import shutil
import os
from datetime import datetime
from fastapi import UploadFile
from pathlib import Path

UPLOAD_DIR = "uploads"


def save_transcription_to_file(transcription_text: str) -> str:
    os.makedirs("./outputs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"./outputs/transcription_{timestamp}.txt"
    with open(file_path, "w") as f:
        f.write(transcription_text)
    return file_path


def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        safe_filename = Path(destination).name
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        return file_path

    except Exception as e:
        raise RuntimeError(f"Failed to save upload file: {e}")
