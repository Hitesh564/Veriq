"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "../context/AuthContext";

const plans = [
  {
    name: "Free",
    price: "$0",
    blurb: "Try the experience and get a feel for the workflow.",
    features: ["Three interviews", "Basic report", "History view"]
  },
  {
    name: "Pro",
    price: "$19.99",
    blurb: "Best for steady practice and a deeper feedback loop.",
    features: ["Unlimited sessions", "Detailed evaluations", "Learning plans"],
    featured: true
  },
  {
    name: "Team",
    price: "Custom",
    blurb: "Built for bootcamps, cohorts, and hiring teams.",
    features: ["Shared setup", "Cohort analytics", "Custom rollout"]
  }
];

export default function PricingPage() {
  const router = useRouter();
  const { setShowAuthModal } = useAuth();

  return (
    <div className="section-shell">
      <div className="page-shell">
        <section className="hero-panel reveal-up" style={{ padding: "36px" }}>
          <div className="eyebrow">Pricing</div>
          <h1 className="page-title text-balance" style={{ marginTop: "16px", maxWidth: "12ch" }}>
            Pricing that matches the product story.
          </h1>
          <p className="hero-copy" style={{ marginTop: "14px", maxWidth: "62ch" }}>
            Start free, move to Pro when you want unlimited practice, and use Team for structured rollouts across a group.
          </p>
          <div style={{ marginTop: "22px", display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <button className="btn btn-primary" onClick={() => setShowAuthModal(true)}>Start free</button>
            <Link href="/product" className="btn btn-secondary">View product</Link>
          </div>
        </section>

        <section className="pricing-grid" style={{ marginTop: "28px" }}>
          {plans.map((plan) => (
            <div key={plan.name} className={`pricing-card ${plan.featured ? "pricing-card--featured" : ""}`}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", alignItems: "center" }}>
                <div>
                  <h2 style={{ fontFamily: "var(--font-outfit)", fontSize: "1.55rem", fontWeight: 800 }}>{plan.name}</h2>
                  <p className="section-copy" style={{ marginTop: "8px" }}>{plan.blurb}</p>
                </div>
                {plan.featured && <span className="badge badge-primary">Most popular</span>}
              </div>
              <div className="pricing-card__price">{plan.price}</div>
              <div style={{ display: "grid", gap: "10px" }}>
                {plan.features.map((feature) => (
                  <div key={feature} style={{ display: "flex", gap: "10px", alignItems: "center", color: "var(--text-secondary)" }}>
                    <span style={{ width: "8px", height: "8px", borderRadius: "999px", background: "var(--color-primary)" }} />
                    <span>{feature}</span>
                  </div>
                ))}
              </div>
              <button
                className={plan.featured ? "btn btn-primary" : "btn btn-secondary"}
                onClick={() => setShowAuthModal(true)}
              >
                {plan.featured ? "Upgrade to Pro" : "Start here"}
              </button>
            </div>
          ))}
        </section>

        <section className="feature-grid" style={{ marginTop: "28px" }}>
          <div className="feature-card" style={{ gridColumn: "span 7" }}>
            <div className="eyebrow">Included in Pro</div>
            <h2 className="section-title text-balance" style={{ marginTop: "14px" }}>Everything you need to keep practicing without friction.</h2>
            <p className="section-copy" style={{ marginTop: "10px" }}>
              Pro is where the full feedback loop comes alive: unlimited interviews, learning plans, and the option to keep sessions focused on your weak spots.
            </p>
          </div>

          <div className="feature-card" style={{ gridColumn: "span 5" }}>
            <div className="eyebrow">Need help</div>
            <h3 style={{ fontFamily: "var(--font-outfit)", fontSize: "1.4rem", fontWeight: 800, marginTop: "14px" }}>Not sure which plan to pick?</h3>
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
  );
}
