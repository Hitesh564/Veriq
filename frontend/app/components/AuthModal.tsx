"use client";

import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { supabase } from "../utils/supabaseClient";

export default function AuthModal() {
  const { showAuthModal, setShowAuthModal, user } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSignUp, setIsSignUp] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  if (!showAuthModal || user) return null;

  const handleOAuth = async (provider: "google" | "github") => {
    setErrorMsg("");
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider,
        options: {
          redirectTo: window.location.origin,
        },
      });
      if (error) throw error;
    } catch (err: any) {
      setErrorMsg(err.message || "OAuth login failed");
    }
  };

  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");
    setLoading(true);

    try {
      if (isSignUp) {
        const { error, data } = await supabase.auth.signUp({
          email,
          password,
        });
        if (error) throw error;
        if (data.session) {
          setSuccessMsg("Signed up successfully!");
        } else {
          setSuccessMsg("Please check your email to verify your registration link.");
        }
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
        setShowAuthModal(false);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: "fixed",
      inset: 0,
      backgroundColor: "rgba(15, 23, 42, 0.4)",
      backdropFilter: "blur(8px)",
      zIndex: 10000,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "20px",
      animation: "fadeIn 0.2s ease-out"
    }}>
      <div style={{
        backgroundColor: "rgba(255, 255, 255, 0.95)",
        borderRadius: "16px",
        width: "100%",
        maxWidth: "420px",
        padding: "32px",
        boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
        position: "relative",
        border: "1px solid rgba(226, 232, 240, 0.8)",
        display: "flex",
        flexDirection: "column",
        gap: "24px"
      }}>
        {/* Close Button */}
        <button
          onClick={() => setShowAuthModal(false)}
          style={{
            position: "absolute",
            top: "16px",
            right: "16px",
            border: "none",
            backgroundColor: "transparent",
            color: "#64748B",
            cursor: "pointer",
            padding: "4px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center"
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        {/* Header */}
        <div style={{ textAlign: "center" }}>
          <h2 style={{
            fontSize: "1.5rem",
            fontWeight: 800,
            color: "#0F172A",
            marginBottom: "6px",
            fontFamily: "var(--font-outfit)"
          }}>
            {isSignUp ? "Create your Account" : "Welcome Back"}
          </h2>
          <p style={{
            fontSize: "0.875rem",
            color: "#64748B",
            fontFamily: "var(--font-jakarta)"
          }}>
            Practice interviews and get real-time evaluations
          </p>
        </div>

        {/* OAuth Buttons */}
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {/* Google (At the top!) */}
          <button
            onClick={() => handleOAuth("google")}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "10px",
              padding: "12px",
              borderRadius: "8px",
              border: "1px solid #E2E8F0",
              backgroundColor: "#FFFFFF",
              color: "#334155",
              fontWeight: 600,
              fontSize: "0.95rem",
              cursor: "pointer",
              transition: "background-color 0.15s ease",
              width: "100%"
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = "#F8FAFC"}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = "#FFFFFF"}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Continue with Google
          </button>

          {/* GitHub */}
          <button
            onClick={() => handleOAuth("github")}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "10px",
              padding: "12px",
              borderRadius: "8px",
              border: "1px solid #E2E8F0",
              backgroundColor: "#24292F",
              color: "#FFFFFF",
              fontWeight: 600,
              fontSize: "0.95rem",
              cursor: "pointer",
              transition: "opacity 0.15s ease",
              width: "100%"
            }}
            onMouseEnter={(e) => e.currentTarget.style.opacity = "0.9"}
            onMouseLeave={(e) => e.currentTarget.style.opacity = "1"}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
            </svg>
            Continue with GitHub
          </button>
        </div>

        {/* Divider */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{ flex: 1, height: "1px", backgroundColor: "#E2E8F0" }} />
          <span style={{ fontSize: "0.75rem", color: "#94A3B8", textTransform: "uppercase", fontWeight: 600 }}>or email</span>
          <div style={{ flex: 1, height: "1px", backgroundColor: "#E2E8F0" }} />
        </div>

        {/* Email & Password Form */}
        <form onSubmit={handleEmailAuth} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <label style={{ fontSize: "0.825rem", fontWeight: 600, color: "#475569" }}>Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="candidate@work.com"
              style={{
                padding: "10px 14px",
                borderRadius: "8px",
                border: "1px solid #CBD5E1",
                outline: "none",
                fontSize: "0.95rem"
              }}
            />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <label style={{ fontSize: "0.825rem", fontWeight: 600, color: "#475569" }}>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
              style={{
                padding: "10px 14px",
                borderRadius: "8px",
                border: "1px solid #CBD5E1",
                outline: "none",
                fontSize: "0.95rem"
              }}
            />
          </div>

          {/* Feedback messages */}
          {errorMsg && (
            <div style={{ fontSize: "0.85rem", color: "#DC2626", fontWeight: 500, backgroundColor: "#FEF2F2", padding: "8px 12px", borderRadius: "6px" }}>
              {errorMsg}
            </div>
          )}

          {successMsg && (
            <div style={{ fontSize: "0.85rem", color: "#16A34A", fontWeight: 500, backgroundColor: "#F0FDF4", padding: "8px 12px", borderRadius: "6px" }}>
              {successMsg}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            style={{
              padding: "12px",
              borderRadius: "8px",
              border: "none",
              backgroundColor: "#2563EB",
              color: "#FFFFFF",
              fontWeight: 700,
              fontSize: "0.95rem",
              cursor: loading ? "not-allowed" : "pointer",
              transition: "background-color 0.15s ease",
              width: "100%",
              marginTop: "8px"
            }}
            onMouseEnter={(e) => { if (!loading) e.currentTarget.style.backgroundColor = "#1D4ED8"; }}
            onMouseLeave={(e) => { if (!loading) e.currentTarget.style.backgroundColor = "#2563EB"; }}
          >
            {loading ? "Authenticating..." : isSignUp ? "Sign Up" : "Sign In"}
          </button>
        </form>

        {/* Footer Toggle */}
        <div style={{ textAlign: "center", fontSize: "0.875rem", color: "#64748B" }}>
          {isSignUp ? "Already have an account?" : "New to the platform?"}{" "}
          <button
            onClick={() => {
              setIsSignUp(!isSignUp);
              setErrorMsg("");
              setSuccessMsg("");
            }}
            style={{
              border: "none",
              backgroundColor: "transparent",
              color: "#2563EB",
              fontWeight: 600,
              cursor: "pointer",
              padding: "0"
            }}
          >
            {isSignUp ? "Sign In" : "Sign Up"}
          </button>
        </div>
      </div>
    </div>
  );
}
