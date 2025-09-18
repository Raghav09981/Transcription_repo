import google.generativeai as genai
import os

genai.configure(api_key="AIzaSyD3z_Ip7MxyFptvES9lKZfOvtt_y_F3o8k")
gemini_model = genai.GenerativeModel("gemini-1.5-flash")


def transcript_audio(audio_file_path: str, save_dir: str = "outputs") -> dict:
    # Ensure save directory exists (auto-create if missing)
    os.makedirs(save_dir, exist_ok=True)

    # Read audio file
    with open(audio_file_path, "rb") as f:
        audio_bytes = f.read()

    # Ask Gemini
    response = gemini_model.generate_content([
        {"mime_type": "audio/wav", "data": audio_bytes},
        """Please:
        1. Transcribe this meeting audio
        2. Summarize into structured meeting minutes (Title, Summary, Key Points)
        3. Extract a bullet list of actionables (with owners if mentioned)"""
    ])

    text_output = response.text if hasattr(response, "text") else str(response)

    # Save in a clean .txt file
    filename = os.path.splitext(os.path.basename(audio_file_path))[
        0] + "_minutes.txt"
    file_path = os.path.join(save_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("📌 Meeting Minutes\n")
        f.write("====================\n\n")
        f.write(text_output.strip())

    print(f"💾 Saved structured meeting notes at: {file_path}")

    return {
        "transcription": text_output,
        "file_path": file_path
    }
