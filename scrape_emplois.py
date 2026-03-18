#!/usr/bin/env python3
import json, time, re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

BASE = "https://talents.aefe.fr"

PAYS_NORM = {
    "MAROC": "Maroc", "TUNISIE": "Tunisie", "ALGERIE": "Algérie",
    "ALGÉRIE": "Algérie", "EGYPTE": "Égypte", "ÉGYPTE": "Égypte",
    "SENEGAL": "Sénégal", "SÉNÉGAL": "Sénégal",
    "COTE D'IVOIRE": "Côte d'Ivoire", "CÔTE D'IVOIRE": "Côte d'Ivoire",
    "COTE DIVOIRE": "Côte d'Ivoire", "CAMEROUN": "Cameroun",
    "GABON": "Gabon", "MADAGASCAR": "Madagascar", "KENYA": "Kenya",
    "TANZANIE": "Tanzanie", "ANGOLA": "Angola", "MOZAMBIQUE": "Mozambique",
    "AFRIQUE DU SUD": "Afrique du Sud", "NIGER": "Niger", "MALI": "Mali",
    "TCHAD": "Tchad", "BURKINA FASO": "Burkina Faso", "TOGO": "Togo",
    "BENIN": "Bénin", "BÉNIN": "Bénin", "GHANA": "Ghana", "NIGERIA": "Nigéria",
    "RWANDA": "Rwanda", "BURUNDI": "Burundi", "OUGANDA": "Ouganda",
    "ETHIOPIE": "Éthiopie", "ÉTHIOPIE": "Éthiopie", "DJIBOUTI": "Djibouti",
    "ZAMBIE": "Zambie", "ZIMBABWE": "Zimbabwe", "ILE MAURICE": "Île Maurice",
    "ÎLE MAURICE": "Île Maurice", "SEYCHELLES": "Seychelles",
    "COMORES": "Comores", "MAURITANIE": "Mauritanie", "GUINEE": "Guinée",
    "GUINÉE": "Guinée", "REP. CENTRAFRICAINE": "Rep. centrafricaine",
    "REPUBLIQUE DEMOCRATIQUE DU CONGO": "RD Congo", "RD CONGO": "RD Congo",
    "REPUBLIQUE DU CONGO": "Congo-Brazzaville", "CONGO-BRAZZAVILLE": "Congo-Brazzaville",
    "ESPAGNE": "Espagne", "ALLEMAGNE": "Allemagne", "ITALIE": "Italie",
    "PORTUGAL": "Portugal", "BELGIQUE": "Belgique", "PAYS-BAS": "Pays-Bas",
    "SUISSE": "Suisse", "LUXEMBOURG": "Luxembourg", "AUTRICHE": "Autriche",
    "POLOGNE": "Pologne", "HONGRIE": "Hongrie", "ROUMANIE": "Roumanie",
    "BULGARIE": "Bulgarie", "GRECE": "Grèce", "GRÈCE": "Grèce",
    "TURQUIE": "Turquie", "LIBAN": "Liban", "JORDANIE": "Jordanie",
    "ARABIE SAOUDITE": "Arabie Saoudite", "EMIRATS ARABES UNIS": "Émirats Arabes Unis",
    "ÉMIRATS ARABES UNIS": "Émirats Arabes Unis", "EAU": "Émirats Arabes Unis",
    "QATAR": "Qatar", "KOWEIT": "Koweït", "KOWEÏT": "Koweït",
    "BAHREIN": "Bahreïn", "BAHREÏN": "Bahreïn", "OMAN": "Oman",
    "ISRAEL": "Israël", "IRAN": "Iran", "IRAK": "Irak",
    "CHINE": "Chine", "JAPON": "Japon", "VIETNAM": "Vietnam",
    "CAMBODGE": "Cambodge", "THAILANDE": "Thaïlande", "THAÏLANDE": "Thaïlande",
    "INDONESIE": "Indonésie", "INDONÉSIE": "Indonésie",
    "SINGAPOUR": "Singapour", "MALAISIE": "Malaisie", "PHILIPPINES": "Philippines",
    "INDE": "Inde", "NEPAL": "Népal", "NÉPAL": "Népal",
    "BANGLADESH": "Bangladesh", "SRI LANKA": "Sri Lanka", "AUSTRALIE": "Australie",
    "COREE DU SUD": "Corée du Sud", "CORÉE DU SUD": "Corée du Sud",
    "TAIWAN": "Taiwan", "MONGOLIE": "Mongolie", "LAOS": "Laos",
    "MYANMAR": "Myanmar", "VANUATU": "Vanuatu",
    "ETATS UNIS": "États-Unis", "ETATS-UNIS": "États-Unis",
    "ÉTATS-UNIS": "États-Unis", "ÉTATS UNIS": "États-Unis",
    "CANADA": "Canada", "MEXIQUE": "Mexique", "BRESIL": "Brésil",
    "BRÉSIL": "Brésil", "ARGENTINE": "Argentine", "CHILI": "Chili",
    "COLOMBIE": "Colombie", "PEROU": "Pérou", "PÉROU": "Pérou",
    "BOLIVIE": "Bolivie", "EQUATEUR": "Équateur", "ÉQUATEUR": "Équateur",
    "URUGUAY": "Uruguay", "PARAGUAY": "Paraguay", "VENEZUELA": "Venezuela",
    "GUATEMALA": "Guatemala", "CUBA": "Cuba", "HAITI": "Haïti", "HAÏTI": "Haïti",
    "REPUBLIQUE DOMINICAINE": "Rép. dominicaine",
    "SALVADOR": "Salvador", "PANAMA": "Panama", "NICARAGUA": "Nicaragua",
    "HONDURAS": "Honduras", "COSTA RICA": "Costa Rica",
    "ALBANIE": "Albanie", "SERBIE": "Serbie", "CROATIE": "Croatie",
    "SLOVAQUIE": "Slovaquie", "RUSSIE": "Russie", "UKRAINE": "Ukraine",
    "GEORGIE": "Géorgie", "GÉORGIE": "Géorgie", "ARMENIE": "Arménie",
    "ARMÉNIE": "Arménie", "LITUANIE": "Lituanie", "LETTONIE": "Lettonie",
    "SUEDE": "Suède", "SUÈDE": "Suède", "NORVEGE": "Norvège", "NORVÈGE": "Norvège",
    "DANEMARK": "Danemark", "IRLANDE": "Irlande",
    "ROYAUME-UNI": "Royaume-Uni", "ROYAUME UNI": "Royaume-Uni",
    "CHYPRE": "Chypre", "MONTENEGRO": "Monténégro", "MONTÉNÉGRO": "Monténégro",
    "BOSNIE-HERZEGOVINE": "Bosnie-Herzégovine", "BOSNIE": "Bosnie-Herzégovine",
    "MACEDOINE": "Macédoine du Nord", "MACÉDOINE": "Macédoine du Nord",
    "KOSOVO": "Kosovo", "UZBEKISTAN": "Ouzbékistan", "OUZBEKISTAN": "Ouzbékistan",
    "KAZAKHSTAN": "Kazakhstan", "TURKMENISTAN": "Turkménistan",
    "SLOVENIE": "Slovénie", "SLOVÉNIE": "Slovénie",
    "FINLANDE": "Finlande", "MONACO": "Monaco",
}

def extract_pays(titre):
    titre_up = titre.upper()
    for pays_key in sorted(PAYS_NORM.keys(), key=len, reverse=True):
        if pays_key in titre_up:
            return PAYS_NORM[pays_key]
    return ""

def extract_id(url):
    m = re.search(r'/annonce/(\d+)-', url)
    return int(m.group(1)) if m else 0

def make_driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--lang=fr-FR")
    return webdriver.Chrome(options=opts)

def get_date_publication(driver, url):
    """Visite la page de l'offre et extrait la date dans <p class="html-block__published-at-text">"""
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "p.html-block__published-at-text")) > 0
                      or len(d.find_elements(By.CSS_SELECTOR, "h1")) > 0
        )
        elems = driver.find_elements(By.CSS_SELECTOR, "p.html-block__published-at-text")
        if elems:
            texte = elems[0].text.strip()  # ex: "Publiée le 01/02/2026"
            m = re.search(r'(\d{2}/\d{2}/\d{4})', texte)
            if m:
                return m.group(1)  # "01/02/2026"
    except:
        pass
    return ""

def parse_cards(driver):
    offers = []
    seen = set()
    cards = driver.find_elements(By.CSS_SELECTOR, "div.job-ad-card-wrapper")
    for card in cards:
        try:
            a = card.find_element(By.CSS_SELECTOR, "a.job-ad-card__link")
            href = a.get_attribute("href") or ""
            if not href or href in seen:
                continue
            seen.add(href)
            try:
                titre = card.find_element(By.CSS_SELECTOR, "h4.job-ad-card__description-title").text.strip()
            except:
                titre = a.text.strip() or "Poste"
            footer_items = [li.text.strip() for li in card.find_elements(By.CSS_SELECTOR, "ul.job-ad-card__description__footer li") if li.text.strip()]
            ville      = footer_items[0] if len(footer_items) > 0 else ""
            contrat    = footer_items[1] if len(footer_items) > 1 else ""
            discipline = footer_items[2] if len(footer_items) > 2 else ""
            pays     = extract_pays(titre)
            id_offre = extract_id(href)
            offers.append({
                "id": id_offre,
                "titre": titre,
                "etab": "",
                "ville": ville,
                "pays": pays,
                "contrat": contrat,
                "discipline": discipline,
                "date": "",
                "url": href
            })
        except:
            pass
    return offers

def scrape():
    driver = make_driver()
    all_offers = []
    page = 1
    try:
        # ── Phase 1 : récupérer toutes les cards ──
        print(f"Chargement {BASE}/fr/annonces ...")
        driver.get(f"{BASE}/fr/annonces")
        try:
            WebDriverWait(driver, 20).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "div.job-ad-card-wrapper")) > 0
            )
            print("  Cartes chargées")
        except:
            print("  Timeout")

        while True:
            time.sleep(2)
            cards = parse_cards(driver)
            new = [c for c in cards if c["url"] not in {o["url"] for o in all_offers}]
            all_offers.extend(new)
            print(f"  Page {page}: +{len(new)} offres (total: {len(all_offers)})")
            if not new:
                break
            next_btn = None
            btns = driver.find_elements(By.CSS_SELECTOR, "button.pagination__controls")
            for btn in btns:
                try:
                    if btn.find_elements(By.CSS_SELECTOR, "span[data-icon-type='chevron_right']"):
                        if btn.is_displayed() and btn.is_enabled() and btn.get_attribute("disabled") is None:
                            next_btn = btn
                            break
                except:
                    pass
            if not next_btn:
                print("  Fin pagination")
                break
            driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", next_btn)
            page += 1
            if page > 2:  # TEST - remettre 40 pour la prod
                break

        # ── Phase 2 : visiter chaque offre pour la date ──
        print(f"\nRécupération des dates pour {len(all_offers)} offres...")
        for i, offer in enumerate(all_offers):
            offer["date"] = get_date_publication(driver, offer["url"])
            if (i + 1) % 50 == 0:
                print(f"  {i+1}/{len(all_offers)} dates récupérées...")
            time.sleep(0.5)
        print("  Toutes les dates récupérées.")

    except Exception as e:
        print(f"Erreur: {e}")
        import traceback; traceback.print_exc()
    finally:
        driver.quit()

    # Trier par ID décroissant (plus récent en premier)
    all_offers.sort(key=lambda o: o.get("id", 0), reverse=True)
    return all_offers

def main():
    print(f"=== Scraping talents.aefe.fr - {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    all_offers = scrape()
    print(f"Total: {len(all_offers)} offres")

    sans_date = sum(1 for o in all_offers if not o["date"])
    sans_pays = sum(1 for o in all_offers if not o["pays"])
    print(f"Sans date: {sans_date} | Sans pays: {sans_pays}")

    output = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": len(all_offers),
        "offers": all_offers
    }
    with open("emplois.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("Sauvegarde emplois.json")
    for o in all_offers[:5]:
        print(f"  - {o['titre']} ({o['ville']}) [{o['pays']}] — {o['date']}")

if __name__ == "__main__":
    main()
