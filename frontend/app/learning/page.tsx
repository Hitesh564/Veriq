"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "../context/AuthContext";
import { supabase } from "../utils/supabaseClient";
import { safeJsonFetch } from "../utils/api";

export default function LearningDashboardPage() {
  const router = useRouter();
  const { user } = useAuth();

  const [profile, setProfile] = useState<any>(null);
  const [studyPlan, setStudyPlan] = useState<any>(null);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [loadingStudy, setLoadingStudy] = useState(true);

  useEffect(() => {
    if (!user) return;

    supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (!session) {
        setLoadingProfile(false);
        return;
      }

      const data = await safeJsonFetch<any>("/api/v1/interviews/profile/card", {
        headers: { Authorization: `Bearer ${session.access_token}` }
      });

      setProfile(data);
      setLoadingProfile(false);
    });
  }, [user]);

  useEffect(() => {
    if (!user) return;

    supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (!session) {
        setLoadingStudy(false);
        return;
      }

      const data = await safeJsonFetch<any>("/api/v1/interviews/study-plans/latest", {
        headers: { Authorization: `Bearer ${session.access_token}` }
      });

      setStudyPlan(data);
      setLoadingStudy(false);
    });
  }, [user]);

  if (loadingProfile || loadingStudy) {
    return (
      <div className="section-shell">
        <div className="page-shell">
          <div className="hero-panel" style={{ minHeight: "260px" }} />
        </div>
      </div>
    );
  }

  const roadmap = studyPlan?.roadmap_json ? JSON.parse(studyPlan.roadmap_json) : [];
  const resources = studyPlan?.recommended_resources_json ? JSON.parse(studyPlan.recommended_resources_json) : [];
  const questions = studyPlan?.practice_questions_json ? JSON.parse(studyPlan.practice_questions_json) : [];
  const readiness = profile?.readiness_scores
    ? Math.round(
        Object.values(profile.readiness_scores).reduce((sum: number, score: any) => sum + Number(score), 0) /
          Math.max(1, Object.values(profile.readiness_scores).length)
      )
    : 0;

  const topicMastery = profile?.topic_mastery
    ? Object.entries(profile.topic_mastery).map(([topic, data]: any) => ({
        name: topic,
        score: data.average_score,
        state: data.mastery_state || "Unknown",
        attempts: data.attempts || 0
      }))
    : [];

  return (
    <main className="section-shell">
      <div className="page-shell">
        <section className="hero-grid">
          <div className="hero-panel">
            <div className="section-kicker">Learning</div>
            <h1 className="page-title" style={{ marginTop: "18px", maxWidth: "13ch" }}>
              Study plans that feel like a product.
            </h1>
            <p className="hero-copy" style={{ marginTop: "14px", maxWidth: "60ch" }}>
              Your weaknesses become a roadmap, and the roadmap becomes a tighter next interview.
            </p>
            <button className="btn btn-primary" style={{ marginTop: "22px" }} onClick={() => router.push("/new-interview")}>
              Practice focus topics
            </button>
          </div>

          <div className="hero-visual" style={{ padding: "28px" }}>
            <div className="card" style={{ padding: "20px" }}>
              <div className="ambient-label">Estimated readiness</div>
              <div style={{ display: "flex", alignItems: "end", gap: "10px", marginTop: "8px" }}>
                <div style={{ fontFamily: "var(--font-display)", fontSize: "3rem", fontWeight: 700 }}>{readiness}%</div>
                <div className="section-copy">average score</div>
              </div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "14px", marginTop: "14px" }}>
              {topicMastery.slice(0, 4).map((topic) => (
                <div key={topic.name} className="card" style={{ padding: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: "8px" }}>
                    <div style={{ fontWeight: 700 }}>{topic.name}</div>
                    <span className={`badge ${topic.state === "Strong" ? "badge-success" : topic.state === "Weak" ? "badge-error" : "badge-primary"}`}>
                      {topic.state}
                    </span>
                  </div>
                  <p className="fine-print" style={{ marginTop: "10px" }}>
                    {Math.round(topic.score)}% · {topic.attempts} attempts
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section style={{ marginTop: "28px" }} className="feature-grid">
          <div className="feature-card feature-card--wide">
            <div className="ambient-label">Roadmap</div>
            <h2 className="headline" style={{ marginTop: "10px" }}>Active study path</h2>
            <div style={{ display: "grid", gap: "12px", marginTop: "16px" }}>
              {roadmap.length === 0 ? (
                <p className="section-copy">No roadmap items available yet.</p>
              ) : (
                roadmap.map((milestone: any, index: number) => (
                  <div key={index} className="card" style={{ padding: "16px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}>
                      <div style={{ fontWeight: 700 }}>{milestone.concept}</div>
                      <span className={`badge ${milestone.priority === "High" ? "badge-error" : "badge-warning"}`}>
                        {milestone.priority}
                      </span>
                    </div>
                    <p className="section-copy" style={{ marginTop: "8px" }}>{milestone.rationale}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="feature-card feature-card--tall">
            <div className="ambient-label">Questions</div>
            <h2 className="headline" style={{ marginTop: "10px" }}>Practice prompts</h2>
            <div style={{ display: "grid", gap: "12px", marginTop: "16px" }}>
              {questions.length === 0 ? (
                <p className="section-copy">No focus questions populated.</p>
              ) : (
                questions.map((q: any, i: number) => (
                  <div key={i} className="card" style={{ padding: "16px" }}>
                    <div style={{ fontWeight: 700 }}>{q.question}</div>
                    <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "10px" }}>
                      {q.expected_keywords?.map((kw: string) => (
                        <span key={kw} className="badge badge-primary">{kw}</span>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>

        <section style={{ marginTop: "28px" }} className="feature-grid">
          <div className="feature-card feature-card--wide">
            <div className="ambient-label">Resources</div>
            <h2 className="headline" style={{ marginTop: "10px" }}>Curated study material</h2>
            <div style={{ display: "grid", gap: "12px", marginTop: "16px" }}>
              {resources.length === 0 ? (
                <p className="section-copy">No study resources available yet.</p>
              ) : (
                resources.map((resource: any, index: number) => (
                  <div key={index} className="card" style={{ padding: "16px" }}>
                    <div style={{ fontWeight: 700 }}>{resource.title || resource.name || "Resource"}</div>
                    <p className="section-copy" style={{ marginTop: "8px" }}>{resource.reason || resource.description || ""}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="feature-card feature-card--tall">
            <div className="ambient-label">Next step</div>
            <h2 className="headline" style={{ marginTop: "10px" }}>Keep the loop going</h2>
            <p className="section-copy" style={{ marginTop: "12px" }}>
              Focus on the topics with the highest leverage, then run another interview to measure change.
            </p>
            <button className="btn btn-primary" style={{ marginTop: "18px" }} onClick={() => router.push("/new-interview")}>
              Start next interview
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}
