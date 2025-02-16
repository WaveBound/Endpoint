import os
import stripe
import base64
import json
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Set your Stripe secret key (keep it secure)
stripe.api_key = "sk_test_51QswfJH7i1hE4ufzDYKoET9UiD0BxGv0zXaY2lSbb9jT2oBCpM4Y4cyPa5Jp8k2KhtM67ygpdpBXmXljqMzwhyle00w6PaX2gL"

# Stripe webhook signing secret from environment variable
endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "your_webhook_secret_here")

# Initialize Firebase:
# Use the encoded credentials if provided; otherwise fall back to default initialization.
ENCODED_CREDS = os.environ.get("ENCODED_CREDS", "ENCODED_CREDS_HERE").strip()
if ENCODED_CREDS:
    try:
        decoded = base64.b64decode(ENCODED_CREDS)
        cred_dict = json.loads(decoded.decode("utf-8"))
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print("Error decoding ENCODED_CREDS:", e)
        firebase_admin.initialize_app()
else:
    firebase_admin.initialize_app()

# Create a Firestore client
db = firestore.client()

def record_purchase(email, transaction_id):
    purchase_data = {
        'email': email,
        'purchased': True,
        'purchase_date': firestore.SERVER_TIMESTAMP,
        'transaction_id': transaction_id
    }
    db.collection('purchases').document(email).set(purchase_data)
    print(f"Recorded purchase for {email} with transaction {transaction_id}")

@app.route('/webhook', methods=['POST'])
def webhook_received():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        print("Error verifying webhook signature:", e)
        return jsonify(success=False), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session.get("customer_details", {}).get("email")
        transaction_id = session.get("payment_intent")
        record_purchase(customer_email, transaction_id)
        print(f"Payment succeeded for {customer_email}. Transaction ID: {transaction_id}")

    return jsonify(success=True), 200

@app.route('/success', methods=['GET'])
def success():
    return "Thank you for your purchase! Your payment was successful."

@app.route('/cancel', methods=['GET'])
def cancel():
    return "Payment was canceled. Please try again."

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
