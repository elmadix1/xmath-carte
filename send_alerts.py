import json
import os
import requests
from datetime import datetime

BREVO_API_KEY = os.environ.get('BREVO_API_KEY')
BREVO_LIST_ID = 3

def load_offers(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {o['url']: o for o in data.get('offers', [])}
    except:
        return {}

def get_new_offers():
    current_aefe = load_offers('emplois.json')
    current_mlf  = load_offers('emplois_mlf.json')
    previous     = load_offers('emplois_previous.json')

    all_current = {**current_aefe, **current_mlf}
    new_offers  = [o for url, o in all_current.items() if url not in previous]
    return new_offers

def build_email_html(offers):
    rows = ""
    for o in offers[:50]:  # max 20 offres par email
        source = (o.get('source') or 'AEFE').upper()
        color  = '#1a56b0' if source == 'AEFE' else '#b01a1a'
        loc    = ', '.join(filter(None, [o.get('ville'), o.get('pays')]))
        rows += f"""
        <tr>
          <td style="padding:14px 16px;border-bottom:1px solid #e8ede4;">
            <a href="{o.get('url','#')}" style="color:#1a1f16;text-decoration:none;font-weight:500;font-size:0.95rem;">{o.get('titre','')}</a><br>
            <span style="font-size:0.82rem;color:#4a5240;">📍 {loc}</span>
            &nbsp;
            <span style="font-size:0.72rem;font-weight:700;padding:2px 7px;border-radius:4px;background:{'#e8f0fe' if source=='AEFE' else '#fce8e8'};color:{color};">{source}</span>
          </td>
        </tr>"""

    total = len(offers)
    plus  = f"<p style='text-align:center;color:#4a5240;font-size:0.85rem;'>+ {total-20} autres offres disponibles</p>" if total > 20 else ""

    return f"""
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:'DM Sans',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;max-width:600px;width:100%;">

        <!-- Header -->
        <tr>
          <td style="background:#1a1f16;padding:24px 32px;border-bottom:3px solid #5a8a3c;">
            <span style="font-size:1.3rem;font-weight:700;">
              <span style="color:#4169E1">Postes</span>
              <span style="color:#ffffff"> Réseau </span>
              <span style="color:#ED2939">Français</span>
            </span>
          </td>
        </tr>

        <!-- Intro -->
        <tr>
          <td style="padding:28px 32px 16px;">
            <h1 style="margin:0 0 8px;font-size:1.2rem;color:#1a1f16;">
              {total} nouveau{'x' if total > 1 else ''} poste{'s' if total > 1 else ''} publié{'s' if total > 1 else ''}
            </h1>
            <p style="margin:0;color:#4a5240;font-size:0.88rem;line-height:1.5;">
              Vous recevez cet email en avant-première car vous êtes abonné aux alertes.
            </p>
          </td>
        </tr>

        <!-- Offres -->
        <tr>
          <td style="padding:0 32px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e8ede4;border-radius:8px;overflow:hidden;">
              {rows}
            </table>
          </td>
        </tr>

        <!-- Plus -->
        <tr><td style="padding:16px 32px;">{plus}</td></tr>

        <!-- CTA -->
        <tr>
          <td style="padding:8px 32px 28px;text-align:center;">
            <a href="https://emplois-scolaires-monde.online/emplois.html"
               style="display:inline-block;background:#5a8a3c;color:#fff;text-decoration:none;padding:12px 32px;border-radius:8px;font-weight:600;font-size:0.95rem;">
              Voir toutes les offres →
            </a>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#f5f8f3;padding:16px 32px;border-top:1px solid #e8ede4;text-align:center;">
            <p style="margin:0;font-size:0.72rem;color:#aaa;">
              Vous recevez cet email car vous êtes abonné aux alertes emplois.<br>
              <a href="https://xmath-carte-production.up.railway.app/desabonnement?email=EMAIL_PLACEHOLDER" style="color:#5a8a3c;">Se désabonner</a>
              · <a href="https://emplois-scolaires-monde.online" style="color:#5a8a3c;">emplois-scolaires-monde.online</a>
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

def get_brevo_contacts():
    url = f"https://api.brevo.com/v3/contacts/lists/{BREVO_LIST_ID}/contacts"
    headers = {"accept": "application/json", "api-key": BREVO_API_KEY}
    contacts = []
    offset = 0
    while True:
        r = requests.get(url, headers=headers, params={"limit": 500, "offset": offset})
        data = r.json()
        batch = data.get('contacts', [])
        if not batch:
            break
        contacts.extend(batch)
        offset += len(batch)
        if len(batch) < 500:
            break
    return contacts

def send_email(to_email, to_name, html_content, nb_offres):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY
    }
    subject = f"{nb_offres} nouveau{'x' if nb_offres > 1 else ''} poste{'s' if nb_offres > 1 else ''} : Postes Réseau Français"
    data = {
        "sender": {"name": "Postes Réseau Français", "email": "contact@emplois-scolaires-monde.online"},
        "to": [{"email": to_email, "name": to_name or "Abonné"}],
        "subject": subject,
        "htmlContent": html_content
    }
    data["htmlContent"] = html_content.replace("EMAIL_PLACEHOLDER", to_email)
    r = requests.post(url, json=data, headers=headers)
    print(f"Brevo response: {r.status_code} {r.text}")
    return r.status_code

def main():
    print("=== Alertes email ===")
    new_offers = get_new_offers()
    print(f"Nouvelles offres détectées : {len(new_offers)}")

    if not new_offers:
        print("Aucune nouvelle offre, pas d'email envoyé.")
        return

    html = build_email_html(new_offers)
    contacts = get_brevo_contacts()
    print(f"Abonnés à contacter : {len(contacts)}")

    sent = 0
    for contact in contacts:
        email  = contact.get('email', '')
        prenom = contact.get('attributes', {}).get('PRENOM', '')
        if email:
            status = send_email(email, prenom, html, len(new_offers))
            if status in [200, 201]:
                sent += 1
                print(f"  ✓ {email}")
            else:
                print(f"  ✗ {email} (status {status})")

    print(f"Emails envoyés : {sent}/{len(contacts)}")

    # Sauvegarder les offres actuelles comme référence pour demain
    current_aefe = load_offers('emplois.json')
    current_mlf  = load_offers('emplois_mlf.json')
    all_current  = {**current_aefe, **current_mlf}
    with open('emplois_previous.json', 'w', encoding='utf-8') as f:
        json.dump({"offers": list(all_current.values())}, f, ensure_ascii=False)
    print("emplois_previous.json mis à jour ✓")

if __name__ == "__main__":
    main()
