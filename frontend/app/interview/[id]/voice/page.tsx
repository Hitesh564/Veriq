"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "../../../context/AuthContext";
import { supabase } from "../../../utils/supabaseClient";

interface ChatMessage {
  sender: "interviewer" | "candidate";
  text: string;
  timestamp: Date;
}

export default function VoiceInterviewRoom() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { user } = useAuth();

  const isAccessTokenValid = (token?: string): token is string => {
    return typeof token === "string" && token.split(".").length === 3;
  };

  const getAuthSession = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session || !isAccessTokenValid(session.access_token)) {
      setError("Session expired or invalid. Please sign in again.");
      await supabase.auth.signOut();
      return null;
    }
    return session;
  };


  // States
  const [role, setRole] = useState("Initializing Coach...");
  const [difficulty, setDifficulty] = useState("");
  const [questionCount, setQuestionCount] = useState(0);
  const [maxQuestionCount, setMaxQuestionCount] = useState(5);
  const [status, setStatus] = useState("in_progress");
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [phase, setPhase] = useState("INTRODUCTION");

  type VoiceState = 
    | "DISCONNECTED"
    | "CONNECTING"
    | "AI_SPEAKING"
    | "LISTENING"
    | "TRANSCRIBING"
    | "THINKING"
    | "ENDED";

  const [callStatus, setCallStatus] = useState<"inactive" | "connecting" | "active" | "ended">("inactive");
  const [speakingStatus, setSpeakingStatus] = useState<"silent" | "listening" | "speaking" | "processing">("silent");
  const [voiceState, setVoiceState] = useState<VoiceState>("DISCONNECTED");
  const [isMuted, setIsMuted] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [liveTranscript, setLiveTranscript] = useState("");
  const [correctedTranscript, setCorrectedTranscript] = useState("");
  const [error, setError] = useState("");
  
  // Timer state
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Sync refs for animation frame loop
  const speakingStatusRef = useRef(speakingStatus);
  const callStatusRef = useRef(callStatus);
  const voiceStateRef = useRef<VoiceState>(voiceState);
  const hasSpokenRef = useRef(false);

  useEffect(() => {
    speakingStatusRef.current = speakingStatus;
  }, [speakingStatus]);

  useEffect(() => {
    callStatusRef.current = callStatus;
  }, [callStatus]);

  useEffect(() => {
    voiceStateRef.current = voiceState;
  }, [voiceState]);

  const transitionTo = (newState: VoiceState) => {
    console.log(`[STATE TRANSITION] ${voiceStateRef.current} -> ${newState}`);
    setVoiceState(newState);
    
    if (newState === "LISTENING") {
      hasSpokenRef.current = false;
    }
    
    // Sync callStatus
    if (newState === "DISCONNECTED") {
      setCallStatus("inactive");
    } else if (newState === "CONNECTING") {
      setCallStatus("connecting");
    } else if (newState === "ENDED") {
      setCallStatus("ended");
    } else {
      setCallStatus("active");
    }

    // Sync speakingStatus
    if (newState === "DISCONNECTED" || newState === "CONNECTING" || newState === "ENDED") {
      setSpeakingStatus("silent");
    } else if (newState === "AI_SPEAKING") {
      setSpeakingStatus("speaking");
    } else if (newState === "LISTENING") {
      setSpeakingStatus("listening");
    } else if (newState === "TRANSCRIBING" || newState === "THINKING") {
      setSpeakingStatus("processing");
    }
  };

  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const geminiWsRef = useRef<WebSocket | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const activeAudioRef = useRef<HTMLAudioElement | null>(null);
  const audioQueueRef = useRef<{ 
    audio: HTMLAudioElement; 
    isLastChunk: boolean;
    chunkIndex: number;
    userStoppedSpeakingMs: number;
    latency: any;
  }[]>([]);
  const isPlayingRef = useRef<boolean>(false);
  
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioWorkletNodeRef = useRef<AudioWorkletNode | null>(null);
  const audioSourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const animationFrameIdRef = useRef<number | null>(null);

  // Scroll to bottom of message list
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, liveTranscript, correctedTranscript]);

  useEffect(() => {
    if (!id || !user) return;

    const initSession = async () => {
      try {
        const authSession = await getAuthSession();
        if (!authSession) return;

        const res = await fetch(`http://127.0.0.1:8000/api/v1/interviews/${id}`, {
          headers: {
            "Authorization": `Bearer ${authSession.access_token}`
          }
        });

        if (!res.ok) {
          if (res.status === 401 || res.status === 403) {
            setError("Authentication failed. Please log in again.");
            await supabase.auth.signOut();
          }
          const body = await res.text();
          throw new Error(`Could not fetch interview session: ${res.status} ${body}`);
        }

        const data = await res.json();
        setRole(data.role);
        setDifficulty(data.difficulty);
        setQuestionCount(data.question_count);
        setMaxQuestionCount(data.max_question_count);
        setStatus(data.status);
        setCurrentQuestion(data.current_question || "");
        setPhase(data.interview_phase || "INTRODUCTION");

        const history: ChatMessage[] = data.transcripts.map((t: any) => ({
          sender: t.sender,
          text: t.text,
          timestamp: new Date(t.timestamp)
        }));
        setMessages(history);

        if (data.status === "completed") {
          router.push(`/transcript/${id}`);
        }
      } catch (err: any) {
        setError(err.message || "Failed to initialize voice room");
      }
    };

    initSession();
  }, [id, user]);

  // Duration Timer
  useEffect(() => {
    if (callStatus !== "active") return;
    const interval = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [callStatus]);

  // Clean up connections on component unmount
  useEffect(() => {
    return () => {
      // React Strict Mode runs effect cleanup once during the development
      // mount check. Release resources without presenting a never-started call
      // as "Ended".
      stopGeminiCall(false);
    };
  }, []);

  const formatTime = (totalSecs: number) => {
    const mins = Math.floor(totalSecs / 60);
    const secs = totalSecs % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };



  const stopAllPlayback = () => {
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    if (activeAudioRef.current) {
      try {
        activeAudioRef.current.pause();
      } catch (e) {}
      activeAudioRef.current = null;
    }
  };

  const playNextChunk = () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      activeAudioRef.current = null;
      if (voiceStateRef.current !== "THINKING" && voiceStateRef.current !== "TRANSCRIBING") {
        transitionTo("LISTENING");
      }
      return;
    }

    isPlayingRef.current = true;
    const { audio, isLastChunk, chunkIndex, latency, userStoppedSpeakingMs } = audioQueueRef.current.shift()!;
    activeAudioRef.current = audio;
    transitionTo("AI_SPEAKING");

    audio.onended = () => {
      if (activeAudioRef.current === audio) {
        if (isLastChunk && audioQueueRef.current.length === 0) {
          activeAudioRef.current = null;
          isPlayingRef.current = false;
          transitionTo("LISTENING");
        } else {
          playNextChunk();
        }
      }
    };

    const playStartTime = Date.now();
    audio.play().then(() => {
      // Calculate Time-to-First-Audio (TTFA) on first chunk play start
      if (chunkIndex === 0 && userStoppedSpeakingMs) {
        const ttfPlay = playStartTime - userStoppedSpeakingMs;
        const totalTurn = Date.now() - userStoppedSpeakingMs;
        
        const groqLatency = latency?.groq ?? 0;
        const geminiLatency = latency?.gemini ?? 0;
        const ttsFirstChunkLatency = latency?.tts_first_chunk ?? 0;
        
        console.log(`
╔════════════════════════════════════════════════════════════════════╗
║             AI PILOT turn performance scorecard                    ║
╠════════════════════════════════════════════════════════════════════╣
║ ASR (Groq Transcription) : ${groqLatency.toString().padStart(5)} ms [Target: < 700ms]   ${groqLatency < 700 ? "✅" : "❌"} ║
║ LangGraph (Gemini LLM)   : ${geminiLatency.toString().padStart(5)} ms [Target: < 1200ms]  ${geminiLatency < 1200 ? "✅" : "❌"} ║
║ TTS First Chunk Synthesis: ${ttsFirstChunkLatency.toString().padStart(5)} ms [Target: < 300ms]   ${ttsFirstChunkLatency < 300 ? "✅" : "❌"} ║
║ Time-to-First-Audio(TTFA): ${ttfPlay.toString().padStart(5)} ms [Target: < 2.0s]    ${ttfPlay < 2000 ? "✅" : "❌"} ║
║ Total Turn Latency       : ${totalTurn.toString().padStart(5)} ms [Target: < 3.0s]    ${totalTurn < 3000 ? "✅" : "❌"} ║
╚════════════════════════════════════════════════════════════════════╝
`);
      }
    }).catch((err) => {
      console.error("Audio playback chunk error:", err);
      playNextChunk();
    });
  };

  const stopGeminiCall = (markAsEnded = true) => {
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach((track) => track.stop());
      audioStreamRef.current = null;
    }
    stopMediaRecording();
    if (animationFrameIdRef.current !== null) {
      cancelAnimationFrame(animationFrameIdRef.current);
      animationFrameIdRef.current = null;
    }
    if (audioContextRef.current) {
      try {
        audioContextRef.current.close();
      } catch (e) {}
      audioContextRef.current = null;
    }
    
    stopAllPlayback();
    if (geminiWsRef.current) {
      geminiWsRef.current.close();
      geminiWsRef.current = null;
    }
    if (markAsEnded) {
      transitionTo("ENDED");
    }
    setLiveTranscript("");
    setCorrectedTranscript("");
  };

  const startMediaRecording = async () => {
    if (!audioStreamRef.current) {
      console.warn("Cannot start AudioWorklet PCM streaming: audioStream is null");
      return;
    }
    
    // Send start_recording signal to backend first
    if (geminiWsRef.current && geminiWsRef.current.readyState === WebSocket.OPEN) {
      geminiWsRef.current.send(JSON.stringify({ type: "start_recording" }));
    }

    try {
      if (!audioContextRef.current) {
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        audioContextRef.current = new AudioContextClass();
      }
      const audioCtx = audioContextRef.current;
      if (audioCtx.state === "suspended") {
        await audioCtx.resume();
      }

      try {
        await audioCtx.audioWorklet.addModule("/audio-processor.js");
      } catch (e) {
        // Module might already be registered, safe to ignore
      }

      // Disconnect previous worklet/source nodes if any
      if (audioWorkletNodeRef.current) {
        try {
          audioWorkletNodeRef.current.disconnect();
        } catch (e) {}
        audioWorkletNodeRef.current = null;
      }
      if (audioSourceNodeRef.current) {
        try {
          audioSourceNodeRef.current.disconnect();
        } catch (e) {}
        audioSourceNodeRef.current = null;
      }

      // Connect source to worklet
      const source = audioCtx.createMediaStreamSource(audioStreamRef.current);
      audioSourceNodeRef.current = source;

      const workletNode = new AudioWorkletNode(audioCtx, "audio-processor");
      audioWorkletNodeRef.current = workletNode;

      workletNode.port.onmessage = (event) => {
        const pcmBuffer = event.data;
        if (geminiWsRef.current && geminiWsRef.current.readyState === WebSocket.OPEN) {
          geminiWsRef.current.send(pcmBuffer);
        }
      };

      source.connect(workletNode);
      console.log("[MEDIA] AudioWorklet PCM streaming started successfully.");
    } catch (e) {
      console.error("[MEDIA] Failed to initialize AudioWorklet streaming:", e);
      setError("Failed to initialize microphone streaming. Please check browser permissions.");
    }
  };

  const stopMediaRecording = () => {
    console.log("[MEDIA] Stopping AudioWorklet PCM streaming");
    if (audioWorkletNodeRef.current) {
      try {
        audioWorkletNodeRef.current.disconnect();
      } catch (e) {}
      audioWorkletNodeRef.current = null;
    }
    if (audioSourceNodeRef.current) {
      try {
        audioSourceNodeRef.current.disconnect();
      } catch (e) {}
      audioSourceNodeRef.current = null;
    }
  };

  useEffect(() => {
    if (voiceState === "LISTENING") {
      startMediaRecording();
    } else {
      stopMediaRecording();
    }
  }, [voiceState]);

  const startGeminiCall = async () => {
    setError("");
    transitionTo("CONNECTING");
    setElapsedSeconds(0);
    setLiveTranscript("");
    setCorrectedTranscript("");

    try {
      // 1. Get microphone access first
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      audioStreamRef.current = stream;

      // 1.5. Initialize and resume AudioContext immediately on user click gesture
      if (!audioContextRef.current) {
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        audioContextRef.current = new AudioContextClass();
      }
      const audioCtx = audioContextRef.current;
      if (audioCtx.state === "suspended") {
        await audioCtx.resume();
      }
      
      // Pre-load worklet module to make transition to LISTENING instant
      try {
        await audioCtx.audioWorklet.addModule("/audio-processor.js");
      } catch (e) {
        // Safe to ignore if already loaded or on page refresh
      }

      // 2. Setup WebSocket and register all handlers immediately
      const session = await getAuthSession();
      if (!session) return;
      const tokenParam = `?token=${session.access_token}`;
      const wsUrl = `ws://127.0.0.1:8000/api/voice/interview/${id}${tokenParam}`;
      const ws = new WebSocket(wsUrl);
      geminiWsRef.current = ws;

      ws.onopen = () => {
        console.log("Voice WebSocket connected.");
      };

      ws.onerror = (e) => {
        console.error("WebSocket error:", e);
        setError("Voice connection error. Please verify backend is running.");
      };

      ws.onclose = (event) => {
        console.log(`WebSocket closed. Code: ${event.code}, Reason: ${event.reason || "no reason"}`);
        transitionTo("ENDED");
        if (event.code !== 1000 && event.code !== 1005) {
          setError(`Voice connection closed (Code: ${event.code}). Reason: ${event.reason || "Connection lost or rejected by server."}`);
        }
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          
          if (msg.type === "status") {
            if (msg.status === "speaking") {
              transitionTo("AI_SPEAKING");
            } else if (msg.status === "listening") {
              transitionTo("LISTENING");
              setLiveTranscript("");
              setCorrectedTranscript("");
            } else if (msg.status === "transcribing") {
              transitionTo("TRANSCRIBING");
            } else if (msg.status === "thinking") {
              transitionTo("THINKING");
            }
          } else if (msg.type === "raw_transcript") {
            setLiveTranscript(msg.text);
          } else if (msg.type === "corrected_transcript") {
            setCorrectedTranscript(msg.text);
          } else if (msg.type === "transcript") {
            const sender = msg.sender;
            const text = msg.text;
            if (text && text.trim()) {
              setMessages((prev) => {
                const isDuplicate = prev.some(
                  (m) => m.sender === sender && m.text.trim() === text.trim()
                );
                if (isDuplicate) return prev;
                return [
                  ...prev,
                  { sender: sender, text: text, timestamp: new Date() }
                ];
              });

              if (sender === "candidate") {
                transitionTo("TRANSCRIBING");
                stopAllPlayback();
              } else if (sender === "interviewer") {
                transitionTo("LISTENING");
                setCurrentQuestion(text);
                if (msg.interview_phase) {
                  setPhase(msg.interview_phase);
                }
                // The backend owns interview progress. The first transcript sent
                // on connect is the existing question, not a second question.
                if (typeof msg.question_count === "number") {
                  setQuestionCount(msg.question_count);
                }
              }
            }
          } else if (msg.type === "assistant_response") {
            const audio = new Audio("data:audio/mp3;base64," + msg.audio);
            audio.preload = "auto";
            audio.load(); // Pre-buffer/decode next chunk

            if (msg.is_stream) {
              audioQueueRef.current.push({
                audio,
                isLastChunk: !!msg.is_last_chunk,
                chunkIndex: msg.chunk_index || 0,
                userStoppedSpeakingMs: msg.user_stopped_speaking_ms || 0,
                latency: msg.latency || {}
              });
              
              if (!isPlayingRef.current) {
                playNextChunk();
              }
            } else {
              // Legacy/single-payload fallback
              stopAllPlayback();
              activeAudioRef.current = audio;
              transitionTo("AI_SPEAKING");

              audio.onended = () => {
                if (activeAudioRef.current === audio) {
                  activeAudioRef.current = null;
                  transitionTo("LISTENING");
                }
              };

              audio.play().catch((err) => {
                console.error("Audio playback error:", err);
              });
            }

          } else if (msg.type === "session_completed") {
            setStatus("completed");
            setTimeout(() => {
              stopGeminiCall();
              router.push(`/transcript/${id}`);
            }, 6000);
          } else if (msg.type === "error") {
            setError(msg.message || "An unexpected error occurred during processing.");
            setTimeout(() => {
              setError("");
            }, 4000);
          }
        } catch (e) {
          console.error("Error parsing WebSocket message:", e);
        }
      };

    } catch (err: any) {
      console.error(err);
      setError(`Failed to initialize voice room: ${err.message || err}`);
      stopGeminiCall(false);
      transitionTo("DISCONNECTED");
    }
  };

  const startCall = async () => {
    await startGeminiCall();
  };

  const stopCall = () => {
    stopGeminiCall();
  };

  const toggleMute = () => {
    const newMute = !isMuted;
    setIsMuted(newMute);
    if (audioStreamRef.current) {
      audioStreamRef.current.getAudioTracks().forEach((track) => {
        track.enabled = !newMute;
      });
    }
  };

  const submitAnswer = () => {
    if (voiceStateRef.current === "LISTENING") {
      transitionTo("TRANSCRIBING");
      if (geminiWsRef.current && geminiWsRef.current.readyState === WebSocket.OPEN) {
        geminiWsRef.current.send(JSON.stringify({ type: "submit_answer" }));
      }
    }
  };

  const handleEndEarly = async () => {
    stopCall();
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const headers: HeadersInit = { "Content-Type": "application/json" };
      if (session) {
        headers["Authorization"] = `Bearer ${session.access_token}`;
      }
      const res = await fetch("http://127.0.0.1:8000/api/interview/end", {
        method: "POST",
        headers,
        body: JSON.stringify({ session_id: id })
      });
      if (res.ok) {
        router.push(`/transcript/${id}`);
      } else {
        router.push("/");
      }
    } catch {
      router.push("/");
    }
  };

  const switchToTextMode = () => {
    stopCall();
    router.push(`/interview/${id}`);
  };

  const [isSidePanelOpen, setIsSidePanelOpen] = useState(true);

  const renderOrb = () => {
    let orbBg = "#E4E7EC";
    let rippleColor = "transparent";
    let statusText = "Initializing...";
    let isPulsing = false;
    let isThinking = false;

    switch (voiceState) {
      case "DISCONNECTED":
        statusText = "Microphone Disconnected";
        break;
      case "CONNECTING":
        statusText = "Connecting audio stream...";
        isPulsing = true;
        break;
      case "LISTENING":
        orbBg = "#10B981"; 
        rippleColor = "rgba(16, 185, 129, 0.4)";
        statusText = "Listening to you speak...";
        isPulsing = true;
        break;
      case "TRANSCRIBING":
      case "THINKING":
        orbBg = "#2563EB"; 
        statusText = "Transcribing response...";
        isThinking = true;
        break;
      case "AI_SPEAKING":
        orbBg = "#2563EB"; 
        rippleColor = "rgba(37, 99, 235, 0.4)";
        statusText = "AI Coach is speaking...";
        isPulsing = true;
        break;
      case "ENDED":
        statusText = "Session ended";
        break;
    }

    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px" }}>
        <div style={{
          position: "relative",
          width: "160px",
          height: "160px",
          borderRadius: "50%",
          backgroundColor: orbBg,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: isPulsing ? "0 0 40px " + rippleColor : "none",
          transition: "all 0.3s ease-in-out"
        }}>
          {isPulsing && (
            <div style={{
              position: "absolute",
              inset: "-12px",
              borderRadius: "50%",
              border: `2px solid ${orbBg}`,
              animation: "ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite",
              opacity: 0.6
            }} />
          )}
          {isThinking && (
            <div style={{
              position: "absolute",
              inset: "-12px",
              borderRadius: "50%",
              border: `3px dashed ${orbBg}`,
              animation: "rotate-slow 4s linear infinite"
            }} />
          )}
          <span style={{ fontSize: "3rem" }}>
            {voiceState === "DISCONNECTED" ? "🔇" : "🎙️"}
          </span>
        </div>
        
        <div style={{ textAlign: "center" }}>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--text-primary)" }}>
            {statusText}
          </h3>
          <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "4px" }}>
            {voiceState === "LISTENING" && "Speak clearly into your microphone"}
            {voiceState === "AI_SPEAKING" && "Listen to the follow-up question"}
          </p>
        </div>
      </div>
    );
  };

  const phaseSteps = ["INTRODUCTION", "TECHNICAL", "BEHAVIORAL", "Q&A"];
  const activePhaseIndex = Math.max(0, phaseSteps.indexOf(phase));
  const progressPercent = maxQuestionCount > 0 ? Math.min(100, Math.round((questionCount / maxQuestionCount) * 100)) : 0;
  const confidenceScore = Math.min(98, Math.max(72, 70 + questionCount * 4 + (voiceState === "AI_SPEAKING" ? 3 : 0)));
  const depthScore = Math.min(96, Math.max(60, 58 + questionCount * 6));
  const transcriptTone =
    voiceState === "AI_SPEAKING"
      ? "Veriq is speaking"
      : voiceState === "LISTENING"
        ? "Waiting for your answer"
        : voiceState === "THINKING"
          ? "Thinking through the next question"
          : voiceState === "TRANSCRIBING"
            ? "Transcribing your response"
            : voiceState === "CONNECTING"
              ? "Preparing microphone"
              : voiceState === "ENDED"
                ? "Session finished"
                : "Ready for the first prompt";
  const transcriptHint =
    voiceState === "AI_SPEAKING"
      ? "Listen closely. The next follow-up is being delivered now."
      : voiceState === "LISTENING"
        ? "Answer naturally. The room is capturing your response."
        : voiceState === "THINKING"
          ? "The model is shaping a follow-up based on your answer."
          : "The room will wake up when the session starts.";
  const topicPills = [
    { label: "System Design", active: phase === "TECHNICAL" || phase === "Q&A" || questionCount > 0 },
    { label: "Scalability", active: progressPercent > 20 },
    { label: "Communication", active: phase === "BEHAVIORAL" || phase === "Q&A" || progressPercent > 35 },
    { label: "Hiring Signals", active: callStatus === "active" }
  ];
  const depthBars = [42, 54, 66, 72, 82, 88];

  const renderVoiceStage = () => {
    const stateClass = voiceState.toLowerCase();

    return (
      <div className={`voice-core voice-core--${stateClass}`}>
        <div className="voice-core__ring voice-core__ring--outer" />
        <div className="voice-core__ring voice-core__ring--inner" />
        <div className="voice-core__center">
          <div className="voice-core__glow" />
          <div className="voice-core__dot" />
        </div>
        <div className="voice-core__pulse" />
      </div>
    );
  };

  return (
    <div className="voice-room-container">
      
      {/* 1. LEFT COLUMN: Live Dialogue Transcript */}
      <div className="voice-left-col">
        <h3 style={{ fontSize: "0.85rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)", paddingBottom: "16px", borderBottom: "1px solid var(--border-subtle)", marginBottom: "20px", fontFamily: "var(--font-mono)" }}>
          Dialogue Transcript
        </h3>
        <div style={{ display: "flex", flexDirection: "column", gap: "16px", flex: 1, overflowY: "auto", paddingRight: "8px" }}>
          {messages.length === 0 && !liveTranscript && !correctedTranscript ? (
            <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", textAlign: "center", marginTop: "40px" }}>
              Dialogue will stream here once speech starts.
            </p>
          ) : (
            <>
              {messages.map((m, index) => (
                <div 
                  key={index} 
                  style={{ 
                    padding: "12px", 
                    borderRadius: "12px", 
                    backgroundColor: m.sender === "interviewer" ? "rgba(255, 255, 255, 0.84)" : "rgba(213, 173, 52, 0.1)",
                    borderLeft: m.sender === "interviewer" ? "3px solid var(--color-primary)" : "3px solid var(--color-success)",
                    border: "1px solid var(--border-subtle)"
                  }}
                >
                  <span style={{ fontSize: "10px", fontWeight: 700, color: m.sender === "interviewer" ? "var(--color-primary)" : "var(--color-success)", display: "block", marginBottom: "4px", textTransform: "uppercase", fontFamily: "var(--font-mono)" }}>
                    {m.sender === "interviewer" ? "Interviewer" : "You"}
                  </span>
                  <p style={{ fontSize: "0.9rem", lineHeight: "1.4", color: "var(--text-primary)" }}>{m.text}</p>
                </div>
              ))}
              {liveTranscript && (
                <div className="active-speaker-glow" style={{ padding: "12px", borderRadius: "12px", background: "rgba(6, 182, 212, 0.08)", border: "1px solid var(--border-subtle)" }}>
                  <span style={{ fontSize: "10px", fontWeight: 700, color: "var(--color-accent)", display: "block", marginBottom: "4px", textTransform: "uppercase", fontFamily: "var(--font-mono)" }}>You (Speaking...)</span>
                  <p style={{ fontSize: "0.9rem", fontStyle: "italic", color: "var(--text-secondary)" }}>"{liveTranscript}"</p>
                </div>
              )}
              {correctedTranscript && (
                <div style={{ padding: "12px", borderRadius: "12px", background: "rgba(16, 185, 129, 0.08)", border: "1px solid var(--border-subtle)" }}>
                  <span style={{ fontSize: "10px", fontWeight: 700, color: "var(--color-success)", display: "block", marginBottom: "4px", textTransform: "uppercase", fontFamily: "var(--font-mono)" }}>You (Processed)</span>
                  <p style={{ fontSize: "0.9rem", color: "var(--text-primary)" }}>"{correctedTranscript}"</p>
                </div>
              )}
              <div ref={chatEndRef} />
            </>
          )}
        </div>
      </div>

      {/* 2. CENTER COLUMN: Interactive Visualizer & Controls */}
      <div className="voice-center-col">
        {/* Header */}
        <header style={{
          height: "64px",
          borderBottom: "1px solid var(--border-subtle)",
          padding: "0 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          backgroundColor: "rgba(255, 253, 249, 0.84)"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <h2 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-primary)" }}>{role}</h2>
            <span className="badge badge-primary" style={{ textTransform: "uppercase" }}>{difficulty}</span>
          </div>
          <button
            onClick={switchToTextMode}
            className="btn btn-secondary"
            style={{ padding: "6px 12px", fontSize: "0.8rem" }}
          >
            💬 Switch to Text
          </button>
        </header>

        {/* Focus visualizer */}
        <div className="voice-room-stage">
          <div className="voice-room-stage__visual">
          {error ? (
          <div style={{ backgroundColor: "rgba(239, 68, 68, 0.08)", border: "1px solid rgba(239, 68, 68, 0.24)", color: "var(--color-error)", padding: "16px", borderRadius: "12px", maxWidth: "480px" }}>
              {error}
            </div>
          ) : (
            renderVoiceStage()
          )}
          </div>
        </div>

        {/* Controls footer */}
        <footer style={{
          padding: "24px",
          backgroundColor: "rgba(255, 253, 249, 0.84)",
          borderTop: "1px solid var(--border-subtle)"
        }}>
          <div style={{ display: "flex", gap: "16px", width: "100%", maxWidth: "480px", margin: "0 auto" }}>
            {callStatus === "inactive" ? (
              <button onClick={startCall} className="btn btn-primary" style={{ width: "100%", padding: "12px 24px" }}>
                Connect Microphone
              </button>
            ) : (
              <>
                <button
                  onClick={toggleMute}
                  className="btn btn-secondary"
                  style={{
                    flex: 1,
                    backgroundColor: isMuted ? "rgba(239, 68, 68, 0.08)" : "rgba(255, 255, 255, 0.8)",
                    borderColor: isMuted ? "rgba(239, 68, 68, 0.3)" : "var(--border-subtle)",
                    color: isMuted ? "#EF4444" : "var(--text-primary)"
                  }}
                >
                  {isMuted ? "🔇 Unmute Mic" : "🎙️ Mute Mic"}
                </button>
                <button
                  onClick={handleEndEarly}
                  className="btn btn-primary"
                  style={{ flex: 1.5, background: "linear-gradient(135deg, #ef4444, #b91c1c)" }}
                >
                  🏁 Finish & Report
                </button>
              </>
            )}
          </div>
        </footer>
      </div>

      {/* 3. RIGHT COLUMN: Metrics & Session Outline */}
      <div className="voice-right-col">
        {/* Progress bar */}
        <div className="telemetry-progress">
          <div className="telemetry-progress__head">
            <h3>Progress</h3>
            <span>{questionCount}/{maxQuestionCount}</span>
          </div>
          <div className="telemetry-progress__bar">
            <div style={{
              width: `${(questionCount / maxQuestionCount) * 100}%`,
              height: "100%",
              backgroundColor: "var(--color-primary)",
              transition: "width 0.3s ease"
            }} />
          </div>
        </div>

        {/* Current phase indicator */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <h3 style={{ fontSize: "0.85rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            Current Phase
          </h3>
          <span className="badge badge-primary" style={{
            alignSelf: "flex-start",
            textTransform: "uppercase",
            fontSize: "0.8rem",
            padding: "6px 12px",
            fontFamily: "var(--font-mono)"
          }}>
            {phase.replace("_", " ")}
          </span>
        </div>

        {/* Timer */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <h3 style={{ fontSize: "0.85rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            Duration
          </h3>
          <div style={{ fontSize: "1.1rem", fontWeight: 600, color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>
            Elapsed: {formatTime(elapsedSeconds)}
          </div>
        </div>

        {/* Simulated Candidate Notes Panel */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px", flex: 1 }}>
          <h3 style={{ fontSize: "0.85rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)" }}>
            Scratchpad / Notes
          </h3>
          <textarea
            placeholder="Type notes or structure your design thoughts here..."
            style={{
              flex: 1,
              resize: "none",
              fontSize: "0.9rem",
              padding: "12px",
              borderRadius: "14px",
              border: "1px solid var(--border-subtle)",
              background: "rgba(255, 255, 255, 0.8)",
              color: "var(--text-primary)",
              width: "100%"
            }}
          />
        </div>
      </div>

      <style jsx>{`
        .voice-room-container {
          display: grid;
          grid-template-columns: 320px 1fr 300px;
          height: 100vh;
          background-color: var(--bg-main);
        }
        .voice-left-col {
          background-color: rgba(255, 253, 249, 0.8);
          border-right: 1px solid var(--border-subtle);
          padding: 32px 24px;
          display: flex;
          flex-direction: column;
          height: 100vh;
        }
        .voice-center-col {
          display: flex;
          flex-direction: column;
          height: 100vh;
        }
        .voice-right-col {
          background-color: rgba(255, 253, 249, 0.8);
          border-left: 1px solid var(--border-subtle);
          padding: 32px 24px;
          display: flex;
          flex-direction: column;
          gap: 32px;
          height: 100vh;
        }
        @keyframes ping {
          75%, 100% {
            transform: scale(1.4);
            opacity: 0;
          }
        }
        @keyframes rotate-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .voice-room-container {
          display: grid;
          grid-template-columns: minmax(280px, 0.86fr) minmax(420px, 1.28fr) minmax(240px, 0.72fr);
          gap: 18px;
          min-height: 100vh;
          padding: 18px;
          background:
            radial-gradient(circle at 50% 8%, rgba(255, 255, 255, 0.94), transparent 24%),
            linear-gradient(180deg, rgba(247, 242, 233, 0.96), rgba(244, 239, 229, 0.98));
        }
        .voice-left-col,
        .voice-right-col,
        .voice-center-col {
          min-height: calc(100vh - 36px);
          border-radius: 28px;
          overflow: hidden;
        }
        .voice-left-col,
        .voice-right-col {
          padding: 0 !important;
          background: rgba(255, 253, 249, 0.82) !important;
          border: 1px solid var(--border-subtle) !important;
          backdrop-filter: blur(18px);
          box-shadow: var(--shadow-card);
          padding-bottom: 18px;
        }
        .voice-left-col > *,
        .voice-right-col > * {
          padding-left: 24px;
          padding-right: 24px;
        }
        .voice-left-col > h3,
        .voice-right-col > div:first-child,
        .voice-right-col > div:nth-child(2),
        .voice-right-col > div:nth-child(3),
        .voice-right-col > div:nth-child(4) {
          padding-top: 18px;
        }
        .voice-left-col > div {
          padding-bottom: 24px;
        }
        .voice-center-col {
          background:
            radial-gradient(circle at 50% 32%, rgba(255, 214, 111, 0.12), transparent 32%),
            linear-gradient(180deg, rgba(255, 253, 249, 0.94), rgba(244, 239, 229, 0.84));
          border: 1px solid var(--border-subtle);
          backdrop-filter: blur(18px);
          box-shadow: var(--shadow-card);
          display: flex;
          flex-direction: column;
        }
        .voice-center-col > header {
          border-bottom: 1px solid var(--border-subtle) !important;
          background: rgba(255, 255, 255, 0.56) !important;
          backdrop-filter: blur(10px);
        }
        .voice-center-col > footer {
          border-top: 1px solid var(--border-subtle) !important;
          background: rgba(255, 255, 255, 0.56) !important;
          backdrop-filter: blur(10px);
        }
        .voice-room-stage {
          flex: 1;
          display: grid;
          place-items: center;
          padding: 20px;
          background: linear-gradient(180deg, rgba(255, 253, 249, 0.95), rgba(247, 242, 233, 0.96));
          overflow: hidden;
        }
        .voice-room-stage__visual {
          width: min(100%, 240px);
          height: min(100%, 240px);
          display: grid;
          place-items: center;
          position: relative;
          border-radius: 999px;
          background: transparent;
        }
        .voice-core {
          position: relative;
          width: 180px;
          height: 180px;
          display: grid;
          place-items: center;
          isolation: isolate;
        }
        .voice-core__ambient,
        .voice-core__ring,
        .voice-core__pulse,
        .voice-core__center {
          position: absolute;
        }
        .voice-core__ring {
          border-radius: 50%;
          border: 1px solid rgba(155, 118, 18, 0.12);
        }
        .voice-core__ring--outer {
          inset: 0;
        }
        .voice-core__ring--inner {
          inset: 16%;
          border-color: rgba(155, 118, 18, 0.22);
        }
        .voice-core__center {
          inset: 32%;
          border-radius: 50%;
          display: grid;
          place-items: center;
          background: radial-gradient(circle, rgba(255, 241, 195, 0.9), rgba(213, 173, 52, 0.2) 48%, rgba(255, 255, 255, 0) 74%);
        }
        .voice-core__glow {
          position: absolute;
          inset: -12px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(213, 173, 52, 0.34), transparent 68%);
          filter: blur(6px);
          animation: pulse-core 2.4s ease-in-out infinite;
        }
        .voice-core__dot {
          width: 44%;
          height: 44%;
          border-radius: 50%;
          background: radial-gradient(circle, #fff5c9 0%, #e8be45 38%, #926a0d 72%, #1a1712 100%);
          box-shadow: 0 0 24px rgba(213, 173, 52, 0.24), inset 0 0 16px rgba(255, 247, 196, 0.22);
          animation: pulse-core 1.8s ease-in-out infinite;
        }
        .voice-core__ambient {
          inset: 18%;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(213, 173, 52, 0.12), transparent 68%);
          filter: blur(16px);
          animation: breathe 5.8s ease-in-out infinite;
          z-index: 0;
        }
        .voice-core__ambient--right {
          inset: 20%;
          opacity: 0.62;
          animation-delay: 1.1s;
        }
        .voice-core__pulse {
          inset: 28%;
          border-radius: 50%;
          border: 1px solid rgba(255, 228, 152, 0.22);
          box-shadow: 0 0 0 14px rgba(213, 173, 52, 0.04);
          animation: pulse-core 2.8s ease-in-out infinite;
          z-index: 2;
        }
        .voice-core--speaking .voice-core__dot {
          transform: scale(1.06);
        }
        .voice-core--listening .voice-core__dot {
          transform: scale(0.98);
        }
        .voice-core--thinking .voice-core__dot,
        .voice-core--transcribing .voice-core__dot {
          animation: pulse-core 1.2s ease-in-out infinite;
        }
        .voice-core--speaking .voice-core__pulse {
          animation-duration: 1.2s;
        }
        .voice-core--speaking .voice-core__center {
          transform: scale(1.03);
        }
        .voice-core--listening .voice-core__center {
          transform: scale(0.98);
        }
        .voice-core--thinking .voice-core__center,
        .voice-core--transcribing .voice-core__center {
          animation: pulse-core 1.4s ease-in-out infinite;
        }
        .voice-core--thinking .voice-core__ring--outer,
        .voice-core--transcribing .voice-core__ring--outer {
          animation: spin 14s linear infinite reverse;
        }
        .voice-core--ended {
          opacity: 0.74;
        }
        .telemetry-card {
          padding: 16px;
          border-radius: 22px;
          border: 1px solid var(--border-subtle);
          background: rgba(255, 255, 255, 0.66);
        }
        .telemetry-progress {
          padding: 14px 16px;
          border-radius: 18px;
          border: 1px solid var(--border-subtle);
          background: rgba(255, 255, 255, 0.64);
          display: grid;
          gap: 10px;
        }
        .telemetry-progress__head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }
        .telemetry-progress__head h3 {
          font-size: 0.78rem;
          text-transform: uppercase;
          letter-spacing: 0.14em;
          color: var(--text-muted);
          font-weight: 800;
        }
        .telemetry-progress__head span {
          font-size: 0.8rem;
          font-family: var(--font-mono);
          color: var(--text-primary);
          font-weight: 700;
        }
        .telemetry-progress__bar {
          width: 100%;
          height: 8px;
          border-radius: 999px;
          background: rgba(28, 23, 18, 0.08);
          overflow: hidden;
        }
        .telemetry-card__row {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 10px;
        }
        .telemetry-card__row--compact {
          align-items: center;
        }
        .telemetry-card__label {
          color: var(--text-muted);
          font-size: 0.7rem;
          text-transform: uppercase;
          letter-spacing: 0.14em;
          font-weight: 800;
        }
        .telemetry-card strong {
          display: block;
          margin-top: 4px;
          font-size: 1.35rem;
          font-family: var(--font-mono);
          color: var(--text-primary);
        }
        .telemetry-card__hint,
        .telemetry-card__note {
          margin-top: 10px;
          color: var(--text-secondary);
          line-height: 1.55;
        }
        .telemetry-bar {
          width: 100%;
          height: 10px;
          border-radius: 999px;
          background: rgba(28, 23, 18, 0.08);
          overflow: hidden;
        }
        .telemetry-bar span {
          display: block;
          height: 100%;
          border-radius: inherit;
          background: linear-gradient(90deg, #d9bd67, var(--accent-strong));
          box-shadow: 0 0 18px rgba(155, 118, 18, 0.24);
        }
        .telemetry-bar--gold span {
          background: linear-gradient(90deg, #f0d889, #9b7612);
        }
        .pill-cloud {
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
        }
        .pill-cloud__pill {
          padding: 8px 12px;
          border-radius: 999px;
          border: 1px solid var(--border-subtle);
          color: var(--text-muted);
          font-size: 0.76rem;
          font-weight: 700;
          background: rgba(255, 255, 255, 0.66);
        }
        .pill-cloud__pill.is-active {
          color: var(--accent-strong);
          border-color: rgba(155, 118, 18, 0.22);
          background: rgba(213, 173, 52, 0.12);
        }
        .depth-bars {
          display: grid;
          grid-template-columns: repeat(6, 1fr);
          align-items: end;
          gap: 8px;
          height: 88px;
          margin-top: 10px;
        }
        .depth-bars span {
          display: block;
          border-radius: 999px 999px 12px 12px;
          background: linear-gradient(180deg, #d6b24b, #8f6a0c);
          box-shadow: 0 6px 14px rgba(155, 118, 18, 0.12);
        }
        .telemetry-card--summary {
          display: grid;
          gap: 12px;
        }
        .telemetry-card__action {
          width: 100%;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes breathe {
          0%, 100% { transform: scale(1); opacity: 0.76; }
          50% { transform: scale(1.04); opacity: 1; }
        }
        @keyframes listen-shift {
          0%, 100% { filter: saturate(1); }
          50% { filter: saturate(1.12) brightness(1.04); }
        }
        @keyframes speak-shift {
          0%, 100% { transform: translateX(-50%) translateY(0) scale(1); }
          50% { transform: translateX(-50%) translateY(0.6%) scale(1.03); }
        }
        @keyframes pulse-core {
          0%, 100% { transform: scale(0.97); opacity: 0.45; }
          50% { transform: scale(1.04); opacity: 0.82; }
        }
        @keyframes wave-flow {
          0%, 100% { opacity: 0.36; transform: translateY(-50%) scaleX(0.92); }
          50% { opacity: 1; transform: translateY(-50%) scaleX(1); }
        }
        @keyframes transcript-pulse {
          0%, 100% { box-shadow: 0 0 0 rgba(213, 173, 52, 0); }
          50% { box-shadow: 0 0 26px rgba(213, 173, 52, 0.12); }
        }
        @media (max-width: 1024px) {
          .voice-room-container {
            grid-template-columns: 280px 1fr;
          }
          .voice-right-col {
            display: none;
          }
        }
        @media (max-width: 768px) {
          .voice-room-container {
            grid-template-columns: 1fr;
          }
          .voice-left-col {
            display: none;
          }
          .voice-room-stage {
            padding: 12px;
          }
          .voice-room-stage__visual {
            width: 100%;
            height: auto;
            min-height: 340px;
          }
          .voice-core {
            width: min(100%, 420px);
          }
        }
      `}</style>
    </div>
  );
}
