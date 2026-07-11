"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "../context/AuthContext";
import { supabase } from "../utils/supabaseClient";

interface InterviewSession {
  id: string;
  role: string;
  difficulty: string;
  duration_minutes: number;
  status: string;
  created_at: string;
  company_name?: string;
  score?: number;
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

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) return;
      fetch("http://127.0.0.1:8000/api/v1/interviews", {
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      })
        .then((res) => {
          if (!res.ok) throw new Error("Failed to load history");
          return res.json();
        })
        .then((data) => {
          setSessions(data);
          setLoading(false);
        })
        .catch((err) => {
          console.error("Error fetching sessions:", err);
          setLoading(false);
        });
    });
  }, [user]);

  const formatDate = (dateString: string) => {
    let s = dateString;
    if (s && !s.endsWith("Z") && !s.includes("+") && !s.includes("-")) {
      s += "Z";
    }
    const d = new Date(s);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const handleDeleteMock = (id: string) => {
    // Perform local client-side state cleanup for UX simplicity
    setSessions((prev) => prev.filter((s) => s.id !== id));
  };

  // Filter logic
  const filteredSessions = sessions.filter((s) => {
    const roleMatch = s.role.toLowerCase().includes(search.toLowerCase());
    const companyMatch = (s.company_name || "").toLowerCase().includes(search.toLowerCase());
    const diffMatch = difficultyFilter === "all" || s.difficulty === difficultyFilter;
    return (roleMatch || companyMatch) && diffMatch;
  });

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        <div style={{ height: "60px", backgroundColor: "#FFFFFF", borderRadius: "12px", border: "1px solid #E4E7EC", width: "100%", animation: "pulse 1.5s infinite" }} />
        <div style={{ height: "180px", backgroundColor: "#FFFFFF", borderRadius: "12px", border: "1px solid #E4E7EC", width: "100%", animation: "pulse 1.5s infinite" }} />
        <div style={{ height: "180px", backgroundColor: "#FFFFFF", borderRadius: "12px", border: "1px solid #E4E7EC", width: "100%", animation: "pulse 1.5s infinite" }} />
        <style jsx>{`
          @keyframes pulse {
            0% { opacity: 0.6; }
            50% { opacity: 0.9; }
            100% { opacity: 0.6; }
          }
        `}</style>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", maxWidth: "800px", margin: "0 auto" }}>
      
      {/* Search & Filters Row */}
      <div className="card" style={{ display: "flex", gap: "16px", flexWrap: "wrap", padding: "16px 24px" }}>
        <div style={{ flex: 1, minWidth: "200px" }}>
          <input
            type="text"
            placeholder="Search by role or company..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div style={{ width: "160px" }}>
          <select
            value={difficultyFilter}
            onChange={(e) => setDifficultyFilter(e.target.value)}
          >
            <option value="all">All Difficulties</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </div>
      </div>

      {/* Sessions Timeline List */}
      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {filteredSessions.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: "48px 0" }}>
            <div style={{ fontSize: "2.4rem", marginBottom: "12px" }}>📋</div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "4px" }}>No sessions found</h3>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "16px" }}>
              {search || difficultyFilter !== "all" 
                ? "Try widening your filter conditions." 
                : "Conduct mock simulations to populate history lists."}
            </p>
            {!search && difficultyFilter === "all" && (
              <button onClick={() => router.push("/new-interview")} className="btn btn-primary">
                Start First Mock Session
              </button>
            )}
          </div>
        ) : (
          filteredSessions.map((s) => (
            <div
              key={s.id}
              className="card"
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "20px"
              }}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                  <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-primary)" }}>{s.role}</h3>
                  <span className="badge badge-primary" style={{ fontSize: "0.7rem" }}>{s.company_name || "General"}</span>
                  <span className={`badge ${
                    s.difficulty === "hard" ? "badge-error" : s.difficulty === "medium" ? "badge-warning" : "badge-success"
                  }`} style={{ fontSize: "0.7rem", textTransform: "capitalize" }}>
                    {s.difficulty}
                  </span>
                </div>
                <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Scheduled: {formatDate(s.created_at)} • Duration: {s.duration_minutes} Mins
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                {s.status === "completed" ? (
                  <>
                    <button
                      onClick={() => router.push(`/transcript/${s.id}`)}
                      className="btn btn-secondary"
                      style={{ padding: "8px 16px", fontSize: "0.85rem" }}
                    >
                      View Report
                    </button>
                    <button
                      onClick={() => handleDeleteMock(s.id)}
                      className="btn btn-secondary"
                      style={{ padding: "8px", color: "var(--color-error)", borderColor: "#FCA5A5" }}
                    >
                      Delete
                    </button>
                  </>
                ) : (
                  <>
                    <span className="badge badge-warning" style={{ textTransform: "uppercase" }}>In Progress</span>
                    <button
                      onClick={() => router.push(`/interview/${s.id}/voice`)}
                      className="btn btn-primary"
                      style={{ padding: "8px 16px", fontSize: "0.85rem" }}
                    >
                      Resume
                    </button>
                  </>
                )}
              </div>
            </div>
          ))
        )}
      </div>

    </div>
  );
}
