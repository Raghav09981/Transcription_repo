import os
from datetime import datetime


def save_transcription_to_file(transcription_text: str) -> str:
    os.makedirs("./outputs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"./outputs/transcription_{timestamp}.txt"
    with open(file_path, "w") as f:
        f.write(transcription_text)
    return file_path
