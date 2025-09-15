import torch
import soundfile as sf
import numpy as np
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torchaudio
import math
from utils.file_utils import save_transcription_to_file
from configs.file_configs import MODEL_NAME

processor = WhisperProcessor.from_pretrained(MODEL_NAME)
model = WhisperForConditionalGeneration.from_pretrained(MODEL_NAME)
device = "cuda" if torch.cuda.is_available() else "cpu"

model = model.to(device)


def transcript_audio(audio_file_path: str) -> dict:
    speech, sample_rate = sf.read(audio_file_path)
    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(
            orig_freq=sample_rate, new_freq=16000)
        speech = resampler(torch.from_numpy(speech).float()).numpy()
        sample_rate = 16000

    if len(speech.shape) > 1:
        speech = np.mean(speech, axis=1)

    chunk_size = 30  # seconds chunk file
    samples_per_chunk = chunk_size*16000
    num_chunks = math.ceil(len(speech)/samples_per_chunk)
    chunks = [
        speech[i*samples_per_chunk: (i+1)*samples_per_chunk] for i in range(num_chunks)]

    transcriptions = []

    for chunk in chunks:
        if len(chunk) < samples_per_chunk:
            padding = np.zeros(samples_per_chunk-len(chunk))
            chunk = np.concatenate([chunk, padding])

        input_features = processor(
            chunk, sampling_rate=16000, return_tensors="pt").input_features.to(device)

        with torch.no_grad():
            generated_ids = model.generate(input_features=input_features)

        text = processor.batch_decode(
            generated_ids, skip_special_tokens=True)[0]
        transcriptions.append(text)

    full_transcription = " ".join(transcriptions)
    file_path = save_transcription_to_file(
        transcription_text=full_transcription)
    return {
        "transcription": full_transcription,
        "file_path": file_path
    }
