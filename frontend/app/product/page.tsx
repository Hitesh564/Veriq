"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "../context/AuthContext";

const pillars = [
  {
    title: "Voice interview engine",
    body: "Run a real interview flow with live conversation instead of a static questionnaire."
  },
  {
    title: "Transcript intelligence",
    body: "Store every question, answer, and topic so the evaluation is based on the full conversation."
  },
  {
    title: "Learning loop",
    body: "Turn weak topics into a roadmap, curated resources, and a targeted re-interview."
  },
  {
    title: "Readiness scoring",
    body: "Track role-specific readiness over time rather than a one-off performance snapshot."
  }
];

const outputs = [
  "Overall score and topic breakdown",
  "Strengths and weaknesses summary",
  "Targeted study milestones",
  "Practice questions for the next run"
];

export default function ProductPage() {
  const router = useRouter();
  const { setShowAuthModal } = useAuth();

  return (
    <div className="section-shell">
      <div className="page-shell">
        <section className="hero-panel reveal-up" style={{ padding: "36px" }}>
          <div className="eyebrow">Product</div>
          <h1 className="page-title text-balance" style={{ marginTop: "16px", maxWidth: "13ch" }}>
            Everything Veriq AI does, in one product loop.
          </h1>
          <p className="hero-copy" style={{ marginTop: "14px", maxWidth: "64ch" }}>
            From interview setup to transcript evaluation to study planning, the product is designed as a continuous system instead of a dead-end mock test.
          </p>
          <div style={{ marginTop: "22px", display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <button className="btn btn-primary" onClick={() => setShowAuthModal(true)}>Start free</button>
            <Link href="/how-it-works" className="btn btn-secondary">See workflow</Link>
          </div>
        </section>

        <section className="feature-grid" style={{ marginTop: "28px" }}>
          {pillars.map((pillar) => (
            <div key={pillar.title} className="feature-card">
              <div className="feature-card__icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 7 9 18l-5-5" />
                </svg>
              </div>
              <h2 style={{ fontFamily: "var(--font-outfit)", fontSize: "1.4rem", fontWeight: 800 }}>{pillar.title}</h2>
              <p className="section-copy" style={{ marginTop: "10px" }}>{pillar.body}</p>
            </div>
          ))}
        </section>

        <section className="feature-grid" style={{ marginTop: "28px" }}>
          <div className="results-panel" style={{ gridColumn: "span 7", padding: "28px" }}>
            <div className="eyebrow">What users get</div>
            <h2 className="section-title text-balance" style={{ marginTop: "14px" }}>A report that makes the next decision obvious.</h2>
            <div style={{ marginTop: "18px", display: "grid", gap: "12px" }}>
              {outputs.map((item) => (
                <div key={item} className="card" style={{ padding: "16px", boxShadow: "none" }}>
                  {item}
                </div>
              ))}
            </div>
          </div>

          <div className="card" style={{ gridColumn: "span 5", padding: "28px" }}>
            <div className="eyebrow">Modes</div>
            <h3 style={{ fontFamily: "var(--font-outfit)", fontSize: "1.5rem", fontWeight: 800, marginTop: "14px" }}>
              Quick, company-specific, resume-based, and JD-based interviews.
            </h3>
            <p className="section-copy" style={{ marginTop: "12px" }}>
              The backend already supports the major flows people actually use when preparing for interviews.
            </p>
            <button className="btn btn-secondary" style={{ marginTop: "16px" }} onClick={() => router.push("/new-interview")}>
              Build an interview
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
