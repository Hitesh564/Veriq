import os
import hmac
import hashlib
import sys
from dotenv import load_dotenv

load_dotenv()

# Test direct imports from app
from app.payments.razorpay import (
    create_razorpay_order,
    verify_razorpay_payment_signature,
    process_payment_verification,
    RazorpayClientManager
)
from fastapi import HTTPException

print("=== Running Razorpay Integration Unit & Verification Tests ===")

# Test 1: Credentials check
key_id = RazorpayClientManager.get_key_id()
key_secret = RazorpayClientManager.get_key_secret()
print(f"[TEST 1] Key ID: {key_id}")
assert key_id == "rzp_test_TTiNj5PVM8xl3r", f"Expected rzp_test_TTiNj5PVM8xl3r but got {key_id}"
assert key_secret == "TFSbnihCAdeSRBt59diajygr", "Key secret mismatch"
print("[PASS] Test 1: Razorpay credentials loaded correctly from environment.")

# Test 2: Minimum amount validation (< 100 paise)
try:
    create_razorpay_order(amount=50, currency="INR")
    print("[FAIL] Test 2 failed: Did not raise for amount < 100")
    sys.exit(1)
except HTTPException as e:
    assert e.status_code == 400, f"Expected status 400, got {e.status_code}"
    print("[PASS] Test 2: Minimum amount validation enforced (< 100 paise rejected with 400).")

# Test 3: Order Creation via Razorpay API
try:
    order = create_razorpay_order(amount=19900, currency="INR", receipt="test_rcpt_1")
    print(f"[TEST 3] Created Order: {order}")
    assert "order_id" in order and order["order_id"].startswith("order_"), "Invalid order_id"
    assert order["amount"] == 19900, f"Expected amount 19900, got {order['amount']}"
    assert order["currency"] == "INR", f"Expected currency INR, got {order['currency']}"
    print(f"[PASS] Test 3: Razorpay order created successfully with Order ID: {order['order_id']}")
    test_order_id = order["order_id"]
except Exception as e:
    print(f"[FAIL] Test 3 failed: {e}")
    sys.exit(1)

# Test 4: Signature Verification - Valid Signature
test_payment_id = "pay_test123456789"
correct_payload = f"{test_order_id}|{test_payment_id}".encode("utf-8")
valid_signature = hmac.new(key_secret.encode("utf-8"), correct_payload, hashlib.sha256).hexdigest()

is_valid = verify_razorpay_payment_signature(
    razorpay_order_id=test_order_id,
    razorpay_payment_id=test_payment_id,
    razorpay_signature=valid_signature
)
assert is_valid is True, "Expected valid signature to verify successfully"

verify_res = process_payment_verification(
    razorpay_order_id=test_order_id,
    razorpay_payment_id=test_payment_id,
    razorpay_signature=valid_signature
)
assert verify_res["status"] == "success", "Expected success status"
print("[PASS] Test 4: Valid HMAC-SHA256 signature correctly verified.")

# Test 5: Signature Verification - Tampered Signature (Mismatch)
invalid_signature = "invalid_tampered_signature_12345"
try:
    process_payment_verification(
        razorpay_order_id=test_order_id,
        razorpay_payment_id=test_payment_id,
        razorpay_signature=invalid_signature
    )
    print("[FAIL] Test 5 failed: Invalid signature was not rejected")
    sys.exit(1)
except HTTPException as e:
    assert e.status_code == 400, f"Expected status 400, got {e.status_code}"
    assert "mismatch" in e.detail.lower() or "failed" in e.detail.lower()
    print("[PASS] Test 5: Signature mismatch rejected with 400 Bad Request and not marked as paid.")

# Test 6: Missing fields validation
try:
    process_payment_verification(
        razorpay_order_id="",
        razorpay_payment_id=test_payment_id,
        razorpay_signature=valid_signature
    )
    print("[FAIL] Test 6 failed: Missing order ID was not rejected")
    sys.exit(1)
except HTTPException as e:
    assert e.status_code == 400
    print("[PASS] Test 6: Missing fields correctly rejected with 400.")

print("\n*** ALL RAZORPAY VERIFICATION TESTS PASSED SUCCESSFULLY! ***")
