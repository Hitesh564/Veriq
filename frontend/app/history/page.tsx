"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "../context/AuthContext";
import { supabase } from "../utils/supabaseClient";
import { safeJsonFetch } from "../utils/api";

interface InterviewSession {
  id: string;
  role: string;
  difficulty: string;
  duration_minutes: number;
  status: string;
  created_at: string;
  company_name?: string;
}

export default function HistoryPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [sessions, setSessions] = useState<InterviewSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [difficultyFilter, setDifficultyFilter] = useState("all");

  useEffect(() => {
    if (!user) return;

    supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (!session) {
        setLoading(false);
        return;
      }

      const data = await safeJsonFetch<InterviewSession[]>("/api/v1/interviews", {
        headers: { Authorization: `Bearer ${session.access_token}` }
      });

      setSessions(Array.isArray(data) ? data : []);
      setLoading(false);
    });
  }, [user]);

  const filteredSessions = useMemo(() => {
    return sessions.filter((s) => {
      const roleMatch = s.role.toLowerCase().includes(search.toLowerCase());
      const companyMatch = (s.company_name || "").toLowerCase().includes(search.toLowerCase());
      const diffMatch = difficultyFilter === "all" || s.difficulty === difficultyFilter;
      return (roleMatch || companyMatch) && diffMatch;
    });
  }, [difficultyFilter, search, sessions]);

  const counts = useMemo(() => ({
    total: sessions.length,
    completed: sessions.filter((s) => s.status === "completed").length,
    active: sessions.filter((s) => s.status !== "completed").length
  }), [sessions]);

  const formatDate = (dateString: string) => {
    let s = dateString;
    if (s && !s.endsWith("Z") && !s.includes("+") && !s.includes("-")) {
      s += "Z";
    }
    return new Date(s).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  };

  if (loading) {
    return (
      <div className="section-shell">
        <div className="page-shell">
          <div className="hero-panel" style={{ minHeight: "320px" }} />
        </div>
      </div>
    );
  }

  return (
    <main className="section-shell">
      <div className="page-shell">
        <section className="hero-grid" style={{ alignItems: "stretch" }}>
          <div className="hero-panel">
            <div className="section-kicker">History</div>
            <h1 className="page-title" style={{ marginTop: "18px", maxWidth: "12ch" }}>
              Interview history in a clean, readable view.
            </h1>
            <p className="hero-copy" style={{ marginTop: "14px", maxWidth: "60ch" }}>
              Review completed sessions, jump back into unfinished practice, and filter by role or difficulty.
            </p>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", marginTop: "22px" }}>
              <button className="btn btn-primary" onClick={() => router.push("/new-interview")}>
                Start interview
              </button>
              <button className="btn btn-secondary" onClick={() => router.push("/learning")}>
                View learning
              </button>
            </div>
          </div>

          <div className="hero-visual" style={{ padding: "28px", minHeight: "320px" }}>
            <div className="soft-grid">
              <div className="card" style={{ padding: "18px" }}>
                <div className="ambient-label">Sessions</div>
                <div style={{ fontFamily: "var(--font-display)", fontSize: "2.8rem", fontWeight: 700, marginTop: "6px" }}>{counts.total}</div>
                <p className="section-copy">Total saved practice runs.</p>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "14px" }}>
                <div className="card" style={{ padding: "16px" }}>
                  <div className="ambient-label">Completed</div>
                  <div style={{ fontSize: "2rem", fontWeight: 700, marginTop: "6px" }}>{counts.completed}</div>
                </div>
                <div className="card" style={{ padding: "16px" }}>
                  <div className="ambient-label">In progress</div>
                  <div style={{ fontSize: "2rem", fontWeight: 700, marginTop: "6px" }}>{counts.active}</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section style={{ marginTop: "28px" }} className="feature-grid">
          <div className="feature-card feature-card--wide">
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", marginBottom: "18px" }}>
              <input
                type="text"
                placeholder="Search by role or company..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ flex: 1, minWidth: "220px" }}
              />
              <select value={difficultyFilter} onChange={(e) => setDifficultyFilter(e.target.value)} style={{ width: "180px" }}>
                <option value="all">All difficulties</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>

            <div style={{ display: "grid", gap: "14px" }}>
              {filteredSessions.length === 0 ? (
                <div className="card" style={{ textAlign: "center", padding: "42px 24px" }}>
                  <div className="ambient-label">No sessions found</div>
                  <p className="section-copy" style={{ marginTop: "10px" }}>
                    {search || difficultyFilter !== "all"
                      ? "Try a wider search or clear the filter."
                      : "Start a practice session to build your history."}
                  </p>
                </div>
              ) : (
                filteredSessions.map((s) => (
                  <div
                    key={s.id}
                    className="card"
                    style={{ display: "flex", justifyContent: "space-between", gap: "16px", alignItems: "center", flexWrap: "wrap" }}
                  >
                    <div style={{ display: "grid", gap: "8px" }}>
                      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", alignItems: "center" }}>
                        <h3 style={{ fontFamily: "var(--font-display)", fontSize: "1.2rem", fontWeight: 700 }}>{s.role}</h3>
                        <span className="badge badge-primary">{s.company_name || "General"}</span>
                        <span className={`badge ${s.difficulty === "hard" ? "badge-error" : s.difficulty === "medium" ? "badge-warning" : "badge-success"}`}>
                          {s.difficulty}
                        </span>
                      </div>
                      <p className="fine-print">
                        {formatDate(s.created_at)} · {s.duration_minutes} mins
                      </p>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      {s.status === "completed" ? (
                        <button className="btn btn-secondary" onClick={() => router.push(`/transcript/${s.id}`)}>
                          View report
                        </button>
                      ) : (
                        <button className="btn btn-primary" onClick={() => router.push(`/interview/${s.id}/voice`)}>
                          Resume
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="feature-card feature-card--tall">
            <div className="ambient-label">Session summary</div>
            <h2 className="headline" style={{ marginTop: "10px" }}>Quick scan</h2>
            <div style={{ display: "grid", gap: "12px", marginTop: "18px" }}>
              {[
                { label: "Most recent", value: sessions[0]?.role || "No sessions yet" },
                { label: "Primary company", value: sessions[0]?.company_name || "N/A" },
                { label: "Most used difficulty", value: sessions[0]?.difficulty || "N/A" }
              ].map((item) => (
                <div key={item.label} className="card" style={{ padding: "16px" }}>
                  <div className="ambient-label">{item.label}</div>
                  <div style={{ fontSize: "1.05rem", fontWeight: 700, marginTop: "8px" }}>{item.value}</div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
