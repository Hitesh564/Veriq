"use client";

import React, { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "../context/AuthContext";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, setShowAuthModal } = useAuth();
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [streak, setStreak] = useState<number>(0);
  const [credits, setCredits] = useState<{
    is_subscribed: boolean;
    plan_id: string;
    plan_name: string;
    interviews_completed: number;
    interviews_remaining: number;
    billing_status: string;
    renewal_date: string | null;
  } | null>(null);

  useEffect(() => {
    if (!user) {
      setCredits(null);
      return;
    }
    
    const fetchCredits = async () => {
      try {
        const { supabase } = await import("../utils/supabaseClient");
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) return;
        
        const res = await fetch("http://127.0.0.1:8000/api/v1/payments/subscription", {
          headers: {
            "Authorization": `Bearer ${session.access_token}`
          }
        });
        if (res.ok) {
          const data = await res.json();
          setCredits(data);
        }
      } catch (err) {
        console.error("Failed to fetch credits status:", err);
      }
    };
    
    fetchCredits();
  }, [pathname, user]);

  const handleUpgrade = async () => {
    try {
      const { supabase } = await import("../utils/supabaseClient");
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;
      
      const res = await fetch("http://127.0.0.1:8000/api/v1/payments/create-checkout-session?plan_id=pro", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });
      if (res.ok) {
        const { url } = await res.json();
        if (url) {
          window.location.href = url;
        }
      }
    } catch (err) {
      console.error("Failed to redirect to checkout:", err);
    }
  };

  // Auto-close mobile sidebar when pathname changes
  useEffect(() => {
    setIsMobileSidebarOpen(false);
  }, [pathname]);

  // Route guard: Redirect guest users attempting to access protected routes
  useEffect(() => {
    const isProtected = ["/history", "/learning", "/profile", "/settings"].includes(pathname) || pathname.includes("/transcript/");
    if (isProtected && !user) {
      router.push("/");
    }
  }, [pathname, user, router]);

  // Fetch streak info from API for the topbar indicator
  useEffect(() => {
    // If not logged in, don't fetch from backend profile card to avoid 401s
    if (!user) {
      setStreak(0);
      return;
    }
    
    // Get session token from Supabase
    import("../utils/supabaseClient").then(({ supabase }) => {
      supabase.auth.getSession().then(({ data: { session } }) => {
        if (!session) return;
        fetch("http://127.0.0.1:8000/api/v1/interviews/profile/card", {
          headers: {
            "Authorization": `Bearer ${session.access_token}`
          }
        })
          .then((res) => res.json())
          .then((data) => {
            if (data && data.history_trends) {
              setStreak(data.history_trends.streak || 0);
            }
          })
          .catch(() => {});
      });
    });
  }, [pathname, user]);

  const isInterviewSession = pathname.includes("/interview/");

  // Simple Page 3 (Interview Session) view - no headers/sidebars, full-screen focus
  if (isInterviewSession) {
    return (
      <div style={{ minHeight: "100vh", backgroundColor: "#FCFCFD" }}>
        {children}
      </div>
    );
  }

  const allNavItems = [
    {
      label: "Home",
      path: "/",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
          <polyline points="9 22 9 12 15 12 15 22" />
        </svg>
      )
    },
    {
      label: "New Interview",
      path: "/new-interview",
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="16" />
          <line x1="8" y1="12" x2="16" y2="12" />
        </svg>
      )
    },
    {
      label: "Interview History",
      path: "/history",
      protected: true,
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
      )
    },
    {
      label: "Learning Dashboard",
      path: "/learning",
      protected: true,
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
          <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
        </svg>
      )
    },
    {
      label: "Profile",
      path: "/profile",
      protected: true,
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
      )
    },
    {
      label: "Billing",
      path: "/billing",
      protected: true,
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="2" y="4" width="20" height="16" rx="2" ry="2" />
          <line x1="2" y1="10" x2="22" y2="10" />
        </svg>
      )
    },
    {
      label: "Settings",
      path: "/settings",
      protected: true,
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
      )
    }
  ];

  const navItems = allNavItems.filter((item: any) => !item.protected || user);

  const getPageTitle = () => {
    const item = navItems.find((n) => n.path === pathname);
    if (item) return item.label;
    if (pathname.includes("/transcript/")) return "Interview Report";
    return "AI Interview Platform";
  };

  const renderSidebarContent = () => (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", padding: "24px 16px" }}>
      {/* Brand Logo */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "32px", padding: "0 8px" }}>
        <div style={{
          backgroundColor: "#3B82F6",
          width: "28px",
          height: "28px",
          borderRadius: "8px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#FFFFFF",
          fontWeight: 800,
          fontSize: "1.1rem"
        }}>
          V
        </div>
        <span style={{
          fontFamily: "var(--font-outfit)",
          fontWeight: 800,
          fontSize: "1.25rem",
          letterSpacing: "-0.5px",
          color: "var(--text-primary)"
        }}>
          Veriq<span style={{ color: "#3B82F6", fontWeight: 400, fontSize: "0.85rem", marginLeft: "2px" }}>AI</span>
        </span>
      </div>

      {/* Navigation List */}
      <nav style={{ display: "flex", flexDirection: "column", gap: "6px", flex: 1 }}>
        {navItems.map((item) => {
          const isActive = pathname === item.path;
          return (
            <button
              key={item.path}
              onClick={() => router.push(item.path)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: "10px 14px",
                borderRadius: "8px",
                border: "none",
                backgroundColor: isActive ? "#EFF6FF" : "transparent",
                color: isActive ? "#1D4ED8" : "var(--text-secondary)",
                fontFamily: "var(--font-jakarta)",
                fontWeight: isActive ? 600 : 500,
                fontSize: "0.95rem",
                textAlign: "left",
                cursor: "pointer",
                transition: "all 0.15s ease",
                width: "100%"
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = "#F2F4F7";
                  e.currentTarget.style.color = "var(--text-primary)";
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.backgroundColor = "transparent";
                  e.currentTarget.style.color = "var(--text-secondary)";
                }
              }}
            >
              {item.icon}
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* Credits Card (Upgrade CTA) */}
      {user && credits && (
        <div style={{
          backgroundColor: credits.is_subscribed ? "#F0FDF4" : "#F8FAFC",
          border: credits.is_subscribed ? "1px solid #BBF7D0" : "1px solid #E2E8F0",
          borderRadius: "12px",
          padding: "16px",
          marginBottom: "16px",
          display: "flex",
          flexDirection: "column",
          gap: "8px"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: 700, color: credits.is_subscribed ? "#166534" : "#475569", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              {credits.is_subscribed ? "Pro Account" : "Free Plan"}
            </span>
            {!credits.is_subscribed && (
              <span style={{ fontSize: "0.75rem", color: "#475569" }}>
                {credits.interviews_remaining} left
              </span>
            )}
          </div>
          {!credits.is_subscribed ? (
            <>
              <div style={{ width: "100%", height: "6px", backgroundColor: "#E2E8F0", borderRadius: "3px", overflow: "hidden" }}>
                <div style={{
                  width: `${(credits.interviews_completed / 3) * 100}%`,
                  height: "100%",
                  backgroundColor: "#2563EB",
                  borderRadius: "3px"
                }} />
              </div>
              <button
                onClick={handleUpgrade}
                style={{
                  width: "100%",
                  padding: "6px 12px",
                  borderRadius: "6px",
                  border: "none",
                  backgroundColor: "#2563EB",
                  color: "#FFFFFF",
                  fontWeight: 600,
                  fontSize: "0.8rem",
                  cursor: "pointer",
                  textAlign: "center",
                  marginTop: "4px"
                }}
              >
                Upgrade to Pro
              </button>
            </>
          ) : (
            <div style={{ fontSize: "0.8rem", color: "#166534", fontWeight: 500, display: "flex", alignItems: "center", gap: "6px" }}>
              ✅ Unlimited mock sessions
            </div>
          )}
        </div>
      )}

      {/* Sidebar Footer */}
      <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "16px", paddingLeft: "8px" }}>
        {user ? (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "10px", width: "100%" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", flex: 1, minWidth: 0 }}>
              <div style={{
                width: "32px",
                height: "32px",
                borderRadius: "50%",
                backgroundColor: "#2563EB",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 600,
                color: "#FFFFFF",
                fontSize: "0.85rem",
                flexShrink: 0
              }}>
                {user.email?.slice(0, 2).toUpperCase() || "US"}
              </div>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {user.user_metadata?.full_name || user.email?.split("@")[0] || "User"}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  Candidate
                </div>
              </div>
            </div>
            <button
              onClick={() => logout().then(() => router.push("/"))}
              title="Logout"
              style={{
                border: "none",
                backgroundColor: "transparent",
                color: "#94A3B8",
                cursor: "pointer",
                padding: "6px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "6px",
                flexShrink: 0
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "#EF4444";
                e.currentTarget.style.backgroundColor = "#FEF2F2";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = "#94A3B8";
                e.currentTarget.style.backgroundColor = "transparent";
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px", width: "100%" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div style={{
                width: "32px",
                height: "32px",
                borderRadius: "50%",
                backgroundColor: "#E2E8F0",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 600,
                color: "#64748B",
                fontSize: "0.85rem"
              }}>
                G
              </div>
              <div>
                <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)" }}>Guest Mode</div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Sign in to save progress</div>
              </div>
            </div>
            <button
              onClick={() => setShowAuthModal(true)}
              style={{
                width: "100%",
                padding: "8px",
                borderRadius: "6px",
                border: "1px solid #2563EB",
                backgroundColor: "#2563EB",
                color: "#FFFFFF",
                fontWeight: 600,
                fontSize: "0.85rem",
                cursor: "pointer",
                textAlign: "center"
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = "#1D4ED8"}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = "#2563EB"}
            >
              Sign In
            </button>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div style={{ display: "flex", minHeight: "100vh", backgroundColor: "var(--bg-main)" }}>
      {/* Desktop Sidebar Sidebar */}
      <aside style={{
        width: "256px",
        backgroundColor: "var(--bg-sidebar)",
        borderRight: "1px solid var(--border-main)",
        position: "sticky",
        top: 0,
        height: "100vh",
        display: "none",
        flexDirection: "column"
      }} className="desktop-sidebar">
        {renderSidebarContent()}
      </aside>

      {/* Mobile Drawer Overlay */}
      {isMobileSidebarOpen && (
        <div
          onClick={() => setIsMobileSidebarOpen(false)}
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(15, 23, 42, 0.4)",
            zIndex: 998,
            backdropFilter: "blur(4px)"
          }}
        />
      )}

      {/* Mobile Drawer */}
      <aside style={{
        position: "fixed",
        top: 0,
        bottom: 0,
        left: isMobileSidebarOpen ? 0 : "-260px",
        width: "256px",
        backgroundColor: "var(--bg-sidebar)",
        zIndex: 999,
        transition: "left 0.2s ease-in-out",
        boxShadow: isMobileSidebarOpen ? "0 4px 20px rgba(0, 0, 0, 0.08)" : "none",
        display: "flex",
        flexDirection: "column"
      }}>
        {renderSidebarContent()}
      </aside>

      {/* Main Content Area */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* Top Header Bar */}
        <header style={{
          height: "64px",
          backgroundColor: "#FFFFFF",
          borderBottom: "1px solid var(--border-main)",
          padding: "0 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          position: "sticky",
          top: 0,
          zIndex: 100
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            {/* Hamburger Button for mobile */}
            <button
              onClick={() => setIsMobileSidebarOpen(true)}
              style={{
                background: "none",
                border: "none",
                cursor: "pointer",
                padding: "4px",
                display: "inline-flex",
                color: "var(--text-secondary)"
              }}
              className="mobile-hamburger"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            <h2 style={{ fontSize: "1.1rem", fontWeight: 600, color: "var(--text-primary)" }}>
              {getPageTitle()}
            </h2>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            {/* Streak Indicator */}
            {streak > 0 && (
              <div style={{
                display: "flex",
                alignItems: "center",
                gap: "4px",
                backgroundColor: "#FFF7ED",
                color: "#C2410C",
                padding: "4px 8px",
                borderRadius: "6px",
                fontSize: "0.8rem",
                fontWeight: 600
              }}>
                🔥 {streak} Day Streak
              </div>
            )}
            
            {/* User Indicator */}
            {user ? (
              <div
                onClick={() => router.push("/profile")}
                style={{
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "6px 12px",
                  borderRadius: "20px",
                  backgroundColor: "var(--bg-main)",
                  border: "1px solid var(--border-main)",
                  fontSize: "0.85rem",
                  fontWeight: 500,
                  color: "var(--text-secondary)"
                }}
              >
                <span className="desktop-only">{user.user_metadata?.full_name || user.email?.split("@")[0] || "User"}</span>
                <div style={{
                  width: "20px",
                  height: "20px",
                  borderRadius: "50%",
                  backgroundColor: "#3B82F6",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#FFFFFF",
                  fontSize: "0.7rem",
                  fontWeight: 700
                }}>
                  {user.email?.slice(0, 1).toUpperCase() || "U"}
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowAuthModal(true)}
                style={{
                  cursor: "pointer",
                  padding: "6px 16px",
                  borderRadius: "20px",
                  backgroundColor: "#2563EB",
                  color: "#FFFFFF",
                  border: "none",
                  fontSize: "0.85rem",
                  fontWeight: 600
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = "#1D4ED8"}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = "#2563EB"}
              >
                Sign In
              </button>
            )}
          </div>
        </header>

        {/* Dynamic Page Content wrapper */}
        <main style={{ flex: 1, padding: "32px", overflowY: "auto" }}>
          {children}
        </main>
      </div>

      <style jsx global>{`
        @media (min-width: 769px) {
          .desktop-sidebar {
            display: flex !important;
          }
          .mobile-hamburger {
            display: none !important;
          }
          .desktop-only {
            display: inline !important;
          }
        }
        @media (max-width: 768px) {
          .desktop-only {
            display: none !important;
          }
        }
      `}</style>
    </div>
  );
}
