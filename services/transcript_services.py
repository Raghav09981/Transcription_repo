import google.generativeai as genai
import os
import mimetypes
import shutil
import subprocess
import tempfile
from typing import List, Tuple

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-1.5-flash")


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _convert_to_wav_16k_mono(src_path: str) -> Tuple[str, bool]:
    """Convert arbitrary audio to 16kHz mono WAV using ffmpeg if available.
    Returns (converted_path, converted_flag). If conversion not possible, returns (src_path, False).
    """
    if not _ffmpeg_available():
        return src_path, False
    dst_dir = tempfile.mkdtemp(prefix="audio_conv_")
    base = os.path.splitext(os.path.basename(src_path))[0]
    dst_path = os.path.join(dst_dir, f"{base}_16k_mono.wav")
    cmd = [
        "ffmpeg", "-y", "-i", src_path,
        "-ac", "1",  # mono
        "-ar", "16000",  # 16kHz
        "-c:a", "pcm_s16le",  # PCM 16-bit
        dst_path
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return dst_path, True
    except Exception:
        return src_path, False


def _segment_audio_wav(src_wav_path: str, segment_seconds: int = 300) -> List[str]:
    """Segment a WAV into fixed-size chunks using ffmpeg if available; otherwise return [src]."""
    if not _ffmpeg_available():
        return [src_wav_path]
    out_dir = tempfile.mkdtemp(prefix="audio_segs_")
    out_pattern = os.path.join(out_dir, "segment_%03d.wav")
    cmd = [
        "ffmpeg", "-y", "-i", src_wav_path,
        "-f", "segment", "-segment_time", str(segment_seconds),
        "-c", "copy", out_pattern
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        # Collect generated segments in sorted order
        segments = sorted(
            [os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.endswith('.wav')]
        )
        return segments if segments else [src_wav_path]
    except Exception:
        return [src_wav_path]


def _guess_mime(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or "application/octet-stream"


def transcript_audio(audio_file_path: str, save_dir: str = "outputs") -> dict:
    # Ensure save directory exists (auto-create if missing)
    os.makedirs(save_dir, exist_ok=True)

    # Convert to robust format for transcription
    conv_path, converted = _convert_to_wav_16k_mono(audio_file_path)

    # Segment long audio
    segments = _segment_audio_wav(conv_path, segment_seconds=300)  # 5 minutes per chunk

    # Transcribe each segment and assemble
    transcripts: List[str] = []
    for idx, seg_path in enumerate(segments):
        with open(seg_path, "rb") as f:
            audio_bytes = f.read()

        # Choose mime type: use wav for converted, else guess
        mime_type = "audio/wav" if converted or seg_path.lower().endswith('.wav') else _guess_mime(seg_path)

        response = gemini_model.generate_content([
            {"mime_type": mime_type, "data": audio_bytes},
            (
                "Please transcribe this meeting audio with speaker diarization. "
                "Return: 1) a clear transcript with speaker labels (Speaker 1, Speaker 2, ...), "
                "2) a concise summary with Title, Summary, Key Points, and "
                "3) a bullet list of action items with owners if mentioned."
            )
        ])

        seg_text = response.text if hasattr(response, "text") else str(response)
        header = f"\n\n=== Segment {idx + 1} ===\n"
        transcripts.append(header + seg_text.strip())

    combined_text = "\n".join(transcripts).strip()

    # Save in a clean .txt file
    filename = os.path.splitext(os.path.basename(audio_file_path))[0] + "_minutes.txt"
    file_path = os.path.join(save_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("📌 Meeting Minutes\n")
        f.write("====================\n\n")
        f.write(combined_text)

    print(f"💾 Saved structured meeting notes at: {file_path}")

    return {
        "transcription": combined_text,
        "file_path": file_path
    }
