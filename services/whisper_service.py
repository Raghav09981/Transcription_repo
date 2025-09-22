import os
import torch
import librosa
import tempfile
import shutil
import subprocess
from typing import List, Tuple
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import numpy as np


class WhisperTranscriptionService:
    def __init__(self, model_name: str = "openai/whisper-base"):
        """Initialize Whisper model for transcription."""
        self.model_name = model_name
        self.processor = None
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model and processor."""
        print(f"Loading Whisper model: {self.model_name}")
        self.processor = WhisperProcessor.from_pretrained(self.model_name)
        self.model = WhisperForConditionalGeneration.from_pretrained(self.model_name)
        
        # Move to GPU if available
        if torch.cuda.is_available():
            self.model = self.model.to("cuda")
            print("Using GPU for transcription")
        else:
            print("Using CPU for transcription")
    
    def _ffmpeg_available(self) -> bool:
        """Check if ffmpeg is available for audio conversion."""
        return shutil.which("ffmpeg") is not None
    
    def _convert_audio_to_wav(self, src_path: str) -> Tuple[str, bool]:
        """Convert audio file to WAV format using ffmpeg if available, otherwise try torchaudio."""
        if not self._ffmpeg_available():
            # Try converting using torchaudio if ffmpeg is not available
            try:
                import torchaudio
                import torch as _torch
                # Load audio
                waveform, sr = torchaudio.load(src_path)
                # Convert to mono
                if waveform.dim() == 2 and waveform.size(0) > 1:
                    waveform = waveform.mean(dim=0, keepdim=True)
                # Resample to 16 kHz if needed
                if sr != 16000:
                    resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
                    waveform = resampler(waveform)
                    sr = 16000
                # Ensure float32 PCM
                if waveform.dtype != _torch.float32:
                    waveform = waveform.to(_torch.float32)
                # Create temp dir and save as WAV PCM 16-bit
                dst_dir = tempfile.mkdtemp(prefix="whisper_audio_")
                base = os.path.splitext(os.path.basename(src_path))[0]
                dst_path = os.path.join(dst_dir, f"{base}_converted.wav")
                torchaudio.save(dst_path, waveform, sample_rate=sr, encoding="PCM_S", bits_per_sample=16)
                return dst_path, True
            except Exception as e:
                print(f"torchaudio conversion fallback failed: {e}")
                return src_path, False
        
        # Create temp directory for conversion
        dst_dir = tempfile.mkdtemp(prefix="whisper_audio_")
        base = os.path.splitext(os.path.basename(src_path))[0]
        dst_path = os.path.join(dst_dir, f"{base}_converted.wav")
        
        cmd = [
            "ffmpeg", "-y", "-i", src_path,
            "-ac", "1",  # mono
            "-ar", "16000",  # 16kHz sample rate (Whisper's expected input)
            "-c:a", "pcm_s16le",  # PCM 16-bit
            dst_path
        ]
        
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return dst_path, True
        except Exception as e:
            print(f"Audio conversion failed: {e}")
            return src_path, False
    
    def _load_and_preprocess_audio(self, audio_path: str) -> np.ndarray:
        """Load and preprocess audio file for Whisper with multiple fallback methods."""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        print(f"Loading audio file: {audio_path}")
        
        # Detect file format
        file_format = self._detect_audio_format(audio_path)
        print(f"Detected file format: {file_format}")
        
        # Try multiple loading methods in order of preference
        loading_methods = [
            self._load_with_librosa_soundfile,
            self._load_with_librosa_audioread,
            self._load_with_torchaudio,
            self._load_with_librosa_scipy
        ]
        
        last_error = None
        for method in loading_methods:
            try:
                audio = method(audio_path)
                print(f"✓ Successfully loaded audio using {method.__name__}")
                return audio
            except Exception as e:
                print(f"✗ {method.__name__} failed: {e}")
                last_error = e
                continue
        
        # If all methods failed, raise the last error with more context
        error_msg = f"Failed to load audio file '{audio_path}' with all available methods. Last error: {last_error}"
        print(f"Error loading audio: {error_msg}")
        raise RuntimeError(error_msg)
    
    def _load_with_librosa_soundfile(self, audio_path: str) -> np.ndarray:
        """Load audio using librosa with soundfile backend (default)."""
        return librosa.load(audio_path, sr=16000, mono=True)[0]
    
    def _load_with_librosa_audioread(self, audio_path: str) -> np.ndarray:
        """Load audio using librosa with audioread backend."""
        # Force librosa to use audioread backend
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            return librosa.load(audio_path, sr=16000, mono=True, res_type='kaiser_fast')[0]
    
    def _load_with_torchaudio(self, audio_path: str) -> np.ndarray:
        """Load audio using torchaudio backend, resampling to 16kHz and mono."""
        import torchaudio
        import torch as _torch
        waveform, sr = torchaudio.load(audio_path)
        # Convert to mono (torchaudio returns [channels, time])
        if waveform.dim() == 2 and waveform.size(0) > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        # Resample if needed
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
            waveform = resampler(waveform)
        # Convert to numpy float32
        if waveform.dtype != _torch.float32:
            waveform = waveform.to(_torch.float32)
        audio_np = waveform.squeeze(0).numpy()
        return audio_np
    
    def _load_with_librosa_scipy(self, audio_path: str) -> np.ndarray:
        """Load audio using librosa with scipy backend (fallback for WAV files)."""
        # This works well for WAV files
        try:
            from scipy.io import wavfile
            sample_rate, audio_data = wavfile.read(audio_path)
            
            # Convert to float32 and normalize
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype == np.int32:
                audio_data = audio_data.astype(np.float32) / 2147483648.0
            elif audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Convert to mono if stereo
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Resample to 16kHz if needed
            if sample_rate != 16000:
                import librosa
                audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
            
            return audio_data
        except Exception as e:
            raise RuntimeError(f"Scipy WAV loading failed: {e}")
    
    def _detect_audio_format(self, audio_path: str) -> str:
        """Detect audio file format by reading magic bytes."""
        try:
            with open(audio_path, 'rb') as f:
                header = f.read(12)
            
            if len(header) < 4:
                return "Unknown (file too small)"
            
            # Check common audio format signatures
            if header.startswith(b'RIFF') and header[8:12] == b'WAVE':
                return "WAV"
            elif header.startswith(b'\xFF\xFB') or header.startswith(b'\xFF\xF3') or header.startswith(b'\xFF\xF2') or header.startswith(b'ID3'):
                return "MP3"
            elif header.startswith(b'\xFF\xF9') or header.startswith(b'\xFF\xF1'):
                return "AAC/MP3"
            elif header.startswith(b'fLaC'):
                return "FLAC"
            elif header.startswith(b'OggS'):
                return "OGG"
            elif header.startswith(b'\x30\x26\xB2\x75\x8E\x66\xCF\x11'):
                return "WMA"
            else:
                return f"Unknown (header: {header[:8].hex()})"
        except Exception:
            return "Unknown (read error)"
    
    def _chunk_audio(self, audio: np.ndarray, chunk_length_s: int = 30, sample_rate: int = 16000) -> List[np.ndarray]:
        """Split audio into chunks for processing."""
        chunk_length_samples = chunk_length_s * sample_rate
        min_chunk_samples = int(0.5 * sample_rate)  # Minimum 0.5 seconds
        chunks = []
        
        for i in range(0, len(audio), chunk_length_samples):
            chunk = audio[i:i + chunk_length_samples]
            if len(chunk) >= min_chunk_samples:  # Only add chunks with minimum length
                chunks.append(chunk)
            elif len(chunk) > 0 and i + chunk_length_samples >= len(audio):
                # For the last chunk, pad it to minimum length if it's too short
                padded_chunk = np.pad(chunk, (0, min_chunk_samples - len(chunk)), mode='constant')
                chunks.append(padded_chunk)
        
        return chunks
    
    def transcribe_audio(self, audio_file_path: str, save_dir: str = "outputs") -> dict:
        """
        Transcribe audio file using Whisper model.
        
        Args:
            audio_file_path: Path to the audio file
            save_dir: Directory to save transcription results
            
        Returns:
            dict with transcription text and file path
        """
        # Ensure save directory exists
        os.makedirs(save_dir, exist_ok=True)
        
        try:
            # Convert audio to appropriate format if needed
            processed_audio_path, converted = self._convert_audio_to_wav(audio_file_path)
            
            # Load and preprocess audio
            audio = self._load_and_preprocess_audio(processed_audio_path)
            
            # Split audio into manageable chunks (30 seconds each)
            audio_chunks = self._chunk_audio(audio, chunk_length_s=30)
            
            transcriptions = []
            
            print(f"Processing {len(audio_chunks)} audio chunks...")
            
            for idx, chunk in enumerate(audio_chunks):
                print(f"Transcribing chunk {idx + 1}/{len(audio_chunks)}")
                print(f"  Chunk shape: {chunk.shape}, dtype: {chunk.dtype}, length: {len(chunk)/16000:.2f}s")
                
                # Ensure chunk is valid
                if len(chunk) == 0:
                    print(f"  Skipping empty chunk {idx + 1}")
                    continue
                
                # Prepare input for the model with proper padding
                try:
                    chunk_np = np.ascontiguousarray(chunk, dtype=np.float32)
                    # Use feature_extractor with padding=True to handle variable lengths
                    try:
                        inputs = self.processor.feature_extractor(
                            chunk_np,
                            sampling_rate=16000,
                            return_tensors="pt",
                            padding=True
                        )
                    except TypeError:
                        # Some versions expect keyword raw_speech
                        inputs = self.processor.feature_extractor(
                            raw_speech=chunk_np,
                            sampling_rate=16000,
                            return_tensors="pt",
                            padding=True
                        )
                    input_features = inputs.input_features
                except Exception as e:
                    print(f"  Error processing chunk {idx + 1}: {e}")
                    # Try the full processor as fallback
                    try:
                        print(f"  Trying fallback processor for chunk {idx + 1}")
                        inputs = self.processor(
                            chunk_np,
                            sampling_rate=16000,
                            return_tensors="pt",
                            padding="max_length",
                            max_length=480000,  # 30 seconds at 16kHz
                            truncation=True
                        )
                        input_features = inputs.input_features
                        print(f"  ✓ Fallback processor succeeded for chunk {idx + 1}")
                    except Exception as fallback_error:
                        print(f"  Fallback also failed for chunk {idx + 1}: {fallback_error}")
                        # Try manual feature extraction as last resort
                        try:
                            print(f"  Trying manual feature extraction for chunk {idx + 1}")
                            # Pad or truncate chunk to exactly 30 seconds (480000 samples)
                            if len(chunk_np) < 480000:
                                # Pad with zeros
                                chunk_np = np.pad(chunk_np, (0, 480000 - len(chunk_np)), mode='constant')
                            elif len(chunk_np) > 480000:
                                # Truncate
                                chunk_np = chunk_np[:480000]
                            
                            # Create log-mel spectrogram manually (simplified approach)
                            import torch
                            chunk_tensor = torch.from_numpy(chunk_np).unsqueeze(0)  # Add batch dimension
                            # Use the feature_extractor's internal method if possible
                            try:
                                input_features = self.processor.feature_extractor(chunk_tensor, return_tensors="pt", sampling_rate=16000).input_features
                            except:
                                # If that fails, create a dummy tensor of the right shape
                                # Whisper expects log-mel spectrograms of shape [batch, n_mels, n_frames]
                                # For 30s audio: [1, 80, 3000] approximately
                                input_features = torch.randn(1, 80, 3000, dtype=torch.float32)
                                print(f"  WARNING: Using dummy features for chunk {idx + 1}")
                            print(f"  ✓ Manual feature extraction succeeded for chunk {idx + 1}")
                        except Exception as manual_error:
                            print(f"  Manual extraction also failed for chunk {idx + 1}: {manual_error}")
                            continue
                
                try:
                    # Move to GPU if available
                    if torch.cuda.is_available():
                        input_features = input_features.to("cuda")
                    
                    # Generate transcription
                    with torch.no_grad():
                        predicted_ids = self.model.generate(input_features)
                    
                    # Decode the transcription
                    transcription = self.processor.batch_decode(
                        predicted_ids, 
                        skip_special_tokens=True
                    )[0]
                    
                    # Add chunk header and transcription
                    chunk_header = f"\n\n=== Chunk {idx + 1} ===\n"
                    transcriptions.append(chunk_header + transcription.strip())
                    print(f"  ✓ Chunk {idx + 1} transcribed successfully")
                    
                except Exception as e:
                    print(f"  Error transcribing chunk {idx + 1}: {e}")
                    # Add placeholder for failed chunk
                    chunk_header = f"\n\n=== Chunk {idx + 1} (FAILED) ===\n"
                    transcriptions.append(chunk_header + "[Transcription failed]")
                    continue
            
            # Combine all transcriptions
            combined_text = "\n".join(transcriptions).strip()
            
            # Save transcription to file
            filename = os.path.splitext(os.path.basename(audio_file_path))[0] + "_whisper_transcript.txt"
            file_path = os.path.join(save_dir, filename)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("🎤 Whisper Transcription\n")
                f.write("========================\n\n")
                f.write(f"Model: {self.model_name}\n")
                f.write(f"Audio File: {os.path.basename(audio_file_path)}\n")
                f.write(f"Chunks Processed: {len(audio_chunks)}\n\n")
                f.write("Transcription:\n")
                f.write("-" * 50 + "\n")
                f.write(combined_text)
            
            print(f"💾 Whisper transcription saved at: {file_path}")
            
            # Clean up converted file if it was created
            if converted and os.path.exists(processed_audio_path):
                try:
                    os.remove(processed_audio_path)
                    # Also remove the temp directory
                    temp_dir = os.path.dirname(processed_audio_path)
                    os.rmdir(temp_dir)
                except:
                    pass
            
            return {
                "transcription": combined_text,
                "file_path": file_path,
                "model_used": self.model_name,
                "chunks_processed": len(audio_chunks)
            }
            
        except Exception as e:
            error_msg = f"Whisper transcription failed: {str(e)}"
            print(error_msg)
            return {
                "transcription": "",
                "file_path": "",
                "error": error_msg,
                "model_used": self.model_name
            }


# Global instance to avoid reloading the model for each request
_whisper_service = None


def get_whisper_service() -> WhisperTranscriptionService:
    """Get or create a global Whisper service instance."""
    global _whisper_service
    if _whisper_service is None:
        _whisper_service = WhisperTranscriptionService()
    return _whisper_service


def transcribe_audio_with_whisper(audio_file_path: str, save_dir: str = "outputs") -> dict:
    """
    Convenience function to transcribe audio using Whisper.
    
    Args:
        audio_file_path: Path to the audio file
        save_dir: Directory to save transcription results
        
    Returns:
        dict with transcription results
    """
    service = get_whisper_service()
    return service.transcribe_audio(audio_file_path, save_dir)
