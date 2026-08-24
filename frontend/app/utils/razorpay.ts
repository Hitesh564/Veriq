import { API_BASE_URL } from "./api";

declare global {
  interface Window {
    Razorpay: any;
  }
}

export interface RazorpayOrderResponse {
  order_id: string;
  amount: number;
  currency: string;
  key_id?: string;
  status?: string;
  receipt?: string;
}

export interface RazorpaySuccessResponse {
  razorpay_payment_id: string;
  razorpay_order_id: string;
  razorpay_signature: string;
}

export interface CheckoutOptions {
  amountInPaise: number; // e.g. 19900 for ₹199
  currency?: string;
  planId?: string;
  planName?: string;
  description?: string;
  userId?: string;
  userEmail?: string;
  userName?: string;
  userPhone?: string;
  onSuccess?: (res: { orderId: string; paymentId: string; signature: string }) => void;
  onError?: (error: { message: string; details?: any }) => void;
  onDismiss?: () => void;
}

/**
 * Dynamically loads the Razorpay checkout.js script into the DOM.
 */
export function loadRazorpayScript(): Promise<boolean> {
  return new Promise((resolve) => {
    if (typeof window === "undefined") {
      resolve(false);
      return;
    }

    if (window.Razorpay) {
      resolve(true);
      return;
    }

    const existingScript = document.getElementById("razorpay-checkout-script");
    if (existingScript) {
      existingScript.addEventListener("load", () => resolve(true));
      existingScript.addEventListener("error", () => resolve(false));
      return;
    }

    const script = document.createElement("script");
    script.id = "razorpay-checkout-script";
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.onload = () => resolve(true);
    script.onerror = () => {
      console.error("Failed to load Razorpay SDK.");
      resolve(false);
    };

    document.body.appendChild(script);
  });
}

/**
 * Initiates Razorpay Standard Checkout:
 * 1. Loads SDK
 * 2. Creates Order on Backend (/api/create-order)
 * 3. Opens Razorpay Modal
 * 4. Verifies Signature on Backend (/api/verify-payment) upon completion
 */
export async function initiateRazorpayPayment(options: CheckoutOptions): Promise<void> {
  const isLoaded = await loadRazorpayScript();
  if (!isLoaded) {
    options.onError?.({
      message: "Could not load Razorpay SDK. Please check your internet connection and try again."
    });
    return;
  }

  // Step 1: Create Order on Backend
  let orderData: RazorpayOrderResponse;
  try {
    const res = await fetch(`${API_BASE_URL}/api/create-order`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        amount: options.amountInPaise,
        currency: options.currency || "INR",
        receipt: `rcpt_${options.userId ? options.userId.slice(0, 8) : "guest"}_${Date.now()}`,
        notes: {
          plan_id: options.planId || "pro",
          user_id: options.userId || "anonymous",
        },
      }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Order creation failed with status ${res.status}`);
    }

    orderData = await res.json();
  } catch (err: any) {
    options.onError?.({
      message: err.message || "Failed to initialize order on server."
    });
    return;
  }

  const razorpayKey =
    process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID ||
    orderData.key_id ||
    "rzp_test_TTiNj5PVM8xl3r";

  // Step 2: Configure Razorpay modal options
  const rzpOptions = {
    key: razorpayKey,
    amount: orderData.amount,
    currency: orderData.currency,
    name: "Veriq AI",
    description: options.description || `${options.planName || "Pro"} Subscription`,
    image: "/favicon.ico",
    order_id: orderData.order_id,
    prefill: {
      name: options.userName || "",
      email: options.userEmail || "",
      contact: options.userPhone || "",
    },
    theme: {
      color: "#4f46e5",
    },
    modal: {
      ondismiss: function () {
        if (options.onDismiss) {
          options.onDismiss();
        }
      },
    },
    handler: async function (response: RazorpaySuccessResponse) {
      // Step 3: Verify Payment Signature on Backend
      try {
        const verifyRes = await fetch(`${API_BASE_URL}/api/verify-payment`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
            user_id: options.userId,
            plan_id: options.planId || "pro",
          }),
        });

        if (!verifyRes.ok) {
          const verifyErr = await verifyRes.json().catch(() => ({}));
          throw new Error(verifyErr.detail || "Payment verification signature mismatch.");
        }

        const verifyData = await verifyRes.json();
        options.onSuccess?.({
          orderId: response.razorpay_order_id,
          paymentId: response.razorpay_payment_id,
          signature: response.razorpay_signature,
        });
      } catch (err: any) {
        options.onError?.({
          message: err.message || "Payment verification failed."
        });
      }
    },
  };

  const rzpInstance = new window.Razorpay(rzpOptions);

  rzpInstance.on("payment.failed", function (response: any) {
    const errorDetail = response.error?.description || "Payment failed or was declined.";
    options.onError?.({
      message: errorDetail,
      details: response.error
    });
  });

  rzpInstance.open();
}
