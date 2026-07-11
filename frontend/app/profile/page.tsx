"use client";

import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { supabase } from "../utils/supabaseClient";

export default function ProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) return;
      fetch("http://127.0.0.1:8000/api/v1/interviews/profile/card", {
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      })
        .then((res) => res.json())
        .then((data) => {
          setProfile(data);
          setLoading(false);
        })
        .catch((err) => {
          console.error("Error fetching profile details:", err);
          setLoading(false);
        });
    });
  }, [user]);

  const getStreak = () => {
    return profile?.history_trends?.streak || 0;
  };

  const getProvenClaimsCount = () => {
    return profile?.proven_skills?.length || 0;
  };

  const getWeakSkillsCount = () => {
    return profile?.weak_skills?.length || 0;
  };

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
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
    <div style={{ display: "flex", flexDirection: "column", gap: "32px", maxWidth: "800px", margin: "0 auto" }}>
      
      {/* Profile Overview Card */}
      <div className="card" style={{ display: "flex", gap: "24px", alignItems: "center", flexWrap: "wrap" }}>
        <div style={{
          width: "80px",
          height: "80px",
          borderRadius: "50%",
          backgroundColor: "#3B82F6",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#FFFFFF",
          fontSize: "2.2rem",
          fontWeight: 700
        }}>
          {user?.email?.slice(0, 2).toUpperCase() || "US"}
        </div>
        <div>
          <h1 style={{ fontFamily: "var(--font-outfit)", fontSize: "1.6rem", fontWeight: 800, color: "var(--text-primary)" }}>
            {user?.user_metadata?.full_name || user?.email?.split("@")[0] || "User"}
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
            Candidate • Connected via {user?.app_metadata?.provider || 'Credentials'}
          </p>
          <div style={{ display: "flex", gap: "8px", marginTop: "8px" }}>
            <span className="badge badge-primary">AI Engineer</span>
            <span className="badge badge-primary">Backend Developer</span>
          </div>
        </div>
      </div>

      {/* Stats Counter Section */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "20px" }}>
        <div className="card" style={{ textAlign: "center", padding: "16px" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 700 }}>Practice Streak</span>
          <span style={{ display: "block", fontSize: "1.8rem", fontWeight: 800, margin: "6px 0", color: "#F97316" }}>🔥 {getStreak()} Days</span>
        </div>
        
        <div className="card" style={{ textAlign: "center", padding: "16px" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 700 }}>Verified Claims</span>
          <span style={{ display: "block", fontSize: "1.8rem", fontWeight: 800, margin: "6px 0", color: "var(--color-success)" }}>✓ {getProvenClaimsCount()}</span>
        </div>

        <div className="card" style={{ textAlign: "center", padding: "16px" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 700 }}>Gaps to Address</span>
          <span style={{ display: "block", fontSize: "1.8rem", fontWeight: 800, margin: "6px 0", color: "var(--color-error)" }}>⚠️ {getWeakSkillsCount()}</span>
        </div>
      </div>

      <div className="card" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, fontFamily: "var(--font-outfit)" }}>Verified Credentials</h2>
        {!profile?.proven_skills || profile.proven_skills.length === 0 ? (
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>No skills verified yet. Accomplish technical evaluation milestones to prove claims.</p>
        ) : (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {profile.proven_skills.map((skill: string) => (
              <span key={skill} className="badge badge-success" style={{ padding: "6px 12px", fontSize: "0.8rem" }}>
                ✓ {skill}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Achievements Badges */}
      <div className="card" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, fontFamily: "var(--font-outfit)" }}>Platform Achievements</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>
          {[
            { title: "First Practice Completed", desc: "Simulated your first mock AI session.", icon: "🏅", unlocked: true },
            { title: "Credibility Established", desc: "Successfully verified 1+ candidate resume claim.", icon: "🎯", unlocked: getProvenClaimsCount() > 0 },
            { title: "Routine Developer", desc: "Maintained a practice streak for 2+ consecutive turns.", icon: "⚡", unlocked: getStreak() >= 2 }
          ].map((ach) => (
            <div
              key={ach.title}
              style={{
                padding: "16px",
                borderRadius: "10px",
                border: "1px solid var(--border-main)",
                backgroundColor: ach.unlocked ? "#FFFFFF" : "#F8F9FA",
                opacity: ach.unlocked ? 1 : 0.5,
                display: "flex",
                gap: "12px",
                alignItems: "center"
              }}
            >
              <div style={{ fontSize: "2rem" }}>{ach.icon}</div>
              <div>
                <h4 style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-primary)" }}>{ach.title}</h4>
                <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "2px" }}>{ach.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
