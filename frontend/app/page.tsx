"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

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
    body: "Practice spoken answers, follow-ups, pacing, and pressure in a voice-first interview room designed for natural conversation.",
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
    body: "Choose a role, difficulty, company style, and optional resume or job description to create a focused practice session."
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
    eyebrow: "01 / Context aware",
    title: "Adaptive intelligence",
    body: "The interview flow reacts to the candidate’s role, resume, and target company instead of relying on one fixed question script."
  },
  {
    eyebrow: "02 / Voice first",
    title: "Live speaking room",
    body: "Candidates answer naturally in a voice-driven room that feels closer to a real interview than a static form."
  },
  {
    eyebrow: "03 / Growth loop",
    title: "Actionable feedback",
    body: "Each session ends with transcript insights, strength areas, and a next-step roadmap for the following practice round."
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
                AI interview practice, made personal
              </div>

              <h1 className="landing-title">
                Practice the interview before it matters.
              </h1>

              <p className="landing-subtitle">
                Veriq gives you a live, role-aware interview room with voice practice, useful feedback, and a clear next step after every session.
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

            {/* Right Column Hero Interactive Showcase */}
            <div className="landing-hero__visual">
              <div className="workspace-card">
                <div className="workspace-card__header">
                  <div>
                    <span className="workspace-card__eyebrow">Veriq workspace</span>
                    <h2>Build interview readiness.</h2>
                  </div>
                  <span className="workspace-card__status"><i /> Ready</span>
                </div>

                <div className="workspace-card__start">
                  <span className="workspace-card__label">Start with a focused practice room</span>
                  <p>Choose a role, difficulty, and interview style. Add your resume or job description when you want more targeted questions.</p>
                  <Link href="/new-interview" className="workspace-card__primary-action">
                    Configure an interview <span aria-hidden="true">→</span>
                  </Link>
                </div>

                <div className="workspace-card__tools">
                  <Link href="/history" className="workspace-card__tool">
                    <span className="workspace-card__tool-icon">↗</span>
                    <div className="workspace-card__tool-copy"><div className="workspace-card__tool-title">Review history</div><div className="workspace-card__tool-subtitle">See transcripts and evaluations</div></div>
                  </Link>
                  <Link href="/learning" className="workspace-card__tool">
                    <span className="workspace-card__tool-icon">✦</span>
                    <div className="workspace-card__tool-copy"><div className="workspace-card__tool-title">Continue learning</div><div className="workspace-card__tool-subtitle">Turn weak spots into a plan</div></div>
                  </Link>
                  <Link href="/how-it-works" className="workspace-card__tool">
                    <span className="workspace-card__tool-icon">i</span>
                    <div className="workspace-card__tool-copy"><div className="workspace-card__tool-title">See how it works</div><div className="workspace-card__tool-subtitle">Understand the Veriq loop</div></div>
                  </Link>
                  <Link href="/product" className="workspace-card__tool">
                    <span className="workspace-card__tool-icon">⌁</span>
                    <div className="workspace-card__tool-copy"><div className="workspace-card__tool-title">Explore the product</div><div className="workspace-card__tool-subtitle">Adaptive, voice-first practice</div></div>
                  </Link>
                </div>

                <div className="workspace-card__footer">
                  <span>Role-aware · Voice-first · Feedback-led</span>
                  <Link href="/new-interview">Open setup <span aria-hidden="true">→</span></Link>
                </div>
              </div>
            </div>
          </div>


          <div className="landing-scroll-hint">
            <span className="landing-scroll-hint__line" />
            Explore how Veriq helps you prepare
          </div>
        </div>
      </section>

      <section className="landing-section">
        <div className="page-shell">
          <div className="landing-section__intro">
            <div className="section-kicker">Why Veriq works</div>
            <h2 className="landing-section__title">
              Everything you need to turn interview practice into measurable progress.
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
            <div className="section-kicker">Your practice loop</div>
            <h2 className="landing-section__title">
              Prepare with intention, practice out loud, and know what to improve next.
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
            <div className="section-kicker">What you gain</div>
            <h2 className="landing-section__title">
              A clearer, more confident way to show up for the real interview.
            </h2>
          </div>

          <div className="star-list">
            {starPoints.map((item, index) => (
              <div key={item.title} className="star-card">
                <div className="star-card__top">
                  <div className="star-card__index">0{index + 1}</div>
                  <div className="star-card__eyebrow">{item.eyebrow}</div>
                </div>
                <h3 className="star-card__title">{item.title}</h3>
                <p className="star-card__body">{item.body}</p>
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
                Start with one focused session and leave with feedback you can use in your next round. Veriq keeps your preparation practical, personal, and moving forward.
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
          grid-template-columns: minmax(0, 1fr) minmax(340px, 460px);
          gap: 48px;
          align-items: center;
          min-height: calc(100svh - 120px);
          width: 100%;
        }

        .landing-hero__visual {
          display: flex;
          justify-content: center;
          align-items: center;
          width: 100%;
        }

        .workspace-card {
          width: 100%;
          padding: 26px;
          border: 1px solid rgba(28, 23, 18, 0.1);
          border-radius: 30px;
          background: rgba(255, 253, 249, 0.88);
          box-shadow: 0 28px 70px rgba(28, 23, 18, 0.13);
          backdrop-filter: blur(18px);
        }

        .workspace-card__header,
        .workspace-card__footer {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
        }

        .workspace-card__eyebrow,
        .workspace-card__label {
          color: var(--accent-strong);
          font-family: var(--font-mono);
          font-size: 0.7rem;
          font-weight: 800;
          letter-spacing: 0.13em;
          text-transform: uppercase;
        }

        .workspace-card h2 {
          margin-top: 8px;
          font-family: var(--font-display);
          font-size: clamp(1.7rem, 3vw, 2.35rem);
          letter-spacing: -0.05em;
          line-height: 1;
        }

        .workspace-card__status {
          display: inline-flex;
          align-items: center;
          gap: 7px;
          padding: 7px 10px;
          border: 1px solid rgba(29, 127, 84, 0.2);
          border-radius: 999px;
          color: var(--success);
          background: rgba(29, 127, 84, 0.08);
          font-size: 0.74rem;
          font-weight: 700;
        }

        .workspace-card__status i {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: var(--success);
        }

        .workspace-card__start {
          margin-top: 22px;
          padding: 20px;
          border-radius: 20px;
          background: linear-gradient(135deg, rgba(213, 173, 52, 0.14), rgba(255, 255, 255, 0.74));
          border: 1px solid rgba(213, 173, 52, 0.2);
        }

        .workspace-card__start p {
          margin-top: 8px;
          color: var(--text-secondary);
          font-size: 0.86rem;
          line-height: 1.6;
        }

        .workspace-card__primary-action {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          margin-top: 16px;
          color: var(--text-primary);
          font-size: 0.86rem;
          font-weight: 800;
        }

        .workspace-card__primary-action:hover,
        .workspace-card__footer a:hover {
          color: var(--accent-strong);
        }

        .workspace-card__tools {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 10px;
          margin-top: 14px;
        }

        .workspace-card__tool {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          min-height: 76px;
          padding: 14px;
          border: 1px solid rgba(28, 23, 18, 0.08);
          border-radius: 17px;
          background: rgba(255, 255, 255, 0.64);
          transition: transform 160ms ease, border-color 160ms ease, background-color 160ms ease;
        }

        .workspace-card__tool:hover {
          transform: translateY(-2px);
          border-color: rgba(213, 173, 52, 0.38);
          background: rgba(255, 255, 255, 0.92);
        }

        .workspace-card__tool-icon {
          display: grid;
          flex: 0 0 24px;
          width: 24px;
          height: 24px;
          place-items: center;
          border-radius: 8px;
          color: var(--accent-strong);
          background: var(--accent-soft);
          font-size: 0.8rem;
          font-weight: 800;
        }

        .workspace-card__tool-copy {
          display: block;
          min-width: 0;
        }

        .workspace-card__tool-title {
          color: var(--text-primary);
          font-size: 0.82rem;
          font-weight: 800;
          line-height: 1.25;
        }

        .workspace-card__tool-subtitle {
          margin-top: 4px;
          color: var(--text-muted);
          font-size: 0.7rem;
          line-height: 1.35;
        }

        .workspace-card__footer {
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid rgba(28, 23, 18, 0.08);
          color: var(--text-muted);
          font-family: var(--font-mono);
          font-size: 0.66rem;
          letter-spacing: 0.05em;
          text-transform: uppercase;
        }

        .workspace-card__footer a {
          color: var(--text-primary);
          font-family: var(--font-sans);
          font-size: 0.78rem;
          font-weight: 800;
          letter-spacing: 0;
          text-transform: none;
          white-space: nowrap;
        }

        .signal-card {
          width: 100%;
          padding: 22px;
          border: 1px solid rgba(119, 143, 174, 0.28);
          border-radius: 30px;
          background: linear-gradient(160deg, rgba(234, 242, 250, 0.96), rgba(190, 202, 220, 0.94));
          box-shadow: 0 28px 70px rgba(43, 63, 94, 0.18);
          color: #16223a;
          animation: floatOrb 10s ease-in-out infinite;
        }

        .signal-card__header {
          display: grid;
          grid-template-columns: auto minmax(0, 1fr) auto;
          align-items: start;
          gap: 12px;
          padding: 0 4px 22px;
        }

        .signal-card__window-dots {
          display: flex;
          gap: 8px;
          padding-top: 5px;
        }

        .signal-card__window-dots span {
          width: 11px;
          height: 11px;
          border-radius: 50%;
          background: #f25757;
        }

        .signal-card__window-dots span:nth-child(2) { background: #f5b52f; }
        .signal-card__window-dots span:nth-child(3) { background: #36b95b; }

        .signal-card__header strong,
        .signal-card__header span,
        .signal-card__session {
          display: block;
        }

        .signal-card__header strong {
          font-size: 1rem;
          letter-spacing: -0.02em;
        }

        .signal-card__header > div:nth-child(2) span,
        .signal-card__session span {
          margin-top: 3px;
          color: #617795;
          font-size: 0.72rem;
        }

        .signal-card__session {
          text-align: right;
        }

        .signal-card__session strong {
          font-size: 1.05rem;
        }

        .signal-card__recommendation,
        .signal-card__metric,
        .signal-card__footer {
          border: 1px solid rgba(255, 255, 255, 0.75);
          background: rgba(248, 251, 254, 0.84);
        }

        .signal-card__recommendation {
          position: relative;
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          gap: 8px 16px;
          padding: 22px;
          border-radius: 20px;
        }

        .signal-card__label {
          display: block;
          color: #6b819f;
          font-size: 0.68rem;
          letter-spacing: 0.18em;
          text-transform: uppercase;
        }

        .signal-card__recommendation-title {
          display: block;
          margin-top: 5px;
          font-size: 1.65rem;
          letter-spacing: -0.04em;
        }

        .signal-card__muted {
          display: block;
          margin-top: 4px;
          color: #6b819f;
          font-size: 0.78rem;
        }

        .signal-card__confidence {
          text-align: right;
        }

        .signal-card__confidence strong {
          display: block;
          margin-top: 3px;
          color: #00a876;
          font-size: 1.8rem;
          letter-spacing: -0.04em;
        }

        .signal-card__progress {
          grid-column: 1 / -1;
          height: 9px;
          margin-top: 7px;
          overflow: hidden;
          border-radius: 999px;
          background: #d5dfeb;
        }

        .signal-card__progress span {
          display: block;
          width: 92%;
          height: 100%;
          border-radius: inherit;
          background: #00bd82;
        }

        .signal-card__grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 12px;
          margin-top: 14px;
        }

        .signal-card__metric {
          min-height: 94px;
          padding: 17px 16px;
          border-radius: 18px;
        }

        .signal-card__metric strong {
          display: block;
          margin-top: 5px;
          font-size: 1rem;
          letter-spacing: -0.02em;
        }

        .signal-card__footer {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          margin-top: 14px;
          padding: 16px 18px;
          border-radius: 18px;
          color: #536987;
          font-size: 0.82rem;
        }

        .signal-card__footer strong {
          color: #16223a;
          white-space: nowrap;
        }

        .hero-card {
          width: 100%;
          border-radius: 32px;
          padding: 24px;
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.86), rgba(248, 243, 233, 0.72));
          border: 1px solid var(--border-subtle);
          box-shadow: 0 24px 60px rgba(28, 23, 18, 0.08), inset 0 0 20px rgba(255, 255, 255, 0.4);
          backdrop-filter: blur(16px);
          display: flex;
          flex-direction: column;
          gap: 18px;
          animation: floatOrb 10s ease-in-out infinite;
        }

        .hero-card__header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }

        .hero-card__badge {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 6px 12px;
          border-radius: 999px;
          background: rgba(6, 182, 212, 0.1);
          border: 1px solid rgba(6, 182, 212, 0.25);
          color: #0891b2;
          font-size: 0.75rem;
          font-weight: 700;
          font-family: var(--font-mono);
          text-transform: uppercase;
        }

        .hero-card__live-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #06b6d4;
          box-shadow: 0 0 10px #06b6d4;
          animation: orbPulse 1.5s ease-in-out infinite;
        }

        .hero-card__role {
          font-size: 0.78rem;
          font-family: var(--font-mono);
          color: var(--text-muted);
          font-weight: 600;
        }

        .hero-card__stage {
          width: 100%;
          height: 270px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: radial-gradient(circle at 50% 50%, rgba(6, 182, 212, 0.08), transparent 70%);
          border-radius: 24px;
          overflow: hidden;
        }

        .hero-card__ticker {
          padding: 16px;
          border-radius: 18px;
          background: rgba(255, 255, 255, 0.8);
          border: 1px solid var(--border-subtle);
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .hero-card__speaker {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.72rem;
          font-weight: 800;
          text-transform: uppercase;
          font-family: var(--font-mono);
          color: var(--accent-strong);
        }

        .hero-card__speaker-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: var(--accent-strong);
        }

        .hero-card__question {
          font-size: 0.88rem;
          line-height: 1.45;
          color: var(--text-primary);
          font-style: italic;
        }

        .hero-card__metrics {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 10px;
          padding-top: 6px;
          border-top: 1px solid rgba(28, 23, 18, 0.06);
        }

        .hero-card__metric-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
        }

        .hero-card__metric-val {
          font-family: var(--font-mono);
          font-weight: 800;
          font-size: 0.88rem;
          color: var(--text-primary);
        }

        .hero-card__metric-lbl {
          font-size: 0.68rem;
          color: var(--text-muted);
          text-transform: uppercase;
          font-weight: 600;
          margin-top: 2px;
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
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 18px;
        }

        .star-card {
          padding: 24px;
          border-radius: 28px;
          background: rgba(255, 255, 255, 0.72);
          border: 1px solid rgba(28, 23, 18, 0.08);
          box-shadow: var(--shadow-card);
          display: grid;
          gap: 14px;
        }

        .star-card__top {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }

        .star-card__index {
          font-family: var(--font-display);
          font-size: 2rem;
          line-height: 1;
          font-weight: 700;
          color: var(--accent-strong);
        }

        .star-card__eyebrow {
          font-family: var(--font-mono);
          font-size: 0.7rem;
          letter-spacing: 0.16em;
          text-transform: uppercase;
          color: var(--text-muted);
        }

        .star-card__title {
          font-family: var(--font-display);
          font-size: clamp(1.5rem, 2.1vw, 2.1rem);
          letter-spacing: -0.05em;
          line-height: 1.02;
        }

        .star-card__body {
          color: var(--text-secondary);
          line-height: 1.7;
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
          .star-list {
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

          .workspace-card {
            padding: 20px;
          }

          .workspace-card__header,
          .workspace-card__footer {
            align-items: flex-start;
            flex-direction: column;
          }

          .workspace-card__tools {
            grid-template-columns: 1fr;
          }

          .star-list {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </main>
  );
}
