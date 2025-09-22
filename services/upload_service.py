import os
import aiofiles
import logging

UPLOAD_DIR = "uploads"


async def save_audio_file(file) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    filename = os.path.basename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, filename)

    # Stream the upload in chunks to handle large files without loading into memory
    chunk_size = 1024 * 1024 * 4  # 4 MB per chunk
    total_bytes = 0
    chunk_index = 0
    logging.getLogger(__name__).info(f"Starting upload: {filename}")
    async with aiofiles.open(file_path, "wb") as out_file:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            await out_file.write(chunk)
            total_bytes += len(chunk)
            chunk_index += 1
            logging.getLogger(__name__).info(
                f"Uploading {filename}: chunk={chunk_index} size={len(chunk)}B total={total_bytes}B")
    logging.getLogger(__name__).info(
        f"Completed upload: {filename} -> {file_path} ({total_bytes} bytes)")

    return f"/uploads/{filename}"
