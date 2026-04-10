#!/usr/bin/env python3
"""
Scraper MLF Monde — recrutement.mlfmonde.org
Génère emplois_mlf.json dans le même format que emplois.json (AEFE)
Met également à jour sitemap.xml avec la date du jour
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
    """Extrait pays et ville depuis 'Maroc / Casablanca'"""
    if not localisation:
        return "", ""
    parts = localisation.split(" / ")
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return localisation.strip(), ""

def scrape_offres():
    print("Scraping MLF Monde...")
    try:
        resp = requests.get(LIST_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"Erreur de connexion : {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.select("table tr")
    if not rows:
        rows = soup.select("tr")

    offres = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue
        link_tag = cols[0].find("a")
        if not link_tag:
            continue
        titre = link_tag.get_text(strip=True)
        url = BASE_URL + "/" + link_tag.get("href", "").lstrip("/")
        cell_text = cols[0].get_text(" ", strip=True)
        num_match = re.search(r'#(\d+)\s+(\d{2}-\d{2}-\d{4})', cell_text)
        annonce_id = int(num_match.group(1)) if num_match else 0
        date_pub = parse_date(num_match.group(2)) if num_match else ""
        localisation = cols[1].get_text(strip=True)
        pays, ville = extract_pays_ville(localisation)
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
            "contrat": "",
            "discipline": "",
            "date": date_pub,
            "date_limite": date_limite,
            "date_prise": date_prise,
            "source": "MLF",
            "url": url
        }
        offres.append(offre)
        print(f"  #{annonce_id} - {titre[:60]}...")
    return offres

def update_sitemap():
    """Met a jour sitemap.xml avec la date du jour"""
    today = datetime.now().strftime("%Y-%m-%d")
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

  <url>
    <loc>https://emplois-scolaires-monde.online/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>

  <url>
    <loc>https://emplois-scolaires-monde.online/emplois.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>

</urlset>
"""
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap)
    print(f"sitemap.xml mis a jour ({today})")

def main():
    offres = scrape_offres()
    if not offres:
        print("Aucune offre trouvee.")
        return
    output = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": len(offres),
        "source": "MLF Monde",
        "offers": offres
    }
    with open("emplois_mlf.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n{len(offres)} offres MLF sauvegardees dans emplois_mlf.json")
    update_sitemap()

if __name__ == "__main__":
    main()
