"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { supabase } from "../utils/supabaseClient";

export default function PricingPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [credits, setCredits] = useState<any>(null);

  useEffect(() => {
    if (!user) return;
    const fetchCredits = async () => {
      try {
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
        console.error(err);
      }
    };
    fetchCredits();
  }, [user]);

  const handleUpgrade = async (planId: string) => {
    if (!user) {
      setError("Please sign in or create an account to upgrade.");
      return;
    }
    
    setLoading(true);
    setError("");
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        setError("User session expired. Please sign in again.");
        setLoading(false);
        return;
      }
      
      const res = await fetch(`http://127.0.0.1:8000/api/v1/payments/create-checkout-session?plan_id=${planId}`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });
      if (!res.ok) throw new Error("Could not initialize Stripe checkout session.");
      const data = await res.json();
      if (data?.url) {
        window.location.href = data.url;
      }
    } catch (err: any) {
      setError(err.message || "Failed to initialize upgrade checkout.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: "900px", margin: "40px auto", padding: "0 20px" }}>
      <div style={{ textAlign: "center", marginBottom: "48px" }}>
        <h1 style={{ fontFamily: "var(--font-outfit)", fontSize: "2.5rem", fontWeight: 800, color: "var(--text-primary)", marginBottom: "12px" }}>
          Simple, Transparent Pricing
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "600px", margin: "0 auto", lineHeight: "1.6" }}>
          Practice adaptive technical simulations, calibrate your skills checklist, and clear coding or system design interviews.
        </p>
      </div>

      {error && (
        <div style={{
          backgroundColor: "#FEF2F2",
          border: "1px solid #FCA5A5",
          color: "#991B1B",
          padding: "12px 16px",
          borderRadius: "8px",
          marginBottom: "32px",
          fontSize: "0.95rem"
        }}>
          {error}
        </div>
      )}

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
        gap: "32px",
        alignItems: "start"
      }}>
        {/* FREE PLAN */}
        <div className="card" style={{ padding: "32px", display: "flex", flexDirection: "column", minHeight: "440px", border: "1px solid var(--border-main)" }}>
          <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "8px" }}>Free Trial</h3>
          <div style={{ display: "flex", alignItems: "baseline", gap: "4px", marginBottom: "20px" }}>
            <span style={{ fontSize: "2.25rem", fontWeight: 800, color: "var(--text-primary)" }}>$0</span>
            <span style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>/ always free</span>
          </div>
          
          <ul style={{ listStyleType: "none", padding: 0, margin: "0 0 32px 0", display: "flex", flexDirection: "column", gap: "14px", flex: 1 }}>
            <li style={{ display: "flex", gap: "10px", fontSize: "0.95rem", color: "var(--text-secondary)" }}>
              ✅ 3 completed mock interviews
            </li>
            <li style={{ display: "flex", gap: "10px", fontSize: "0.95rem", color: "var(--text-secondary)" }}>
              ✅ Basic performance feedback report
            </li>
            <li style={{ display: "flex", gap: "10px", fontSize: "0.95rem", color: "var(--text-secondary)" }}>
              ✅ Text transcript verification
            </li>
            <li style={{ display: "flex", gap: "10px", fontSize: "0.95rem", color: "var(--text-secondary)", textDecoration: "line-through", opacity: 0.6 }}>
              ❌ Unlimited mock simulations
            </li>
          </ul>

          <button
            disabled
            className="btn btn-secondary"
            style={{ width: "100%", padding: "12px", fontSize: "1rem", cursor: "not-allowed" }}
          >
            {credits && credits.plan_id === "free" ? "Active Plan" : "Current Plan"}
          </button>
        </div>

        {/* PRO PLAN */}
        <div className="card" style={{
          padding: "32px",
          display: "flex",
          flexDirection: "column",
          minHeight: "440px",
          border: "2px solid #3B82F6",
          position: "relative",
          boxShadow: "0 10px 30px rgba(59, 130, 246, 0.08)"
        }}>
          <div style={{
            position: "absolute",
            top: "-14px",
            left: "50%",
            transform: "translateX(-50%)",
            backgroundColor: "#3B82F6",
            color: "#FFFFFF",
            padding: "4px 14px",
            borderRadius: "20px",
            fontSize: "0.75rem",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.5px"
          }}>
            Most Popular
          </div>
          
          <h3 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "8px" }}>Pro Access</h3>
          <div style={{ display: "flex", alignItems: "baseline", gap: "4px", marginBottom: "20px" }}>
            <span style={{ fontSize: "2.25rem", fontWeight: 800, color: "var(--text-primary)" }}>$19.99</span>
            <span style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>/ month</span>
          </div>

          <ul style={{ listStyleType: "none", padding: 0, margin: "0 0 32px 0", display: "flex", flexDirection: "column", gap: "14px", flex: 1 }}>
            <li style={{ display: "flex", gap: "10px", fontSize: "0.95rem", color: "var(--text-secondary)" }}>
              ✅ <strong>Unlimited</strong> mock simulations
            </li>
            <li style={{ display: "flex", gap: "10px", fontSize: "0.95rem", color: "var(--text-secondary)" }}>
              ✅ Multi-dimensional AI grading report
            </li>
            <li style={{ display: "flex", gap: "10px", fontSize: "0.95rem", color: "var(--text-secondary)" }}>
              ✅ Resume gap mapping & checklist updates
            </li>
            <li style={{ display: "flex", gap: "10px", fontSize: "0.95rem", color: "var(--text-secondary)" }}>
              ✅ Real-time EdgeTTS byte streaming
            </li>
            <li style={{ display: "flex", gap: "10px", fontSize: "0.95rem", color: "var(--text-secondary)" }}>
              ✅ Priority support & portal configuration
            </li>
          </ul>

          <button
            onClick={() => handleUpgrade("pro")}
            disabled={loading || (credits && credits.is_subscribed)}
            className="btn btn-primary"
            style={{ width: "100%", padding: "12px", fontSize: "1rem" }}
          >
            {loading ? "Redirecting..." : (credits && credits.is_subscribed) ? "Already Subscribed" : "Upgrade to Pro"}
          </button>
        </div>
      </div>
    </div>
  );
}
