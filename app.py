import os
import stripe
from flask import Flask, request, jsonify

app = Flask(__name__)

# Set your Stripe secret key (make sure to keep this secure)
stripe.api_key = "sk_test_51QswfJH7i1hE4ufzDYKoET9UiD0BxGv0zXaY2lSbb9jT2oBCpM4Y4cyPa5Jp8k2KhtM67ygpdpBXmXljqMzwhyle00w6PaX2gL"

# The webhook secret provided by Stripe. Set this as an environment variable in Render for production.
endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "your_webhook_secret_here")

@app.route('/webhook', methods=['POST'])
def webhook_received():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception as e:
        print(f"Error verifying webhook signature: {str(e)}")
        return jsonify(success=False), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session.get("customer_details", {}).get("email")
        transaction_id = session.get("payment_intent")
        # Here you can process the successful payment (e.g., record the purchase in your database)
        print(f"Payment succeeded for {customer_email}. Transaction ID: {transaction_id}")

    return jsonify(success=True), 200

if __name__ == '__main__':
    app.run(debug=True)
