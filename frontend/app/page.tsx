"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "./context/AuthContext";
import { supabase } from "./utils/supabaseClient";

interface InterviewSession {
  id: string;
  role: string;
  difficulty: string;
  duration_minutes: number;
  status: string;
  created_at: string;
}

export default function HomePage() {
  const router = useRouter();
  const { user, setShowAuthModal } = useAuth();
  const [sessions, setSessions] = useState<InterviewSession[]>([]);
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("voice");

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationId: number;
    let phase = 0;

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.lineWidth = 2.5;

      const colors = [
        "rgba(59, 130, 246, 0.6)", 
        "rgba(6, 182, 212, 0.4)",  
        "rgba(99, 102, 241, 0.2)"  
      ];

      for (let i = 0; i < colors.length; i++) {
        ctx.strokeStyle = colors[i];
        ctx.beginPath();
        const amplitude = 30 - i * 8;
        const frequency = 0.015 + i * 0.005;

        for (let x = 0; x < canvas.width; x++) {
          const y =
            canvas.height / 2 +
            Math.sin(x * frequency + phase + i) *
              amplitude *
              Math.sin(x * 0.003); 
          if (x === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.stroke();
      }

      phase += 0.05;
      animationId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animationId);
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      if (!user) {
        setSessions([
          {
            id: "guest-demo-1",
            role: "Senior AI Solutions Engineer",
            difficulty: "medium",
            duration_minutes: 20,
            status: "completed",
            created_at: new Date().toISOString()
          }
        ]);
        setProfile({
          topic_mastery: {
            "System Architecture & Scaling": { average_score: 65, mastery_state: "Weak" },
            "Large Language Model Integration": { average_score: 84, mastery_state: "Verified" }
          },
          readiness_scores: {
            "Coding": 75,
            "Design": 70,
            "Communication": 80
          },
          history_trends: [
            { date: "2026-07-05", score: 76 }
          ]
        });
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) {
          setLoading(false);
          return;
        }

        const historyRes = await fetch("http://127.0.0.1:8000/api/v1/interviews", {
          headers: { "Authorization": `Bearer ${session.access_token}` }
        });
        const historyData = await historyRes.json();
        setSessions(Array.isArray(historyData) ? historyData : []);

        const profileRes = await fetch("http://127.0.0.1:8000/api/v1/interviews/profile/card", {
          headers: { "Authorization": `Bearer ${session.access_token}` }
        });
        if (profileRes.ok) {
          const profileData = await profileRes.json();
          setProfile(profileData);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [user]);

  const scrollToFeatures = () => {
    const featuresEl = document.getElementById("features-section");
    if (featuresEl) {
      featuresEl.scrollIntoView({ behavior: "smooth" });
    }
  };

  const getLatestSession = () => {
    if (!sessions || sessions.length === 0) return null;
    return sessions[0];
  };

  const latestSession = getLatestSession();

  return (
    <div style={{
      backgroundColor: "#0B0F19",
      color: "#F8FAFC",
      minHeight: "100vh",
      fontFamily: "var(--font-jakarta)",
      position: "relative",
      overflow: "hidden",
      margin: "-32px" 
    }}>
      <div style={{
        position: "absolute",
        top: "-10%",
        left: "20%",
        width: "600px",
        height: "600px",
        background: "radial-gradient(circle, rgba(37, 99, 235, 0.12) 0%, transparent 70%)",
        pointerEvents: "none",
        zIndex: 0
      }} />
      <div style={{
        position: "absolute",
        bottom: "10%",
        right: "-10%",
        width: "500px",
        height: "500px",
        background: "radial-gradient(circle, rgba(6, 182, 212, 0.1) 0%, transparent 70%)",
        pointerEvents: "none",
        zIndex: 0
      }} />

      <section style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "85vh",
        padding: "60px 24px",
        textAlign: "center",
        zIndex: 1,
        position: "relative"
      }}>
        <div className="pulse-logo" style={{
          width: "72px",
          height: "72px",
          borderRadius: "24px",
          background: "linear-gradient(135deg, #2563EB 0%, #06B6D4 100%)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 0 40px rgba(37, 99, 235, 0.4)",
          fontSize: "2rem",
          fontWeight: 800,
          marginBottom: "32px",
          color: "#FFFFFF"
        }}>
          🚀
        </div>

        <h1 style={{
          fontFamily: "var(--font-outfit)",
          fontSize: "3.5rem",
          fontWeight: 900,
          background: "linear-gradient(to right, #FFFFFF, #E2E8F0, #94A3B8)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          letterSpacing: "-1.5px",
          marginBottom: "16px",
          maxWidth: "750px",
          lineHeight: "1.15"
        }}>
          Meet Your AI Interview Pilot
        </h1>

        <p style={{
          fontSize: "1.15rem",
          color: "#94A3B8",
          maxWidth: "580px",
          lineHeight: "1.6",
          marginBottom: "32px"
        }}>
          Practice highly realistic, adaptive mock technical interviews with a voice-based AI coach. Get evaluated instantly with multi-dimensional scoring and roadmap planner tools.
        </p>

        <div style={{ position: "relative", width: "100%", maxWidth: "480px", height: "80px", marginBottom: "40px" }}>
          <canvas
            ref={canvasRef}
            width="480"
            height="80"
            style={{ width: "100%", height: "100%" }}
          />
        </div>

        <div style={{ display: "flex", gap: "16px", flexWrap: "wrap", justifyContent: "center" }}>
          {user ? (
            <button
              onClick={() => router.push("/new-interview")}
              className="btn btn-primary"
              style={{
                padding: "14px 28px",
                fontSize: "1.05rem",
                borderRadius: "12px",
                boxShadow: "0 4px 20px rgba(37, 99, 235, 0.3)"
              }}
            >
              Start New Simulation
            </button>
          ) : (
            <button
              onClick={() => setShowAuthModal(true)}
              className="btn btn-primary"
              style={{
                padding: "14px 28px",
                fontSize: "1.05rem",
                borderRadius: "12px",
                boxShadow: "0 4px 20px rgba(37, 99, 235, 0.3)"
              }}
            >
              Get Started Free
            </button>
          )}

          <button
            onClick={scrollToFeatures}
            className="btn btn-secondary"
            style={{
              padding: "14px 28px",
              fontSize: "1.05rem",
              borderRadius: "12px",
              border: "1px solid #334155",
              backgroundColor: "rgba(30, 41, 59, 0.4)",
              color: "#F8FAFC"
            }}
          >
            Explore Features ↓
          </button>
        </div>

        {user && latestSession && (
          <div style={{ marginTop: "32px", fontSize: "0.9rem", color: "#64748B" }}>
            Working on: <strong style={{ color: "#3B82F6" }}>{latestSession.role}</strong> (Difficulty: {latestSession.difficulty})
            <span
              onClick={() => router.push(`/interview/${latestSession.id}/voice`)}
              style={{ marginLeft: "12px", color: "#38BDF8", cursor: "pointer", textDecoration: "underline", fontWeight: 600 }}
            >
              Resume turn
            </span>
          </div>
        )}
      </section>

      <section
        id="features-section"
        style={{
          padding: "100px 32px",
          borderTop: "1px solid #1E293B",
          backgroundColor: "#0A0D16",
          zIndex: 1,
          position: "relative"
        }}
      >
        <div style={{ maxWidth: "1000px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "64px" }}>
            <h2 style={{
              fontFamily: "var(--font-outfit)",
              fontSize: "2.25rem",
              fontWeight: 800,
              color: "#FFFFFF",
              marginBottom: "12px"
            }}>
              Calibrated to Land Your Target Offer
            </h2>
            <p style={{ color: "#64748B", fontSize: "1.05rem", maxWidth: "600px", margin: "0 auto" }}>
              Explore how our continuous agent-driven engine accelerates interview proficiency.
            </p>
          </div>

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "12px",
            marginBottom: "40px"
          }}>
            {[
              { id: "voice", label: "Voice Engine", icon: "🎙️" },
              { id: "blueprint", label: "Custom Blueprints", icon: "📋" },
              { id: "report", label: "Detailed Scorecards", icon: "🎯" },
              { id: "roadmap", label: "Study Roadmaps", icon: "📈" }
            ].map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  style={{
                    padding: "16px",
                    borderRadius: "12px",
                    border: isActive ? "1px solid #3B82F6" : "1px solid #1E293B",
                    backgroundColor: isActive ? "rgba(59, 130, 246, 0.08)" : "transparent",
                    color: isActive ? "#3B82F6" : "#94A3B8",
                    fontFamily: "var(--font-outfit)",
                    fontWeight: 700,
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    justifyContent: "center"
                  }}
                >
                  <span style={{ fontSize: "1.2rem" }}>{tab.icon}</span>
                  {tab.label}
                </button>
              );
            })}
          </div>

          <div className="card" style={{
            padding: "40px",
            backgroundColor: "rgba(15, 23, 42, 0.4)",
            border: "1px solid #1E293B",
            borderRadius: "16px",
            backdropFilter: "blur(12px)",
            minHeight: "260px",
            display: "flex",
            flexDirection: "column",
            justifyContent: "center"
          }}>
            {activeTab === "voice" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <h3 style={{ fontSize: "1.5rem", fontWeight: 800, color: "#FFFFFF" }}>🗣️ Voice-First Low Latency Pipeline</h3>
                <p style={{ color: "#94A3B8", lineHeight: "1.7", fontSize: "1.05rem" }}>
                  Engage in fluid conversations with our voice coach. The system uses Whisper transcript normalizers to ignore background noise and streams high-fidelity EdgeTTS audio segments sequentially over WebSockets. If logic decisions take longer than usual, pre-synthesized conversational fillers play in less than 1ms to keep the speech rhythm natural.
                </p>
                <div style={{ display: "flex", gap: "24px", color: "#38BDF8", fontSize: "0.9rem", fontWeight: 600, marginTop: "8px" }}>
                  <span>✓ EdgeTTS Stream Synthesis</span>
                  <span>✓ 1ms Background Fillers</span>
                  <span>✓ VAD Transcript Normalizer</span>
                </div>
              </div>
            )}

            {activeTab === "blueprint" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <h3 style={{ fontSize: "1.5rem", fontWeight: 800, color: "#FFFFFF" }}>📋 Dynamically Calibrated Blueprints</h3>
                <p style={{ color: "#94A3B8", lineHeight: "1.7", fontSize: "1.05rem" }}>
                  No more static questionnaires. Before the interview starts, the planner maps target job descriptions, resumes, and company styles (e.g. Google's scale, NVIDIA's kernel performance) into a structured concept tree. During the session, the LangGraph interviewer verifies specific conceptual claims, adjusts difficulty, and pivots topics when memory gaps are identified.
                </p>
                <div style={{ display: "flex", gap: "24px", color: "#38BDF8", fontSize: "0.9rem", fontWeight: 600, marginTop: "8px" }}>
                  <span>✓ Adaptive Concept Trees</span>
                  <span>✓ Resumes & Job Profiles Mapping</span>
                  <span>✓ Company Philosophy Profiles</span>
                </div>
              </div>
            )}

            {activeTab === "report" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <h3 style={{ fontSize: "1.5rem", fontWeight: 800, color: "#FFFFFF" }}>🎯 Five-Dimensional Performance Reports</h3>
                <p style={{ color: "#94A3B8", lineHeight: "1.7", fontSize: "1.05rem" }}>
                  Get calibrated scoring that helps you improve. Our evaluator agent grades five distinct zones (Architecture, Implementation, Design Choice Trade-offs, Future Optimization, and Project Ownership). Marks are awarded using a Knowledge Hierarchy (core ideas first, syntax details later) and technical scores are fully decoupled from fluency marks.
                </p>
                <div style={{ display: "flex", gap: "24px", color: "#38BDF8", fontSize: "0.9rem", fontWeight: 600, marginTop: "8px" }}>
                  <span>✓ Decoupled Technical & Speech Grades</span>
                  <span>✓ Verified Claims Logs</span>
                  <span>✓ Strengths & Weaknesses Checklist</span>
                </div>
              </div>
            )}

            {activeTab === "roadmap" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <h3 style={{ fontSize: "1.5rem", fontWeight: 800, color: "#FFFFFF" }}>📈 Actionable Learning Roadmap Plans</h3>
                <p style={{ color: "#94A3B8", lineHeight: "1.7", fontSize: "1.05rem" }}>
                  Close the loop on your preparation gaps. Weak spots identified in report cards automatically populate your topic mastery tracker. The system generates step-by-step roadmaps, recommend docs and articles from our pre-built knowledge index, and formats test questions. You can launch targeted, 15-minute focused re-interviews to verify your mastery.
                </p>
                <div style={{ display: "flex", gap: "24px", color: "#38BDF8", fontSize: "0.9rem", fontWeight: 600, marginTop: "8px" }}>
                  <span>✓ Dynamic Learning Timelines</span>
                  <span>✓ Knowledge Base Recommendations</span>
                  <span>✓ Focused Re-Interview Launcher</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      <style jsx global>{`
        .pulse-logo {
          animation: pulse-shadow 3s infinite ease-in-out;
        }
        @keyframes pulse-shadow {
          0%, 100% { box-shadow: 0 0 40px rgba(37, 99, 235, 0.4); transform: scale(1); }
          50% { box-shadow: 0 0 60px rgba(6, 182, 212, 0.6); transform: scale(1.05); }
        }
      `}</style>
    </div>
  );
}
