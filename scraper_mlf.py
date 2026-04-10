#!/usr/bin/env python3
"""
Scraper MLF Monde — recrutement.mlfmonde.org
Génère emplois_mlf.json dans le même format que emplois.json (AEFE)
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

BASE_URL = "https://recrutement.mlfmonde.org"
LIST_URL = f"{BASE_URL}/espace-candidats-offres.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; xmath-academy-bot/1.0)"
}

def parse_date(date_str):
    """Convertit '25-08-2025' en '25/08/2025'"""
    if not date_str:
        return ""
    return date_str.replace("-", "/")

def extract_pays_ville(localisation):
    """
    Extrait pays et ville depuis 'Maroc / Casablanca'
    """
    if not localisation:
        return "", ""
    parts = localisation.split(" / ")
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return localisation.strip(), ""

def scrape_offres():
    print("🔄 Scraping MLF Monde...")

    try:
        resp = requests.get(LIST_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Trouver le tableau des offres
    rows = soup.select("table tr")
    if not rows:
        # Essai avec une autre sélection
        rows = soup.select("tr")

    offres = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue

        # Colonne 1 : lien + titre + numéro
        link_tag = cols[0].find("a")
        if not link_tag:
            continue

        titre = link_tag.get_text(strip=True)
        url = BASE_URL + "/" + link_tag.get("href", "").lstrip("/")

        # Numéro d'annonce et date de publication (dans le texte de la cellule)
        cell_text = cols[0].get_text(" ", strip=True)
        # Format : "Titre #XXXX DD-MM-YYYY"
        num_match = re.search(r'#(\d+)\s+(\d{2}-\d{2}-\d{4})', cell_text)
        annonce_id = int(num_match.group(1)) if num_match else 0
        date_pub = parse_date(num_match.group(2)) if num_match else ""

        # Colonne 2 : localisation "Pays / Ville"
        localisation = cols[1].get_text(strip=True)
        pays, ville = extract_pays_ville(localisation)

        # Colonne 3 : date limite + date de prise de fonction
        date_limite = ""
        date_prise = ""
        if len(cols) >= 3:
            dates_text = cols[2].get_text(" ", strip=True)
            dates = re.findall(r'\d{2}-\d{2}-\d{4}', dates_text)
            if len(dates) >= 1:
                date_limite = parse_date(dates[0])
            if len(dates) >= 2:
                date_prise = parse_date(dates[1])

        offre = {
            "id": annonce_id,
            "titre": titre,
            "etab": "",
            "ville": ville,
            "pays": pays,
            "contrat": "",          # MLF ne précise pas CDI/CDD dans la liste
            "discipline": "",       # Pas de discipline dans la liste MLF
            "date": date_pub,       # Date de publication
            "date_limite": date_limite,
            "date_prise": date_prise,
            "source": "MLF",        # ← champ supplémentaire pour différencier
            "url": url
        }

        offres.append(offre)
        print(f"  ✓ #{annonce_id} — {titre[:60]}...")

    return offres

def main():
    offres = scrape_offres()

    if not offres:
        print("⚠️ Aucune offre trouvée.")
        return

    output = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": len(offres),
        "source": "MLF Monde",
        "offers": offres
    }

    with open("emplois_mlf.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {len(offres)} offres MLF sauvegardées dans emplois_mlf.json")

if __name__ == "__main__":
    main()
