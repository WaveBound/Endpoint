import os
import stripe
from flask import Flask, request, jsonify

app = Flask(__name__)

stripe.api_key = "sk_test_51QswfJH7i1hE4ufzDYKoET9UiD0BxGv0zXaY2lSbb9jT2oBCpM4Y4cyPa5Jp8k2KhtM67ygpdpBXmXljqMzwhyle00w6PaX2gL"
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
        # Process the successful payment (e.g., record purchase)
        print(f"Payment succeeded for {customer_email}. Transaction ID: {transaction_id}")

    return jsonify(success=True), 200

@app.route('/success', methods=['GET'])
def success():
    # You can render an HTML template or simply return a message.
    return "Thank you for your purchase! Your payment was successful."

@app.route('/cancel', methods=['GET'])
def cancel():
    return "Payment was canceled. Please try again."

if __name__ == '__main__':
    app.run(debug=True)
