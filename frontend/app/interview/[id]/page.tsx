"use client";

import React, { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "../../context/AuthContext";
import { supabase } from "../../utils/supabaseClient";

interface ChatMessage {
  sender: "interviewer" | "candidate";
  text: string;
  timestamp: Date;
}

export default function TextInterviewRoom() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [role, setRole] = useState("Initializing Coach...");
  const [difficulty, setDifficulty] = useState("");
  const [questionCount, setQuestionCount] = useState(0);
  const [maxQuestionCount, setMaxQuestionCount] = useState(5);
  const [status, setStatus] = useState("in_progress");
  const [phase, setPhase] = useState("INTRODUCTION");
  
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [isWaiting, setIsWaiting] = useState(false);
  const [error, setError] = useState("");
  const [isSidePanelOpen, setIsSidePanelOpen] = useState(true);

  const wsRef = useRef<WebSocket | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const { user } = useAuth();

  useEffect(() => {
    if (!id || !user) return;

    let ws: WebSocket | null = null;

    const initSession = async () => {
      try {
        const { data: { session: authSession } } = await supabase.auth.getSession();
        if (!authSession) {
          setError("Unauthenticated request");
          return;
        }

        const headers = {
          "Authorization": `Bearer ${authSession.access_token}`
        };

        const res = await fetch(`http://127.0.0.1:8000/api/v1/interviews/${id}`, { headers });
        if (!res.ok) throw new Error("Could not fetch interview session.");
        const data = await res.json();

        setRole(data.role);
        setDifficulty(data.difficulty);
        setQuestionCount(data.question_count);
        setMaxQuestionCount(data.max_question_count);
        setStatus(data.status);
        setPhase(data.interview_phase || "INTRODUCTION");

        const history: ChatMessage[] = data.transcripts.map((t: any) => ({
          sender: t.sender,
          text: t.text,
          timestamp: new Date(t.timestamp)
        }));
        setMessages(history);

        if (data.status === "completed") {
          router.push(`/transcript/${id}`);
          return;
        }

        ws = new WebSocket(`ws://127.0.0.1:8000/api/v1/interviews/${id}/stream?token=${authSession.access_token}`);
        wsRef.current = ws;

        ws.onmessage = (event) => {
          const payload = JSON.parse(event.data);
          
          if (payload.error) {
            setError(payload.error);
            setIsWaiting(false);
            return;
          }

          if (payload.sender === "interviewer") {
            setMessages((prev) => [
              ...prev,
              {
                sender: "interviewer",
                text: payload.text,
                timestamp: new Date()
              }
            ]);
            setQuestionCount(payload.question_count);
            setStatus(payload.status);
            setPhase(payload.interview_phase || "TECHNICAL_EVALUATION");
            setIsWaiting(false);

            if (payload.status === "completed") {
              setTimeout(() => {
                router.push(`/transcript/${id}`);
              }, 4000);
            }
          }
        };

        ws.onerror = () => {
          setError("Lost server connection. Please verify backend state.");
          setIsWaiting(false);
        };
      } catch (err: any) {
        setError(err.message || "Failed to initialize interview room");
      }
    };

    initSession();

    return () => {
      if (ws) ws.close();
    };
  }, [id, user]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isWaiting || status === "completed") return;

    const answerText = inputText.trim();
    setInputText("");
    setIsWaiting(true);

    setMessages((prev) => [
      ...prev,
      {
        sender: "candidate",
        text: answerText,
        timestamp: new Date()
      }
    ]);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ text: answerText }));
    } else {
      setError("WebSocket is not connected. Message not sent.");
      setIsWaiting(false);
    }
  };

  const handleEndEarly = () => {
    if (wsRef.current) wsRef.current.close();
    router.push(`/transcript/${id}`);
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh", backgroundColor: "#FCFCFD" }}>
      {/* Center Chat View */}
      <div style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        position: "relative",
        borderRight: isSidePanelOpen ? "1px solid var(--border-main)" : "none"
      }}>
        {/* Header bar */}
        <header style={{
          height: "64px",
          borderBottom: "1px solid var(--border-main)",
          padding: "0 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          backgroundColor: "#FFFFFF"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <h2 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-primary)" }}>{role}</h2>
            <span className="badge badge-primary" style={{ textTransform: "capitalize" }}>{difficulty}</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <button
              onClick={() => router.push(`/interview/${id}/voice`)}
              className="btn btn-secondary"
              style={{ padding: "6px 12px", fontSize: "0.8rem" }}
            >
              🎙️ Switch to Voice
            </button>
            <button
              onClick={() => setIsSidePanelOpen(!isSidePanelOpen)}
              className="btn btn-secondary"
              style={{ padding: "6px 10px", display: "flex", alignItems: "center" }}
            >
              {isSidePanelOpen ? "Hide Progress" : "Show Progress"}
            </button>
          </div>
        </header>

        {/* Chat Thread */}
        <div style={{
          flex: 1,
          overflowY: "auto",
          padding: "32px 24px",
          display: "flex",
          flexDirection: "column",
          gap: "24px"
        }}>
          {messages.length === 0 && (
            <div style={{ display: "flex", justifyContent: "center", alignItems: "center", flex: 1, color: "var(--text-muted)", fontSize: "0.9rem" }}>
              Connecting to mock environment...
            </div>
          )}

          {messages.map((msg, index) => {
            const isInterviewer = msg.sender === "interviewer";
            return (
              <div
                key={index}
                style={{
                  display: "flex",
                  justifyContent: isInterviewer ? "flex-start" : "flex-end",
                  width: "100%"
                }}
              >
                <div style={{
                  maxWidth: "600px",
                  backgroundColor: isInterviewer ? "#FFFFFF" : "#EFF6FF",
                  border: isInterviewer ? "1px solid var(--border-main)" : "1px solid #BFDBFE",
                  padding: "16px 20px",
                  borderRadius: "12px",
                  boxShadow: "0 1px 2px rgba(0,0,0,0.02)"
                }}>
                  <div style={{
                    fontSize: "0.75rem",
                    fontWeight: 700,
                    textTransform: "uppercase",
                    color: isInterviewer ? "#3B82F6" : "#2563EB",
                    marginBottom: "6px"
                  }}>
                    {isInterviewer ? "Interviewer" : "You (Candidate)"}
                  </div>
                  <p style={{
                    fontSize: "0.95rem",
                    color: "var(--text-primary)",
                    lineHeight: "1.5",
                    whiteSpace: "pre-line"
                  }}>
                    {msg.text}
                  </p>
                </div>
              </div>
            );
          })}

          {isWaiting && (
            <div style={{ display: "flex", justifyContent: "flex-start", width: "100%" }}>
              <div style={{
                backgroundColor: "#FFFFFF",
                border: "1px solid var(--border-main)",
                padding: "12px 18px",
                borderRadius: "12px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                color: "var(--text-muted)"
              }}>
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span style={{ fontSize: "0.85rem", marginLeft: "4px" }}>AI Coach is reviewing your response...</span>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Bottom Input Panel */}
        <div style={{
          padding: "24px",
          backgroundColor: "#FFFFFF",
          borderTop: "1px solid var(--border-main)"
        }}>
          <form onSubmit={handleSend} style={{ display: "flex", gap: "12px", maxWidth: "800px", margin: "0 auto" }}>
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={isWaiting ? "Reviewing..." : "Type your answer and press Send..."}
              disabled={isWaiting || status === "completed"}
              style={{
                flex: 1,
                padding: "14px 18px",
                borderRadius: "10px",
                border: "1px solid var(--border-main)",
                fontSize: "0.95rem"
              }}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isWaiting || !inputText.trim() || status === "completed"}
              style={{ padding: "0 24px" }}
            >
              Send Response
            </button>
          </form>
        </div>
      </div>

      {/* Sidebar Progress Panel (Collapsible) */}
      {isSidePanelOpen && (
        <aside style={{
          width: "280px",
          backgroundColor: "#FFFFFF",
          height: "100vh",
          padding: "32px 24px",
          display: "flex",
          flexDirection: "column",
          gap: "32px",
          position: "sticky",
          top: 0
        }}>
          {/* Progress Circle & Text */}
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <h3 style={{ fontSize: "0.85rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)" }}>
              Progress
            </h3>
            <div style={{ fontSize: "1.8rem", fontWeight: 800, fontFamily: "var(--font-outfit)" }}>
              {questionCount} <span style={{ fontSize: "1rem", fontWeight: 500, color: "var(--text-muted)" }}>/ {maxQuestionCount} Qs</span>
            </div>
            <div style={{ width: "100%", height: "6px", borderRadius: "3px", backgroundColor: "#E4E7EC", overflow: "hidden" }}>
              <div style={{
                width: `${(questionCount / maxQuestionCount) * 100}%`,
                height: "100%",
                backgroundColor: "#3B82F6",
                transition: "width 0.3s ease"
              }} />
            </div>
          </div>

          {/* Current Phase */}
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <h3 style={{ fontSize: "0.85rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)" }}>
              Current Phase
            </h3>
            <span className="badge badge-primary" style={{
              alignSelf: "flex-start",
              textTransform: "uppercase",
              fontSize: "0.8rem",
              padding: "6px 12px"
            }}>
              {phase.replace("_", " ")}
            </span>
          </div>

          {/* Time Remaining */}
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            <h3 style={{ fontSize: "0.85rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)" }}>
              Time Remaining
            </h3>
            <div style={{ fontSize: "1.1rem", fontWeight: 600 }}>
              ~{Math.max(1, Math.round((maxQuestionCount - questionCount) * 1.5))} Mins Remaining
            </div>
          </div>

          <div style={{ flex: 1 }} />

          {/* Action buttons */}
          <button
            onClick={handleEndEarly}
            className="btn btn-secondary"
            style={{ width: "100%", border: "1px solid #FCA5A5", color: "#EF4444" }}
          >
            End Interview Early
          </button>
        </aside>
      )}

      <style jsx>{`
        .typing-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background-color: var(--text-muted);
          animation: bounce 1.4s infinite ease-in-out both;
        }
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1.0); }
        }
      `}</style>
    </div>
  );
}
