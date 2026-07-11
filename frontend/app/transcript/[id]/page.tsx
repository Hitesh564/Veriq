"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "../../context/AuthContext";
import { supabase } from "../../utils/supabaseClient";

interface TranscriptItem {
  sender: "interviewer" | "candidate";
  text: string;
  timestamp: string;
  topic?: string;
  audio_url?: string;
}

interface InterviewDetail {
  id: string;
  role: string;
  difficulty: string;
  duration_minutes: number;
  max_question_count: number;
  question_count: number;
  status: string;
  created_at: string;
  ended_at?: string;
  transcripts: TranscriptItem[];
  knowledge_model_json?: string;
}

export default function TranscriptView() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [session, setSession] = useState<InterviewDetail | null>(null);
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeClaimId, setActiveClaimId] = useState<string | null>(null);
  const [replayTurnIndex, setReplayTurnIndex] = useState<number>(-1);

  const handleScrollToQuestion = (turnName: string) => {
    const qNum = parseInt(turnName.replace("Question", "").trim());
    if (isNaN(qNum)) return;
    const el = document.getElementById(`msg-question-${qNum}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      const origBg = el.style.backgroundColor;
      el.style.backgroundColor = "var(--color-accent-bg)";
      el.style.transition = "background-color 0.5s ease";
      setTimeout(() => {
        el.style.backgroundColor = origBg || "transparent";
      }, 3000);
    }
  };

  const { user } = useAuth();

  useEffect(() => {
    if (!id || !user) return;

    let pollInterval: NodeJS.Timeout;

    const fetchData = async () => {
      try {
        const { data: { session: authSession } } = await supabase.auth.getSession();
        if (!authSession) {
          setError("Unauthenticated request");
          setLoading(false);
          return;
        }

        const headers = {
          "Authorization": `Bearer ${authSession.access_token}`
        };

        const [sessionData, reportData] = await Promise.all([
          fetch(`http://127.0.0.1:8000/api/v1/interviews/${id}`, { headers }).then((res) => {
            if (!res.ok) throw new Error("Could not find session data.");
            return res.json();
          }),
          fetch(`http://127.0.0.1:8000/api/evaluation/${id}`, { headers }).then((res) => {
            if (res.status === 404) return null;
            if (!res.ok) return null;
            return res.json();
          }).catch(() => null)
        ]);

        setSession(sessionData);
        setReport(reportData);
        setLoading(false);

        if (sessionData.status === "completed" && !reportData) {
          let attempts = 0;
          pollInterval = setInterval(() => {
            attempts++;
            if (attempts > 30) {
              clearInterval(pollInterval);
              return;
            }
            fetch(`http://127.0.0.1:8000/api/evaluation/${id}`, { headers })
              .then((res) => {
                if (res.ok) return res.json();
                return null;
              })
              .then((data) => {
                if (data) {
                  setReport(data);
                  clearInterval(pollInterval);
                }
              })
              .catch(() => {});
          }, 2000);
        }
      } catch (err: any) {
        console.error(err);
        setError("Failed to fetch interview transcript summary.");
        setLoading(false);
      }
    };

    fetchData();

    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [id, user]);

  useEffect(() => {
    if (replayTurnIndex >= 0 && session) {
      const el = document.getElementById(`msg-candidate-${replayTurnIndex + 1}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
        const origBg = el.style.backgroundColor;
        el.style.backgroundColor = "var(--color-accent-bg)";
        el.style.transition = "background-color 0.5s ease";
        setTimeout(() => {
          el.style.backgroundColor = origBg || "transparent";
        }, 3000);
      }
    }
  }, [replayTurnIndex, session]);

  const parseUTC = (dateString: string | Date | undefined): Date => {
    if (!dateString) return new Date();
    if (dateString instanceof Date) return dateString;
    let s = dateString;
    if (!s.endsWith("Z") && !s.includes("+") && !s.includes("-")) {
      s += "Z";
    }
    return new Date(s);
  };

  const formatDate = (dateString: string) => {
    const d = parseUTC(dateString);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const getDurationText = (created: string, ended?: string) => {
    if (!ended) return "N/A";
    const start = parseUTC(created).getTime();
    const end = parseUTC(ended).getTime();
    const diffSeconds = Math.max(0, Math.floor((end - start) / 1000));
    
    const minutes = Math.floor(diffSeconds / 60);
    const seconds = diffSeconds % 60;
    
    if (minutes === 0) return `${seconds}s`;
    return `${minutes}m ${seconds}s`;
  };

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "300px", flex: 1 }}>
        <p style={{ color: "var(--text-secondary)" }}>Loading session transcript...</p>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div style={{ maxWidth: "600px", margin: "40px auto", padding: "20px", textAlign: "center" }}>
        <div style={{ backgroundColor: "#FEF2F2", border: "1px solid #FCA5A5", color: "#991B1B", padding: "16px", borderRadius: "12px", marginBottom: "20px" }}>
          {error || "Interview details not found."}
        </div>
        <button onClick={() => router.push("/")} className="btn btn-secondary">Return to Dashboard</button>
      </div>
    );
  }

  return (
    <div style={{
      maxWidth: "960px",
      margin: "0 auto",
      display: "flex",
      flexDirection: "column",
      gap: "32px"
    }}>
      {/* Session Header Card */}
      <div className="card" style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <h1 style={{ fontFamily: "var(--font-outfit)", fontSize: "1.8rem", fontWeight: 800, letterSpacing: "-0.5px" }}>
              Interview Report
            </h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
              Practice mock evaluation feedback generated by the adaptive AI Coach.
            </p>
          </div>
          <div style={{ display: "flex", gap: "12px" }}>
            <button onClick={() => router.push("/learning")} className="btn btn-secondary">
              Study Plan
            </button>
            <button onClick={() => router.push("/new-interview")} className="btn btn-primary">
              Retake Practice
            </button>
          </div>
        </div>

        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "20px",
          paddingTop: "20px",
          borderTop: "1px solid var(--border-subtle)"
        }}>
          <div>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 700, display: "block", textTransform: "uppercase", marginBottom: "4px" }}>Role Target</span>
            <span style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--text-primary)" }}>{session.role}</span>
          </div>
          <div>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 700, display: "block", textTransform: "uppercase", marginBottom: "4px" }}>Difficulty</span>
            <span style={{ fontWeight: 700, fontSize: "0.95rem", textTransform: "capitalize", color: "var(--text-primary)" }}>{session.difficulty}</span>
          </div>
          <div>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 700, display: "block", textTransform: "uppercase", marginBottom: "4px" }}>Completed Date</span>
            <span style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--text-primary)" }}>{formatDate(session.ended_at || session.created_at)}</span>
          </div>
          <div>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 700, display: "block", textTransform: "uppercase", marginBottom: "4px" }}>Duration</span>
            <span style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--text-primary)" }}>{getDurationText(session.created_at, session.ended_at)}</span>
          </div>
        </div>
      </div>

      {session.status === "completed" && !report && (
        <div className="card" style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          padding: "48px 32px",
          backgroundColor: "var(--card-bg)",
          borderRadius: "16px",
          border: "1px dashed var(--border-subtle)",
          gap: "16px"
        }}>
          <div style={{
            width: "48px",
            height: "48px",
            borderRadius: "50%",
            border: "3px solid var(--border-subtle)",
            borderTopColor: "#3B82F6",
            animation: "spin 1s linear infinite"
          }} />
          <div>
            <h3 style={{ fontFamily: "var(--font-outfit)", fontSize: "1.15rem", fontWeight: 700, color: "var(--text-primary)" }}>
              Analyzing Interview Performance...
            </h3>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginTop: "6px", maxWidth: "460px" }}>
              Our AI Pilot Coach is parsing transcripts, measuring claims verification rates, and compiling your final feedback report. This usually takes 3-5 seconds.
            </p>
          </div>
          <style>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      )}

      {/* Recruiter Evaluation Report */}
      {report && (
        <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
          
          {/* Main Hire Recommendation */}
          <div className="card" style={{ borderLeft: "4px solid #3B82F6" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingBottom: "16px", marginBottom: "16px", borderBottom: "1px solid var(--border-subtle)", flexWrap: "wrap", gap: "12px" }}>
              <h2 style={{ fontFamily: "var(--font-outfit)", fontSize: "1.25rem", fontWeight: 700 }}>
                Hiring Assessment Summary
              </h2>
              {report.hire_recommendation && (
                <span className={`badge ${
                  report.hire_recommendation.toLowerCase().includes("strong hire") || 
                  (report.hire_recommendation.toLowerCase().includes("hire") && !report.hire_recommendation.toLowerCase().includes("no hire"))
                    ? "badge-success"
                    : "badge-error"
                }`} style={{ padding: "6px 14px", borderRadius: "12px" }}>
                  {report.hire_recommendation} (Confidence: {report.confidence_level || "Medium"})
                </span>
              )}
            </div>
            <p style={{ fontSize: "0.95rem", lineHeight: "1.6", color: "var(--text-secondary)", whiteSpace: "pre-line" }}>
              {report.summary}
            </p>
          </div>

          {/* Scores Metrics cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "24px" }}>
            
            <div className="card" style={{ textAlign: "center", padding: "20px" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase" }}>Overall Score</span>
              <span style={{ fontSize: "2.4rem", fontWeight: 800, color: "var(--color-primary)", display: "block", margin: "8px 0" }}>
                {report.overall_score}%
              </span>
            </div>

            <div className="card" style={{ textAlign: "center", padding: "20px" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase" }}>Technical Score</span>
              <span style={{ fontSize: "2.4rem", fontWeight: 800, color: "var(--color-accent)", display: "block", margin: "8px 0" }}>
                {report.technical_score}%
              </span>
            </div>

            <div className="card" style={{ textAlign: "center", padding: "20px" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase" }}>Communication</span>
              <span style={{ fontSize: "2.4rem", fontWeight: 800, color: "var(--text-primary)", display: "block", margin: "8px 0" }}>
                {report.communication_score}%
              </span>
            </div>

            {report.ownership_score !== undefined && report.ownership_score !== null && (
              <div className="card" style={{ textAlign: "center", padding: "20px" }}>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase" }}>Project Ownership</span>
                <span style={{ fontSize: "2.4rem", fontWeight: 800, color: "var(--color-success)", display: "block", margin: "8px 0" }}>
                  {report.ownership_score}%
                </span>
              </div>
            )}
          </div>

          {/* Gaps, Gaps & Claims Checklist */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "24px" }}>
            
            {/* Strengths & Weaknesses */}
            <div className="card" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              <h3 style={{ fontSize: "1.05rem", fontWeight: 700, borderBottom: "1px solid var(--border-subtle)", paddingBottom: "10px" }}>
                Strengths & Gaps
              </h3>
              
              <div>
                <h4 style={{ fontSize: "0.8rem", color: "var(--color-success)", fontWeight: 700, textTransform: "uppercase", marginBottom: "8px" }}>✓ Core Strengths</h4>
                <ul style={{ paddingLeft: "16px", margin: 0, fontSize: "0.9rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
                  {report.strengths?.map((s: string, i: number) => (
                    <li key={i} style={{ marginBottom: "6px" }}>{s}</li>
                  ))}
                </ul>
              </div>

              <div>
                <h4 style={{ fontSize: "0.8rem", color: "var(--color-warning)", fontWeight: 700, textTransform: "uppercase", marginBottom: "8px" }}>⚠️ Identified Gaps</h4>
                {report.categorized_weaknesses && Object.keys(report.categorized_weaknesses).length > 0 ? (
                  Object.entries(report.categorized_weaknesses).map(([cat, list]: any) => (
                    list && list.length > 0 && (
                      <div key={cat} style={{ marginBottom: "10px" }}>
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 600, textTransform: "capitalize", display: "block", marginBottom: "4px" }}>
                          {cat.replace("_", " ")}
                        </span>
                        <ul style={{ paddingLeft: "16px", margin: 0, fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
                          {list.map((item: string, idx: number) => (
                            <li key={idx} style={{ marginBottom: "3px" }}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )
                  ))
                ) : (
                  <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>No major weakness identified.</p>
                )}
              </div>
            </div>

            {/* Claims Verification Matrix */}
            <div className="card" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              <h3 style={{ fontSize: "1.05rem", fontWeight: 700, borderBottom: "1px solid var(--border-subtle)", paddingBottom: "10px" }}>
                Claims Verification Matrix
              </h3>
              
              {(() => {
                let claims: any[] = [];
                if (session?.knowledge_model_json) {
                  try {
                    const km = JSON.parse(session.knowledge_model_json);
                    claims = km.claims || km.unproven_claims || [];
                  } catch (e) {}
                }
                
                if (claims.length === 0) {
                  return <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>No technical claims found in resume or discussion.</p>;
                }
                
                return (
                  <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    {claims.map((claim, idx) => {
                      const claimId = `claim-${idx}`;
                      const isExpanded = activeClaimId === claimId;
                      const confidence = claim.confidence !== undefined ? claim.confidence : (claim.state === "VERIFIED" ? 100 : 0);
                      
                      const filledBlocks = Math.round(confidence / 10);
                      const emptyBlocks = 10 - filledBlocks;
                      const strengthBarStr = "█".repeat(filledBlocks) + "░".repeat(emptyBlocks);
                      
                      const coverage = (claim.evidence_coverage || {
                        architecture: claim.verified_evidence?.includes("architecture") ? "Strong" : "Missing",
                        implementation: claim.verified_evidence?.includes("implementation") ? "Strong" : "Missing",
                        tradeoffs: claim.verified_evidence?.includes("tradeoffs") ? "Strong" : "Missing",
                        debugging: claim.verified_evidence?.includes("debugging") ? "Strong" : "Missing",
                        scaling: claim.verified_evidence?.includes("scaling") ? "Strong" : "Missing"
                      }) as Record<string, string>;
                      
                      const supporting = claim.supporting_turns || [];
                      
                      return (
                        <div key={idx} style={{
                          border: "1px solid var(--border-subtle)",
                          borderRadius: "12px",
                          overflow: "hidden",
                          backgroundColor: isExpanded ? "var(--bg-subtle)" : "transparent",
                          transition: "all 0.2s ease"
                        }}>
                          {/* Card Header */}
                          <div 
                            onClick={() => setActiveClaimId(isExpanded ? null : claimId)}
                            style={{
                              padding: "14px 16px",
                              cursor: "pointer",
                              display: "flex",
                              justifyContent: "space-between",
                              alignItems: "center",
                              userSelect: "none"
                            }}
                          >
                            <div style={{ display: "flex", flexDirection: "column", gap: "4px", flex: 1, marginRight: "16px" }}>
                              <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase" }}>
                                {claim.project || "General Project"}
                              </span>
                              <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)" }}>
                                {claim.claim}
                              </span>
                              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "4px", flexWrap: "wrap" }}>
                                <span style={{ fontSize: "0.75rem", fontFamily: "monospace", color: "var(--color-accent)", fontWeight: 700 }}>
                                  Strength: {strengthBarStr} {confidence}%
                                </span>
                                <span className={`badge ${
                                  claim.state === "VERIFIED" ? "badge-success" : (claim.state === "FAILED_VERIFICATION" ? "badge-error" : "badge-warning")
                                }`} style={{ fontSize: "0.65rem", padding: "1px 6px" }}>
                                  {claim.state || "UNVERIFIED"}
                                </span>
                              </div>
                            </div>
                            <span style={{ fontSize: "1.1rem", color: "var(--text-muted)" }}>
                              {isExpanded ? "−" : "+"}
                            </span>
                          </div>
                          
                          {/* Expanded Details */}
                          {isExpanded && (
                            <div style={{
                              padding: "14px 16px",
                              borderTop: "1px solid var(--border-subtle)",
                              backgroundColor: "var(--card-bg)",
                              display: "flex",
                              flexDirection: "column",
                              gap: "14px"
                            }}>
                              <div>
                                <h4 style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", marginBottom: "6px" }}>
                                  Evidence Coverage Rating
                                </h4>
                                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: "8px" }}>
                                  {Object.entries(coverage).map(([cat, strength]: any) => (
                                    <div key={cat} style={{
                                      padding: "6px 10px",
                                      borderRadius: "6px",
                                      backgroundColor: "var(--bg-subtle)",
                                      border: "1px solid var(--border-subtle)",
                                      display: "flex",
                                      flexDirection: "column",
                                      gap: "2px"
                                    }}>
                                      <span style={{ fontSize: "0.65rem", color: "var(--text-muted)", textTransform: "capitalize" }}>{cat}</span>
                                      <span style={{ fontSize: "0.75rem", fontWeight: 700, color: strength === "Strong" ? "var(--color-success)" : (strength === "Moderate" ? "var(--color-warning)" : "var(--text-muted)") }}>
                                        {strength === "Strong" ? "✅ Strong" : (strength === "Moderate" ? "⚠️ Moderate" : "❌ Missing")}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                              
                              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px" }}>
                                <div>
                                  <span style={{ fontSize: "0.7rem", color: "var(--color-success)", fontWeight: 700, textTransform: "uppercase", display: "block", marginBottom: "4px" }}>
                                    Verified Categories
                                  </span>
                                  <ul style={{ paddingLeft: "16px", margin: 0, fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
                                    {Object.entries(coverage).filter(([_, s]) => s === "Strong" || s === "Moderate").map(([cat, s]) => (
                                      <li key={cat} style={{ marginBottom: "3px" }}>
                                        Demonstrated <strong>{cat}</strong> skills ({s}).
                                      </li>
                                    ))}
                                    {Object.entries(coverage).filter(([_, s]) => s === "Strong" || s === "Moderate").length === 0 && (
                                      <li style={{ color: "var(--text-muted)", listStyleType: "none", marginLeft: "-16px" }}>No categories verified yet.</li>
                                    )}
                                  </ul>
                                </div>
                                
                                <div>
                                  <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", display: "block", marginBottom: "4px" }}>
                                    Missing/Weak Areas
                                  </span>
                                  <ul style={{ paddingLeft: "16px", margin: 0, fontSize: "0.75rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
                                    {Object.entries(coverage).filter(([_, s]) => s === "Missing").map(([cat]) => (
                                      <li key={cat} style={{ marginBottom: "3px" }}>
                                        No <strong>{cat}</strong> choices probed.
                                      </li>
                                    ))}
                                    {Object.entries(coverage).filter(([_, s]) => s === "Missing").length === 0 && (
                                      <li style={{ color: "var(--color-success)", listStyleType: "none", marginLeft: "-16px" }}>✓ All categories fully covered!</li>
                                    )}
                                  </ul>
                                </div>
                              </div>
                              
                              {supporting.length > 0 && (
                                <div style={{ borderTop: "1px dashed var(--border-subtle)", paddingTop: "8px", display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
                                  <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 600 }}>Supporting Turns:</span>
                                  {supporting.map((turn: string, i: number) => (
                                    <button 
                                      key={i} 
                                      onClick={() => handleScrollToQuestion(turn)}
                                      style={{
                                        border: "none",
                                        backgroundColor: "var(--color-accent-bg)",
                                        color: "var(--color-accent)",
                                        padding: "3px 8px",
                                        borderRadius: "4px",
                                        fontSize: "0.7rem",
                                        fontWeight: 600,
                                        cursor: "pointer",
                                        transition: "opacity 0.2s"
                                      }}
                                    >
                                      {turn} ↗
                                    </button>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                );
              })()}
            </div>
          </div>

          {/* Coaching & Suggested Study Materials */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "24px" }}>
            
            {/* Learning Plan priorities */}
            <div className="card" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <h3 style={{ fontSize: "1.05rem", fontWeight: 700, borderBottom: "1px solid var(--border-subtle)", paddingBottom: "10px" }}>
                Target Learning Priorities
              </h3>
              
              {report.learning_plan ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  {report.learning_plan.high_priority?.length > 0 && (
                    <div>
                      <span className="badge badge-error" style={{ fontSize: "0.7rem", marginBottom: "4px" }}>HIGH PRIORITY</span>
                      <ul style={{ paddingLeft: "16px", margin: 0, fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                        {report.learning_plan.high_priority.map((item: string, i: number) => (
                          <li key={i} style={{ marginBottom: "2px" }}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {report.learning_plan.medium_priority?.length > 0 && (
                    <div>
                      <span className="badge badge-warning" style={{ fontSize: "0.7rem", marginBottom: "4px" }}>MEDIUM PRIORITY</span>
                      <ul style={{ paddingLeft: "16px", margin: 0, fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                        {report.learning_plan.medium_priority.map((item: string, i: number) => (
                          <li key={i} style={{ marginBottom: "2px" }}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ) : (
                <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>No priorities logged.</p>
              )}
            </div>

            {/* General Recommendations */}
            <div className="card" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <h3 style={{ fontSize: "1.05rem", fontWeight: 700, borderBottom: "1px solid var(--border-subtle)", paddingBottom: "10px" }}>
                Coaching Suggestions
              </h3>
              <ul style={{ paddingLeft: "16px", margin: 0, fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: "1.5" }}>
                {report.recommendations?.map((rec: string, i: number) => (
                  <li key={i} style={{ marginBottom: "6px" }}>{rec}</li>
                )) || (
                  <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>No recommendations drafted.</p>
                )}
              </ul>
            </div>
          </div>

        </div>
      )}

      {/* Interactive Interview Replay Player */}
      {session && report && (
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: "20px", marginBottom: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "12px", flexWrap: "wrap", gap: "10px" }}>
            <h2 style={{ fontFamily: "var(--font-outfit)", fontSize: "1.2rem", fontWeight: 700 }}>
              Interactive Interview Replay
            </h2>
            <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Step through the candidate's verification milestones turn-by-turn.
            </span>
          </div>
          
          {(() => {
            const candidateTurns = session.transcripts
              .map((t, originalIdx) => ({ ...t, originalIdx }))
              .filter(t => t.sender === "candidate");
              
            if (candidateTurns.length === 0) {
              return <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>No dialogue exchanges completed yet.</p>;
            }
            
            const activeIndex = replayTurnIndex >= 0 ? replayTurnIndex : 0;
            const activeTurn = candidateTurns[activeIndex];
            
            let metadata: any = null;
            if (activeTurn && (activeTurn as any).turn_metadata_json) {
              try {
                metadata = JSON.parse((activeTurn as any).turn_metadata_json);
              } catch (e) {}
            }
            
            return (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                {/* Controller Bar */}
                <div style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  backgroundColor: "var(--bg-subtle)",
                  padding: "12px 16px",
                  borderRadius: "8px",
                  border: "1px solid var(--border-subtle)",
                  flexWrap: "wrap",
                  gap: "10px"
                }}>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button 
                      disabled={replayTurnIndex <= 0}
                      onClick={() => setReplayTurnIndex(prev => Math.max(0, prev - 1))}
                      className="btn btn-secondary"
                      style={{ padding: "4px 12px", fontSize: "0.8rem", opacity: replayTurnIndex <= 0 ? 0.5 : 1 }}
                    >
                      ◀ Prev
                    </button>
                    <button 
                      disabled={replayTurnIndex >= candidateTurns.length - 1}
                      onClick={() => {
                        if (replayTurnIndex < 0) setReplayTurnIndex(0);
                        else setReplayTurnIndex(prev => Math.min(candidateTurns.length - 1, prev + 1));
                      }}
                      className="btn btn-primary"
                      style={{ padding: "4px 12px", fontSize: "0.8rem", opacity: replayTurnIndex >= candidateTurns.length - 1 ? 0.5 : 1 }}
                    >
                      Next ▶
                    </button>
                  </div>
                  
                  <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-primary)" }}>
                    Turn {replayTurnIndex >= 0 ? replayTurnIndex + 1 : 0} of {candidateTurns.length}
                  </span>
                  
                  <button 
                    onClick={() => setReplayTurnIndex(replayTurnIndex >= 0 ? -1 : 0)}
                    className="btn btn-secondary"
                    style={{ padding: "4px 12px", fontSize: "0.8rem" }}
                  >
                    {replayTurnIndex >= 0 ? "Reset Player" : "Start Replay"}
                  </button>
                </div>
                
                {/* Replay Details Panel */}
                {replayTurnIndex >= 0 && (
                  <div style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                    gap: "16px",
                    padding: "16px",
                    borderRadius: "12px",
                    border: "1px solid rgba(59, 130, 246, 0.2)",
                    backgroundColor: "rgba(59, 130, 246, 0.02)"
                  }}>
                    {/* Left Column: Dialogue snippet */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                      <div>
                        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase" }}>Question Probed</span>
                        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", fontStyle: "italic", margin: "4px 0", lineHeight: "1.4" }}>
                          "{session.transcripts[activeTurn.originalIdx - 1]?.text || "First question"}"
                        </p>
                      </div>
                      <div>
                        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase" }}>Candidate Answer</span>
                        <p style={{ fontSize: "0.85rem", color: "var(--text-primary)", margin: "4px 0", lineHeight: "1.4" }}>
                          "{activeTurn.text.slice(0, 150)}..."
                        </p>
                      </div>
                    </div>
                    
                    {/* Right Column: Turn Verification Scorecard */}
                    <div style={{
                      padding: "12px",
                      borderRadius: "8px",
                      backgroundColor: "var(--card-bg)",
                      border: "1px solid var(--border-subtle)",
                      display: "flex",
                      flexDirection: "column",
                      gap: "8px"
                    }}>
                      <span style={{ fontSize: "0.75rem", color: "var(--color-accent)", fontWeight: 700, textTransform: "uppercase", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "4px" }}>
                        Turn Metrics Scorecard
                      </span>
                      
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem" }}>
                        <span style={{ color: "var(--text-muted)" }}>Interview Phase:</span>
                        <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>{metadata?.phase || "TECHNICAL"}</span>
                      </div>
                      
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem" }}>
                        <span style={{ color: "var(--text-muted)" }}>Active Objective:</span>
                        <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>{metadata?.objective || "None"}</span>
                      </div>
                      
                      {metadata?.claim && metadata?.claim !== "None" && (
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem" }}>
                          <span style={{ color: "var(--text-muted)" }}>Active Claim:</span>
                          <span style={{ fontWeight: 600, color: "var(--text-primary)", maxWidth: "160px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            {metadata.claim}
                          </span>
                        </div>
                      )}
                      
                      {metadata?.confidence_gain !== undefined && (
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem" }}>
                          <span style={{ color: "var(--text-muted)" }}>Confidence Increase:</span>
                          <span style={{ fontWeight: 700, color: "var(--color-success)" }}>+{metadata.confidence_gain}%</span>
                        </div>
                      )}
                      
                      {metadata?.evidence && Object.keys(metadata.evidence).length > 0 && (
                        <div style={{ marginTop: "4px" }}>
                          <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", display: "block", marginBottom: "4px" }}>
                            Evidence Categories Detected
                          </span>
                          <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                            {Object.entries(metadata.evidence).map(([cat, strength]: any) => (
                              <span key={cat} className="badge badge-success" style={{ fontSize: "0.65rem", padding: "1px 6px" }}>
                                {cat} ({strength})
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })()}
        </div>
      )}

      {/* Recruiter Evidence Timeline */}
      {session && report && (
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: "20px", marginBottom: "24px" }}>
          <h3 style={{ fontFamily: "var(--font-outfit)", fontSize: "1.05rem", fontWeight: 700, borderBottom: "1px solid var(--border-subtle)", paddingBottom: "10px" }}>
            Recruiter Evidence Timeline
          </h3>
          
          {(() => {
            const candidateTurns = session.transcripts.filter(t => t.sender === "candidate");
            if (candidateTurns.length === 0) {
              return <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Timeline empty.</p>;
            }
            return (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px", paddingLeft: "12px", borderLeft: "2px solid var(--border-subtle)", margin: "8px 0" }}>
                {candidateTurns.map((turn, index) => {
                  let metadata: any = null;
                  if ((turn as any).turn_metadata_json) {
                    try {
                      metadata = JSON.parse((turn as any).turn_metadata_json);
                    } catch (e) {}
                  }
                  
                  return (
                    <div key={index} style={{ position: "relative", paddingLeft: "16px" }}>
                      {/* Circle Node */}
                      <div style={{
                        position: "absolute",
                        left: "-23px",
                        top: "4px",
                        width: "10px",
                        height: "10px",
                        borderRadius: "50%",
                        backgroundColor: metadata?.confidence_gain > 0 ? "var(--color-success)" : "var(--border-subtle)",
                        border: "2px solid var(--card-bg)"
                      }} />
                      
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: "8px" }}>
                        <span style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--text-primary)" }}>
                          Turn {index + 1}: {metadata?.objective || "Introduction"}
                        </span>
                        {metadata?.confidence_gain > 0 && (
                          <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--color-success)" }}>
                            +{metadata.confidence_gain}% Confidence
                          </span>
                        )}
                      </div>
                      <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "4px 0", lineHeight: "1.4" }}>
                        <strong>Answer:</strong> "{turn.text.slice(0, 160)}..."
                      </p>
                      {metadata?.claim && metadata.claim !== "None" && (
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                          Probed Claim: <em>{metadata.claim}</em>
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            );
          })()}
        </div>
      )}

      {/* Transcript Log Timeline Section */}
      <div className="card" style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        <h2 style={{ fontFamily: "var(--font-outfit)", fontSize: "1.2rem", fontWeight: 700, borderBottom: "1px solid var(--border-subtle)", paddingBottom: "12px" }}>
          Dialogue Transcript ({session.transcripts.length} Exchanges)
        </h2>

        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {(() => {
            let interviewerCount = 0;
            let candidateCount = 0;
            return session.transcripts.map((item, index) => {
              const isInterviewer = item.sender === "interviewer";
              if (isInterviewer) interviewerCount++;
              else candidateCount++;
              
              const elementId = isInterviewer ? `msg-question-${interviewerCount}` : `msg-candidate-${candidateCount}`;
              const isReplayingThis = !isInterviewer && (replayTurnIndex === candidateCount - 1);
              
              return (
                <div
                  key={index}
                  id={elementId}
                  style={{
                    display: "flex",
                    gap: "16px",
                    alignItems: "flex-start",
                    borderBottom: index === session.transcripts.length - 1 ? "none" : "1px solid var(--border-subtle)",
                    paddingBottom: "16px",
                    paddingTop: "8px",
                    paddingLeft: "8px",
                    paddingRight: "8px",
                    borderRadius: "8px",
                    backgroundColor: isReplayingThis ? "rgba(59, 130, 246, 0.08)" : "transparent",
                    border: isReplayingThis ? "1px solid rgba(59, 130, 246, 0.3)" : "none",
                    transition: "all 0.3s ease"
                  }}
                >
                  <div style={{
                    width: "36px",
                    height: "36px",
                    borderRadius: "8px",
                    backgroundColor: isInterviewer ? "var(--color-accent-bg)" : "#EFF6FF",
                    color: isInterviewer ? "var(--color-accent)" : "#2563EB",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    fontSize: "0.8rem",
                    flexShrink: 0
                  }}>
                    {isInterviewer ? "AI" : "ME"}
                  </div>

                  <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "4px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                      <span style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--text-primary)" }}>
                        {isInterviewer ? "AI Pilot Coach" : "You (Candidate)"}
                      </span>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        {parseUTC(item.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    
                    <p style={{
                      color: "var(--text-secondary)",
                      fontSize: "0.9rem",
                      lineHeight: "1.5",
                      whiteSpace: "pre-line"
                    }}>
                      {item.text}
                    </p>

                    {!isInterviewer && item.audio_url && (
                      <div style={{ marginTop: "8px" }}>
                        <audio controls src={item.audio_url} style={{ height: "28px", maxWidth: "240px" }} />
                      </div>
                    )}
                  </div>
                </div>
              );
            });
          })()}
        </div>
      </div>
    </div>
  );
}
