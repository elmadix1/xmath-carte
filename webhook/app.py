import os
import stripe
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
BREVO_API_KEY = os.environ.get('BREVO_API_KEY')
BREVO_LIST_ID = 3  # ta liste #3

stripe.api_key = STRIPE_SECRET_KEY

def add_to_brevo(email, prenom):
    url = "https://api.brevo.com/v3/contacts"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    data = {
        "email": email,
        "attributes": {"PRENOM": prenom},
        "listIds": [BREVO_LIST_ID],
        "updateEnabled": True
    }
    requests.post(url, json=data, headers=headers)

def remove_from_brevo(email):
    url = f"https://api.brevo.com/v3/contacts/{email}"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    data = {"listIds": [BREVO_LIST_ID], "unlinkListIds": [BREVO_LIST_ID]}
    requests.put(url, json=data, headers=headers)

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        email = session.get('customer_details', {}).get('email', '')
        prenom = session.get('customer_details', {}).get('name', '').split()[0]
        if email:
            add_to_brevo(email, prenom)

    elif event['type'] in ['customer.subscription.deleted', 'invoice.payment_failed']:
        obj = event['data']['object']
        customer_id = obj.get('customer')
        customer = stripe.Customer.retrieve(customer_id)
        email = customer.get('email', '')
        if email:
            remove_from_brevo(email)

    return jsonify({'status': 'ok'}), 200

@app.route('/')
def index():
    return 'OK', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
