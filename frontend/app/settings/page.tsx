"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { supabase } from "../utils/supabaseClient";

export default function SettingsPage() {
  const router = useRouter();
  
  // Settings States
  const [defaultDifficulty, setDefaultDifficulty] = useState("medium");
  const [defaultDuration, setDefaultDuration] = useState(15);
  const [voicePreference, setVoicePreference] = useState("alloy");
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);

    // Simulate saving preferences to localStorage
    setTimeout(() => {
      setSaving(false);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    }, 800);
  };

  const handleResetProfile = async () => {
    if (!confirm("Are you sure you want to reset all profiles and study plans? This permanently deletes all mock session histories and parsed credentials.")) return;
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        alert("You must be logged in to reset your profile data.");
        return;
      }
      const res = await fetch("http://127.0.0.1:8000/api/v1/interviews/profile/reset", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });
      if (!res.ok) throw new Error("Reset failed.");
      alert("All interview history and parsed profiles reset successfully.");
      router.push("/");
    } catch (e: any) {
      alert("Error resetting credentials: " + e.message);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px", maxWidth: "600px", margin: "0 auto" }}>
      
      {/* General Settings Form */}
      <div className="card">
        <h2 style={{ fontSize: "1.15rem", fontWeight: 700, fontFamily: "var(--font-outfit)", marginBottom: "16px" }}>
          Simulation Preferences
        </h2>

        {success && (
          <div style={{
            backgroundColor: "#ECFDF5",
            border: "1px solid #A7F3D0",
            color: "#065F46",
            padding: "10px 14px",
            borderRadius: "8px",
            marginBottom: "16px",
            fontSize: "0.85rem"
          }}>
            ✓ Preferences saved successfully.
          </div>
        )}

        <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <label style={{ fontSize: "0.85rem", fontWeight: 600 }}>Default Difficulty</label>
            <select value={defaultDifficulty} onChange={(e) => setDefaultDifficulty(e.target.value)}>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <label style={{ fontSize: "0.85rem", fontWeight: 600 }}>Default Session Duration</label>
            <select value={defaultDuration} onChange={(e) => setDefaultDuration(Number(e.target.value))}>
              <option value={5}>5 Minutes (5 Questions)</option>
              <option value={15}>15 Minutes (10 Questions)</option>
              <option value={30}>30 Minutes (15 Questions)</option>
            </select>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <label style={{ fontSize: "0.85rem", fontWeight: 600 }}>Voice Synthesizer Preference</label>
            <select value={voicePreference} onChange={(e) => setVoicePreference(e.target.value)}>
              <option value="alloy">Alloy (Standard Neutral)</option>
              <option value="echo">Echo (Warm)</option>
              <option value="fable">Fable (British Accent)</option>
              <option value="onyx">Onyx (Deep Bass)</option>
            </select>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={saving}
            style={{ alignSelf: "flex-start", marginTop: "8px" }}
          >
            {saving ? "Saving..." : "Save Preferences"}
          </button>
        </form>
      </div>

      {/* Danger Zone Profile Reset */}
      <div className="card" style={{ borderColor: "#FCA5A5", backgroundColor: "#FEF2F2" }}>
        <h2 style={{ fontSize: "1.15rem", fontWeight: 700, fontFamily: "var(--font-outfit)", color: "#EF4444", marginBottom: "8px" }}>
          Danger Zone
        </h2>
        <p style={{ fontSize: "0.85rem", color: "#991B1B", marginBottom: "16px", lineHeight: "1.4" }}>
          Resetting will clear all parsed resume credentials, gap analyses, coaching roadmaps, milestone study plans, and historical transcripts. This action is irreversible.
        </p>
        <button
          onClick={handleResetProfile}
          className="btn btn-danger"
        >
          Reset All Profile Data
        </button>
      </div>

    </div>
  );
}
