"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../context/AuthContext";
import { supabase } from "../utils/supabaseClient";
import { safeFetch, safeJsonFetch } from "../utils/api";

export default function NewInterviewWizard() {
  const router = useRouter();
  const { user, triggerAuthGuard } = useAuth();
  const PREPARE_INTERVIEW_TIMEOUT_MS = 60000;
  
  // Wizard States
  const [step, setStep] = useState(1);
  const [error, setError] = useState("");
  const [credits, setCredits] = useState<{
    is_subscribed: boolean;
    interviews_completed: number;
    interviews_remaining: number;
  } | null>(null);

  React.useEffect(() => {
    if (!user) return;
    
    const fetchCredits = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;
      const data = await safeJsonFetch<any>("/api/v1/payments/subscription", {
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });
      if (data) {
        setCredits(data);
      }
    };
    fetchCredits();
  }, [user]);

  const handleUpgrade = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;
      const res = await safeFetch("/api/v1/payments/create-checkout-session?plan_id=pro", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });
      if (res?.ok) {
        const { url } = await res.json();
        if (url) {
          window.location.href = url;
        }
      }
    } catch (err: any) {
      setError(`Upgrade failed: ${err.message}`);
    }
  };

  const limitReached = credits && !credits.is_subscribed && credits.interviews_remaining <= 0;
  
  // Form States
  const [mode, setMode] = useState("role"); // "role", "resume", "jd", "resume_jd"
  const [company, setCompany] = useState("Target Company"); // "Target Company", "Google", "Amazon", "NVIDIA", "Custom"
  const [customCompany, setCustomCompany] = useState("");
  const [role, setRole] = useState("AI Engineer");
  const [difficulty, setDifficulty] = useState("medium");
  const [duration, setDuration] = useState(5);
  
  // Text & Parsing
  const [resumeText, setResumeText] = useState("");
  const [jdText, setJdText] = useState("");
  const [parsingResume, setParsingResume] = useState(false);
  const [parsingJd, setParsingJd] = useState(false);
  
  // Prep Details Preview
  const [preparedSession, setPreparedSession] = useState<any>(null);
  const [loadingBlueprint, setLoadingBlueprint] = useState(false);

  const roles = [
    "AI Engineer",
    "Data Scientist",
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer"
  ];
  const difficulties = ["easy", "medium", "hard"];
  const durations = [
    { value: 5, label: "5 Mins (5 Qs)" },
    { value: 15, label: "15 Mins (10 Qs)" },
    { value: 30, label: "30 Mins (15 Qs)" }
  ];
  const companies = ["Target Company", "Google", "Amazon", "NVIDIA", "Custom"];

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>, type: "resume" | "jd") => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (type === "resume") setParsingResume(true);
    else setParsingJd(true);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await safeFetch("/api/v1/interviews/parse-file", {
        method: "POST",
        body: formData
      });

      if (!res || !res.ok) throw new Error("Failed to parse file.");
      const data = await res.json();

      if (type === "resume") {
        setResumeText(data.text);
      } else {
        setJdText(data.text);
      }
    } catch (err: any) {
      setError(`Error parsing ${type === "resume" ? "Resume" : "Job Description"}: ${err.message}`);
    } finally {
      if (type === "resume") setParsingResume(false);
      else setParsingJd(false);
    }
  };

  const handleMoveToReview = async () => {
    // Validate Step 2 before moving forward
    if ((mode === "resume" || mode === "resume_jd") && !resumeText) {
      setError("Please upload your resume to proceed in resume mode.");
      return;
    }
    if ((mode === "jd" || mode === "resume_jd") && !jdText) {
      setError("Please upload the job description to proceed in JD mode.");
      return;
    }

    const triggerPrepare = async (authToken: string) => {
      setLoadingBlueprint(true);
      setError("");

      try {
        const res = await safeFetch("/api/v1/interviews/prepare-interview", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${authToken}`
          },
          body: JSON.stringify({
            role,
            difficulty,
            duration_minutes: duration,
            mode: mode === "role" ? "quick" : mode,
            resume_text: (mode === "resume" || mode === "resume_jd") ? resumeText : null,
            jd_text: (mode === "jd" || mode === "resume_jd") ? jdText : null,
            company_name: company === "Custom" ? customCompany : company
          })
        }, PREPARE_INTERVIEW_TIMEOUT_MS);

        if (!res || !res.ok) {
          let backendDetail = "";
          try {
            const errorData = res ? await res.json() : null;
            backendDetail = errorData?.detail || errorData?.message || "";
          } catch {
            try {
              backendDetail = res ? await res.text() : "";
            } catch {
              backendDetail = "";
            }
          }

          const statusLabel = res ? `${res.status} ${res.statusText}`.trim() : "Network unavailable";
          throw new Error(
            backendDetail
              ? `Failed to prepare interview blueprint (${statusLabel}): ${backendDetail}`
              : `Failed to prepare interview blueprint (${statusLabel}).`
          );
        }

        const data = await res.json();
        setPreparedSession(data);
        setStep(4);
      } catch (err: any) {
        setError(err.message || "Failed to initialize interview plan.");
      } finally {
        setLoadingBlueprint(false);
      }
    };

    triggerAuthGuard(() => {
      supabase.auth.getSession().then(({ data: { session } }) => {
        if (session) {
          triggerPrepare(session.access_token);
        } else {
          setError("Failed to resolve authentication session");
        }
      });
    });
  };

  const handleStartInterview = () => {
    if (!preparedSession) return;
    router.push(`/interview/${preparedSession.id}/voice`);
  };

  // UI Helpers
  const renderStepIndicators = () => (
    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "40px", position: "relative" }}>
      {/* Background connecting line */}
      <div style={{
        position: "absolute",
        top: "16px",
        left: "5%",
        right: "5%",
        height: "2px",
        backgroundColor: "var(--border-subtle)",
        zIndex: 0
      }} />
      <div style={{
        position: "absolute",
        top: "16px",
        left: "5%",
        width: `${((step - 1) / 3) * 90}%`,
        height: "2px",
        backgroundColor: "var(--color-primary)",
        transition: "width 0.3s ease",
        zIndex: 0
      }} />

      {[
        { num: 1, label: "Mode" },
        { num: 2, label: "Uploads" },
        { num: 3, label: "Config" },
        { num: 4, label: "Review" }
      ].map((s) => {
        const isCurrent = step === s.num;
        const isCompleted = step > s.num;
        return (
          <div key={s.num} style={{ display: "flex", flexDirection: "column", alignItems: "center", zIndex: 1, flex: 1 }}>
            <div style={{
              width: "32px",
              height: "32px",
              borderRadius: "50%",
              backgroundColor: isCompleted ? "var(--color-primary)" : isCurrent ? "var(--bg-main)" : "var(--bg-main)",
              border: isCurrent ? "2px solid var(--color-primary)" : isCompleted ? "2px solid var(--color-primary)" : "2px solid var(--border-subtle)",
              color: isCompleted ? "#FFFFFF" : isCurrent ? "var(--color-primary)" : "var(--text-muted)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: "0.85rem",
              transition: "all 0.2s ease",
              fontFamily: "var(--font-mono)"
            }}>
              {isCompleted ? "✓" : s.num}
            </div>
            <span style={{
              marginTop: "8px",
              fontSize: "0.8rem",
              fontWeight: isCurrent || isCompleted ? 600 : 500,
              color: isCurrent ? "var(--color-primary)" : isCompleted ? "var(--text-primary)" : "var(--text-muted)"
            }}>
              {s.label}
            </span>
          </div>
        );
      })}
    </div>
  );

  if (limitReached) {
    return (
      <div style={{ maxWidth: "600px", margin: "40px auto", textAlign: "center" }} className="card">
        <div style={{ fontSize: "3.5rem", marginBottom: "20px" }}>🚀</div>
        <h2 style={{ fontFamily: "var(--font-outfit)", fontSize: "2rem", fontWeight: 800, color: "var(--text-primary)", marginBottom: "12px" }}>
          Upgrade to Veriq Pro
        </h2>
        <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", lineHeight: "1.6", marginBottom: "32px" }}>
          You have completed all 3 of your free mock interview sessions. Upgrade today to unlock unlimited simulations, direct resume matching, and deep technical evaluation insights.
        </p>
        
        <div style={{
          backgroundColor: "rgba(255, 255, 255, 0.02)",
          borderRadius: "12px",
          border: "1px solid var(--border-subtle)",
          padding: "24px",
          marginBottom: "32px",
          textAlign: "left"
        }}>
          <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "16px", color: "var(--text-primary)" }}>Pro Features Include:</h3>
          <ul style={{ listStyleType: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "12px" }}>
            <li style={{ display: "flex", gap: "10px", fontSize: "0.95rem", color: "var(--text-secondary)" }}>
              ✅ <strong>Unlimited Mocks:</strong> Conduct unlimited technical, system design, and behavioral interviews.
            </li>
            <li style={{ display: "flex", gap: "10px", fontSize: "0.95rem", color: "var(--text-secondary)" }}>
              ✅ <strong>Advanced ASR & TTS:</strong> High-performance speech processing and streaming byte playback.
            </li>
            <li style={{ display: "flex", gap: "10px", fontSize: "0.95rem", color: "var(--text-secondary)" }}>
              ✅ <strong>Resume & JD Mapping:</strong> Full profile comparison and technical gap blueprints.
            </li>
            <li style={{ display: "flex", gap: "10px", fontSize: "0.95rem", color: "var(--text-secondary)" }}>
              ✅ <strong>Detailed Recruiter Reports:</strong> Exportable performance analytics, readiness match metrics, and feedback.
            </li>
          </ul>
        </div>
        
        <div style={{ display: "flex", flexDirection: "column", gap: "12px", alignItems: "center" }}>
          <div style={{ fontSize: "2rem", fontWeight: 800, color: "var(--text-primary)" }}>
            $19.99 <span style={{ fontSize: "1rem", fontWeight: 500, color: "var(--text-secondary)" }}>/ month</span>
          </div>
          <button
            onClick={handleUpgrade}
            className="btn btn-primary"
            style={{ width: "100%", padding: "14px 28px", fontSize: "1.1rem" }}
          >
            Unlock Unlimited Mocks Now
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: "720px", margin: "0 auto" }}>
      {/* Step Indicators */}
      {renderStepIndicators()}

      {/* Error Alert */}
      {error && (
        <div style={{
          backgroundColor: "#FEF2F2",
          border: "1px solid #FCA5A5",
          color: "#991B1B",
          padding: "12px 16px",
          borderRadius: "8px",
          marginBottom: "24px",
          fontSize: "0.9rem"
        }}>
          {error}
        </div>
      )}

      {/* WIZARD CONTAINER */}
      <div className="card" style={{ padding: "32px" }}>
        
        {/* STEP 1: INTERVIEW MODE */}
        {step === 1 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            <div>
              <h2 style={{ fontSize: "1.3rem", fontWeight: 700, fontFamily: "var(--font-outfit)", marginBottom: "8px" }}>
                Select Interview Focus
              </h2>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                Choose how you want to center your mock interview topics.
              </p>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              {[
                { id: "role", title: "Role-Based", desc: "Evaluate general skills for your target role.", icon: "💼" },
                { id: "resume", title: "Resume-Based", desc: "Focus specifically on claims/projects on your resume.", icon: "📄" },
                { id: "jd", title: "JD-Based", desc: "Align questions directly to a job description.", icon: "📋" },
                { id: "resume_jd", title: "Resume + JD", desc: "Perform a gap analysis matching your resume to requirements.", icon: "⚡" }
              ].map((m) => {
                const isSelected = mode === m.id;
                return (
                  <div
                    key={m.id}
                    onClick={() => setMode(m.id)}
                    style={{
                      border: isSelected ? "2px solid var(--color-primary)" : "1px solid var(--border-subtle)",
                      borderRadius: "12px",
                      padding: "20px",
                      cursor: "pointer",
                      backgroundColor: isSelected ? "rgba(213, 173, 52, 0.12)" : "transparent",
                      transition: "all 0.15s ease"
                    }}
                  >
                    <div style={{ fontSize: "1.8rem", marginBottom: "12px" }}>{m.icon}</div>
                    <h3 style={{ fontSize: "1rem", fontWeight: 700, color: isSelected ? "var(--color-primary)" : "var(--text-primary)", marginBottom: "4px" }}>
                      {m.title}
                    </h3>
                    <p style={{ fontSize: "0.8rem", color: isSelected ? "var(--text-accent)" : "var(--text-secondary)", lineHeight: "1.4" }}>
                      {m.desc}
                    </p>
                  </div>
                );
              })}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "12px" }}>
              <button
                onClick={() => setStep(mode === "role" ? 3 : 2)}
                className="btn btn-primary"
              >
                Continue
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: FILE UPLOADS */}
        {step === 2 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            <div>
              <h2 style={{ fontSize: "1.3rem", fontWeight: 700, fontFamily: "var(--font-outfit)", marginBottom: "8px" }}>
                Upload Materials
              </h2>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                Upload PDF files to parse skills, projects, and requirements.
              </p>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              {/* Resume Upload Block */}
              {(mode === "resume" || mode === "resume_jd") && (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <label style={{ fontSize: "0.85rem", fontWeight: 600 }}>Candidate Resume (PDF)</label>
                  <div style={{
                    border: "2px dashed var(--border-main)",
                    borderRadius: "8px",
                    padding: "20px",
                    textAlign: "center",
                    backgroundColor: "rgba(255, 255, 255, 0.82)",
                    position: "relative"
                  }}>
                    {parsingResume ? (
                      <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                        Parsing resume claims...
                      </div>
                    ) : resumeText ? (
                      <div style={{ color: "var(--color-success)", fontSize: "0.85rem", fontWeight: 600 }}>
                        ✓ Resume parsed successfully ({resumeText.slice(0, 45)}...)
                      </div>
                    ) : (
                      <div>
                        <input
                          type="file"
                          accept="application/pdf"
                          onChange={(e) => handleFileUpload(e, "resume")}
                          style={{ position: "absolute", inset: 0, opacity: 0, cursor: "pointer" }}
                        />
                        <span style={{ fontSize: "0.85rem", color: "var(--color-primary)", fontWeight: 600 }}>Upload File</span>
                        <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginLeft: "4px" }}>or drag it here</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* JD Upload Block */}
              {(mode === "jd" || mode === "resume_jd") && (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <label style={{ fontSize: "0.85rem", fontWeight: 600 }}>Job Description (PDF)</label>
                  <div style={{
                    border: "2px dashed var(--border-main)",
                    borderRadius: "8px",
                    padding: "20px",
                    textAlign: "center",
                    backgroundColor: "rgba(255, 255, 255, 0.82)",
                    position: "relative"
                  }}>
                    {parsingJd ? (
                      <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                        Parsing job criteria...
                      </div>
                    ) : jdText ? (
                      <div style={{ color: "var(--color-success)", fontSize: "0.85rem", fontWeight: 600 }}>
                        ✓ Job description parsed successfully ({jdText.slice(0, 45)}...)
                      </div>
                    ) : (
                      <div>
                        <input
                          type="file"
                          accept="application/pdf"
                          onChange={(e) => handleFileUpload(e, "jd")}
                          style={{ position: "absolute", inset: 0, opacity: 0, cursor: "pointer" }}
                        />
                        <span style={{ fontSize: "0.85rem", color: "var(--color-primary)", fontWeight: 600 }}>Upload File</span>
                        <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginLeft: "4px" }}>or drag it here</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", marginTop: "12px" }}>
              <button onClick={() => setStep(1)} className="btn btn-secondary">
                Back
              </button>
              <button
                onClick={() => setStep(3)}
                className="btn btn-primary"
                disabled={parsingResume || parsingJd}
              >
                Continue
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: CONFIGURATION */}
        {step === 3 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            <div>
              <h2 style={{ fontSize: "1.3rem", fontWeight: 700, fontFamily: "var(--font-outfit)", marginBottom: "8px" }}>
                Simulation Settings
              </h2>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                Tailor the interview parameters and constraints.
              </p>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {/* Role Select */}
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <label style={{ fontSize: "0.85rem", fontWeight: 600 }}>Target Role</label>
                <select value={role} onChange={(e) => setRole(e.target.value)}>
                  {roles.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                {/* Difficulty Select */}
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <label style={{ fontSize: "0.85rem", fontWeight: 600 }}>Difficulty</label>
                  <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                    {difficulties.map((d) => <option key={d} value={d}>{d.toUpperCase()}</option>)}
                  </select>
                </div>

                {/* Duration Select */}
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <label style={{ fontSize: "0.85rem", fontWeight: 600 }}>Duration</label>
                  <select value={duration} onChange={(e) => setDuration(Number(e.target.value))}>
                    {durations.map((d) => <option key={d.value} value={d.value}>{d.label}</option>)}
                  </select>
                </div>
              </div>

              {/* Company Select */}
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <label style={{ fontSize: "0.85rem", fontWeight: 600 }}>Company Interview Style</label>
                <select value={company} onChange={(e) => setCompany(e.target.value)}>
                  {companies.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>

              {company === "Custom" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <label style={{ fontSize: "0.85rem", fontWeight: 600 }}>Custom Company Name</label>
                  <input
                    type="text"
                    placeholder="Enter company name..."
                    value={customCompany}
                    onChange={(e) => setCustomCompany(e.target.value)}
                  />
                </div>
              )}
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", marginTop: "12px" }}>
              <button
                onClick={() => setStep(mode === "role" ? 1 : 2)}
                className="btn btn-secondary"
              >
                Back
              </button>
              <button
                onClick={handleMoveToReview}
                className="btn btn-primary"
                disabled={loadingBlueprint}
              >
                {loadingBlueprint ? "Analyzing Profile..." : "Analyze & Review"}
              </button>
            </div>
          </div>
        )}

        {/* STEP 4: BLUEPRINT REVIEW */}
        {step === 4 && preparedSession && (
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            <div>
              <h2 style={{ fontSize: "1.3rem", fontWeight: 700, fontFamily: "var(--font-outfit)", marginBottom: "8px" }}>
                Pre-Interview Report
              </h2>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                Review the parsed summaries and objectives scheduled for this session.
              </p>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              {/* Gap Analysis Summary */}
              {preparedSession.gap_analysis_json && (
                <div style={{ padding: "16px", borderRadius: "12px", border: "1px solid var(--border-subtle)", backgroundColor: "rgba(255, 255, 255, 0.82)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                    <h3 style={{ fontSize: "0.95rem", fontWeight: 700 }}>Job-Specific Readiness</h3>
                    {(() => {
                      const gap = JSON.parse(preparedSession.gap_analysis_json);
                      const readiness = gap.job_readiness || {};
                      const score = readiness.estimated_readiness_score || 0;
                      return (
                        <span className={`badge ${score >= 70 ? 'badge-success' : 'badge-warning'}`} style={{ fontFamily: "var(--font-mono)" }}>
                          {score}% Ready
                        </span>
                      );
                    })()}
                  </div>
                  {(() => {
                    const gap = JSON.parse(preparedSession.gap_analysis_json);
                    const readiness = gap.job_readiness || {};
                    return (
                      <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>
                        {readiness.match_rationale || "Ready to evaluate matching credentials against parameters."}
                      </p>
                    );
                  })()}
                </div>
              )}

              {/* Objectives List */}
              {preparedSession.interview_objectives_json && (
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  <h3 style={{ fontSize: "0.85rem", fontWeight: 600 }}>Scheduled Objectives</h3>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                    {(() => {
                      const objectives = JSON.parse(preparedSession.interview_objectives_json);
                      const mustList = Object.keys(objectives.must_verify || {});
                      const niceList = Object.keys(objectives.nice_to_verify || {});
                      return (
                        <>
                          {mustList.map((obj) => (
                            <span key={obj} className="badge badge-primary" style={{ fontFamily: "var(--font-mono)" }}>
                              Must: {obj}
                            </span>
                          ))}
                          {niceList.map((obj) => (
                            <span key={obj} className="badge" style={{ backgroundColor: "rgba(16, 185, 129, 0.12)", color: "var(--color-success)", fontFamily: "var(--font-mono)" }}>
                              Nice: {obj}
                            </span>
                          ))}
                        </>
                      );
                    })()}
                  </div>
                </div>
              )}

              {/* Param Grid Summary */}
              <div style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "12px",
                padding: "16px",
                borderRadius: "8px",
                backgroundColor: "rgba(255, 255, 255, 0.82)",
                fontSize: "0.8rem"
              }}>
                <div>
                  <span style={{ color: "var(--text-muted)" }}>Target Role:</span>
                  <span style={{ fontWeight: 600, marginLeft: "4px", color: "var(--text-primary)" }}>{preparedSession.role}</span>
                </div>
                <div>
                  <span style={{ color: "var(--text-muted)" }}>Difficulty:</span>
                  <span style={{ fontWeight: 600, marginLeft: "4px", textTransform: "capitalize", color: "var(--text-primary)" }}>{preparedSession.difficulty}</span>
                </div>
                <div>
                  <span style={{ color: "var(--text-muted)" }}>Interview Style:</span>
                  <span style={{ fontWeight: 600, marginLeft: "4px", color: "var(--text-primary)" }}>{preparedSession.company_name}</span>
                </div>
                <div>
                  <span style={{ color: "var(--text-muted)" }}>Duration:</span>
                  <span style={{ fontWeight: 600, marginLeft: "4px", color: "var(--text-primary)" }}>{preparedSession.max_question_count} Questions</span>
                </div>
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", marginTop: "12px" }}>
              <button onClick={() => setStep(3)} className="btn btn-secondary">
                Back
              </button>
              <button onClick={handleStartInterview} className="btn btn-primary">
                Start Interview Session
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
