import io
from abc import ABC, abstractmethod
import edge_tts

class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        pass

class EdgeTTSProvider(TTSProvider):
    def __init__(self, voice: str = "en-US-AvaNeural"):
        self.voice = voice

    async def synthesize(self, text: str) -> bytes:
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            audio_data = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.write(chunk["data"])
            return audio_data.getvalue()
        except Exception as e:
            print(f"EdgeTTS synthesis failed: {e}")
            return b""

class GeminiTTSProvider(TTSProvider):
    async def synthesize(self, text: str) -> bytes:
        # Stub for future integration if needed
        return b""

# Default provider instance
_default_provider = EdgeTTSProvider()

async def synthesize_text(text: str) -> bytes:
    """
    Synthesizes text into MP3 bytes using the default provider.
    """
    return await _default_provider.synthesize(text)
