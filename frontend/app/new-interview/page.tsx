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
  const focusModes = [
    { id: "role", title: "Role-Based", desc: "Master core competencies for a specific job title.", badge: "ROLE", accent: false },
    { id: "resume", title: "Resume", desc: "Deep-dive into your project history and claims.", badge: "CV", accent: false },
    { id: "jd", title: "JD Match", desc: "Align with a specific job description.", badge: "JD", accent: false },
    { id: "resume_jd", title: "Combined", desc: "Use every data point for the richest simulation.", badge: "ALL", accent: true }
  ] as const;

  const previewBullets = [
    { title: "Cognitive mapping", body: "Resume, role, and job description signals are merged into one scenario model." },
    { title: "Voice tuning", body: "Answer pacing and tone can be used to adapt the interviewer’s pace." },
    { title: "Prediction layer", body: "Difficulty and duration determine the likely depth of follow-ups." }
  ];

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
      <main className="section-shell">
        <div className="page-shell">
          <div className="hero-panel soft-raise" style={{ textAlign: "center", maxWidth: "820px", margin: "0 auto" }}>
            <div className="section-kicker" style={{ margin: "0 auto" }}>
              Pro required
            </div>
            <h1 className="page-title" style={{ marginTop: "18px" }}>
              Unlock unlimited interview sessions.
            </h1>
            <p className="hero-copy" style={{ margin: "14px auto 0", maxWidth: "60ch" }}>
              You have exhausted the free tier. Upgrade to continue using resume matching, deep reports, and richer simulations.
            </p>

            <div className="feature-grid" style={{ marginTop: "28px" }}>
              {[
                "Unlimited technical and behavioral mocks",
                "Resume and JD gap analysis",
                "Detailed recruiter-style reports"
              ].map((item) => (
                <div key={item} className="card" style={{ gridColumn: "span 4", textAlign: "left" }}>
                  <div className="ambient-label">Included</div>
                  <div style={{ fontWeight: 700, marginTop: "10px" }}>{item}</div>
                </div>
              ))}
            </div>

            <div style={{ display: "flex", justifyContent: "center", gap: "12px", flexWrap: "wrap", marginTop: "28px" }}>
              <div className="subtle-chip">$19.99 / month</div>
              <button onClick={handleUpgrade} className="btn btn-primary">
                Upgrade now
              </button>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="section-shell">
      <div className="page-shell">
        {error && (
          <div className="card" style={{ border: "1px solid rgba(185, 79, 79, 0.25)", background: "rgba(255, 255, 255, 0.8)", marginBottom: "18px" }}>
            <div className="ambient-label" style={{ color: "var(--error)" }}>Error</div>
            <p className="section-copy" style={{ marginTop: "8px", color: "var(--error)" }}>{error}</p>
          </div>
        )}

        <section className="hero-grid">
          <div className="hero-panel">
            <div className="section-kicker">Setup phase</div>
            <h1 className="page-title" style={{ marginTop: "18px", maxWidth: "12ch" }}>
              Configure Your Experience
            </h1>
            <p className="hero-copy" style={{ marginTop: "14px", maxWidth: "58ch" }}>
              Select the focus of your simulation. Veriq adapts its cognitive model to match your role, resume, and target job.
            </p>
          </div>

          <div className="hero-visual" style={{ padding: "28px", overflow: "hidden" }}>
            <div style={{ display: "grid", gap: "14px" }}>
              <div className="card" style={{ padding: "16px", width: "fit-content" }}>
                <div className="ambient-label">Ready for launch</div>
                <div style={{ fontWeight: 700, marginTop: "6px" }}>
                  {mode === "resume_jd" ? "Combined mode" : mode === "jd" ? "JD match" : mode === "resume" ? "Resume mode" : "Role based"}
                </div>
              </div>
              <div style={{ display: "grid", gap: "12px" }}>
                <div className="card" style={{ minHeight: "120px", padding: "16px" }}>
                  <div className="ambient-label">Preview signal</div>
                  <div style={{ display: "flex", gap: "8px", marginTop: "12px", flexWrap: "wrap" }}>
                    {["Cognitive", "Adaptive", "Editorial", "Gold accents"].map((pill) => (
                      <span key={pill} className="badge badge-primary">{pill}</span>
                    ))}
                  </div>
                </div>
                <div className="card" style={{ minHeight: "120px", padding: "16px" }}>
                  <div className="ambient-label">Target role</div>
                  <div style={{ fontFamily: "var(--font-display)", fontSize: "1.6rem", fontWeight: 700, marginTop: "8px" }}>{role}</div>
                  <p className="section-copy" style={{ marginTop: "8px" }}>{company === "Custom" ? customCompany || "Custom company" : company}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section style={{ marginTop: "24px" }} className="feature-grid">
          {focusModes.map((item) => {
            const isSelected = mode === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setMode(item.id)}
                className="feature-card"
                style={{
                  textAlign: "left",
                  gridColumn: "span 3",
                  border: isSelected ? "1px solid rgba(213, 173, 52, 0.45)" : "1px solid var(--border-subtle)",
                  background: isSelected ? "rgba(255, 255, 255, 0.92)" : "rgba(255, 255, 255, 0.64)",
                  boxShadow: isSelected ? "0 18px 40px rgba(213, 173, 52, 0.10)" : "var(--shadow-card)",
                  transform: isSelected ? "translateY(-4px)" : "translateY(0)"
                }}
              >
                <div style={{
                  width: "48px",
                  height: "48px",
                  borderRadius: "16px",
                  display: "grid",
                  placeItems: "center",
                  background: isSelected ? "rgba(213, 173, 52, 0.16)" : "rgba(255, 255, 255, 0.86)",
                  border: "1px solid var(--border-subtle)"
                }}>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.74rem",
                      letterSpacing: "0.14em",
                      color: isSelected ? "var(--accent-strong)" : "var(--text-secondary)"
                    }}
                  >
                    {item.badge}
                  </span>
                </div>
                <h3 className="headline" style={{ marginTop: "12px", fontSize: "1.35rem" }}>{item.title}</h3>
                <p className="section-copy" style={{ marginTop: "8px" }}>{item.desc}</p>
                <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "14px" }}>
                  <span
                    className="subtle-chip"
                    style={{
                      opacity: isSelected ? 1 : 0,
                      transform: isSelected ? "translateY(0)" : "translateY(4px)",
                      transition: "opacity 180ms ease, transform 180ms ease",
                      padding: "6px 10px"
                    }}
                  >
                    Selected
                  </span>
                </div>
              </button>
            );
          })}
        </section>

        <section style={{ marginTop: "28px" }} className="feature-grid">
          <div className="feature-card feature-card--wide">
            <div className="section-kicker">Simulation Deep Dive</div>
            <h2 className="section-title" style={{ marginTop: "14px" }}>
              Fine-tune the behavioral parameters of your interviewer.
            </h2>
            <p className="section-copy" style={{ marginTop: "10px", maxWidth: "56ch" }}>
              From stress testing to industry standard formality, shape the session around the exact level of challenge you want.
            </p>

            <div style={{ display: "grid", gap: "18px", marginTop: "22px" }}>
              <div className="card" style={{ padding: "18px" }}>
                <label className="ambient-label">Target Role</label>
                <select value={role} onChange={(e) => setRole(e.target.value)} style={{ marginTop: "10px" }}>
                  {roles.map((r) => <option key={r} value={r}>{r}</option>)}
                </select>
              </div>

              <div className="card" style={{ padding: "18px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", alignItems: "end" }}>
                  <label className="ambient-label">Interrogation level</label>
                  <span className="headline" style={{ fontSize: "1rem" }}>
                    {difficulty === "easy" ? "Beginner" : difficulty === "medium" ? "Advanced" : "Expert"}
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={2}
                  value={difficulties.indexOf(difficulty)}
                  onChange={(e) => setDifficulty(difficulties[Number(e.target.value)])}
                  style={{ width: "100%", marginTop: "16px", accentColor: "var(--accent)" }}
                />
                <div style={{ display: "flex", justifyContent: "space-between", marginTop: "6px" }}>
                  {["Easy", "Medium", "Hard"].map((label) => (
                    <span key={label} className="fine-print">{label}</span>
                  ))}
                </div>
              </div>

              <div className="card" style={{ padding: "18px" }}>
                <label className="ambient-label">Company Style</label>
                <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginTop: "12px" }}>
                  {companies.map((c) => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => setCompany(c)}
                      className="btn btn-secondary"
                      style={{
                        background: company === c ? "rgba(213, 173, 52, 0.12)" : "rgba(255, 255, 255, 0.7)",
                        borderColor: company === c ? "rgba(213, 173, 52, 0.45)" : "var(--border-subtle)"
                      }}
                    >
                      {c}
                    </button>
                  ))}
                </div>
              </div>

              {(mode === "resume" || mode === "resume_jd" || mode === "jd") && (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "14px" }}>
                  {(mode === "resume" || mode === "resume_jd") && (
                    <div className="card" style={{ padding: "18px" }}>
                      <div className="ambient-label">Resume upload</div>
                      <div style={{ position: "relative", border: "1px dashed var(--border-main)", borderRadius: "18px", padding: "18px", marginTop: "12px", minHeight: "120px", display: "grid", placeItems: "center" }}>
                        <input type="file" accept="application/pdf" onChange={(e) => handleFileUpload(e, "resume")} style={{ position: "absolute", inset: 0, opacity: 0, cursor: "pointer" }} />
                        {parsingResume ? (
                          <span className="section-copy">Parsing resume...</span>
                        ) : resumeText ? (
                          <span className="badge badge-success">Resume parsed</span>
                        ) : (
                          <div style={{ textAlign: "center" }}>
                            <span className="material-symbols-outlined" style={{ color: "var(--accent)", fontSize: 28 }}>upload</span>
                            <div className="fine-print" style={{ marginTop: "8px" }}>Upload your resume</div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  {(mode === "jd" || mode === "resume_jd") && (
                    <div className="card" style={{ padding: "18px" }}>
                      <div className="ambient-label">JD upload</div>
                      <div style={{ position: "relative", border: "1px dashed var(--border-main)", borderRadius: "18px", padding: "18px", marginTop: "12px", minHeight: "120px", display: "grid", placeItems: "center" }}>
                        <input type="file" accept="application/pdf" onChange={(e) => handleFileUpload(e, "jd")} style={{ position: "absolute", inset: 0, opacity: 0, cursor: "pointer" }} />
                        {parsingJd ? (
                          <span className="section-copy">Parsing job description...</span>
                        ) : jdText ? (
                          <span className="badge badge-success">JD parsed</span>
                        ) : (
                          <div style={{ textAlign: "center" }}>
                            <span className="material-symbols-outlined" style={{ color: "var(--accent)", fontSize: 28 }}>upload_file</span>
                            <div className="fine-print" style={{ marginTop: "8px" }}>Upload a job description</div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="feature-card feature-card--tall">
            <div className="card" style={{ padding: "16px", minHeight: "280px", position: "relative", overflow: "hidden" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div className="ambient-label">Simulation preview</div>
                <span className="badge badge-primary">Live</span>
              </div>
              <div style={{ marginTop: "16px", borderRadius: "22px", border: "1px solid var(--border-subtle)", background: "linear-gradient(180deg, rgba(255,255,255,0.92), rgba(247,242,233,0.92))", padding: "12px", minHeight: "220px", boxShadow: "inset 0 1px 0 rgba(255,255,255,0.7)" }}>
                <div style={{ display: "flex", gap: "6px", marginBottom: "12px" }}>
                  <span style={{ width: "10px", height: "10px", borderRadius: "999px", background: "#d9c7a3" }} />
                  <span style={{ width: "10px", height: "10px", borderRadius: "999px", background: "#f0e5cf" }} />
                  <span style={{ width: "10px", height: "10px", borderRadius: "999px", background: "#ffffff", border: "1px solid var(--border-subtle)" }} />
                </div>
                <div className="card" style={{ padding: "14px", minHeight: "180px", position: "relative", overflow: "hidden" }}>
                  <div style={{ display: "grid", gap: "12px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: "10px", alignItems: "center" }}>
                      <div>
                        <div style={{ fontFamily: "var(--font-display)", fontSize: "1.3rem", fontWeight: 700 }}>Veriq Preview</div>
                        <div className="fine-print">A cleaner meaning-first replacement for the incorrect image</div>
                      </div>
                      <div className="subtle-chip">01</div>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                      <div className="card" style={{ padding: "12px" }}>
                        <div className="ambient-label">Signal</div>
                        <div style={{ fontWeight: 700, marginTop: "8px" }}>{mode === "resume_jd" ? "Combined" : mode === "jd" ? "JD match" : mode === "resume" ? "Resume" : "Role"}</div>
                      </div>
                      <div className="card" style={{ padding: "12px" }}>
                        <div className="ambient-label">Difficulty</div>
                        <div style={{ fontWeight: 700, marginTop: "8px" }}>{difficulty.toUpperCase()}</div>
                      </div>
                    </div>
                    <div style={{ display: "grid", gap: "10px" }}>
                      {previewBullets.map((item) => (
                        <div key={item.title} className="card" style={{ padding: "12px", borderLeft: "3px solid var(--accent)" }}>
                          <div style={{ fontWeight: 700 }}>{item.title}</div>
                          <p className="fine-print" style={{ marginTop: "6px" }}>{item.body}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="card ai-border" style={{ marginTop: "14px", padding: "18px" }}>
              <div className="ambient-label" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span className="material-symbols-outlined" style={{ fontSize: 18, color: "var(--accent)" }}>auto_awesome</span>
                AI Model Tuning
              </div>
              <p className="section-copy" style={{ marginTop: "10px" }}>
                Based on <strong>{mode === "resume_jd" ? "Combined" : mode === "jd" ? "JD Match" : mode === "resume" ? "Resume" : "Role-Based"}</strong> and <strong>{difficulty.toUpperCase()}</strong>, Veriq will prioritize the right follow-ups and estimate a session length of roughly <strong>{duration * 2 + 35} minutes</strong>.
              </p>
            </div>
          </div>
        </section>

        <section style={{ marginTop: "28px" }} className="feature-grid">
          <div className="feature-card feature-card--wide">
            <div className="section-kicker">The Intelligence Preview</div>
            <h2 className="section-title" style={{ marginTop: "14px" }}>
              See how the model processes your inputs to create a bespoke simulation.
            </h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "14px", marginTop: "18px" }}>
              {[
                { title: "Cognitive Mapping", icon: "psychology_alt", body: "We map your resume and role against interview patterns to surface likely gaps." },
                { title: "Aura Voice Synthesis", icon: "graphic_eq", body: "A smoother speaking cadence keeps the session conversational and composed." },
                { title: "Predictive Analytics", icon: "query_stats", body: "The model estimates interview depth, focus areas, and confidence range." }
              ].map((item) => (
                <div key={item.title} className="card" style={{ padding: "18px", textAlign: "center" }}>
                  <div style={{ width: "56px", height: "56px", margin: "0 auto", borderRadius: "18px", background: "rgba(213, 173, 52, 0.12)", display: "grid", placeItems: "center" }}>
                    <span className="material-symbols-outlined" style={{ color: "var(--primary)" }}>{item.icon}</span>
                  </div>
                  <h3 className="headline" style={{ marginTop: "12px", fontSize: "1.2rem" }}>{item.title}</h3>
                  <p className="section-copy" style={{ marginTop: "8px" }}>{item.body}</p>
                </div>
              ))}
            </div>
            <div className="hero-visual" style={{ minHeight: "260px", marginTop: "18px", padding: "22px" }}>
              <div className="card" style={{ maxWidth: "560px", margin: "0 auto", padding: "18px" }}>
                <div className="ambient-label">Live settings snapshot</div>
                <div style={{ display: "grid", gap: "12px", marginTop: "12px" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: "10px" }}>
                    {[
                      { label: "Role", value: role },
                      { label: "Difficulty", value: difficulty },
                      { label: "Duration", value: `${duration} min` },
                      { label: "Company", value: company }
                    ].map((item) => (
                      <div key={item.label} className="card" style={{ padding: "12px" }}>
                        <div className="ambient-label">{item.label}</div>
                        <div style={{ fontWeight: 700, marginTop: "8px" }}>{item.value}</div>
                      </div>
                    ))}
                  </div>
                  <div className="card" style={{ padding: "14px", borderLeft: "3px solid var(--accent)" }}>
                    <div className="ambient-label">Analysis insight</div>
                    <p className="section-copy" style={{ marginTop: "8px" }}>
                      The current setup points toward a balanced but challenging session with a strong emphasis on practical depth and follow-up pressure.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="feature-card feature-card--tall">
            <div className="card" style={{ padding: "18px" }}>
              <div className="ambient-label">Ready for launch</div>
              <h3 className="headline" style={{ marginTop: "10px" }}>Start analysis when the configuration feels right.</h3>
              <p className="section-copy" style={{ marginTop: "8px" }}>
                Veriq will prepare the session blueprint, then take you into the live interview room.
              </p>
              <button onClick={handleMoveToReview} className="btn btn-primary" disabled={loadingBlueprint} style={{ width: "100%", marginTop: "18px" }}>
                {loadingBlueprint ? "Analyzing..." : "Start analysis"}
              </button>
            </div>

            <div className="card" style={{ marginTop: "14px", padding: "18px" }}>
              <div className="ambient-label">Current selection</div>
              <div style={{ display: "grid", gap: "10px", marginTop: "12px" }}>
                <div className="subtle-chip">Mode: {mode === "resume_jd" ? "Combined" : mode === "jd" ? "JD Match" : mode === "resume" ? "Resume" : "Role-Based"}</div>
                <div className="subtle-chip">Role: {role}</div>
                <div className="subtle-chip">Difficulty: {difficulty}</div>
                <div className="subtle-chip">Duration: {duration} mins</div>
              </div>
            </div>
          </div>
        </section>

        {preparedSession && (
          <section style={{ marginTop: "28px" }} className="feature-grid">
            <div className="feature-card feature-card--wide">
              <div className="section-kicker">Pre-interview report</div>
              <h2 className="section-title" style={{ marginTop: "14px" }}>Review the blueprint before starting the session.</h2>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "14px", marginTop: "18px" }}>
                <div className="card" style={{ padding: "16px" }}>
                  <div className="ambient-label">Target role</div>
                  <div style={{ fontWeight: 700, marginTop: "8px" }}>{preparedSession.role}</div>
                </div>
                <div className="card" style={{ padding: "16px" }}>
                  <div className="ambient-label">Difficulty</div>
                  <div style={{ fontWeight: 700, marginTop: "8px", textTransform: "capitalize" }}>{preparedSession.difficulty}</div>
                </div>
                <div className="card" style={{ padding: "16px" }}>
                  <div className="ambient-label">Interview style</div>
                  <div style={{ fontWeight: 700, marginTop: "8px" }}>{preparedSession.company_name}</div>
                </div>
                <div className="card" style={{ padding: "16px" }}>
                  <div className="ambient-label">Questions</div>
                  <div style={{ fontWeight: 700, marginTop: "8px" }}>{preparedSession.max_question_count}</div>
                </div>
              </div>
              <button onClick={handleStartInterview} className="btn btn-primary" style={{ marginTop: "18px" }}>
                Start interview session
              </button>
            </div>
            <div className="feature-card feature-card--tall">
              <div className="ambient-label">Objectives</div>
              <div style={{ display: "grid", gap: "12px", marginTop: "14px" }}>
                {preparedSession.interview_objectives_json && (() => {
                  const objectives = JSON.parse(preparedSession.interview_objectives_json);
                  const mustList = Object.keys(objectives.must_verify || {});
                  const niceList = Object.keys(objectives.nice_to_verify || {});
                  return (
                    <>
                      {mustList.map((obj: string) => <span key={obj} className="badge badge-primary">Must: {obj}</span>)}
                      {niceList.map((obj: string) => <span key={obj} className="badge badge-success">Nice: {obj}</span>)}
                    </>
                  );
                })()}
              </div>
              {preparedSession.gap_analysis_json && (
                <div className="card" style={{ marginTop: "14px", padding: "16px", borderLeft: "3px solid var(--accent)" }}>
                  <div className="ambient-label">Match rationale</div>
                  <p className="section-copy" style={{ marginTop: "8px" }}>
                    {(() => {
                      const gap = JSON.parse(preparedSession.gap_analysis_json);
                      return gap?.job_readiness?.match_rationale || "Ready to evaluate matching credentials against parameters.";
                    })()}
                  </p>
                </div>
              )}
            </div>
          </section>
        )}
      </div>
      <style jsx>{`
        @keyframes drift {
          0% { transform: translate3d(0, 0, 0) scale(1); }
          50% { transform: translate3d(0, -8px, 0) scale(1.01); }
          100% { transform: translate3d(0, 0, 0) scale(1); }
        }
        @keyframes glowPulse {
          0%, 100% { box-shadow: 0 0 0 rgba(213,173,52,0); }
          50% { box-shadow: 0 0 30px rgba(213,173,52,0.14); }
        }
        .hero-visual {
          animation: drift 10s ease-in-out infinite;
        }
        .feature-card {
          transition: transform 220ms ease, box-shadow 220ms ease, border-color 220ms ease;
        }
        .feature-card:hover {
          transform: translateY(-4px);
          animation: glowPulse 2s ease-in-out infinite;
        }
      `}</style>
    </main>
  );
}
