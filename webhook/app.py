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

def send_welcome_email(email, prenom):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    prenom_display = prenom if prenom else "vous"
    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;max-width:600px;width:100%;">
        <tr>
          <td style="background:#1a1f16;padding:24px 32px;border-bottom:3px solid #5a8a3c;">
            <span style="font-size:1.3rem;font-weight:700;">
              <span style="color:#4169E1">Postes</span>
              <span style="color:#ffffff"> Réseau </span>
              <span style="color:#ED2939">Français</span>
            </span>
          </td>
        </tr>
        <tr>
          <td style="padding:32px;">
            <h1 style="color:#1a1f16;font-size:1.3rem;margin:0 0 16px;">Bienvenue {prenom_display} !</h1>
            <p style="color:#4a5240;font-size:0.95rem;line-height:1.6;margin:0 0 16px;">
              Votre abonnement aux alertes emploi est actif. Vous recevrez les nouvelles offres dès leur publication, avant tout le monde.
            </p>
            <p style="color:#4a5240;font-size:0.95rem;line-height:1.6;margin:0 0 24px;">
              En attendant, consultez les 900+ offres disponibles dès maintenant :
            </p>
            <a href="https://emplois-scolaires-monde.online/emplois.html"
               style="display:inline-block;background:#5a8a3c;color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:600;font-size:0.95rem;">
              Voir les offres →
            </a>
          </td>
        </tr>
        <tr>
          <td style="background:#f5f8f3;padding:16px 32px;border-top:1px solid #e8ede4;text-align:center;">
            <p style="margin:0;font-size:0.72rem;color:#aaa;">
              Pour gérer ou annuler votre abonnement : <a href="https://xmath-carte-production.up.railway.app/desabonnement?email={email}" style="color:#5a8a3c;">Se désabonner</a>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
    data = {
        "sender": {{"name": "Postes Réseau Français", "email": "contact@emplois-scolaires-monde.online"}},
        "to": [{{"email": email, "name": prenom or ""}}],
        "subject": "Bienvenue — vos alertes emploi sont activées",
        "htmlContent": html
    }
    requests.post(url, json=data, headers=headers)

def cancel_stripe_subscription(customer_id):
    try:
        subs = stripe.Subscription.list(customer=customer_id, status='active', limit=1)
        if subs.data:
            sub = stripe.Subscription.modify(subs.data[0].id, cancel_at_period_end=True)
            from datetime import datetime
            ts = sub.current_period_end
            fin = datetime.utcfromtimestamp(ts).strftime('%d/%m/%Y')
            return fin
    except Exception as e:
        print(f"Erreur annulation Stripe : {e}")
    return ''

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
        email       = session.customer_details.email if session.customer_details else ''
        nom_complet = session.customer_details.name if session.customer_details else ''
        prenom      = session.collected_information.individual_name if session.collected_information else nom_complet
        prenom      = nom_complet.split()[0] if nom_complet else ''
        customer_id = session.customer or ''
        if email:
            add_to_brevo(email, prenom, customer_id)
            send_welcome_email(email, prenom)
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
