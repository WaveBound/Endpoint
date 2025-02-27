import os
import stripe
import json
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify

app = Flask(__name__)

# Stripe and webhook configuration
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "your_webhook_secret_here")

# Firebase service account setup
service_account_info = {
    "type": os.environ.get("FIREBASE_TYPE"),
    "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
    "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.environ.get("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
    "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
    "auth_uri": os.environ.get("FIREBASE_AUTH_URI"),
    "token_uri": os.environ.get("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.environ.get("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL"),
    "universe_domain": os.environ.get("FIREBASE_UNIVERSE_DOMAIN")
}

try:
    cred = credentials.Certificate(service_account_info)
    firebase_admin.initialize_app(cred)
except Exception as e:
    print("Error initializing Firebase with provided credentials:", e)
    firebase_admin.initialize_app()

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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
