import requests
import os

BREVO_API_KEY = input("Colle ta clé Brevo ici : ").strip()

test_offers = [
    {"titre": "Professeur de mathématiques F/H", "pays": "Maroc", "ville": "Casablanca", "contrat": "Contrat permanent", "source": "AEFE", "url": "https://talents.aefe.fr"},
    {"titre": "Directeur du primaire F/H", "pays": "Émirats Arabes Unis", "ville": "Dubai", "contrat": "Contrat temporaire", "source": "MLF", "url": "https://recrutement.mlfmonde.org"},
    {"titre": "Infirmier scolaire F/H", "pays": "Tunisie", "ville": "Tunis", "contrat": "Contrat permanent", "source": "AEFE", "url": "https://talents.aefe.fr"},
]

rows = ""
for o in test_offers:
    source = o['source']
    color = '#1a56b0' if source == 'AEFE' else '#b01a1a'
    bg = '#e8f0fe' if source == 'AEFE' else '#fce8e8'
    loc = f"{o['ville']}, {o['pays']}"
    rows += f"""
    <tr>
      <td style="padding:14px 16px;border-bottom:1px solid #e8ede4;">
        <a href="{o['url']}" style="color:#1a1f16;text-decoration:none;font-weight:500;font-size:0.95rem;">{o['titre']}</a><br>
        <span style="font-size:0.82rem;color:#4a5240;">📍 {loc}</span>
        &nbsp;
        <span style="font-size:0.72rem;font-weight:700;padding:2px 7px;border-radius:4px;background:{bg};color:{color};">{source}</span>
      </td>
    </tr>"""

email = input("Ton email de test : ").strip()

html = f"""<!DOCTYPE html>
<html lang="fr">
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
          <td style="padding:28px 32px 16px;">
            <h1 style="margin:0 0 8px;font-size:1.2rem;color:#1a1f16;">3 nouveaux postes publiés</h1>
            <p style="margin:0;color:#4a5240;font-size:0.88rem;">Vous recevez cet email en avant-première car vous êtes abonné aux alertes.</p>
          </td>
        </tr>
        <tr>
          <td style="padding:0 32px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e8ede4;border-radius:8px;overflow:hidden;">
              {rows}
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 32px;text-align:center;">
            <a href="https://emplois-scolaires-monde.online/emplois.html" style="display:inline-block;background:#5a8a3c;color:#fff;text-decoration:none;padding:12px 32px;border-radius:8px;font-weight:600;font-size:0.95rem;">Voir toutes les offres →</a>
          </td>
        </tr>
        <tr>
          <td style="background:#f5f8f3;padding:16px 32px;border-top:1px solid #e8ede4;text-align:center;">
            <p style="margin:0;font-size:0.72rem;color:#aaa;">
              Vous recevez cet email car vous êtes abonné aux alertes emplois.<br>
              <a href="https://xmath-carte-production.up.railway.app/desabonnement?email={email}" style="color:#5a8a3c;">Se désabonner</a>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

data = {
    "sender": {"name": "Postes Réseau Français", "email": "contact@emplois-scolaires-monde.online"},
    "to": [{"email": email}],
    "subject": "3 nouveaux postes — Postes Réseau Français [TEST]",
    "htmlContent": html
}

r = requests.post(
    "https://api.brevo.com/v3/smtp/email",
    json=data,
    headers={"accept": "application/json", "content-type": "application/json", "api-key": BREVO_API_KEY}
)

if r.status_code in [200, 201]:
    print(f"✓ Email envoyé à {email}")
else:
    print(f"✗ Erreur {r.status_code} : {r.text}")
