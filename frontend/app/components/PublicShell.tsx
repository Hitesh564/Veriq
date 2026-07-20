"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "../context/AuthContext";

export default function PublicShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { setShowAuthModal } = useAuth();

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <header className="topbar">
        <div className="topbar__inner">
          <button
            type="button"
            onClick={() => router.push("/")}
            className="topbar__brand"
            style={{ background: "transparent", cursor: "pointer" }}
          >
            <div className="brand-mark">I</div>
            <div style={{ textAlign: "left" }}>
              <div style={{ fontFamily: "var(--font-display)", fontSize: "1.25rem", fontWeight: 700, letterSpacing: "-0.05em" }}>
                Veriq
              </div>
              <div className="fine-print">The future of interviewing</div>
            </div>
          </button>

          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <button type="button" onClick={() => setShowAuthModal(true)} className="btn btn-primary">
              Start free
            </button>
            <button
              type="button"
              onClick={() => setShowAuthModal(true)}
              className="btn btn-secondary icon-avatar-button"
              aria-label="Open account"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="none">
                <circle cx="12" cy="8" r="3.25" stroke="currentColor" strokeWidth="1.7" />
                <path d="M5.5 19c1.7-3 4-4.5 6.5-4.5S16.8 16 18.5 19" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      <main style={{ flex: 1 }}>{children}</main>

      <footer className="footer-shell">
        <div className="page-shell">
          <div className="footer-divider" />
          <div className="footer-grid">
            <div className="footer-brand-block">
              <div style={{ fontFamily: "var(--font-display)", fontSize: "1.5rem", fontWeight: 700, letterSpacing: "-0.05em" }}>
                Veriq
              </div>
              <p className="section-copy footer-brand-copy">
                The cognitive co-pilot for high-stakes interviews. Practice with precision, speak with confidence, and turn every session into progress.
              </p>
              <div className="footer-socials" aria-label="Veriq shortcuts">
                <Link href="/" className="footer-social" aria-label="Home">
                  <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="none">
                    <path d="M4 11.5 12 5l8 6.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
                    <path d="M7 10.8V19h10v-8.2" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </Link>
                <Link href="/how-it-works" className="footer-social" aria-label="How it works">
                  <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="none">
                    <path d="M8 16 16 8" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
                    <path d="M10.5 8H16v5.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </Link>
              </div>
            </div>

            <div className="footer-column">
              <div className="footer-title">Product</div>
              <Link href="/new-interview" className="footer-link">Live interview</Link>
              <Link href="/learning" className="footer-link">Learning</Link>
              <Link href="/history" className="footer-link">History</Link>
              <Link href="/profile" className="footer-link">Profile</Link>
            </div>

            <div className="footer-column">
              <div className="footer-title">What it does</div>
              <div className="footer-note">Adaptive sessions</div>
              <div className="footer-note">Voice-based practice</div>
              <div className="footer-note">Transcript insights</div>
              <div className="footer-note">Personal growth loop</div>
            </div>

            <div className="footer-column footer-column--actions">
              <div className="footer-title">Ready to start</div>
              <p className="section-copy footer-brand-copy">
                Launch a new session, review your progress, and keep improving with a cleaner feedback loop.
              </p>
              <div className="footer-actions">
                <button type="button" onClick={() => setShowAuthModal(true)} className="btn btn-primary">
                  Start free
                </button>
                <Link href="/pricing" className="btn btn-secondary">
                  Pricing
                </Link>
              </div>
            </div>
          </div>
          <div className="footer-bottom">
            <div className="fine-print">Copyright 2026 Veriq. Designed for thoughtful practice.</div>
            <div className="footer-bottom__links">
              <Link href="/product">Product</Link>
              <Link href="/how-it-works">How it works</Link>
              <Link href="/pricing">Pricing</Link>
              <Link href="/learning">Learning</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
