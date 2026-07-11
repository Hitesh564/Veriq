import asyncio
import io
import av
import riva.client
import traceback
from app.config import NVIDIA_API_KEY, WHISPER_API_KEY

def log_debug(msg: str):
    try:
        with open("c:/Users/hites/Desktop/AI Int/backend/voice_debug.log", "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception as e:
        print(f"Failed to write to debug log: {e}")

def webm_to_wav(webm_bytes: bytes) -> bytes:
    """
    Decodes input audio bytes (e.g. WebM/Opus) and resamples to 16kHz mono PCM WAV.
    Falls back to original bytes if decoding fails.
    """
    log_debug(f"--- webm_to_wav called with {len(webm_bytes)} bytes ---")
    try:
        input_file = io.BytesIO(webm_bytes)
        container = av.open(input_file)
        
        # Check if there is an audio stream
        if not container.streams.audio:
            log_debug("[WARNING] No audio stream found in input bytes.")
            return webm_bytes
            
        resampler = av.AudioResampler(
            format='s16',
            layout='mono',
            rate=16000
        )
        
        out_file = io.BytesIO()
        out_file.write(b'\x00' * 44)  # Placeholder for WAV header
        
        data_size = 0
        for frame in container.decode(audio=0):
            resampled_frames = resampler.resample(frame)
            for resampled_frame in resampled_frames:
                for plane in resampled_frame.planes:
                    chunk = bytes(plane)
                    out_file.write(chunk)
                    data_size += len(chunk)
                    
        log_debug(f"Decoded data size: {data_size} bytes")
        if data_size == 0:
            log_debug("[WARNING] Decoded data size is 0.")
            return webm_bytes
            
        # Go back to start and write WAV header
        out_file.seek(0)
        out_file.write(b'RIFF')
        out_file.write((36 + data_size).to_bytes(4, 'little'))
        out_file.write(b'WAVEfmt ')
        out_file.write((16).to_bytes(4, 'little'))
        out_file.write((1).to_bytes(2, 'little'))  # PCM
        out_file.write((1).to_bytes(2, 'little'))  # mono
        out_file.write((16000).to_bytes(4, 'little'))  # 16kHz
        out_file.write((32000).to_bytes(4, 'little'))  # byte rate (16000 * 2)
        out_file.write((2).to_bytes(2, 'little'))  # block align
        out_file.write((16).to_bytes(2, 'little'))  # bits
        out_file.write(b'data')
        out_file.write(data_size.to_bytes(4, 'little'))
        
        return out_file.getvalue()
    except Exception as e:
        err_msg = traceback.format_exc()
        log_debug(f"[WARNING] Failed to decode WebM to WAV using PyAV: {e}\n{err_msg}")
        return webm_bytes

def _transcribe_sync(audio_bytes: bytes, api_key: str) -> str:
    log_debug(f"--- _transcribe_sync called with {len(audio_bytes)} bytes ---")
    # 1. Convert input audio bytes to PCM WAV (16kHz mono)
    wav_bytes = webm_to_wav(audio_bytes)
    
    # 2. Determine encoding based on whether conversion succeeded
    if wav_bytes.startswith(b'RIFF'):
        encoding = riva.client.AudioEncoding.LINEAR_PCM
        log_debug(f"Encoding determined: LINEAR_PCM, size: {len(wav_bytes)}")
    else:
        encoding = riva.client.AudioEncoding.OGGOPUS
        log_debug(f"Encoding determined: OGGOPUS (fallback), size: {len(wav_bytes)}")
        
    auth = riva.client.Auth(
        uri="grpc.nvcf.nvidia.com:443",
        use_ssl=True,
        metadata_args=[
            ["authorization", f"Bearer {api_key}"],
            ["function-id", "b702f636-f60c-4a3d-a6f4-f3568c13bd7d"]
        ]
    )
    asr_service = riva.client.ASRService(auth)
    
    config = riva.client.RecognitionConfig(
        encoding=encoding,
        sample_rate_hertz=16000,
        language_code="en-US",
        max_alternatives=1,
        enable_automatic_punctuation=True
    )
    
    try:
        response = asr_service.offline_recognize(wav_bytes, config)
        if response.results and response.results[0].alternatives:
            transcript = response.results[0].alternatives[0].transcript
            log_debug(f"Transcription successful: '{transcript}'")
            return transcript
        log_debug("Transcription returned empty results.")
        return ""
    except Exception as e:
        err_msg = traceback.format_exc()
        log_debug(f"[ERROR] offline_recognize failed: {e}\n{err_msg}")
        raise e

async def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribes the given audio bytes using Whisper Large v3 on NVIDIA NIM gRPC.
    """
    api_key = NVIDIA_API_KEY or WHISPER_API_KEY
    if not api_key:
        raise ValueError("NVIDIA_API_KEY or WHISPER_API_KEY is not configured on the backend.")
        
    loop = asyncio.get_running_loop()
    try:
        # Run gRPC in thread pool to avoid blocking the FastAPI event loop
        return await loop.run_in_executor(None, _transcribe_sync, audio_bytes, api_key)
    except Exception as e:
        log_debug(f"[ERROR] transcribe_audio exception: {e}")
        raise e
