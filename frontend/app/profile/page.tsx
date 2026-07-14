"use client";

import { useEffect, useState } from "react";

import { useAuth } from "../context/AuthContext";
import { supabase } from "../utils/supabaseClient";
import { safeJsonFetch } from "../utils/api";

export default function ProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;

    supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (!session) {
        setLoading(false);
        return;
      }

      const data = await safeJsonFetch<any>("/api/v1/interviews/profile/card", {
        headers: { Authorization: `Bearer ${session.access_token}` }
      });

      setProfile(data);
      setLoading(false);
    });
  }, [user]);

  if (loading) {
    return (
      <div className="section-shell">
        <div className="page-shell">
          <div className="hero-panel" style={{ minHeight: "240px" }} />
        </div>
      </div>
    );
  }

  const getStreak = () => profile?.history_trends?.streak || 0;
  const getProvenClaimsCount = () => profile?.proven_skills?.length || 0;
  const getWeakSkillsCount = () => profile?.weak_skills?.length || 0;

  return (
    <main className="section-shell">
      <div className="page-shell">
        <section className="hero-grid">
          <div className="hero-panel">
            <div className="section-kicker">Profile</div>
            <h1 className="page-title" style={{ marginTop: "18px", maxWidth: "12ch" }}>
              Candidate profile and progress.
            </h1>
            <p className="hero-copy" style={{ marginTop: "14px", maxWidth: "58ch" }}>
              View your verified skills, practice streak, and the gaps the system is watching.
            </p>
          </div>

          <div className="hero-visual" style={{ padding: "28px" }}>
            <div style={{ display: "grid", gap: "16px" }}>
              <div className="card" style={{ display: "flex", gap: "18px", alignItems: "center" }}>
                <div style={{
                  width: "84px",
                  height: "84px",
                  borderRadius: "28px",
                  background: "linear-gradient(135deg, #111110, #d5ad34)",
                  color: "#fff",
                  display: "grid",
                  placeItems: "center",
                  fontFamily: "var(--font-display)",
                  fontSize: "1.6rem",
                  fontWeight: 700
                }}>
                  {(user?.email?.slice(0, 2).toUpperCase()) || "AI"}
                </div>
                <div>
                  <div style={{ fontFamily: "var(--font-display)", fontSize: "1.8rem", fontWeight: 700 }}>
                    {user?.user_metadata?.full_name || user?.email?.split("@")[0] || "User"}
                  </div>
                  <p className="section-copy">Candidate · Connected via {user?.app_metadata?.provider || "credentials"}</p>
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "12px" }}>
                <div className="card" style={{ textAlign: "center", padding: "16px" }}>
                  <div className="ambient-label">Streak</div>
                  <div style={{ fontSize: "2rem", fontWeight: 700, marginTop: "6px" }}>{getStreak()}</div>
                </div>
                <div className="card" style={{ textAlign: "center", padding: "16px" }}>
                  <div className="ambient-label">Verified</div>
                  <div style={{ fontSize: "2rem", fontWeight: 700, marginTop: "6px" }}>{getProvenClaimsCount()}</div>
                </div>
                <div className="card" style={{ textAlign: "center", padding: "16px" }}>
                  <div className="ambient-label">Gaps</div>
                  <div style={{ fontSize: "2rem", fontWeight: 700, marginTop: "6px" }}>{getWeakSkillsCount()}</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section style={{ marginTop: "28px" }} className="feature-grid">
          <div className="feature-card feature-card--wide">
            <div className="ambient-label">Verified Credentials</div>
            <h2 className="headline" style={{ marginTop: "10px" }}>Claims you have already proven</h2>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", marginTop: "16px" }}>
              {!profile?.proven_skills || profile.proven_skills.length === 0 ? (
                <p className="section-copy">No skills verified yet. Complete sessions to establish proof.</p>
              ) : (
                profile.proven_skills.map((skill: string) => (
                  <span key={skill} className="badge badge-success">{skill}</span>
                ))
              )}
            </div>
          </div>

          <div className="feature-card feature-card--tall">
            <div className="ambient-label">Focus areas</div>
            <h2 className="headline" style={{ marginTop: "10px" }}>Topics to tighten</h2>
            <div style={{ display: "grid", gap: "12px", marginTop: "16px" }}>
              {(profile?.weak_skills || []).length === 0 ? (
                <p className="section-copy">No weak skills are flagged right now.</p>
              ) : (
                profile.weak_skills.map((skill: string) => (
                  <div key={skill} className="card" style={{ padding: "14px" }}>
                    <div style={{ fontWeight: 700 }}>{skill}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
