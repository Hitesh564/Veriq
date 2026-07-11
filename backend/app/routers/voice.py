import base64
import json
import asyncio
import io
import wave
import re
import time
import collections
import webrtcvad
import random
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from sqlmodel import Session, select
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.services.auth_service import auth_service

from app.config import GEMINI_API_KEY, WHISPER_API_KEY
from app.database import get_session, engine
from app.models.interview import Interview, Transcript, EvaluationReport
from app.routers.interview import (
    create_interview,
    get_evaluation_report,
    end_interview,
    process_interview_turn,
    InterviewCreate
)
from app.services.speech_to_text import speech_to_text_service
from app.services.transcript_normalizer import normalize_transcript
from app.services.tts_service import synthesize_text

router = APIRouter(tags=["voice"])


class VoiceTurnInput(BaseModel):
    session_id: str
    candidate_text: str
    audio_url: Optional[str] = None

class VoiceEndInput(BaseModel):
    session_id: str


@router.post("/api/interview/start")
def start_voice_interview(payload: InterviewCreate, db: Session = Depends(get_session)):
    """
    Initializes a new mock interview session and returns only the session_id.
    """
    try:
        interview = create_interview(payload, db)
        return {"session_id": interview.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize voice interview: {str(e)}")


@router.post("/api/interview/turn")
def voice_interview_turn(payload: VoiceTurnInput, db: Session = Depends(get_session)):
    """
    Processes a voice turn using candidate speech transcript and optional audio recording URL.
    Returns the interviewer's next response text.
    """
    try:
        res = process_interview_turn(
            id=payload.session_id,
            candidate_text=payload.candidate_text,
            session=db,
            audio_url=payload.audio_url
        )
        return {"interviewer_response": res["text"]}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing voice turn: {str(e)}")


@router.post("/api/interview/end")
def voice_interview_end(payload: VoiceEndInput, db: Session = Depends(get_session), user_id: str = Depends(auth_service.require_auth)):
    """
    Manually ends the interview and triggers evaluation report generation.
    """
    if not isinstance(user_id, str):
        user_id = "default"
    try:
        end_interview(payload.session_id, db, user_id=user_id)
        return {"status": "completed", "message": "Interview completed and evaluation triggered."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ending voice interview: {str(e)}")


@router.get("/api/evaluation/{session_id}")
def get_voice_evaluation(session_id: str, db: Session = Depends(get_session), user_id: str = Depends(auth_service.require_auth)):
    """
    Retrieves the final evaluation report for the voice session.
    """
    if not isinstance(user_id, str):
        user_id = "default"
    try:
        # Pass keyword args explicitly because the shared helper is also used as a FastAPI route.
        return get_evaluation_report(interview_id=session_id, user_id=user_id, db=db)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching evaluation: {str(e)}")


async def safe_send_json(websocket: WebSocket, data: dict):
    try:
        await websocket.send_json(data)
    except Exception:
        pass


def log_voice(msg: str):
    print(msg)
    try:
        with open("c:/Users/hites/Desktop/AI Int/backend/voice_debug.log", "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception as e:
        print(f"Failed to write to debug log: {e}")


def split_into_sentences(text: str) -> list[str]:
    # Common abbreviations to ignore
    abbreviations = {"mr", "ms", "mrs", "dr", "prof", "vs", "eg", "ie", "al", "etc", "js", "net", "env", "gov", "co", "org", "edu"}
    
    # Simple rule-based splitter
    sentences = []
    current = []
    words = text.split()
    
    for i, word in enumerate(words):
        current.append(word)
        # Check if the word ends with sentence-terminating punctuation
        if word and word[-1] in ".!?":
            # Strip punctuation to check if the root is an abbreviation
            clean = word.rstrip(".!?").lower()
            
            # Check if clean word matches known abbreviations
            if clean in abbreviations:
                continue
                
            # Check for decimals (e.g., "8.5")
            if re.match(r'^\d+\.\d*$', word) or re.match(r'^\d*\.\d+$', word):
                continue
                
            # Check if next word starts with lowercase, suggesting it's not a new sentence
            if i + 1 < len(words) and words[i + 1] and words[i + 1][0].islower():
                continue
                
            sentences.append(" ".join(current))
            current = []
            
    if current:
        sentences.append(" ".join(current))
        
    return sentences


class VoiceSessionState:
    def __init__(self, sample_rate: int = 16000, channels: int = 1, bytes_per_sample: int = 2):
        self.sample_rate = sample_rate
        self.channels = channels
        self.bytes_per_sample = bytes_per_sample
        self.bytes_per_second = sample_rate * channels * bytes_per_sample
        
        self.audio_buffer = bytearray()
        self.vad_accumulator = bytearray()
        self.pre_roll = collections.deque(maxlen=10) # 300ms pre-roll (10 frames of 30ms)
        
        self.is_speaking = False
        self.is_recording = False
        self.silence_duration_ms = 0
        
        self.speech_start_time = None
        self.speech_end_time = None
        self.recording_start_time = None
        self.recording_stop_time = None
        
        self.processing_lock = asyncio.Lock()
        self.last_filler = None
        
    def reset(self):
        self.audio_buffer.clear()
        self.vad_accumulator.clear()
        self.pre_roll.clear()
        self.is_speaking = False
        self.is_recording = False
        self.silence_duration_ms = 0
        self.speech_start_time = None
        self.speech_end_time = None
        self.recording_start_time = None
        self.recording_stop_time = None
        # Keep last_filler persistent across resets to avoid consecutive repeats

def is_valid_transcript(text: str) -> bool:
    if not text:
        return False
    text_stripped = text.strip()
    if not text_stripped:
        return False
        
    # Check if punctuation-only
    clean_text = re.sub(r'[^\w\s]', '', text_stripped).strip().lower()
    if not clean_text:
        return False
        
    # Non-speech sound filler words from ASR models
    non_speech_fillers = {
        "hmm", "uh", "um", "ah", "oh", "mhm", "cough", "coughing", 
        "throat", "clearing", "breathing", "sigh", "noise", "laughter",
        "snort", "gasp", "grunt", "groan"
    }
    
    # Common Whisper hallucinations triggered by silent audio/ambient noise
    whisper_hallucinations = {
        "thank you", "thank you for watching", "thank you very much", 
        "thank you so much", "thanks for watching", "thanks watching", 
        "please subscribe", "subscribe to my channel", "thanks", "bye", 
        "you", "go", "oh", "watching", "show", "thank you watch", 
        "thank you watching", "thanks for watching", "thank you so much for watching",
        "please subscribe to my channel", "subscribed", "subscribe", 
        "there is no audio", "no audio", "sound", "silence", "silent",
        "coughing", "clearing throat", "throat clearing", "screaming"
    }
    
    # Clean any trailing/leading whitespace and check exact match or if it only contains filler words
    if clean_text in whisper_hallucinations:
        return False
        
    # If the clean_text consists entirely of a repeating single word/phrase or single character
    words = clean_text.split()
    if not words:
        return False
        
    # If all words are in fillers/hallucinations
    if all(w in non_speech_fillers or w in whisper_hallucinations for w in words):
        return False
        
    # Extra check: if the transcription is extremely short (e.g. 1-2 words) and contains only generic fillers/sound terms
    if len(words) <= 2:
        fillers_short = {"yeah", "yes", "no", "ok", "okay", "hi", "hello", "hey", "right", "good"}
        if all(w in non_speech_fillers or w in whisper_hallucinations or w in fillers_short for w in words):
            return False
            
    return True

FILLERS = ["Okay.", "I see.", "Got it.", "Interesting.", "Understood.", "Right."]

PRE_SYNTHESIZED_FILLERS = {}

async def pre_synthesize_fillers():
    log_voice("[TTS] Pre-synthesizing conversational bridge fillers...")
    for f in FILLERS:
        try:
            audio = await synthesize_text(f)
            if audio:
                PRE_SYNTHESIZED_FILLERS[f] = base64.b64encode(audio).decode("utf-8")
        except Exception as e:
            log_voice(f"[ERROR] Failed to pre-synthesize filler '{f}': {e}")

def select_non_repeating_filler(last_filler: str = None) -> str:
    choices = [f for f in FILLERS if f != last_filler]
    return random.choice(choices) if choices else FILLERS[0]



@router.websocket("/api/voice/interview/{session_id}")
async def voice_interview_websocket(websocket: WebSocket, session_id: str, token: Optional[str] = None):
    """
    Main WebSocket voice integration combining Groq Whisper Large v3, Technical Terminology Normalization,
    LangGraph Agent, and EdgeTTS.
    """
    # Verify token
    try:
        user_id = auth_service.get_user_id(token) if token else None
        if not auth_service.IS_TESTING and not user_id:
            await websocket.accept()
            await websocket.close(code=4001, reason="Unauthorized WebSocket connection")
            return
    except Exception as e:
        try:
            await websocket.accept()
            await websocket.close(code=4001, reason=f"Authentication failed: {str(e)}")
        except:
            pass
        return

    await websocket.accept()
    log_voice(f"\n[WS] Connection Established for session: {session_id}")
    
    # 1. Fetch current question from DB to start the call
    with Session(engine) as db:
        interview = db.get(Interview, session_id)
        if not interview or (not auth_service.IS_TESTING and interview.user_id != user_id):
            log_voice(f"[WS] Connection rejected: Session {session_id} not found or forbidden")
            await websocket.close(code=1008, reason="Session not found or forbidden")
            return
        current_question = interview.current_question or "Hello, welcome to your mock interview. Let's begin."
        question_count = interview.question_count
        
    # 2. Verify API Keys
    if not WHISPER_API_KEY:
        log_voice("[WS] Connection rejected: GROQ_API_KEY / WHISPER_API_KEY is not configured on the backend.")
        await websocket.close(code=1011, reason="GROQ_API_KEY or WHISPER_API_KEY is not configured on the backend.")
        return
        
    try:
        # Pre-synthesize fillers asynchronously if they aren't pre-loaded yet
        if not PRE_SYNTHESIZED_FILLERS:
            asyncio.create_task(pre_synthesize_fillers())
            
        # Send connected status to client immediately to activate the UI
        await safe_send_json(websocket, {"type": "status", "status": "connected"})
        
        # Send initial greeting
        greeting_msg = f"Welcome back. Let's resume the interview. Here is the question: {current_question}" if question_count > 1 else current_question
        
        log_voice(f"[AGENT] Initial Greeting: {greeting_msg}")
        
        # Set state to speaking while greeting plays
        await safe_send_json(websocket, {"type": "status", "status": "speaking"})
        await safe_send_json(websocket, {
            "type": "transcript",
            "sender": "interviewer",
            "text": greeting_msg,
            # Reconnecting repeats the current question; it must not advance it.
            "question_count": question_count
        })
        
        # Synthesize and send initial greeting
        t_tts = asyncio.get_event_loop().time()
        greeting_audio = await synthesize_text(greeting_msg)
        tts_elapsed = int((asyncio.get_event_loop().time() - t_tts) * 1000)
        log_voice(f"[TTS] Greeting audio generated in {tts_elapsed} ms")
        
        greeting_b64 = base64.b64encode(greeting_audio).decode("utf-8")
        await safe_send_json(websocket, {
            "type": "assistant_response",
            "text": greeting_msg,
            "audio": greeting_b64
        })
        log_voice("[WS] Sent greeting assistant_response")
        
        # Voice Room Configurations
        ENDPOINT_MS = 1500
        POST_ROLL_MS = 200
        MAX_DURATION_SECONDS = 150
        
        # Instantiate VAD and Session State
        vad = webrtcvad.Vad(2) # Mode 2: Moderate noise suppression, higher voice sensitivity
        session = VoiceSessionState()
        
        # Helper to convert PCM to WAV
        def pcm_to_wav(pcm_bytes: bytes) -> bytes:
            out = io.BytesIO()
            with wave.open(out, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2) # 16-bit PCM (2 bytes)
                wav.setframerate(16000)
                wav.writeframes(pcm_bytes)
            return out.getvalue()
        
        async def process_turn(is_final: bool = True):
            async with session.processing_lock:
                if not session.audio_buffer:
                    log_voice("[WARNING] Empty audio buffer on process_turn.")
                    return
                
                # Capture stopped speaking timestamp
                user_stopped_speaking_ms = session.recording_stop_time or int(time.time() * 1000)
                
                # Calculate dynamic post-roll trimming
                bytes_per_second = session.bytes_per_second
                post_roll_trim_seconds = (ENDPOINT_MS - POST_ROLL_MS) / 1000.0
                trim_bytes = int(post_roll_trim_seconds * bytes_per_second)
                
                audio_len = len(session.audio_buffer)
                if audio_len > trim_bytes:
                    trimmed_payload = bytes(session.audio_buffer[:-trim_bytes])
                else:
                    trimmed_payload = bytes(session.audio_buffer)
                
                # Convert trimmed raw PCM to WAV
                turn_audio_bytes = pcm_to_wav(trimmed_payload)
                
                # Immediately reset the session state to prepare for next turn
                session.reset()
                
                log_voice(f"\n[WS] Processing final turn (audio WAV size: {len(turn_audio_bytes)} bytes)")
                
                # Update status to transcribing
                await safe_send_json(websocket, {"type": "status", "status": "transcribing"})
                
                t_start = time.perf_counter()
                
                try:
                    # 1. Transcribe the accumulated audio using Whisper
                    log_voice(f"[ASR] Starting Transcription (input size: {len(turn_audio_bytes)} bytes)")
                    t0 = time.perf_counter()
                    raw_transcript = await speech_to_text_service.transcribe(turn_audio_bytes)
                    groq_latency = int((time.perf_counter() - t0) * 1000)
                    
                    log_voice(f"[ASR] Groq Response received in {groq_latency} ms: '{raw_transcript}'")
                    
                    # Validate transcript locally
                    if not is_valid_transcript(raw_transcript):
                        log_voice(f"[WARNING] Invalid or filler-only speech detected: '{raw_transcript}'. Resetting to listen...")
                        session.reset()
                        await safe_send_json(websocket, {"type": "status", "status": "listening"})
                        return
                        
                    # Update status to thinking (Gemini and LangGraph processing)
                    await safe_send_json(websocket, {"type": "status", "status": "thinking"})
                    
                    # Define nested async helper for main pipeline processing (Normalizer + Agent)
                    async def run_pipeline():
                        # A. Normalization pass (run_gemini=False for speed!)
                        t_norm = time.perf_counter()
                        corrected_transcript = await normalize_transcript(raw_transcript, run_gemini=False)
                        norm_latency = int((time.perf_counter() - t_norm) * 1000)
                        log_voice(f"[NORMALIZER] Corrected transcript (dict-only): '{corrected_transcript}' in {norm_latency} ms")
                        
                        # Send corrected transcript to UI
                        await safe_send_json(websocket, {
                            "type": "corrected_transcript",
                            "text": corrected_transcript
                        })
                        
                        # Forward transcription to client history
                        await safe_send_json(websocket, {
                            "type": "transcript",
                            "sender": "candidate",
                            "text": corrected_transcript
                        })
                        
                        # B. Process turn through agent
                        log_voice("[AGENT] Sending to LangGraph")
                        t_agent = time.perf_counter()
                        response_question_count = None
                        with Session(engine) as db:
                            try:
                                res = process_interview_turn(
                                    id=session_id,
                                    candidate_text=corrected_transcript,
                                    session=db
                                )
                                interviewer_response = res["text"]
                                is_completed = (res["status"] == "completed")
                                response_question_count = res.get("question_count")
                            except Exception as e:
                                log_voice(f"[ERROR] process_interview_turn failed: {e}")
                                interviewer_response = "I encountered an error processing that. Could you please repeat?"
                                is_completed = False
                        gemini_latency = int((time.perf_counter() - t_agent) * 1000)
                        log_voice(f"[AGENT] Gemini Response received in {gemini_latency} ms: '{interviewer_response}'")
                        
                        # Send interviewer response text to UI
                        await safe_send_json(websocket, {
                            "type": "transcript",
                            "sender": "interviewer",
                            "text": interviewer_response,
                            "question_count": response_question_count
                        })
                        
                        return {
                            "interviewer_response": interviewer_response,
                            "is_completed": is_completed,
                            "response_question_count": response_question_count,
                            "norm_latency": norm_latency,
                            "gemini_latency": gemini_latency
                        }
                    
                    # Launch pipeline task concurrently
                    pipeline_task = asyncio.create_task(run_pipeline())
                    
                    # Race pipeline task with 800ms threshold
                    done, pending = await asyncio.wait([pipeline_task], timeout=0.8)
                    
                    used_filler = False
                    if pipeline_task in done:
                        # Fast Turn: Pipeline finished within 800ms. Send directly.
                        result = pipeline_task.result()
                        log_voice("[FLOW] Fast turn: skipped conversational bridge filler.")
                    else:
                        # Slow Turn: Exceeded 800ms. Play pre-synthesized bridge filler phrase first.
                        used_filler = True
                        filler_text = select_non_repeating_filler(session.last_filler)
                        session.last_filler = filler_text
                        log_voice(f"[FLOW] Slow turn: streaming pre-synthesized transition filler phrase: '{filler_text}'")
                        
                        # Retrieve pre-synthesized filler Base64 string instantly
                        filler_b64 = PRE_SYNTHESIZED_FILLERS.get(filler_text)
                        
                        if filler_b64:
                            await safe_send_json(websocket, {"type": "status", "status": "speaking"})
                            await safe_send_json(websocket, {
                                "type": "assistant_response",
                                "text": filler_text,
                                "audio": filler_b64,
                                "chunk_index": 0,
                                "is_last_chunk": False,
                                "is_stream": True,
                                "user_stopped_speaking_ms": user_stopped_speaking_ms
                            })
                            
                        # Now await the pipeline task completion
                        result = await pipeline_task
                        
                    # Extract pipeline outputs
                    interviewer_response = result["interviewer_response"]
                    is_completed = result["is_completed"]
                    response_question_count = result["response_question_count"]
                    
                    # C. Split response into sentences
                    sentences = split_into_sentences(interviewer_response)
                    log_voice(f"[TTS] Split response into {len(sentences)} sentences: {sentences}")
                    
                    # Stream the actual question chunks
                    start_index = 1 if used_filler else 0
                    
                    # D. Launch all EdgeTTS synthesis tasks concurrently in the background
                    log_voice("[TTS] Launching concurrent EdgeTTS background tasks...")
                    tts_tasks = [asyncio.create_task(synthesize_text(s)) for s in sentences]
                    
                    # E. Await and stream audio chunks sequentially in-order
                    tts_first_chunk_latency = 0
                    for idx, task in enumerate(tts_tasks):
                        try:
                            t_c_start = time.perf_counter()
                            audio_bytes = await task
                            chunk_latency = int((time.perf_counter() - t_c_start) * 1000)
                            
                            if idx == 0:
                                tts_first_chunk_latency = chunk_latency
                                log_voice(f"[TTS] First chunk synthesized/retrieved in {tts_first_chunk_latency} ms")
                                
                            if not audio_bytes:
                                continue
                                
                            chunk_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                            await safe_send_json(websocket, {"type": "status", "status": "speaking"})
                            
                            total_latency = int((time.perf_counter() - t_start) * 1000)
                            await safe_send_json(websocket, {
                                "type": "assistant_response",
                                "text": sentences[idx],
                                "audio": chunk_b64,
                                "chunk_index": start_index + idx,
                                "is_last_chunk": (idx == len(tts_tasks) - 1),
                                "is_stream": True,
                                "user_stopped_speaking_ms": user_stopped_speaking_ms,
                                "latency": {
                                    "groq": groq_latency,
                                    "gemini": result["gemini_latency"],
                                    "tts": chunk_latency,
                                    "tts_first_chunk": tts_first_chunk_latency,
                                    "total": total_latency
                                }
                            })
                        except Exception as chunk_err:
                            log_voice(f"[ERROR] Failed to synthesize chunk {idx}: {chunk_err}")
                            if idx == len(tts_tasks) - 1:
                                await safe_send_json(websocket, {
                                    "type": "assistant_response",
                                    "text": "",
                                    "audio": "",
                                    "chunk_index": start_index + idx,
                                    "is_last_chunk": True,
                                    "is_stream": True,
                                    "user_stopped_speaking_ms": user_stopped_speaking_ms,
                                    "latency": {"groq": 0, "gemini": 0, "tts": 0, "total": 0}
                                })
                                
                    # Profile timing logs
                    total_latency = int((time.perf_counter() - t_start) * 1000)
                    log_voice(f"""
======================================================
           VOICE TURN LATENCY SCORECARD
======================================================
ASR (Whisper)      : {groq_latency} ms
Normalization      : {result["norm_latency"]} ms
LLM (LangGraph)    : {result["gemini_latency"]} ms
TTS (First Chunk)  : {tts_first_chunk_latency} ms
Used Filler        : {used_filler}
Total Turn Latency : {total_latency} ms
======================================================
""")
                    
                    if is_completed:
                        log_voice("[WS] Session completed. Sending session_completed.")
                        await safe_send_json(websocket, {"type": "session_completed"})
                        
                except Exception as e:
                    log_voice(f"[ERROR] Error processing turn: {e}")
                    await safe_send_json(websocket, {
                        "type": "error",
                        "message": f"An error occurred while transcribing your answer: {str(e)}"
                    })
                    session.reset()
                    await safe_send_json(websocket, {"type": "status", "status": "listening"})

        # Read loop
        while True:
            data = await websocket.receive()
            log_voice(f"[WS] Received ASGI event keys: {list(data.keys())} - type: {data.get('type')}")
            if data.get("type") == "websocket.disconnect":
                raise WebSocketDisconnect(data.get("code", 1000))
                
            if "bytes" in data:
                if session.is_recording:
                    log_voice(f"[WS] Received binary chunk of size {len(data['bytes'])} bytes")
                    # Accumulate incoming raw PCM bytes
                    session.vad_accumulator.extend(data["bytes"])
                    
                    # Process complete 30ms (960 bytes) frames
                    while len(session.vad_accumulator) >= 960:
                        frame = bytes(session.vad_accumulator[:960])
                        del session.vad_accumulator[:960]
                        
                        try:
                            is_speech_frame = vad.is_speech(frame, 16000)
                        except Exception as e:
                            log_voice(f"[VAD ERROR] Frame verification failed: {e}")
                            is_speech_frame = False
                            
                        if is_speech_frame:
                            if not session.is_speaking:
                                session.is_speaking = True
                                session.speech_start_time = time.perf_counter()
                                log_voice("[VAD] Speech Detected (User started speaking)")
                                
                                # Add the pre-roll to prevent cutting consonants
                                session.audio_buffer.extend(b"".join(session.pre_roll))
                                session.pre_roll.clear()
                            
                            session.silence_duration_ms = 0
                            session.audio_buffer.extend(frame)
                        else:
                            if session.is_speaking:
                                session.audio_buffer.extend(frame)
                                session.silence_duration_ms += 30
                                
                                 # Check silence endpoint (1.2 seconds)
                                if session.silence_duration_ms >= ENDPOINT_MS:
                                    session.is_speaking = False
                                    session.is_recording = False
                                    session.speech_end_time = time.perf_counter()
                                    session.recording_stop_time = int(time.time() * 1000)
                                    vad_elapsed = int((session.speech_end_time - session.speech_start_time) * 1000)
                                    log_voice(f"[VAD] Silence Endpoint Triggered (Silence >= {ENDPOINT_MS}ms). User spoke for {vad_elapsed} ms.")
                                    
                                    # Trigger final transcription and LangGraph turn
                                    asyncio.create_task(process_turn(is_final=True))
                                    break
                            else:
                                # Not speaking yet: keep a small pre-roll buffer
                                session.pre_roll.append(frame)
                                
                        # Check if answer duration exceeds maximum cap (150s)
                        if len(session.audio_buffer) >= (MAX_DURATION_SECONDS * session.bytes_per_second):
                            log_voice(f"[VAD] Hard cap reached: Answer duration exceeded {MAX_DURATION_SECONDS}s. Auto-submitting...")
                            session.is_speaking = False
                            session.is_recording = False
                            session.speech_end_time = time.perf_counter()
                            session.recording_stop_time = int(time.time() * 1000)
                            asyncio.create_task(process_turn(is_final=True))
                            break
                            
            elif "text" in data:
                try:
                    msg = json.loads(data["text"])
                    msg_type = msg.get("type")
                    if msg_type == "start_recording":
                        session.reset()
                        session.is_recording = True
                        session.recording_start_time = time.perf_counter()
                        log_voice("[WS] Recording started by client. Cleared VAD state.")
                    elif msg_type == "submit_answer":
                        # Legacy manual trigger, stop recording and force process
                        session.is_recording = False
                        session.is_speaking = False
                        session.recording_stop_time = int(time.time() * 1000)
                        asyncio.create_task(process_turn(is_final=True))
                except json.JSONDecodeError:
                    pass
                
    except WebSocketDisconnect:
        log_voice(f"[WS] WebSocket disconnected for session: {session_id}")
    except Exception as e:
        log_voice(f"[WS] Error in voice_interview_websocket: {e}")
        try:
            await websocket.close(code=1011, reason=f"Connection error: {str(e)}")
        except Exception:
            pass
