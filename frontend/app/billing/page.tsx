"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { supabase } from "../utils/supabaseClient";
import { safeFetch, safeJsonFetch } from "../utils/api";

interface PaymentHistoryItem {
  id: string;
  amount: number;
  currency: string;
  payment_status: string;
  transaction_id: string;
  invoice_url: string | null;
  created_at: string;
}

export default function BillingPage() {
  const { user } = useAuth();
  const [subStatus, setSubStatus] = useState<any>(null);
  const [history, setHistory] = useState<PaymentHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const fetchData = async () => {
    if (!user) return;
    setLoading(true);
    setError("");
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      setLoading(false);
      return;
    }

    const [subscription, paymentHistory] = await Promise.all([
      safeJsonFetch<any>("/api/v1/payments/subscription", {
        headers: { "Authorization": `Bearer ${session.access_token}` }
      }),
      safeJsonFetch<PaymentHistoryItem[]>("/api/v1/payments/history", {
        headers: { "Authorization": `Bearer ${session.access_token}` }
      })
    ]);

    if (subscription) setSubStatus(subscription);
    if (Array.isArray(paymentHistory)) setHistory(paymentHistory);
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [user]);

  const handlePortalRedirect = async () => {
    setActionLoading(true);
    setError("");
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const res = await safeFetch("/api/v1/payments/customer-portal", {
        method: "POST",
        headers: { "Authorization": `Bearer ${session.access_token}` }
      });
      if (!res || !res.ok) throw new Error("Could not initialize Stripe Customer Portal.");
      const data = await res.json();
      if (data?.url) {
        window.location.href = data.url;
      }
    } catch (err: any) {
      setError(err.message || "Failed to launch billing portal.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancelSub = async () => {
    if (!subStatus?.subscription_id) return;
    if (!confirm("Are you sure you want to cancel your Pro membership? You will retain access until the end of your billing cycle.")) return;

    setActionLoading(true);
    setError("");
    setSuccess("");
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const res = await safeFetch(`/api/v1/payments/cancel?subscription_id=${subStatus.subscription_id}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${session.access_token}` }
      });
      if (!res || !res.ok) throw new Error("Could not process cancellation.");
      const data = await res.json();
      setSuccess(data.message || "Subscription set to cancel successfully.");
      fetchData();
    } catch (err: any) {
      setError(err.message || "Failed to cancel subscription.");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <div style={{ color: "var(--text-secondary)" }}>Loading billing details...</div>;
  }

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "32px" }}>
      <div>
        <h1 style={{ fontFamily: "var(--font-outfit)", fontSize: "2rem", fontWeight: 800, color: "var(--text-primary)" }}>
          Billing & Subscriptions
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
          Manage your plan, check renewal dates, and view your billing statement history.
        </p>
      </div>

      {error && (
        <div style={{ backgroundColor: "#FEF2F2", border: "1px solid #FCA5A5", color: "#991B1B", padding: "12px 16px", borderRadius: "8px" }}>
          {error}
        </div>
      )}

      {success && (
        <div style={{ backgroundColor: "#F0FDF4", border: "1px solid #BBF7D0", color: "#166534", padding: "12px 16px", borderRadius: "8px" }}>
          {success}
        </div>
      )}

      {/* PLAN HIGHLIGHT CARD */}
      <div className="card" style={{ padding: "32px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "24px" }}>
        <div>
          <span style={{
            fontSize: "0.75rem",
            fontWeight: 700,
            color: subStatus?.is_subscribed ? "#1D4ED8" : "#475569",
            backgroundColor: subStatus?.is_subscribed ? "#EFF6FF" : "#F1F5F9",
            padding: "4px 10px",
            borderRadius: "12px",
            textTransform: "uppercase"
          }}>
            {subStatus?.plan_name}
          </span>
          <h2 style={{ fontSize: "1.75rem", fontWeight: 800, color: "var(--text-primary)", marginTop: "12px", marginBottom: "6px" }}>
            {subStatus?.is_subscribed ? "$19.99 / Month" : "Free Account"}
          </h2>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", margin: 0 }}>
            {subStatus?.is_subscribed
              ? subStatus.billing_status === "canceled"
                ? `Subscription canceled. Access ends on: ${new Date(subStatus.renewal_date).toLocaleDateString()}`
                : `Next renewal date: ${new Date(subStatus.renewal_date).toLocaleDateString()}`
              : `Usage: ${subStatus?.interviews_completed} / 3 Free Sessions Completed`}
          </p>
        </div>

        <div style={{ display: "flex", gap: "12px" }}>
          {subStatus?.is_subscribed ? (
            <>
              <button
                disabled={actionLoading}
                onClick={handlePortalRedirect}
                className="btn btn-secondary"
                style={{ padding: "10px 18px" }}
              >
                Stripe Customer Portal
              </button>
              {subStatus.billing_status !== "canceled" && (
                <button
                  disabled={actionLoading}
                  onClick={handleCancelSub}
                  className="btn btn-secondary"
                  style={{ color: "#EF4444", border: "1px solid #FCA5A5" }}
                >
                  Cancel Plan
                </button>
              )}
            </>
          ) : (
            <button
              onClick={() => window.location.href = "/pricing"}
              className="btn btn-primary"
              style={{ padding: "10px 20px" }}
            >
              Upgrade to Pro
            </button>
          )}
        </div>
      </div>

      {/* TRANSACTION LOG */}
      <div className="card" style={{ padding: "28px" }}>
        <h3 style={{ fontSize: "1.15rem", fontWeight: 700, marginBottom: "20px", fontFamily: "var(--font-outfit)" }}>
          Payment History
        </h3>

        {history.length === 0 ? (
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", textAlign: "center", padding: "20px 0" }}>
            No transaction records found for this account.
          </p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-subtle)", color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                  <th style={{ padding: "12px" }}>Date</th>
                  <th style={{ padding: "12px" }}>Transaction ID</th>
                  <th style={{ padding: "12px" }}>Amount</th>
                  <th style={{ padding: "12px" }}>Status</th>
                  <th style={{ padding: "12px" }}>Invoice</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => (
                  <tr key={item.id} style={{ borderBottom: "1px solid var(--border-subtle)", fontSize: "0.9rem" }}>
                    <td style={{ padding: "12px", color: "var(--text-primary)" }}>
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ padding: "12px", color: "var(--text-secondary)", fontFamily: "monospace" }}>
                      {item.transaction_id.slice(0, 16)}...
                    </td>
                    <td style={{ padding: "12px", fontWeight: 600, color: "var(--text-primary)" }}>
                      ${item.amount.toFixed(2)} {item.currency.toUpperCase()}
                    </td>
                    <td style={{ padding: "12px" }}>
                      <span style={{
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        color: "#15A34A",
                        backgroundColor: "#F0FDF4",
                        padding: "2px 8px",
                        borderRadius: "8px",
                        textTransform: "capitalize"
                      }}>
                        {item.payment_status}
                      </span>
                    </td>
                    <td style={{ padding: "12px" }}>
                      {item.invoice_url ? (
                        <a
                          href={item.invoice_url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ color: "#3B82F6", fontWeight: 600, textDecoration: "none" }}
                        >
                          Download 📄
                        </a>
                      ) : (
                        <span style={{ color: "var(--text-muted)" }}>N/A</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
