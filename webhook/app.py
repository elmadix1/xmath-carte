import os
import stripe
import requests
from flask import Flask, request, jsonify, redirect

app = Flask(__name__)

STRIPE_SECRET_KEY     = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
BREVO_API_KEY         = os.environ.get('BREVO_API_KEY')
BREVO_LIST_ID         = 3

stripe.api_key = STRIPE_SECRET_KEY

def add_to_brevo(email, prenom, customer_id):
    url = "https://api.brevo.com/v3/contacts"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    data = {
        "email": email,
        "attributes": {"PRENOM": prenom, "STRIPE_ID": customer_id},
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
    data = {"unlinkListIds": [BREVO_LIST_ID]}
    requests.put(url, json=data, headers=headers)

def get_brevo_contact(email):
    url = f"https://api.brevo.com/v3/contacts/{email}"
    headers = {"accept": "application/json", "api-key": BREVO_API_KEY}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()
    return None

def cancel_stripe_subscription(customer_id):
    try:
        subs = stripe.Subscription.list(customer=customer_id, status='active', limit=1)
        if subs.data:
            stripe.Subscription.delete(subs.data[0].id)
            return True
    except Exception as e:
        print(f"Erreur annulation Stripe : {e}")
    return False

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload    = request.data
    sig_header = request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    if event['type'] == 'checkout.session.completed':
        session     = event['data']['object']
        email       = session.get('customer_details', {}).get('email', '')
        nom_complet = session.get('customer_details', {}).get('name', '') or ''
        prenom      = nom_complet.split()[0] if nom_complet else ''
        customer_id = session.get('customer', '')
        if email:
            add_to_brevo(email, prenom, customer_id)
            print(f"Abonné ajouté : {email}")

    elif event['type'] in ['customer.subscription.deleted', 'invoice.payment_failed']:
        obj         = event['data']['object']
        customer_id = obj.get('customer')
        customer    = stripe.Customer.retrieve(customer_id)
        email       = customer.get('email', '')
        if email:
            remove_from_brevo(email)
            print(f"Abonné supprimé : {email}")

    return jsonify({'status': 'ok'}), 200

@app.route('/desabonnement', methods=['GET'])
def desabonnement():
    email = request.args.get('email', '').strip()
    if not email:
        return redirect('https://emplois-scolaires-monde.online/desabonnement.html?status=erreur')

    contact = get_brevo_contact(email)
    if not contact:
        return redirect('https://emplois-scolaires-monde.online/desabonnement.html?status=introuvable')

    customer_id = contact.get('attributes', {}).get('STRIPE_ID', '')
    if customer_id:
        cancel_stripe_subscription(customer_id)

    remove_from_brevo(email)
    return redirect('https://emplois-scolaires-monde.online/desabonnement.html?status=ok')

@app.route('/')
def index():
    return 'OK', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
