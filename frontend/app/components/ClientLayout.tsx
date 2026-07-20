"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useAuth } from "../context/AuthContext";
import PublicShell from "./PublicShell";
import { safeJsonFetch } from "../utils/api";

type NavItem = {
  label: string;
  path: string;
  protected?: boolean;
};

type SubscriptionState = {
  is_subscribed: boolean;
  plan_name: string;
  interviews_remaining: number;
};

const navItems: NavItem[] = [
  { label: "Home", path: "/" },
  { label: "Interviews", path: "/new-interview" },
  { label: "History", path: "/history", protected: true },
  { label: "Learning", path: "/learning", protected: true },
  { label: "Profile", path: "/profile", protected: true },
  { label: "Billing", path: "/billing", protected: true }
];

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, setShowAuthModal, logout } = useAuth();
  const [credits, setCredits] = useState<SubscriptionState | null>(null);
  const [accountOpen, setAccountOpen] = useState(false);

  const isPublicView = !user;
  const isInterviewSession = pathname.includes("/interview/");

  const activePath = useMemo(() => {
    if (pathname.includes("/transcript/")) return "/history";
    if (pathname.startsWith("/interview/")) return "/new-interview";
    if (pathname === "/payment-success") return "/billing";
    return pathname;
  }, [pathname]);

  const visibleNavItems = useMemo(
    () => navItems.filter((item) => !item.protected || Boolean(user)),
    [user]
  );

  useEffect(() => {
    if (pathname === "/") return;
    const protectedRoute =
      ["/history", "/learning", "/profile", "/settings", "/billing"].includes(pathname) ||
      pathname.includes("/transcript/");
    if (protectedRoute && !user) {
      router.push("/");
    }
  }, [pathname, router, user]);

  useEffect(() => {
    if (!user) return;

    let cancelled = false;

    const loadWorkspaceState = async () => {
      const { supabase } = await import("../utils/supabaseClient");
      const { data: { session } } = await supabase.auth.getSession();
      if (!session || cancelled) return;

      const subscription = await safeJsonFetch<SubscriptionState>("/api/v1/payments/subscription", {
        headers: { Authorization: `Bearer ${session.access_token}` }
      });

      if (!cancelled && subscription) {
        setCredits(subscription);
      }
    };

    loadWorkspaceState();

    return () => {
      cancelled = true;
    };
  }, [user]);

  if (isInterviewSession) {
    return <div style={{ minHeight: "100vh" }}>{children}</div>;
  }

  if (isPublicView) {
    return <PublicShell>{children}</PublicShell>;
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <header className="topbar">
        <div className="topbar__inner" style={{ justifyContent: "space-between" }}>
          <button
            type="button"
            onClick={() => router.push("/")}
            className="topbar__brand"
            style={{ background: "transparent", cursor: "pointer" }}
          >
            <div className="brand-mark">I</div>
            <div style={{ textAlign: "left" }}>
              <div style={{ fontFamily: "var(--font-display)", fontSize: "1.2rem", fontWeight: 700, letterSpacing: "-0.05em" }}>
                Veriq
              </div>
              <div className="fine-print">AI co-pilot active</div>
            </div>
          </button>

          <nav className="topbar__nav" style={{ flex: 1, justifyContent: "center" }}>
            {visibleNavItems.map((item) => {
              const active = activePath === item.path || (item.path === "/history" && pathname.includes("/transcript/"));
              return (
                <Link
                  key={item.path}
                  href={item.path}
                  className={`topbar__link ${active ? "topbar__link--active" : ""}`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div className="subtle-chip" style={{ display: "none" }}>
              {credits?.is_subscribed ? "Pro" : "Free"}
            </div>
            <button
              type="button"
              onClick={() => setAccountOpen((prev) => !prev)}
              className="btn btn-secondary icon-avatar-button"
              aria-label="Account menu"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="none">
                <circle cx="12" cy="8" r="3.25" stroke="currentColor" strokeWidth="1.7" />
                <path d="M5.5 19c1.7-3 4-4.5 6.5-4.5S16.8 16 18.5 19" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
              </svg>
            </button>
            <button
              type="button"
              onClick={async () => {
                await logout();
                router.push("/");
              }}
              className="btn btn-secondary"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {accountOpen && (
        <div className="page-shell" style={{ marginTop: "12px" }}>
          <div className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "16px" }}>
            <div>
              <div className="ambient-label">Account</div>
              <div style={{ fontFamily: "var(--font-display)", fontSize: "1.35rem", fontWeight: 700, marginTop: "8px" }}>
                {user?.email || "Signed in"}
              </div>
              <p className="section-copy" style={{ marginTop: "6px" }}>
                {credits?.is_subscribed
                  ? `${credits.plan_name} plan`
                  : "Free plan"}
              </p>
            </div>
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", justifyContent: "flex-end" }}>
              <button type="button" className="btn btn-secondary" onClick={() => router.push("/profile")}>
                Profile
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => router.push("/settings")}>
                Settings
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={async () => {
                  await logout();
                  router.push("/");
                }}
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      )}

      <main style={{ flex: 1 }}>{children}</main>
    </div>
  );
}
