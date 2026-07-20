"use client";

import { useMemo, useState } from "react";

import { useAuth } from "./context/AuthContext";

type ModeKey = "adaptive" | "voice" | "growth";

const capabilityModes: Array<{
  key: ModeKey;
  kicker: string;
  title: string;
  body: string;
  signal: string[];
}> = [
  {
    key: "adaptive",
    kicker: "Adaptive intelligence",
    title: "The session changes around your role, resume, and job target.",
    body: "Veriq does not ask the same static questions. It blends role, resume, JD, and difficulty into a single interview model that keeps adjusting as the conversation moves.",
    signal: ["Role-aware", "Resume-aware", "JD-aware"]
  },
  {
    key: "voice",
    kicker: "Voice-native interview",
    title: "A live conversation feels closer to a real interview room.",
    body: "The experience is built for spoken answers, follow-ups, pacing, and pressure. The interaction feels active instead of like a form with AI sprinkled on top.",
    signal: ["Listening", "Speaking", "Follow-up depth"]
  },
  {
    key: "growth",
    kicker: "Personalized growth loop",
    title: "Every session ends with a clearer next move.",
    body: "Scores, weak topics, verified claims, and study plans turn the interview into a learning loop, so the next run is more focused than the last.",
    signal: ["Readiness", "Weak spots", "Next practice"]
  }
];

const proofNotes = [
  "Adaptive scenarios",
  "Voice-native rooms",
  "Actionable feedback"
];

const scrollSteps = [
  {
    num: "01",
    title: "Configure the session",
    body: "Choose a role, difficulty, company style, and optional resume or JD input. The setup is designed to feel editorial, not like a long form."
  },
  {
    num: "02",
    title: "Run the interview",
    body: "The live interview responds with questions, clarifications, and pressure where it matters. You are not just filling a questionnaire."
  },
  {
    num: "03",
    title: "Turn it into a loop",
    body: "Your transcript, score, strengths, and weaknesses become the basis for the next interview and the next study plan."
  }
];

const starPoints = [
  {
    title: "Adaptive intelligence",
    body: "The model reacts to the userâ€™s profile and target role instead of using one fixed script."
  },
  {
    title: "Voice-first interaction",
    body: "A live speaking experience creates more energy than a static landing page or plain setup wizard."
  },
  {
    title: "Feedback that moves users forward",
    body: "The product closes the loop by turning performance into a next-step roadmap."
  }
];

export default function HomePage() {
  const { setShowAuthModal } = useAuth();
  const [activeMode, setActiveMode] = useState<ModeKey>("adaptive");

  const activeCapability = useMemo(
    () => capabilityModes.find((mode) => mode.key === activeMode) || capabilityModes[0],
    [activeMode]
  );

  return (
    <main className="landing-page">
      <section className="landing-hero">
        <div className="landing-orb landing-orb--one" />
        <div className="landing-orb landing-orb--two" />
        <div className="landing-noise" />

        <div className="page-shell">
          <div className="landing-hero__grid">
            <div className="landing-hero__copy">
              <div className="section-kicker landing-kicker">
                <span className="material-symbols-outlined" style={{ fontSize: 18, color: "var(--accent)" }}>
                  auto_awesome
                </span>
                AI co-pilot active
              </div>

              <h1 className="landing-title">
                Interview practice that feels alive.
              </h1>

              <p className="landing-subtitle">
                Veriq turns interview preparation into a premium, scrollable experience with adaptive sessions, live voice flow, and a feedback loop that keeps improving your next run.
              </p>

              <div className="landing-actions">
                <button type="button" className="btn btn-primary" onClick={() => setShowAuthModal(true)}>
                  Start practice free
                </button>
                <a href="/new-interview" className="btn btn-secondary">
                  Explore setup
                </a>
              </div>

              <div className="landing-proof">
                {proofNotes.map((item) => (
                  <div key={item} className="landing-proof__item">
                    <span className="landing-proof__dot" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>

          </div>

          <div className="landing-scroll-hint">
            <span className="landing-scroll-hint__line" />
            Scroll to explore the product story
          </div>
        </div>
      </section>

      <section className="landing-section">
        <div className="page-shell">
          <div className="landing-section__intro">
            <div className="section-kicker">Why it stands out</div>
            <h2 className="landing-section__title">
              Three strengths that make the product feel premium, useful, and hard to ignore.
            </h2>
          </div>

          <div className="mode-rail">
            <div className="mode-rail__buttons">
              {capabilityModes.map((mode) => {
                const isActive = mode.key === activeMode;
                return (
                  <button
                    key={mode.key}
                    type="button"
                    onClick={() => setActiveMode(mode.key)}
                    className={`mode-toggle ${isActive ? "mode-toggle--active" : ""}`}
                  >
                    <span className="mode-toggle__index">0{capabilityModes.indexOf(mode) + 1}</span>
                    <span>{mode.kicker}</span>
                  </button>
                );
              })}
            </div>

            <div className="mode-rail__detail">
              <div className="mode-detail">
                <div className="mode-detail__eyebrow">{activeCapability.kicker}</div>
                <h3 className="mode-detail__title">{activeCapability.title}</h3>
                <p className="mode-detail__body">{activeCapability.body}</p>
              </div>

              <div className="signal-strip" aria-hidden="true">
                {activeCapability.signal.map((signal, index) => (
                  <div key={signal} className={`signal-strip__item signal-strip__item--${index + 1}`}>
                    <span />
                    <strong>{signal}</strong>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-section landing-section--tight">
        <div className="page-shell">
          <div className="landing-section__intro landing-section__intro--center">
            <div className="section-kicker">How the experience flows</div>
            <h2 className="landing-section__title">
              The page scrolls like a story, not a brochure.
            </h2>
          </div>

          <div className="process-flow">
            {scrollSteps.map((step, index) => (
              <div key={step.num} className="process-row">
                <div className="process-row__index">{step.num}</div>
                <div className="process-row__content">
                  <h3 className="process-row__title">{step.title}</h3>
                  <p className="process-row__body">{step.body}</p>
                </div>
                <div className="process-row__mark" aria-hidden="true">
                  <span className={`process-row__dot process-row__dot--${index + 1}`} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="landing-section">
        <div className="page-shell">
          <div className="landing-section__intro landing-section__intro--center">
            <div className="section-kicker">Core strengths</div>
            <h2 className="landing-section__title">
              The three points we should highlight on the home page.
            </h2>
          </div>

          <div className="star-list">
            {starPoints.map((item, index) => (
              <div key={item.title} className="star-row">
                <div className="star-row__number">0{index + 1}</div>
                <div className="star-row__text">
                  <h3 className="star-row__title">{item.title}</h3>
                  <p className="star-row__body">{item.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="landing-section landing-section--cta">
        <div className="page-shell">
          <div className="cta-band">
            <div>
              <div className="section-kicker">Ready to practice</div>
              <h2 className="cta-band__title">Launch a better interview loop in a few seconds.</h2>
              <p className="cta-band__body">
                A premium landing page should feel calm, active, and memorable. This layout keeps the tone elegant while still showing the product in motion.
              </p>
            </div>
            <div className="cta-band__actions">
              <button type="button" className="btn btn-primary" onClick={() => setShowAuthModal(true)}>
                Start free
              </button>
              <a href="/new-interview" className="btn btn-secondary">
                Go to setup
              </a>
            </div>
          </div>
        </div>
      </section>

      <style jsx>{`
        .landing-page {
          position: relative;
          overflow: hidden;
        }

        .landing-hero {
          position: relative;
          min-height: 100svh;
          padding: 34px 0 42px;
        }

        .landing-orb {
          position: absolute;
          border-radius: 50%;
          filter: blur(6px);
          opacity: 0.75;
          pointer-events: none;
        }

        .landing-orb--one {
          width: 380px;
          height: 380px;
          top: 8%;
          right: -120px;
          background: radial-gradient(circle, rgba(213, 173, 52, 0.18), transparent 66%);
          animation: floatOrb 14s ease-in-out infinite;
        }

        .landing-orb--two {
          width: 290px;
          height: 290px;
          left: -90px;
          bottom: 8%;
          background: radial-gradient(circle, rgba(255, 255, 255, 0.8), transparent 60%);
          animation: floatOrb 17s ease-in-out infinite reverse;
        }

        .landing-noise {
          position: absolute;
          inset: 0;
          pointer-events: none;
          opacity: 0.22;
          background-image:
            linear-gradient(rgba(24, 20, 17, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(24, 20, 17, 0.03) 1px, transparent 1px);
          background-size: 84px 84px;
          mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.28), transparent 80%);
        }

        .landing-hero__grid {
          position: relative;
          z-index: 1;
          display: grid;
          grid-template-columns: 1fr;
          gap: 28px;
          align-items: center;
          min-height: calc(100svh - 120px);
          max-width: 860px;
        }

        .landing-hero__copy {
          display: grid;
          gap: 22px;
          max-width: 720px;
        }

        .landing-kicker {
          animation: fadeUp 900ms cubic-bezier(0.22, 1, 0.36, 1) both;
        }

        .landing-title {
          font-family: var(--font-display);
          font-size: clamp(3.1rem, 7vw, 6.1rem);
          font-weight: 700;
          line-height: 0.95;
          letter-spacing: -0.05em;
          max-width: 10ch;
        }

        .landing-subtitle {
          max-width: 62ch;
          font-size: 1.02rem;
          line-height: 1.8;
          color: var(--text-secondary);
        }

        .landing-actions {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
        }

        .landing-proof {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
        }

        .landing-proof__item {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 10px 14px;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.65);
          border: 1px solid var(--border-subtle);
          color: var(--text-secondary);
          animation: gentleRise 8s ease-in-out infinite;
        }

        .landing-proof__dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--accent);
          box-shadow: 0 0 0 4px rgba(213, 173, 52, 0.12);
        }

        .loop-frame {
          position: relative;
          border-radius: 34px;
          padding: 18px;
          border: 1px solid rgba(28, 23, 18, 0.08);
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(255, 252, 247, 0.7));
          box-shadow: var(--shadow-soft);
          overflow: hidden;
        }

        .loop-frame::before {
          content: "";
          position: absolute;
          inset: -30%;
          background: radial-gradient(circle, rgba(213, 173, 52, 0.1), transparent 55%);
          animation: slowRotate 18s linear infinite;
          pointer-events: none;
        }

        .loop-frame__top,
        .loop-screen__header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
        }

        .loop-frame__top {
          margin-bottom: 16px;
        }

        .loop-frame__eyebrow {
          font-family: var(--font-mono);
          font-size: 0.72rem;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: var(--text-muted);
        }

        .loop-screen {
          position: relative;
          z-index: 1;
          border-radius: 28px;
          padding: 18px;
          border: 1px solid rgba(28, 23, 18, 0.06);
          background: rgba(255, 255, 255, 0.78);
          display: grid;
          gap: 18px;
        }

        .loop-screen__badge {
          display: inline-flex;
          align-items: center;
          padding: 6px 10px;
          border-radius: 999px;
          font-size: 0.72rem;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          background: var(--accent-soft);
          color: var(--accent-strong);
        }

        .loop-screen__metric {
          font-family: var(--font-display);
          font-size: 1.3rem;
          font-weight: 700;
          letter-spacing: -0.04em;
        }

        .landing-scroll-hint {
          display: inline-flex;
          align-items: center;
          gap: 12px;
          margin-top: 22px;
          color: var(--text-muted);
          font-size: 0.78rem;
          letter-spacing: 0.12em;
          text-transform: uppercase;
        }

        .landing-scroll-hint__line {
          width: 64px;
          height: 1px;
          background: linear-gradient(90deg, transparent, rgba(28, 23, 18, 0.42), transparent);
          animation: pulseLine 2.5s ease-in-out infinite;
        }

        .landing-section {
          padding: 96px 0;
        }

        .landing-section--tight {
          padding-top: 40px;
        }

        .landing-section__intro {
          display: grid;
          gap: 12px;
          max-width: 820px;
          margin-bottom: 28px;
        }

        .landing-section__intro--center {
          margin-left: auto;
          margin-right: auto;
          text-align: center;
          justify-items: center;
        }

        .landing-section__title {
          font-family: var(--font-display);
          font-size: clamp(2rem, 3.6vw, 4rem);
          line-height: 1;
          font-weight: 700;
          letter-spacing: -0.05em;
        }

        .mode-rail {
          display: grid;
          grid-template-columns: 280px minmax(0, 1fr);
          gap: 24px;
          align-items: stretch;
        }

        .mode-rail__buttons {
          display: grid;
          gap: 12px;
          align-content: start;
        }

        .mode-toggle {
          display: grid;
          grid-template-columns: 56px minmax(0, 1fr);
          gap: 14px;
          align-items: center;
          width: 100%;
          padding: 16px;
          border-radius: 22px;
          border: 1px solid var(--border-subtle);
          background: rgba(255, 255, 255, 0.6);
          color: var(--text-secondary);
          text-align: left;
          cursor: pointer;
          transition: transform 180ms ease, border-color 180ms ease, background-color 180ms ease, box-shadow 180ms ease;
        }

        .mode-toggle:hover {
          transform: translateY(-2px);
          border-color: rgba(213, 173, 52, 0.26);
          box-shadow: 0 16px 40px rgba(49, 34, 9, 0.06);
        }

        .mode-toggle--active {
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(255, 251, 244, 0.9));
          color: var(--text-primary);
          border-color: rgba(213, 173, 52, 0.34);
          box-shadow: 0 18px 44px rgba(213, 173, 52, 0.08);
        }

        .mode-toggle__index {
          display: grid;
          place-items: center;
          width: 54px;
          height: 54px;
          border-radius: 18px;
          background: var(--accent-soft);
          color: var(--accent-strong);
          font-family: var(--font-mono);
          font-size: 0.78rem;
          letter-spacing: 0.12em;
        }

        .mode-rail__detail {
          border-radius: 30px;
          padding: clamp(22px, 3vw, 34px);
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.78), rgba(255, 252, 247, 0.62));
          border: 1px solid var(--border-subtle);
          box-shadow: var(--shadow-card);
          display: grid;
          gap: 22px;
        }

        .mode-detail {
          display: grid;
          gap: 10px;
          max-width: 68ch;
        }

        .mode-detail__eyebrow {
          font-size: 0.72rem;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: var(--text-muted);
          font-family: var(--font-mono);
        }

        .mode-detail__title {
          font-family: var(--font-display);
          font-size: clamp(1.8rem, 3vw, 3rem);
          line-height: 1.02;
          letter-spacing: -0.05em;
        }

        .mode-detail__body {
          color: var(--text-secondary);
          line-height: 1.7;
          font-size: 1rem;
        }

        .signal-strip {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 12px;
        }

        .signal-strip__item {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 14px 16px;
          border-radius: 18px;
          background: rgba(255, 255, 255, 0.72);
          border: 1px solid var(--border-subtle);
        }

        .signal-strip__item span {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: var(--accent);
        }

        .signal-strip__item strong {
          font-size: 0.9rem;
        }

        .process-flow {
          display: grid;
          gap: 20px;
        }

        .process-row {
          display: grid;
          grid-template-columns: 88px minmax(0, 1fr) 64px;
          align-items: center;
          gap: 18px;
          padding: 22px 0;
          border-top: 1px solid rgba(28, 23, 18, 0.08);
        }

        .process-row:last-child {
          border-bottom: 1px solid rgba(28, 23, 18, 0.08);
        }

        .process-row__index {
          font-family: var(--font-display);
          font-size: 3rem;
          line-height: 1;
          font-weight: 700;
          color: var(--accent-strong);
        }

        .process-row__title {
          font-family: var(--font-display);
          font-size: clamp(1.5rem, 2vw, 2.2rem);
          letter-spacing: -0.04em;
          line-height: 1.02;
        }

        .process-row__body {
          margin-top: 10px;
          color: var(--text-secondary);
          line-height: 1.7;
          max-width: 68ch;
        }

        .process-row__mark {
          display: grid;
          place-items: center;
        }

        .process-row__dot {
          width: 14px;
          height: 14px;
          border-radius: 50%;
          background: var(--accent);
          box-shadow: 0 0 0 8px rgba(213, 173, 52, 0.12);
          animation: orbPulse 3s ease-in-out infinite;
        }

        .star-list {
          display: grid;
          gap: 20px;
        }

        .star-row {
          display: grid;
          grid-template-columns: 90px minmax(0, 1fr);
          gap: 20px;
          align-items: start;
          padding: 22px 0;
          border-top: 1px solid rgba(28, 23, 18, 0.08);
        }

        .star-row:last-child {
          border-bottom: 1px solid rgba(28, 23, 18, 0.08);
        }

        .star-row__number {
          font-family: var(--font-display);
          font-size: 2.8rem;
          line-height: 1;
          font-weight: 700;
          color: var(--accent-strong);
        }

        .star-row__title {
          font-family: var(--font-display);
          font-size: clamp(1.6rem, 2.4vw, 2.4rem);
          letter-spacing: -0.05em;
          line-height: 1.02;
        }

        .star-row__body {
          margin-top: 10px;
          color: var(--text-secondary);
          line-height: 1.7;
          max-width: 64ch;
        }

        .landing-section--cta {
          padding-bottom: 120px;
        }

        .cta-band {
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          gap: 24px;
          align-items: center;
          padding: clamp(28px, 4vw, 42px);
          border-radius: 34px;
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(255, 252, 247, 0.66));
          border: 1px solid var(--border-subtle);
          box-shadow: var(--shadow-soft);
        }

        .cta-band__title {
          margin-top: 12px;
          font-family: var(--font-display);
          font-size: clamp(2rem, 3.3vw, 3.6rem);
          line-height: 1;
          letter-spacing: -0.05em;
          max-width: 14ch;
        }

        .cta-band__body {
          max-width: 64ch;
          margin-top: 12px;
          color: var(--text-secondary);
          line-height: 1.7;
        }

        .cta-band__actions {
          display: grid;
          gap: 12px;
          justify-items: end;
        }

        @keyframes floatOrb {
          0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
          50% { transform: translate3d(0, -18px, 0) scale(1.04); }
        }

        @keyframes slowRotate {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        @keyframes reelCycle {
          0%, 20% { transform: translateX(0); }
          33%, 53% { transform: translateX(-33.333%); }
          66%, 86% { transform: translateX(-66.666%); }
          100% { transform: translateX(0); }
        }

        @keyframes pulseLine {
          0%, 100% { opacity: 0.45; transform: scaleX(0.9); }
          50% { opacity: 1; transform: scaleX(1); }
        }

        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @keyframes gentleRise {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-2px); }
        }

        @keyframes orbPulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.15); }
        }

        @media (max-width: 1100px) {
          .landing-hero__grid,
          .mode-rail,
          .cta-band {
            grid-template-columns: 1fr;
          }

          .landing-hero {
            min-height: auto;
          }

          .signal-strip {
            grid-template-columns: 1fr;
          }

          .process-row,
          .star-row {
            grid-template-columns: 1fr;
          }

          .process-row__mark {
            justify-content: start;
          }

          .cta-band__actions {
            justify-items: start;
          }
        }

        @media (max-width: 760px) {
          .landing-hero {
            padding-top: 18px;
          }

          .landing-title {
            max-width: 12ch;
          }

          .landing-section {
            padding: 72px 0;
          }

          .landing-section--cta {
            padding-bottom: 90px;
          }

          .landing-actions {
            width: 100%;
          }
        }
      `}</style>
    </main>
  );
}
