"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../context/AuthContext";
import { supabase } from "../utils/supabaseClient";

export default function LearningDashboardPage() {
  const router = useRouter();
  const { user } = useAuth();
  
  const [profile, setProfile] = useState<any>(null);
  const [studyPlan, setStudyPlan] = useState<any>(null);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [loadingStudy, setLoadingStudy] = useState(true);

  // Fetch User Progress Profile
  useEffect(() => {
    if (!user) return;

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) return;
      fetch("http://127.0.0.1:8000/api/v1/interviews/profile/card", {
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      })
        .then((res) => {
          if (!res.ok) throw new Error("Failed to load progress card");
          return res.json();
        })
        .then((data) => {
          setProfile(data);
          setLoadingProfile(false);
        })
        .catch((err) => {
          console.error("Error fetching profile:", err);
          setLoadingProfile(false);
        });
    });
  }, [user]);

  // Fetch Coaching / Study Plan
  useEffect(() => {
    if (!user) return;

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) return;
      fetch("http://127.0.0.1:8000/api/v1/interviews/study-plans/latest", {
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      })
        .then((res) => {
          if (!res.ok) throw new Error("Failed to load study plan");
          return res.json();
        })
        .then((data) => {
          setStudyPlan(data);
          setLoadingStudy(false);
        })
        .catch((err) => {
          console.error("Error fetching study plan:", err);
          setLoadingStudy(false);
        });
    });
  }, [user]);

  const getReadinessPercentage = () => {
    if (!profile || !profile.readiness_scores) return 0;
    const scores = Object.values(profile.readiness_scores) as number[];
    if (scores.length === 0) return 0;
    const avg = scores.reduce((sum, s) => sum + s, 0) / scores.length;
    return Math.round(avg);
  };

  const getTopicMasteryList = () => {
    if (!profile || !profile.topic_mastery) return [];
    return Object.entries(profile.topic_mastery).map(([topic, data]: any) => ({
      name: topic,
      score: data.average_score,
      state: data.mastery_state || "Unknown",
      attempts: data.attempts || 0
    }));
  };

  const topicList = getTopicMasteryList();

  if (loadingProfile || loadingStudy) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        <div style={{ height: "160px", backgroundColor: "#FFFFFF", borderRadius: "12px", border: "1px solid #E4E7EC", width: "100%", animation: "pulse 1.5s infinite" }} />
        <div style={{ height: "300px", backgroundColor: "#FFFFFF", borderRadius: "12px", border: "1px solid #E4E7EC", width: "100%", animation: "pulse 1.5s infinite" }} />
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

  const roadmap = studyPlan?.roadmap_json ? JSON.parse(studyPlan.roadmap_json) : [];
  const resources = studyPlan?.recommended_resources_json ? JSON.parse(studyPlan.recommended_resources_json) : [];
  const questions = studyPlan?.practice_questions_json ? JSON.parse(studyPlan.practice_questions_json) : [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px", maxWidth: "960px", margin: "0 auto" }}>
      
      {/* Overview Card */}
      <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "24px" }}>
        <div>
          <h1 style={{ fontFamily: "var(--font-outfit)", fontSize: "1.8rem", fontWeight: 800, marginBottom: "8px", letterSpacing: "-0.5px" }}>
            Coaching & Mastery Dashboard
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
            Track your verified skills, weak concepts, and study milestones.
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div style={{ textAlign: "right" }}>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase" }}>Estimated Readiness</span>
            <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "var(--color-primary)" }}>{getReadinessPercentage()}%</div>
          </div>
          <button
            onClick={() => router.push("/new-interview")}
            className="btn btn-primary"
          >
            Practice Focus Topics
          </button>
        </div>
      </div>

      {/* TOPIC MASTERY MATRIX */}
      <div className="card" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <h2 style={{ fontSize: "1.2rem", fontWeight: 700, fontFamily: "var(--font-outfit)" }}>Skill Area Mastery</h2>
        {topicList.length === 0 ? (
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", padding: "12px 0" }}>
            No skill mastery scores logged yet. Complete mock interview sessions to verify proficiency.
          </p>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
            {topicList.map((topic) => (
              <div
                key={topic.name}
                style={{
                  padding: "16px",
                  borderRadius: "10px",
                  border: "1px solid var(--border-main)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px"
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontWeight: 700, fontSize: "0.9rem", color: "var(--text-primary)" }}>{topic.name}</span>
                  <span className={`badge ${
                    topic.state === "Strong" ? "badge-success" : topic.state === "Weak" ? "badge-error" : "badge-primary"
                  }`}>
                    {topic.state}
                  </span>
                </div>
                
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    <span>Score: {Math.round(topic.score)}%</span>
                    <span>Attempts: {topic.attempts}</span>
                  </div>
                  <div style={{ width: "100%", height: "4px", borderRadius: "2px", backgroundColor: "#E4E7EC", overflow: "hidden" }}>
                    <div style={{
                      width: `${topic.score}%`,
                      height: "100%",
                      backgroundColor: topic.state === "Strong" ? "var(--color-success)" : topic.state === "Weak" ? "var(--color-error)" : "var(--color-primary)"
                    }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ROADMAP / STUDY PLAN TIMELINE */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "24px", alignItems: "start" }}>
        
        {/* Milestone Milestones Roadmap */}
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <h2 style={{ fontSize: "1.15rem", fontWeight: 700, fontFamily: "var(--font-outfit)" }}>Active Learning Roadmap</h2>
          {roadmap.length === 0 ? (
            <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", padding: "16px 0", textAlign: "center" }}>
              No study plan milestones calculated yet. Gaps will appear here after evaluations.
            </p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px", position: "relative", paddingLeft: "20px" }}>
              {/* Connecting line */}
              <div style={{
                position: "absolute",
                top: "10px",
                bottom: "10px",
                left: "6px",
                width: "2px",
                backgroundColor: "#E4E7EC"
              }} />

              {roadmap.map((milestone: any, index: number) => (
                <div key={index} style={{ position: "relative", display: "flex", flexDirection: "column", gap: "4px" }}>
                  {/* Circle indicator */}
                  <div style={{
                    position: "absolute",
                    top: "4px",
                    left: "-18px",
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    backgroundColor: milestone.priority === "High" ? "var(--color-error)" : milestone.priority === "Medium" ? "var(--color-warning)" : "var(--color-primary)",
                    border: "2px solid #FFFFFF"
                  }} />
                  
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                    <h4 style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-primary)" }}>{milestone.concept}</h4>
                    <span className={`badge ${milestone.priority === "High" ? "badge-error" : "badge-warning"}`} style={{ fontSize: "0.65rem" }}>
                      {milestone.priority} Priority
                    </span>
                  </div>
                  <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", lineHeight: "1.4" }}>{milestone.rationale}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Suggested Resources & Practice Questions */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          
          {/* Practice Questions */}
          <div className="card" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <h3 style={{ fontSize: "1.05rem", fontWeight: 700, fontFamily: "var(--font-outfit)" }}>Suggested Practice Questions</h3>
            {questions.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No focus questions populated.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {questions.map((q: any, i: number) => (
                  <div
                    key={i}
                    style={{
                      padding: "12px",
                      borderRadius: "8px",
                      border: "1px solid var(--border-subtle)",
                      backgroundColor: "#FCFCFD",
                      fontSize: "0.85rem"
                    }}
                  >
                    <div style={{ fontWeight: 700, color: "var(--text-primary)", marginBottom: "4px" }}>Q: {q.question}</div>
                    <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "6px" }}>
                      {q.expected_keywords?.map((kw: string) => (
                        <span key={kw} className="badge badge-primary" style={{ fontSize: "0.65rem" }}>{kw}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Curated Resources */}
          <div className="card" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <h3 style={{ fontSize: "1.05rem", fontWeight: 700, fontFamily: "var(--font-outfit)" }}>Curated Documentation</h3>
            {resources.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>No suggested readings.</p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {resources.map((res: any, i: number) => (
                  <a
                    key={i}
                    href={res.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      padding: "10px 14px",
                      borderRadius: "8px",
                      border: "1px solid var(--border-subtle)",
                      backgroundColor: "#FCFCFD",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      fontSize: "0.85rem",
                      color: "var(--text-primary)",
                      fontWeight: 600
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = "#F9FAFB";
                      e.currentTarget.style.borderColor = "var(--border-hover)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = "#FCFCFD";
                      e.currentTarget.style.borderColor = "var(--border-subtle)";
                    }}
                  >
                    <span>📖 {res.title} ({res.type})</span>
                    <span style={{ color: "#3B82F6", fontSize: "0.8rem" }}>Read →</span>
                  </a>
                ))}
              </div>
            )}
          </div>

        </div>

      </div>

    </div>
  );
}
