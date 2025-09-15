import streamlit as st
import requests

MAX_FILE_SIZE_MB = 5
API_URL = "http://localhost:8080/meetings"
st.title("🎤 Meeting Transcription Service")
st.info(f"Upload only WAV files (Max size: {MAX_FILE_SIZE_MB} MB)")

audio_file = st.file_uploader("Upload Audio File (.wav)", type=["wav"])

if st.button("Upload & Transcribe"):
    if not audio_file:
        st.error("Please upload an audio file.")
    else:
        audio_file.seek(0, 2)
        size = audio_file.tell()
        audio_file.seek(0)

        if size > MAX_FILE_SIZE_MB * 1024 * 1024:
            st.warning(
                f"File too large. Max allowed size is {MAX_FILE_SIZE_MB} MB.")
        else:
            files = {"upload_file": (
                audio_file.name, audio_file, audio_file.type)}

            with st.spinner("Uploading file and transcribing..."):
                try:
                    response = requests.post(API_URL, files=files)

                    if response.status_code in [200, 201]:
                        st.success("Transcription completed successfully!")
                        # Extract transcription from 'notes'
                        transcription = response.json().get("data", {}).get("notes", "")
                        if transcription:
                            st.text_area("Transcription",
                                         value=transcription, height=300)
                        else:
                            st.warning(
                                "No transcription returned from API.")
                    else:
                        st.error(
                            f"Error {response.status_code}: {response.text}")

                except Exception as e:
                    st.error(f"Failed to connect to API: {str(e)}")
