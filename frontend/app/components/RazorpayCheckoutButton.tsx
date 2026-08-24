"use client";

import React, { useState } from "react";
import { initiateRazorpayPayment } from "../utils/razorpay";
import { useRouter } from "next/navigation";

interface RazorpayCheckoutButtonProps {
  amountInPaise?: number; // default 19900 (₹199)
  planId?: string;
  planName?: string;
  buttonText?: string;
  className?: string;
  style?: React.CSSProperties;
  userId?: string;
  userEmail?: string;
  userName?: string;
  onPaymentSuccess?: (data: { orderId: string; paymentId: string; signature: string }) => void;
  onPaymentError?: (error: { message: string }) => void;
}

export default function RazorpayCheckoutButton({
  amountInPaise = 19900,
  planId = "pro",
  planName = "Pro Plan",
  buttonText = "Pay with Razorpay",
  className = "btn btn-primary",
  style = {},
  userId,
  userEmail,
  userName,
  onPaymentSuccess,
  onPaymentError,
}: RazorpayCheckoutButtonProps) {
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const router = useRouter();

  const handleCheckout = async () => {
    setLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    await initiateRazorpayPayment({
      amountInPaise,
      planId,
      planName,
      userId,
      userEmail,
      userName,
      description: `Veriq AI - ${planName}`,
      onSuccess: (data) => {
        setLoading(false);
        setSuccessMessage(`Payment successful! Payment ID: ${data.paymentId}`);
        if (onPaymentSuccess) {
          onPaymentSuccess(data);
        } else {
          router.push(`/payment-success?session_id=${data.paymentId}&provider=razorpay&plan_id=${planId}`);
        }
      },
      onError: (err) => {
        setLoading(false);
        setErrorMessage(err.message || "Payment process encountered an error.");
        if (onPaymentError) {
          onPaymentError(err);
        }
      },
      onDismiss: () => {
        setLoading(false);
      },
    });
  };

  return (
    <div style={{ display: "inline-flex", flexDirection: "column", gap: "8px" }}>
      <button
        type="button"
        id="razorpay-checkout-btn"
        className={className}
        style={{
          cursor: loading ? "not-allowed" : "pointer",
          opacity: loading ? 0.7 : 1,
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "8px",
          ...style,
        }}
        onClick={handleCheckout}
        disabled={loading}
      >
        {loading ? (
          <>
            <span
              style={{
                width: "14px",
                height: "14px",
                border: "2px solid currentColor",
                borderTopColor: "transparent",
                borderRadius: "50%",
                display: "inline-block",
                animation: "spin 1s linear infinite",
              }}
            />
            <span>Initializing...</span>
          </>
        ) : (
          <span>{buttonText}</span>
        )}
      </button>

      {errorMessage && (
        <div
          role="alert"
          style={{
            fontSize: "0.85rem",
            color: "#EF4444",
            backgroundColor: "#FEF2F2",
            border: "1px solid #FCA5A5",
            borderRadius: "6px",
            padding: "6px 10px",
            maxWidth: "320px",
          }}
        >
          ⚠️ {errorMessage}
        </div>
      )}

      {successMessage && (
        <div
          role="status"
          style={{
            fontSize: "0.85rem",
            color: "#16A34A",
            backgroundColor: "#F0FDF4",
            border: "1px solid #BBF7D0",
            borderRadius: "6px",
            padding: "6px 10px",
            maxWidth: "320px",
          }}
        >
          ✓ {successMessage}
        </div>
      )}
    </div>
  );
}
