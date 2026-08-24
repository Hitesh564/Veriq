"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Script from "next/script";

import { useAuth } from "../context/AuthContext";
import { initiateRazorpayPayment } from "../utils/razorpay";

const plans = [
  {
    name: "Free",
    price: "₹0",
    cadence: "forever",
    blurb: "A simple way to experience the interview workflow.",
    features: ["3 practice interviews", "Basic interview report", "Interview history"]
  },
  {
    name: "Pro",
    id: "pro",
    price: "₹199",
    amountInPaise: 19900,
    cadence: "per month",
    blurb: "For consistent practice and a deeper feedback loop.",
    features: ["Unlimited practice sessions", "Detailed evaluations", "Personalized learning plans"],
    featured: true
  },
  {
    name: "Team",
    price: "Custom",
    cadence: "for your team",
    blurb: "For bootcamps, cohorts, and structured hiring programs.",
    features: ["Shared interview setup", "Cohort-level analytics", "Guided rollout support"]
  }
];

export default function PricingPage() {
  const router = useRouter();
  const { user, setShowAuthModal } = useAuth();
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  const handleProCheckout = async () => {
    setErrorMsg("");
    setSuccessMsg("");

    if (!user) {
      setShowAuthModal(true);
      return;
    }

    setCheckoutLoading(true);
    await initiateRazorpayPayment({
      amountInPaise: 19900,
      currency: "INR",
      planId: "pro",
      planName: "Pro Plan",
      userId: user.id,
      userEmail: user.email,
      onSuccess: (data) => {
        setCheckoutLoading(false);
        setSuccessMsg(`Payment confirmed! ID: ${data.paymentId}`);
        router.push(`/payment-success?session_id=${data.paymentId}&provider=razorpay&plan_id=pro`);
      },
      onError: (err) => {
        setCheckoutLoading(false);
        setErrorMsg(err.message || "Checkout could not be completed.");
      },
      onDismiss: () => {
        setCheckoutLoading(false);
      }
    });
  };

  return (
    <>
      <Script src="https://checkout.razorpay.com/v1/checkout.js" strategy="lazyOnload" />
      <div className="section-shell">
        <div className="page-shell">
          <section className="hero-panel reveal-up" style={{ padding: "36px" }}>
            <div className="eyebrow">Pricing</div>
            <h1 className="page-title text-balance" style={{ marginTop: "16px", maxWidth: "12ch" }}>
              Choose your practice rhythm.
            </h1>
            <p className="hero-copy" style={{ marginTop: "14px", maxWidth: "62ch" }}>
              Start with a few focused sessions, move to Pro for unlimited practice, or bring Veriq to your team.
            </p>
            <div style={{ marginTop: "22px", display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <button className="btn btn-primary" onClick={() => (user ? router.push("/interview") : setShowAuthModal(true))}>
                Start free
              </button>
              <Link href="/product" className="btn btn-secondary">View product</Link>
            </div>

            {errorMsg && (
              <div style={{ marginTop: "16px", padding: "10px 14px", backgroundColor: "#FEF2F2", color: "#991B1B", border: "1px solid #FCA5A5", borderRadius: "8px", fontSize: "0.9rem" }}>
                ⚠️ {errorMsg}
              </div>
            )}
            {successMsg && (
              <div style={{ marginTop: "16px", padding: "10px 14px", backgroundColor: "#F0FDF4", color: "#166534", border: "1px solid #BBF7D0", borderRadius: "8px", fontSize: "0.9rem" }}>
                ✓ {successMsg}
              </div>
            )}
          </section>

          <section className="pricing-grid" style={{ marginTop: "28px" }}>
            {plans.map((plan) => (
              <div key={plan.name} className={`pricing-card ${plan.featured ? "pricing-card--featured" : ""}`}>
                <div className="pricing-card__topline">
                  <h2>{plan.name}</h2>
                  {plan.featured && <span className="badge badge-primary">Most popular</span>}
                </div>
                <p className="pricing-card__blurb">{plan.blurb}</p>
                <div className="pricing-card__price-row">
                  <span className="pricing-card__price">{plan.price}</span>
                  <span className="pricing-card__cadence">{plan.cadence}</span>
                </div>
                <div className="pricing-card__features">
                  {plan.features.map((feature) => (
                    <div key={feature} className="pricing-card__feature">
                      <span className="pricing-card__check">✓</span>
                      <span>{feature}</span>
                    </div>
                  ))}
                </div>
                {plan.featured ? (
                  <button
                    id="upgrade-pro-razorpay-btn"
                    type="button"
                    className="btn btn-primary"
                    disabled={checkoutLoading}
                    onClick={handleProCheckout}
                  >
                    {checkoutLoading ? "Opening Razorpay..." : "Upgrade to Pro (₹199)"}
                  </button>
                ) : (
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => {
                      if (plan.name === "Team") {
                        window.location.href = "mailto:support@veriq.ai?subject=Team%20Inquiry";
                      } else {
                        user ? router.push("/interview") : setShowAuthModal(true);
                      }
                    }}
                  >
                    {plan.name === "Team" ? "Talk to us" : "Start practicing"}
                  </button>
                )}
              </div>
            ))}
          </section>

          <section className="feature-grid" style={{ marginTop: "28px" }}>
            <div className="feature-card" style={{ gridColumn: "span 7" }}>
              <div className="eyebrow">Included in Pro</div>
              <h2 className="section-title text-balance" style={{ marginTop: "14px" }}>
                Everything you need to keep practicing without friction.
              </h2>
              <p className="section-copy" style={{ marginTop: "10px" }}>
                Pro is where the full feedback loop comes alive: unlimited interviews, learning plans, and the option to keep sessions focused on your weak spots. Powered securely via Razorpay.
              </p>
            </div>

            <div className="feature-card" style={{ gridColumn: "span 5" }}>
              <div className="eyebrow">Need help</div>
              <h3 style={{ fontFamily: "var(--font-outfit)", fontSize: "1.4rem", fontWeight: 800, marginTop: "14px" }}>
                Not sure which plan to pick?
              </h3>
              <p className="section-copy" style={{ marginTop: "10px" }}>
                If you are just validating the product, start free. If you are practicing weekly, Pro is the better fit.
              </p>
              <button className="btn btn-secondary" style={{ marginTop: "16px" }} onClick={() => router.push("/how-it-works")}>
                See the workflow
              </button>
            </div>
          </section>
        </div>
      </div>
    </>
  );
}
