"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "../utils/supabaseClient";

export default function PaymentSuccessPage() {
  const router = useRouter();
  const [activated, setActivated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get("session_id");
    
    if (sessionId && sessionId.startsWith("mock_checkout_session_")) {
      const userId = sessionId.replace("mock_checkout_session_", "");
      
      supabase.auth.getSession().then(({ data: { session } }) => {
        if (!session) {
          setLoading(false);
          return;
        }
        
        fetch("http://127.0.0.1:8000/api/v1/payments/webhook", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            type: "checkout.session.completed",
            data: {
              object: {
                customer: "cus_mock_dev",
                subscription: "sub_mock_" + Math.random().toString(36).substr(2, 9),
                metadata: {
                  user_id: userId,
                  plan_id: "pro"
                }
              }
            }
          })
        })
          .then(() => {
            setActivated(true);
            setLoading(false);
          })
          .catch((err) => {
            console.error("Mock webhook registration failed:", err);
            setLoading(false);
          });
      });
    } else {
      setActivated(true);
      setLoading(false);
    }
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "60vh", color: "var(--text-secondary)" }}>
        Activating your Pro membership plan...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: "600px", margin: "80px auto", textAlign: "center" }} className="card">
      <div style={{ fontSize: "5rem", marginBottom: "24px", animation: "bounce 2s infinite" }}>🎉</div>
      
      <h1 style={{ fontFamily: "var(--font-outfit)", fontSize: "2.25rem", fontWeight: 800, color: "var(--text-primary)", marginBottom: "16px" }}>
        Welcome to Veriq Pro!
      </h1>
      
      <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", lineHeight: "1.6", marginBottom: "40px", padding: "0 20px" }}>
        Payment successful! Your account has been upgraded. You now have unlimited mock sessions, advanced system architecture analysis, and full recruiter report outputs.
      </p>

      <div style={{ display: "flex", gap: "16px", justifyContent: "center" }}>
        <button
          onClick={() => router.push("/")}
          className="btn btn-secondary"
          style={{ padding: "12px 24px" }}
        >
          Go to Dashboard
        </button>
        <button
          onClick={() => router.push("/new-interview")}
          className="btn btn-primary"
          style={{ padding: "12px 24px" }}
        >
          Start New Simulation
        </button>
      </div>

      <style jsx global>{`
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }
      `}</style>
    </div>
  );
}
