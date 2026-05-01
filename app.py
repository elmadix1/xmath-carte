import os
import json
import stripe
import requests
from flask import Flask, request, jsonify, redirect
from datetime import datetime

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
    r = requests.post(url, json=data, headers=headers)
    print(f"Brevo add: {r.status_code} {r.text}")

def remove_from_brevo(email):
    url = f"https://api.brevo.com/v3/contacts/{email}"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    data = {"unlinkListIds": [BREVO_LIST_ID]}
    r = requests.put(url, json=data, headers=headers)
    print(f"Brevo remove: {r.status_code} {r.text}")

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
    html = f"""<!DOCTYPE html>
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
              Votre abonnement aux alertes emploi est actif. Vous recevrez les nouvelles offres
              des leur publication, avant tout le monde.
            </p>
            <p style="color:#4a5240;font-size:0.95rem;line-height:1.6;margin:0 0 24px;">
              En attendant, consultez les 900+ offres disponibles des maintenant :
            </p>
            <a href="https://emplois-scolaires-monde.online/emplois.html"
               style="display:inline-block;background:#5a8a3c;color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:600;font-size:0.95rem;">
              Voir les offres
            </a>
          </td>
        </tr>
        <tr>
          <td style="background:#f5f8f3;padding:16px 32px;border-top:1px solid #e8ede4;text-align:center;">
            <p style="margin:0;font-size:0.72rem;color:#aaa;">
              Pour résilier votre abonnement aux alertes emploi :
              <a href="https://xmath-carte-production.up.railway.app/desabonnement?email={email}" style="color:#5a8a3c;">Résilier mon abonnement</a>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
    data = {
        "sender": {"name": "Postes Reseau Francais", "email": "contact@emplois-scolaires-monde.online"},
        "to": [{"email": email, "name": prenom or ""}],
        "subject": "Bienvenue - vos alertes emploi sont activees",
        "htmlContent": html
    }
    r = requests.post(url, json=data, headers=headers)
    print(f"Welcome email: {r.status_code} {r.text}")

def notify_owner(email, prenom):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    data = {
        "sender": {"name": "Postes Réseau Français", "email": "contact@emplois-scolaires-monde.online"},
        "to": [{"email": "elmadix1@gmail.com", "name": "Mo"}],
        "subject": "🎉 Nouvel abonné : " + (prenom or email) + " (" + email + ")",
        "htmlContent": f"<p>Nouvel abonné : <strong>{prenom or 'inconnu'}</strong> ({email})</p>"
    }
    r = requests.post(url, json=data, headers=headers)
    print(f"Notify owner: {r.status_code}")

def notify_owner_unsubscribe(email):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    data = {
        "sender": {"name": "Postes Réseau Français", "email": "contact@emplois-scolaires-monde.online"},
        "to": [{"email": "elmadix1@gmail.com", "name": "Mo"}],
        "subject": "👋 Désabonnement : " + email,
        "htmlContent": f"<p>Désabonnement : <strong>{email}</strong></p>"
    }
    r = requests.post(url, json=data, headers=headers)
    print(f"Notify owner unsubscribe: {r.status_code}")

def send_unsubscribe_confirmation(email, fin_periode):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    if fin_periode:
        message = f"Votre abonnement a bien été résilié. Vous continuerez à recevoir les alertes jusqu'au <strong>{fin_periode}</strong>, sans aucun prélèvement supplémentaire."
    else:
        message = "Votre abonnement a bien été résilié. Vous ne recevrez plus d'alertes emploi."
    html = f"""<!DOCTYPE html>
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
            <h1 style="color:#1a1f16;font-size:1.3rem;margin:0 0 16px;">Désabonnement confirmé</h1>
            <p style="color:#4a5240;font-size:0.95rem;line-height:1.6;margin:0 0 16px;">{message}</p>
            <p style="color:#4a5240;font-size:0.95rem;line-height:1.6;margin:0 0 24px;">
              Vous pouvez toujours consulter les offres gratuitement sur notre site.
            </p>
            <a href="https://emplois-scolaires-monde.online/emplois.html"
               style="display:inline-block;background:#5a8a3c;color:#fff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:600;font-size:0.95rem;">
              Voir les offres gratuitement
            </a>
          </td>
        </tr>
        <tr>
          <td style="background:#f5f8f3;padding:16px 32px;border-top:1px solid #e8ede4;text-align:center;">
            <p style="margin:0;font-size:0.72rem;color:#aaa;">Postes Réseau Français</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
    data = {
        "sender": {"name": "Postes Réseau Français", "email": "contact@emplois-scolaires-monde.online"},
        "to": [{"email": email, "name": "Abonné"}],
        "subject": "Désabonnement confirmé : Postes Réseau Français",
        "htmlContent": html
    }
    r = requests.post(url, json=data, headers=headers)
    print(f"Unsubscribe confirmation: {r.status_code}")

def cancel_stripe_subscription(customer_id):
    try:
        subs = stripe.Subscription.list(customer=customer_id, status='active', limit=1)
        if subs.data:
            stripe.Subscription.modify(subs.data[0].id, cancel_at_period_end=True)
            sub = stripe.Subscription.retrieve(subs.data[0].id)
            sub_dict = sub.to_dict()
            ts = sub_dict.get("cancel_at") or sub_dict.get("billing_cycle_anchor")
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
        print(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 400

    event_type = event['type']
    event_dict = json.loads(request.data)
    obj        = event_dict.get('data', {}).get('object', {})

    print(f"Event recu: {event_type}")

    if event_type == 'checkout.session.completed':
        cd          = obj.get('customer_details') or {}
        email       = cd.get('email', '')
        nom_complet = cd.get('name', '')
        collected   = obj.get('collected_information') or {}
        prenom      = collected.get('individual_name') or (nom_complet.split()[0] if nom_complet else '')
        customer_id = obj.get('customer', '')
        print(f"Checkout: email={email} prenom={prenom} customer_id={customer_id}")
        if email:
            add_to_brevo(email, prenom, customer_id)
            send_welcome_email(email, prenom)
            notify_owner(email, prenom)

    elif event_type in ['customer.subscription.deleted', 'invoice.payment_failed']:
        customer_id = obj.get('customer', '')
        cancel_at_period_end = obj.get('cancel_at_period_end', False)
        print(f"Sub deleted/failed: customer_id={customer_id} cancel_at_period_end={cancel_at_period_end}")
        if customer_id and not cancel_at_period_end:
            try:
                customer = stripe.Customer.retrieve(customer_id)
                email    = customer.email or ''
                print(f"Email recupere: {email}")
                if email:
                    remove_from_brevo(email)
            except Exception as e:
                print(f"Erreur retrieve customer: {e}")

    return jsonify({'status': 'ok'}), 200

@app.route('/desabonnement', methods=['GET'])
def desabonnement():
    email = request.args.get('email', '').strip()
    if not email:
        return redirect('https://emplois-scolaires-monde.online/desabonnement.html?status=erreur')

    contact = get_brevo_contact(email)
    if not contact:
        return redirect('https://emplois-scolaires-monde.online/desabonnement.html?status=deja-desabonne')

    # Vérifier si le contact est encore dans la liste
    lists = contact.get('listIds', [])
    if BREVO_LIST_ID not in lists:
        return redirect('https://emplois-scolaires-monde.online/desabonnement.html?status=deja-desabonne')

    customer_id = contact.get('attributes', {}).get('STRIPE_ID', '')
    print(f"Desabonnement: email={email} customer_id={customer_id}")
    fin_periode = ''
    if customer_id:
        fin_periode = cancel_stripe_subscription(customer_id)
        print(f"Fin periode: {fin_periode}")
    else:
        print("Pas de customer_id trouve dans Brevo")

    remove_from_brevo(email)
    notify_owner_unsubscribe(email)
    send_unsubscribe_confirmation(email, fin_periode)

    print(f"Redirection: status=ok fin={fin_periode}")
    if fin_periode:
        return redirect(f'https://emplois-scolaires-monde.online/desabonnement.html?status=ok&fin={fin_periode}')
    return redirect('https://emplois-scolaires-monde.online/desabonnement.html?status=ok')

@app.route('/')
def index():
    return 'OK', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
