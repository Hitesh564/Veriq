"use client";

import { useAuth } from "./context/AuthContext";

const features = [
  {
    icon: "auto_graph",
    title: "Real-time sentiment analysis",
    body: "Track pacing, clarity, confidence, and answer structure while the interview is still in motion."
  },
  {
    icon: "videocam",
    title: "Hyper-realistic scenarios",
    body: "Shape the conversation by role, company, difficulty, resume, or job description."
  },
  {
    icon: "history",
    title: "Transcript mapping",
    body: "Replay the conversation with follow-up depth, topic coverage, and improvement signals."
  }
];

const proof = [
  { value: "Voice-native", label: "interview flow" },
  { value: "Resume + JD", label: "personalization modes" },
  { value: "Readiness", label: "score tracking" },
  { value: "Study plan", label: "next-step output" }
];

const previewItems = [
  {
    title: "Interview session",
    body: "Senior Backend Engineer · System Design",
    note: "Live question flow"
  },
  {
    title: "AI feedback",
    body: "Confidence high, clarity strong, depth needs more evidence.",
    note: "Post-turn signal"
  },
  {
    title: "Study focus",
    body: "Caching tradeoffs, failure handling, and stronger architecture detail.",
    note: "Roadmap item"
  }
];

export default function HomePage() {
  const { setShowAuthModal } = useAuth();

  return (
    <main className="section-shell">
      <div className="page-shell">
        <section className="hero-grid">
          <div style={{ display: "grid", gap: "22px", alignContent: "center" }}>
            <div className="section-kicker">
              <span className="material-symbols-outlined" style={{ fontSize: 18, color: "var(--accent)" }}>auto_awesome</span>
              AI co-pilot active
            </div>

            <div style={{ display: "grid", gap: "16px" }}>
              <h1 className="display-title">
                The Future of Interviewing is Here.
              </h1>
              <p className="hero-copy" style={{ maxWidth: "58ch" }}>
                Elevate your career trajectory with an adaptive interview engine. IntervAI turns ideas into practice sessions,
                practice into feedback, and feedback into a clearer next move.
              </p>
            </div>

            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <button type="button" className="btn btn-primary" onClick={() => setShowAuthModal(true)}>
                Start Practice Free
              </button>
              <a href="/product" className="btn btn-secondary">
                View Features
              </a>
            </div>

            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              {proof.map((item) => (
                <div key={item.label} className="subtle-chip">
                  <strong style={{ color: "var(--text-primary)" }}>{item.value}</strong>
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="hero-visual" style={{ padding: "28px", overflow: "hidden" }}>
            <div style={{ display: "grid", gap: "16px", position: "relative", zIndex: 1 }}>
              <div className="card" style={{ padding: "18px", width: "100%", maxWidth: "340px" }}>
                <div className="ambient-label">Live session</div>
                <div style={{ fontFamily: "var(--font-display)", fontSize: "1.6rem", fontWeight: 700, marginTop: "10px" }}>
                  Senior Backend Engineer
                </div>
                <p className="section-copy" style={{ marginTop: "8px" }}>
                  System design, behavioral follow-ups, and live evaluation in one flow.
                </p>
              </div>

              <div style={{ display: "grid", gap: "14px", gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}>
                {previewItems.map((item, index) => (
                  <div
                    key={item.title}
                    className="card"
                    style={{
                      minHeight: "150px",
                      padding: "18px",
                      transform: index === 1 ? "translateY(18px)" : "translateY(0)",
                      background: index === 1 ? "rgba(255, 255, 255, 0.9)" : "rgba(255, 253, 249, 0.78)"
                    }}
                  >
                    <div className="ambient-label">{item.note}</div>
                    <div style={{ fontSize: "1.05rem", fontWeight: 700, marginTop: "10px" }}>{item.title}</div>
                    <p className="body-copy" style={{ marginTop: "10px" }}>{item.body}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section style={{ paddingTop: "92px" }}>
          <div style={{ textAlign: "center", marginBottom: "28px" }}>
            <h2 className="section-title">Cognitive Capabilities</h2>
            <p className="section-copy" style={{ marginTop: "10px" }}>
              Advanced tools designed to refine your narrative and amplify your interview presence.
            </p>
          </div>

          <div className="feature-grid">
            {features.map((feature, index) => (
              <article
                key={feature.title}
                className={`feature-card ${index === 1 ? "soft-raise" : ""}`}
                style={index === 1 ? { borderTop: "4px solid var(--accent)" } : undefined}
              >
                <div style={{
                  width: "48px",
                  height: "48px",
                  borderRadius: "16px",
                  display: "grid",
                  placeItems: "center",
                  background: "rgba(255,255,255,0.82)",
                  border: "1px solid var(--border-subtle)"
                }}>
                  <span className="material-symbols-outlined" style={{ color: index === 1 ? "var(--accent)" : "var(--text-primary)" }}>
                    {feature.icon}
                  </span>
                </div>
                <h3 className="headline" style={{ marginTop: "10px" }}>{feature.title}</h3>
                <p className="section-copy" style={{ marginTop: "8px" }}>{feature.body}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
