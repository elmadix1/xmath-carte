"""
newsletter_app.py
Service Flask autonome pour la newsletter gratuite.
Deployer comme un deuxieme service Railway dans le meme repo.
Procfile pour ce service : web: gunicorn newsletter_app:app
"""

import os
import requests
from flask import Flask, request, jsonify, redirect

app = Flask(__name__)

BREVO_API_KEY            = os.environ.get('BREVO_API_KEY')
BREVO_NEWSLETTER_LIST_ID = 4


# ── Helpers Brevo ─────────────────────────────────────────────────────────────

def add_to_brevo_newsletter(email):
    url = "https://api.brevo.com/v3/contacts"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    r = requests.post(url, json={
        "email": email,
        "listIds": [BREVO_NEWSLETTER_LIST_ID],
        "updateEnabled": True
    }, headers=headers)
    print(f"Brevo newsletter add: {r.status_code} {r.text}")
    return r.status_code in [200, 201, 204]


def remove_from_brevo_newsletter(email):
    url = f"https://api.brevo.com/v3/contacts/{email}"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    r = requests.put(url, json={
        "unlinkListIds": [BREVO_NEWSLETTER_LIST_ID]
    }, headers=headers)
    print(f"Brevo newsletter remove: {r.status_code}")
    return r.status_code in [200, 201, 204]


def send_welcome_email(email):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
         style="background:#fff;border-radius:12px;overflow:hidden;max-width:600px;width:100%;">

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
            <h1 style="color:#1a1f16;font-size:1.3rem;margin:0 0 16px;">
              Inscription confirmée
            </h1>
            <p style="color:#4a5240;font-size:0.95rem;line-height:1.6;margin:0 0 16px;">
              Vous recevrez chaque lundi matin un résumé des nouvelles offres
              dans les établissements français à l'étranger (AEFE et MLF).
            </p>
            <p style="color:#4a5240;font-size:0.95rem;line-height:1.6;margin:0 0 24px;">
              Vous voulez recevoir les offres <strong>en temps réel</strong>,
              dès leur publication, avant tout le monde ?
            </p>
            <a href="https://emplois-scolaires-monde.online/alertes.html"
               style="display:inline-block;background:#5a8a3c;color:#fff;
                  text-decoration:none;padding:12px 28px;border-radius:8px;
                  font-weight:600;font-size:0.95rem;">
              Passer aux alertes temps réel (9 EUR/mois) →
            </a>
            <p style="color:#4a5240;font-size:0.85rem;line-height:1.6;margin:24px 0 0;">
              En attendant, consultez les 900+ offres disponibles :
            </p>
            <a href="https://emplois-scolaires-monde.online/emplois.html"
               style="display:inline-block;margin-top:8px;color:#5a8a3c;
                  text-decoration:none;font-weight:600;font-size:0.9rem;">
              Voir toutes les offres gratuitement →
            </a>
          </td>
        </tr>

        <tr>
          <td style="background:#f5f8f3;padding:16px 32px;
             border-top:1px solid #e8ede4;text-align:center;">
            <p style="margin:0;font-size:0.72rem;color:#aaa;">
              Vous recevez cet email car vous vous êtes inscrit à la newsletter gratuite.<br>
              <a href="https://newsletter-emplois.up.railway.app/desabonnement?email={email}"
                 style="color:#5a8a3c;">Se désabonner</a>
              &nbsp;·&nbsp;
              <a href="https://emplois-scolaires-monde.online" style="color:#5a8a3c;">
                emplois-scolaires-monde.online
              </a>
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""
    r = requests.post(url, json={
        "sender": {
            "name": "Postes Réseau Français",
            "email": "contact@emplois-scolaires-monde.online"
        },
        "to": [{"email": email}],
        "subject": "Inscription confirmée : newsletter hebdomadaire gratuite",
        "htmlContent": html
    }, headers=headers)
    print(f"Welcome newsletter: {r.status_code}")


def notify_owner(email):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    requests.post(url, json={
        "sender": {
            "name": "Postes Réseau Français",
            "email": "contact@emplois-scolaires-monde.online"
        },
        "to": [{"email": "elmadix1@gmail.com", "name": "Mo"}],
        "subject": f"📬 Nouvelle inscription newsletter : {email}",
        "htmlContent": f"<p>Nouvelle inscription newsletter gratuite : <strong>{email}</strong></p>"
    }, headers=headers)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/inscription-newsletter', methods=['POST'])
def inscription_newsletter():
    data  = request.get_json(silent=True) or {}
    email = (data.get('email') or request.form.get('email', '')).strip().lower()

    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        return jsonify({'error': 'Email invalide'}), 400

    ok = add_to_brevo_newsletter(email)
    if ok:
        send_welcome_email(email)
        notify_owner(email)
        return jsonify({'status': 'ok'}), 200

    return jsonify({'error': 'Erreur inscription'}), 500


@app.route('/desabonnement', methods=['GET'])
def desabonnement():
    email = request.args.get('email', '').strip()
    if not email:
        return redirect('https://emplois-scolaires-monde.online?desabonne=erreur')
    remove_from_brevo_newsletter(email)
    return redirect('https://emplois-scolaires-monde.online?desabonne=ok')


@app.route('/')
def index():
    return 'Newsletter service OK', 200


# ── Lancement ─────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
