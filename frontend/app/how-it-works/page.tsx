"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "../context/AuthContext";

const steps = [
  {
    title: "Configure the session",
    body: "Choose a role, difficulty, duration, and optionally a company, resume, or job description.",
    tag: "Setup"
  },
  {
    title: "Run the interview",
    body: "The AI asks, follows up, and shifts depth based on the quality of each answer.",
    tag: "Conversation"
  },
  {
    title: "Review and improve",
    body: "The session closes with a report, readiness score, and a learning plan for the next run.",
    tag: "Outcome"
  }
];

export default function HowItWorksPage() {
  const router = useRouter();
  const { setShowAuthModal } = useAuth();

  return (
    <div className="section-shell">
      <div className="page-shell">
        <section className="hero-panel reveal-up" style={{ padding: "36px" }}>
          <div className="eyebrow">Workflow</div>
          <h1 className="page-title text-balance" style={{ marginTop: "16px", maxWidth: "13ch" }}>
            A startup-style flow that guides the user from start to finish.
          </h1>
          <p className="hero-copy" style={{ marginTop: "14px", maxWidth: "64ch" }}>
            The design follows the same logic as the product: fewer choices up front, more clarity after each step, and a better next action once the interview ends.
          </p>
          <div style={{ marginTop: "22px", display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <button className="btn btn-primary" onClick={() => setShowAuthModal(true)}>Start free</button>
            <Link href="/product" className="btn btn-secondary">Product details</Link>
          </div>
        </section>

        <section className="workflow-grid" style={{ marginTop: "28px" }}>
          {steps.map((step, index) => (
            <div key={step.title} className="workflow-panel" style={{ padding: "28px" }}>
              <div className="eyebrow">{step.tag}</div>
              <div style={{ marginTop: "18px", width: "60px", height: "60px", borderRadius: "20px", background: "rgba(37,99,235,0.1)", display: "grid", placeItems: "center", fontFamily: "var(--font-outfit)", fontSize: "1.4rem", fontWeight: 800 }}>
                0{index + 1}
              </div>
              <h2 style={{ fontFamily: "var(--font-outfit)", fontSize: "1.45rem", fontWeight: 800, marginTop: "18px" }}>{step.title}</h2>
              <p className="section-copy" style={{ marginTop: "10px" }}>{step.body}</p>
            </div>
          ))}
        </section>

        <section className="feature-grid" style={{ marginTop: "28px" }}>
          <div className="feature-card" style={{ gridColumn: "span 6" }}>
            <div className="eyebrow">Why it feels better</div>
            <h2 className="section-title text-balance" style={{ marginTop: "14px" }}>The workflow is split across pages, not crammed into one screen.</h2>
            <p className="section-copy" style={{ marginTop: "12px" }}>
              That makes the experience feel more like a real SaaS product and less like a prototype with every detail thrown onto the home page.
            </p>
          </div>

          <div className="card" style={{ gridColumn: "span 6", padding: "28px" }}>
            <div className="eyebrow">Ready to try it</div>
            <h3 style={{ fontFamily: "var(--font-outfit)", fontSize: "1.5rem", fontWeight: 800, marginTop: "14px" }}>Move into the interview room when you are ready.</h3>
            <p className="section-copy" style={{ marginTop: "10px" }}>
              The real value starts once the AI begins probing your answer in context.
            </p>
            <button className="btn btn-primary" style={{ marginTop: "16px" }} onClick={() => router.push("/new-interview")}>
              Start interview
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
