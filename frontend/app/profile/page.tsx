"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "../context/AuthContext";
import { supabase } from "../utils/supabaseClient";
import { safeJsonFetch } from "../utils/api";

type InterviewSession = {
  id: string;
  role: string;
  difficulty: string;
  duration_minutes: number;
  status: string;
  created_at: string;
  company_name?: string;
};

type ProfileCard = {
  readiness_scores?: Record<string, number>;
  history_trends?: { streak?: number };
  weak_topics?: string[];
  weak_skills?: string[];
  strong_topics?: string[];
  proven_skills?: string[];
  topic_mastery?: Record<string, {
    average_score?: number;
    mastery_state?: string;
    attempts?: number;
  }>;
};

type ViewMode = "overview" | "skills" | "telemetry";

export default function ProfilePage() {
  const router = useRouter();
  const { user } = useAuth();
  const [profile, setProfile] = useState<ProfileCard | null>(null);
  const [sessions, setSessions] = useState<InterviewSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>("overview");

  useEffect(() => {
    if (!user) return;

    let cancelled = false;

    const load = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session || cancelled) {
        setLoading(false);
        return;
      }

      const [profileData, sessionsData] = await Promise.all([
        safeJsonFetch<ProfileCard>("/api/v1/interviews/profile/card", {
          headers: { Authorization: `Bearer ${session.access_token}` }
        }),
        safeJsonFetch<InterviewSession[]>("/api/v1/interviews", {
          headers: { Authorization: `Bearer ${session.access_token}` }
        })
      ]);

      if (cancelled) return;

      setProfile(profileData || null);
      setSessions(Array.isArray(sessionsData) ? sessionsData : []);
      setLoading(false);
    };

    load();

    return () => {
      cancelled = true;
    };
  }, [user]);

  const fullName = user?.user_metadata?.full_name || user?.email?.split("@")[0] || "Candidate";
  const initials = (fullName || "AI").slice(0, 2).toUpperCase();

  const readiness = useMemo(() => {
    const scores = profile?.readiness_scores || {};
    const values = Object.values(scores).filter((v) => typeof v === "number") as number[];
    if (!values.length) return 0;
    return Math.round(values.reduce((sum, v) => sum + v, 0) / values.length);
  }, [profile]);

  const streak = profile?.history_trends?.streak || 0;
  const verifiedSkills = profile?.proven_skills || [];
  const weakSkills = profile?.weak_skills || [];
  const strongTopics = profile?.strong_topics || [];
  const weakTopics = profile?.weak_topics || [];
  const completedSessions = sessions.filter((s) => s.status === "completed").length;
  const inProgressSessions = sessions.length - completedSessions;
  const topicMastery = profile?.topic_mastery || {};

  const heroFocus = useMemo(() => {
    if (viewMode === "skills") {
      return {
        label: "Verified expertise",
        title: `${verifiedSkills.length} proven skill${verifiedSkills.length === 1 ? "" : "s"}`,
        body: verifiedSkills.length
          ? "These are the claims your interview history has already backed up."
          : "Complete a few sessions and the verified skill set will populate here."
      };
    }

    if (viewMode === "telemetry") {
      return {
        label: "Performance telemetry",
        title: `${completedSessions} completed session${completedSessions === 1 ? "" : "s"}`,
        body: "Your practice pattern, readiness, and weak areas all feed into this view."
      };
    }

    return {
      label: "Career momentum",
      title: `${readiness}% readiness`,
      body: "A quick view of how the profile is trending across the interview engine."
    };
  }, [completedSessions, readiness, verifiedSkills.length, viewMode]);

  const focusChips: Array<{ label: string; value: string }> = [
    { label: "Verified skills", value: String(verifiedSkills.length) },
    { label: "Average score", value: `${readiness}%` },
    { label: "Current streak", value: `${streak} days` },
    { label: "Completed", value: String(completedSessions) }
  ];

  const strongestTopics = useMemo(() => {
    return Object.entries(topicMastery)
      .map(([topic, data]) => ({
        topic,
        score: Number(data?.average_score || 0),
        state: data?.mastery_state || "Unknown",
        attempts: Number(data?.attempts || 0)
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 3);
  }, [topicMastery]);

  const growthItems = useMemo(() => {
    const items: Array<{ title: string; body: string; score?: string }> = [];

    if (weakSkills.length) {
      items.push({
        title: weakSkills[0],
        body: "Worth another targeted interview run and a focused study plan.",
      });
    }

    if (weakTopics.length) {
      items.push({
        title: weakTopics[0],
        body: "This topic showed up as an opportunity in your recent interviews.",
      });
    }

    if (!items.length) {
      items.push({
        title: "Keep the practice loop going",
        body: "New weak spots and growth signals will surface after a few more sessions.",
      });
    }

    return items.slice(0, 2);
  }, [weakSkills, weakTopics]);

  if (loading) {
    return (
      <main className="section-shell">
        <div className="page-shell">
          <div className="hero-panel" style={{ minHeight: "360px" }} />
          <div style={{ display: "grid", gridTemplateColumns: "repeat(12, minmax(0, 1fr))", gap: "20px", marginTop: "24px" }}>
            <div className="card" style={{ gridColumn: "span 8", minHeight: "220px" }} />
            <div className="card" style={{ gridColumn: "span 4", minHeight: "220px" }} />
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="section-shell">
      <div className="page-shell">
        <section className="hero-grid" style={{ alignItems: "stretch" }}>
          <div className="hero-panel" style={{ overflow: "hidden" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "16px", flexWrap: "wrap" }}>
              <div className="section-kicker">Executive profile</div>
              <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                {["overview", "skills", "telemetry"].map((mode) => (
                  <button
                    key={mode}
                    type="button"
                    onClick={() => setViewMode(mode as ViewMode)}
                    className="btn btn-secondary"
                    style={{
                      minHeight: "40px",
                      padding: "0 14px",
                      background: viewMode === mode ? "rgba(213, 173, 52, 0.14)" : "rgba(255,255,255,0.72)",
                      borderColor: viewMode === mode ? "rgba(213, 173, 52, 0.38)" : "var(--border-subtle)"
                    }}
                  >
                    {mode.charAt(0).toUpperCase() + mode.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1.1fr 0.9fr", gap: "28px", marginTop: "22px", alignItems: "center" }}>
              <div style={{ display: "grid", gap: "18px" }}>
                <div style={{ display: "grid", gap: "10px" }}>
                  <h1 className="page-title" style={{ maxWidth: "11ch" }}>
                    {fullName}
                  </h1>
                  <p className="hero-copy" style={{ maxWidth: "60ch" }}>
                    {user?.user_metadata?.headline || "Interview candidate focused on measurable growth through adaptive practice."}
                  </p>
                </div>

                <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
                  <button className="btn btn-primary" onClick={() => router.push("/new-interview")}>
                    Start practice session
                  </button>
                  <button className="btn btn-secondary" onClick={() => router.push("/history")}>
                    View history
                  </button>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "12px" }}>
                  {focusChips.map((chip) => (
                    <div key={chip.label} className="subtle-chip" style={{ justifyContent: "space-between", minHeight: "56px", width: "100%" }}>
                      <span>{chip.label}</span>
                      <strong style={{ color: "var(--text-primary)" }}>{chip.value}</strong>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ display: "grid", justifyItems: "center", gap: "14px" }}>
                <div style={{
                  width: "300px",
                  height: "300px",
                  borderRadius: "50%",
                  background: `conic-gradient(var(--accent) 0 ${readiness}%, rgba(28, 23, 18, 0.08) ${readiness}% 100%)`,
                  padding: "12px",
                  boxShadow: "0 18px 45px rgba(49, 34, 9, 0.08)",
                  animation: "ringPulse 6s ease-in-out infinite"
                }}>
                  <div style={{
                    width: "100%",
                    height: "100%",
                    borderRadius: "50%",
                    background: "radial-gradient(circle at 30% 20%, rgba(255,255,255,0.98), rgba(247,242,233,0.94))",
                    display: "grid",
                    placeItems: "center",
                    border: "1px solid rgba(28, 23, 18, 0.06)"
                  }}>
                    <div style={{ textAlign: "center" }}>
                      <div style={{ fontFamily: "var(--font-display)", fontSize: "4rem", fontWeight: 700, lineHeight: 1 }}>
                        {readiness}
                      </div>
                      <div className="ambient-label" style={{ marginTop: "6px" }}>
                        Career momentum
                      </div>
                    </div>
                  </div>
                </div>

                <div className="card" style={{ width: "220px", textAlign: "center", padding: "16px" }}>
                  <div className="ambient-label">{heroFocus.label}</div>
                  <div style={{ fontWeight: 700, marginTop: "10px" }}>{heroFocus.title}</div>
                  <p className="fine-print" style={{ marginTop: "6px" }}>{heroFocus.body}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="hero-visual" style={{ padding: "24px" }}>
            <div style={{ display: "grid", gap: "14px" }}>
              <div className="card" style={{ display: "flex", gap: "16px", alignItems: "center" }}>
                <div style={{
                  width: "74px",
                  height: "74px",
                  borderRadius: "24px",
                  background: "linear-gradient(135deg, #111110, #d5ad34)",
                  color: "#fff",
                  display: "grid",
                  placeItems: "center",
                  fontFamily: "var(--font-display)",
                  fontSize: "1.55rem",
                  fontWeight: 700,
                  boxShadow: "0 16px 30px rgba(49, 34, 9, 0.18)"
                }}>
                  {initials}
                </div>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontFamily: "var(--font-display)", fontSize: "1.65rem", fontWeight: 700, letterSpacing: "-0.04em" }}>
                    {fullName}
                  </div>
                  <p className="section-copy" style={{ marginTop: "6px" }}>
                    {user?.email || "Signed in candidate"}
                  </p>
                  <div style={{ display: "flex", gap: "8px", marginTop: "10px", flexWrap: "wrap" }}>
                    <span className="badge badge-primary">{streak} day streak</span>
                    <span className="badge badge-success">{completedSessions} sessions completed</span>
                  </div>
                </div>
              </div>

              <div className="card" style={{ padding: "18px" }}>
                <div className="ambient-label">Current status</div>
                <div style={{ display: "grid", gap: "10px", marginTop: "10px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}>
                    <span className="fine-print">Active sessions</span>
                    <strong>{inProgressSessions}</strong>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}>
                    <span className="fine-print">Strong topics</span>
                    <strong>{strongTopics.length || strongestTopics.length}</strong>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}>
                    <span className="fine-print">Weak areas</span>
                    <strong>{weakSkills.length + weakTopics.length}</strong>
                  </div>
                </div>
              </div>

              <div className="card" style={{ padding: "18px" }}>
                <div className="ambient-label">View mode</div>
                <p className="section-copy" style={{ marginTop: "10px" }}>
                  Switching the mode changes the focus card below and gives the profile page a more interactive feel.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section style={{ marginTop: "28px" }} className="feature-grid">
          <div className="feature-card feature-card--wide">
            <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", flexWrap: "wrap", alignItems: "end" }}>
              <div>
                <div className="section-kicker">Verified expertise</div>
                <h2 className="section-title" style={{ marginTop: "12px" }}>
                  Skills established through interview performance.
                </h2>
              </div>
              <div style={{ display: "flex", gap: "14px", flexWrap: "wrap" }}>
                <div className="subtle-chip">Verified: {verifiedSkills.length}</div>
                <div className="subtle-chip">Avg score: {readiness}%</div>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "14px", marginTop: "18px" }}>
              {(verifiedSkills.length ? verifiedSkills.slice(0, 3) : strongestTopics.map((t) => t.topic)).map((item: string, idx: number) => (
                <div key={item} className="card" style={{ padding: "16px", borderLeft: "3px solid var(--accent)" }}>
                  <div className="ambient-label">Skill {idx + 1}</div>
                  <div style={{ fontWeight: 700, fontSize: "1.02rem", marginTop: "8px" }}>{item}</div>
                  <p className="fine-print" style={{ marginTop: "8px" }}>
                    {idx === 0
                      ? "Demonstrated in recent interviews."
                      : idx === 1
                        ? "Backed by repeated follow-up depth."
                        : "Shown in strong answer structure and clarity."}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="feature-card feature-card--tall">
            <div className="section-kicker">Growth horizons</div>
            <h2 className="headline" style={{ marginTop: "12px" }}>What to tighten next</h2>
            <p className="section-copy" style={{ marginTop: "10px" }}>
              These are the highest leverage areas to revisit in the next practice round.
            </p>
            <div style={{ display: "grid", gap: "12px", marginTop: "16px" }}>
              {growthItems.map((item) => (
                <div key={item.title} className="card" style={{ padding: "16px", borderLeft: "3px solid var(--accent)" }}>
                  <div style={{ fontWeight: 700 }}>{item.title}</div>
                  <p className="fine-print" style={{ marginTop: "8px" }}>{item.body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section style={{ marginTop: "28px" }} className="feature-grid">
          <div className="feature-card feature-card--wide">
            <div className="section-kicker">Performance telemetry</div>
            <h2 className="section-title" style={{ marginTop: "12px" }}>
              Readiness pattern over your interview history.
            </h2>
            <p className="section-copy" style={{ marginTop: "10px", maxWidth: "60ch" }}>
              The visual below is generated from your topic mastery scores so it stays meaningful to the app, not just decorative.
            </p>

            <div style={{ marginTop: "20px", display: "grid", gap: "10px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div className="fine-print" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ width: "10px", height: "10px", borderRadius: "999px", background: "var(--accent)" }} />
                  Live readiness: {readiness}%
                </div>
                <div className="fine-print">Lighter = low activity · Darker = strong performance</div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(8, minmax(0, 1fr))", gap: "8px" }}>
                {Array.from({ length: 24 }).map((_, index) => {
                  const topicValues = Object.values(topicMastery);
                  const base = topicValues.length ? (topicValues[index % topicValues.length]?.average_score || readiness || 40) : readiness || 40;
                  const intensity = Math.max(18, Math.min(92, Math.round(base)));
                  return (
                    <div
                      key={index}
                      className="card"
                      style={{
                        minHeight: "36px",
                        padding: 0,
                        borderRadius: "10px",
                        background: `rgba(213, 173, 52, ${intensity / 160})`,
                        boxShadow: "none",
                        border: "1px solid rgba(28, 23, 18, 0.05)",
                        animation: `fadeFloat ${4 + (index % 4)}s ease-in-out infinite`
                      }}
                    />
                  );
                })}
              </div>
            </div>
          </div>

          <div className="feature-card feature-card--tall">
            <div className="ambient-label">Session pulse</div>
            <div style={{ display: "grid", gap: "14px", marginTop: "12px" }}>
              <div className="card" style={{ padding: "16px" }}>
                <div className="ambient-label">Current streak</div>
                <div style={{ fontFamily: "var(--font-display)", fontSize: "2.8rem", fontWeight: 700, marginTop: "6px" }}>
                  {streak} days
                </div>
                <p className="fine-print">Keep the streak alive with a targeted practice run.</p>
              </div>
              <div className="card" style={{ padding: "16px" }}>
                <div className="ambient-label">Simulations complete</div>
                <div style={{ fontFamily: "var(--font-display)", fontSize: "2.4rem", fontWeight: 700, marginTop: "6px" }}>
                  {completedSessions}
                </div>
                <p className="fine-print">{inProgressSessions} still in progress</p>
              </div>
            </div>
          </div>
        </section>

        <section style={{ marginTop: "28px" }} className="feature-grid">
          <div className="feature-card feature-card--wide">
            <div className="section-kicker">Recent performance</div>
            <h2 className="section-title" style={{ marginTop: "12px" }}>
              Your strongest interview signals.
            </h2>
            <div style={{ display: "grid", gap: "12px", marginTop: "18px" }}>
              {strongestTopics.length === 0 ? (
                <div className="card" style={{ padding: "16px" }}>
                  <p className="section-copy">Run a few interviews and your topic mastery cards will appear here.</p>
                </div>
              ) : strongestTopics.map((topic) => (
                <div key={topic.topic} className="card" style={{ padding: "16px", display: "flex", justifyContent: "space-between", gap: "14px", alignItems: "center" }}>
                  <div>
                    <div style={{ fontWeight: 700 }}>{topic.topic}</div>
                    <p className="fine-print" style={{ marginTop: "6px" }}>
                      {topic.attempts} attempt{topic.attempts === 1 ? "" : "s"} · {topic.state}
                    </p>
                  </div>
                  <div style={{ fontFamily: "var(--font-display)", fontSize: "1.5rem", fontWeight: 700, color: "var(--accent-strong)" }}>
                    {Math.round(topic.score)}%
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="feature-card feature-card--tall">
            <div className="ambient-label">Next action</div>
            <h2 className="headline" style={{ marginTop: "12px" }}>Turn profile insight into practice.</h2>
            <p className="section-copy" style={{ marginTop: "10px" }}>
              Your next best move is to run another interview with the weakest topic as the focus.
            </p>
            <button className="btn btn-primary" style={{ marginTop: "18px", width: "100%" }} onClick={() => router.push("/new-interview")}>
              Start focused practice
            </button>
            <button className="btn btn-secondary" style={{ marginTop: "10px", width: "100%" }} onClick={() => router.push("/learning")}>
              Open learning roadmap
            </button>
          </div>
        </section>
      </div>

      <style jsx>{`
        @keyframes ringPulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.02); }
        }

        @keyframes fadeFloat {
          0%, 100% { transform: translateY(0); opacity: 0.88; }
          50% { transform: translateY(-2px); opacity: 1; }
        }
      `}</style>
    </main>
  );
}
