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
                IntervAI
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
              className="btn btn-secondary"
              style={{ minWidth: "42px", width: "42px", padding: 0 }}
              aria-label="Open account"
            >
              <span className="material-symbols-outlined" style={{ fontSize: 22 }}>account_circle</span>
            </button>
          </div>
        </div>
      </header>

      <main style={{ flex: 1 }}>{children}</main>

      <footer className="footer-shell">
        <div className="page-shell">
          <div className="footer-divider" />
          <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: "24px", alignItems: "start" }}>
            <div style={{ maxWidth: "540px" }}>
              <div style={{ fontFamily: "var(--font-display)", fontSize: "1.5rem", fontWeight: 700, letterSpacing: "-0.05em" }}>
                IntervAI
              </div>
              <p className="section-copy" style={{ marginTop: "12px" }}>
                A premium interview coach for live practice, evaluation, and structured improvement.
              </p>
            </div>
            <div style={{ display: "grid", gap: "10px", justifyItems: "end" }}>
              <Link href="/pricing" className="btn btn-secondary">
                Pricing
              </Link>
              <Link href="/product" className="btn btn-secondary">
                Features
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
