import os
import aiofiles

UPLOAD_DIR = "uploads"


async def save_audio_file(file) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    filename = os.path.basename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, filename)

    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    return f"/uploads/{filename}"
