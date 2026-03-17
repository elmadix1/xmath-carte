#!/usr/bin/env python3
"""
Scraper talents.aefe.fr → emplois.json
Tourne chaque nuit via GitHub Actions
"""
import requests, json, time, re
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer": "https://talents.aefe.fr/fr/annonces",
}

BASE_URL = "https://talents.aefe.fr"

def get_offers_page(page=1, per_page=50):
    """Essaie plusieurs endpoints connus de Digital Recruiters / Cegid HR"""
    endpoints = [
        f"{BASE_URL}/api/v1/offers?page={page}&limit={per_page}",
        f"{BASE_URL}/api/offers?page={page}&perPage={per_page}",
        f"{BASE_URL}/fr/annonces?page={page}&format=json",
        f"{BASE_URL}/api/v2/jobs?page={page}&size={per_page}",
    ]
    for url in endpoints:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                try:
                    data = r.json()
                    # Normaliser selon la structure retournée
                    offers = (data.get("offers") or data.get("data") or
                              data.get("results") or data.get("jobs") or [])
                    if isinstance(offers, list) and len(offers) > 0:
                        print(f"✓ API trouvée: {url} → {len(offers)} offres")
                        return offers, data
                except:
                    pass
        except Exception as e:
            print(f"  ✗ {url}: {e}")
    return [], {}

def scrape_html_offers():
    """Fallback: scraper le HTML de la page annonces"""
    offers = []
    try:
        r = requests.get(f"{BASE_URL}/fr/annonces", headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return offers
        html = r.text
        
        # Chercher les JSON embarqués dans le HTML (common avec SPA)
        # Pattern: __NUXT_DATA__ ou window.__data__ ou similar
        patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
            r'window\.__data__\s*=\s*({.*?});',
            r'"offers"\s*:\s*(\[.*?\])',
            r'"jobs"\s*:\s*(\[.*?\])',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    if isinstance(data, list):
                        offers = data
                    elif isinstance(data, dict):
                        offers = data.get("offers", data.get("jobs", []))
                    if offers:
                        print(f"✓ JSON trouvé dans HTML: {len(offers)} offres")
                        return offers
                except:
                    pass
    except Exception as e:
        print(f"✗ Scraping HTML: {e}")
    return offers

def normalize_offer(raw):
    """Normalise une offre brute en format standard"""
    if not isinstance(raw, dict):
        return None
    
    # Essayer différents champs selon la version de l'API
    titre = (raw.get("title") or raw.get("label") or raw.get("name") or
             raw.get("jobTitle") or "Poste à pourvoir")
    
    etab = (raw.get("company") or raw.get("establishment") or
            raw.get("employer") or raw.get("organization") or "")
    
    ville = (raw.get("city") or raw.get("location") or
             raw.get("place") or raw.get("address", {}).get("city", "") or "")
    
    pays = (raw.get("country") or raw.get("countryName") or
            raw.get("address", {}).get("country", "") or "")
    
    contrat = (raw.get("contract_type") or raw.get("contractType") or
               raw.get("type") or raw.get("employmentType") or "")
    
    date_pub = (raw.get("publication_date") or raw.get("publishedAt") or
                raw.get("date") or raw.get("createdAt") or "")
    
    url_id = raw.get("id") or raw.get("uid") or ""
    url_slug = raw.get("slug") or raw.get("url") or ""
    if url_slug and url_slug.startswith("http"):
        url = url_slug
    elif url_id:
        url = f"{BASE_URL}/fr/annonce/{url_id}-{url_slug}" if url_slug else f"{BASE_URL}/fr/annonce/{url_id}"
    else:
        url = f"{BASE_URL}/fr/annonces"
    
    # Disciplines / catégories
    discipline = (raw.get("category") or raw.get("discipline") or
                  raw.get("jobCategory") or raw.get("domain") or "")
    
    return {
        "titre": titre,
        "etab": etab,
        "ville": ville,
        "pays": pays,
        "contrat": contrat,
        "date": str(date_pub)[:10] if date_pub else "",
        "discipline": discipline,
        "url": url,
    }

def main():
    print(f"=== Scraping talents.aefe.fr — {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    
    all_offers = []
    
    # Tentative API paginée
    for page in range(1, 20):  # max 19 pages × 50 = 950 offres
        offers_raw, meta = get_offers_page(page=page)
        if not offers_raw:
            if page == 1:
                # API non accessible, essayer HTML
                print("API non disponible, tentative HTML...")
                offers_raw = scrape_html_offers()
                if offers_raw:
                    all_offers.extend([o for o in [normalize_offer(r) for r in offers_raw] if o])
            break
        
        normalized = [o for o in [normalize_offer(r) for r in offers_raw] if o]
        all_offers.extend(normalized)
        print(f"  Page {page}: {len(normalized)} offres (total: {len(all_offers)})")
        
        # Vérifier s'il y a encore des pages
        total = (meta.get("total") or meta.get("totalCount") or
                 meta.get("count") or meta.get("total_count") or 0)
        if total and len(all_offers) >= total:
            break
        if len(offers_raw) < 50:  # Dernière page
            break
        
        time.sleep(0.5)  # Respecter le serveur
    
    print(f"\n✅ Total offres récupérées: {len(all_offers)}")
    
    # Sauvegarder
    output = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": len(all_offers),
        "offers": all_offers
    }
    
    with open("emplois.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Sauvegardé dans emplois.json")
    
    # Aperçu
    if all_offers:
        print("\nAperçu des 5 premières offres:")
        for o in all_offers[:5]:
            print(f"  • {o['titre']} — {o['etab']} ({o['ville']}, {o['pays']})")
    else:
        print("⚠️  Aucune offre récupérée — emplois.json vide créé")

if __name__ == "__main__":
    main()
