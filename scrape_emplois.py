#!/usr/bin/env python3
"""
Scraper talents.aefe.fr → emplois.json
Utilise Selenium headless pour exécuter le JavaScript du site
"""
import json, time, re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://talents.aefe.fr/fr/annonces"

def make_driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--lang=fr-FR")
    opts.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=opts)

def extract_json_from_page(driver):
    try:
        result = driver.execute_script("""
            const sources = [window.__NUXT__, window.__DATA__, window.__STATE__, window.__INITIAL_STATE__];
            for (const src of sources) {
                if (!src) continue;
                const str = JSON.stringify(src);
                const m = str.match(/"offers":\s*(\[.{10,}\])/);
                if (m) { try { return JSON.parse(m[1]); } catch(e) {} }
            }
            // Chercher dans tous les scripts inline
            for (const s of document.querySelectorAll('script:not([src])')) {
                const m = s.textContent.match(/"offers":\s*(\[.{10,}\])/);
                if (m) { try { const d = JSON.parse(m[1]); if (d.length > 0) return d; } catch(e) {} }
            }
            return null;
        """)
        if result and isinstance(result, list) and len(result) > 0:
            print(f"  JSON JS: {len(result)} offres")
            return result
    except Exception as e:
        print(f"  JS extract err: {e}")
    return None

def parse_cards(driver):
    offers = []
    selectors = [
        "article", ".offer", "[class*='offer-card']", "[class*='OfferCard']",
        "[class*='job-card']", "[class*='annonce']", "[data-offer]"
    ]
    cards = []
    for sel in selectors:
        try:
            found = driver.find_elements(By.CSS_SELECTOR, sel)
            if found:
                cards = found
                print(f"  Sélecteur '{sel}': {len(found)} éléments")
                break
        except:
            pass

    for card in cards:
        try:
            text = card.text.strip()
            if not text or len(text) < 5:
                continue
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            titre = lines[0] if lines else "Poste"
            etab  = lines[1] if len(lines) > 1 else ""
            ville, pays, contrat = "", "", ""
            for line in lines[2:]:
                if ',' in line or '·' in line:
                    parts = re.split(r'[,·]', line)
                    ville = parts[0].strip()
                    if len(parts) > 1: pays = parts[-1].strip()
                if any(w in line.lower() for w in ['cdi','cdd','permanent','temporaire']):
                    contrat = line
            url = BASE_URL
            try:
                a = card.find_element(By.TAG_NAME, "a")
                href = a.get_attribute("href")
                if href: url = href
            except:
                pass
            offers.append({"titre": titre, "etab": etab, "ville": ville,
                           "pays": pays, "contrat": contrat, "date": "", "url": url})
        except:
            pass
    return offers

def load_more(driver, max_clicks=30):
    for i in range(max_clicks):
        clicked = False
        try:
            btns = driver.find_elements(By.TAG_NAME, "button")
            for btn in btns:
                if btn.is_displayed() and btn.is_enabled():
                    txt = btn.text.lower()
                    if any(w in txt for w in ['voir plus', 'load more', 'charger', 'afficher plus', 'suivant', 'more']):
                        driver.execute_script("arguments[0].scrollIntoView();", btn)
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(2)
                        clicked = True
                        print(f"  Clic '{btn.text}' ({i+1})")
                        break
        except:
            pass
        if not clicked:
            break

def normalize(raw):
    if not isinstance(raw, dict):
        return None
    uid = raw.get("id") or raw.get("uid") or ""
    slug = raw.get("slug") or ""
    if slug and slug.startswith("http"):
        url = slug
    elif uid:
        url = f"https://talents.aefe.fr/fr/annonce/{uid}-{slug}" if slug else f"https://talents.aefe.fr/fr/annonce/{uid}"
    else:
        url = "https://talents.aefe.fr/fr/annonces"
    return {
        "titre":   raw.get("title") or raw.get("label") or raw.get("name") or "Poste",
        "etab":    raw.get("company") or raw.get("establishment") or raw.get("employer") or "",
        "ville":   raw.get("city") or raw.get("location") or "",
        "pays":    raw.get("country") or raw.get("countryName") or "",
        "contrat": raw.get("contract_type") or raw.get("contractType") or raw.get("type") or "",
        "date":    str(raw.get("publication_date") or raw.get("publishedAt") or "")[:10],
        "url":     url
    }

def main():
    print(f"=== Scraping talents.aefe.fr — {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    all_offers = []
    driver = None
    try:
        driver = make_driver()
        print(f"Chargement {BASE_URL}...")
        driver.get(BASE_URL)
        time.sleep(5)

        # 1. JSON dans variables JS
        json_offers = extract_json_from_page(driver)
        if json_offers:
            all_offers = [o for o in [normalize(r) for r in json_offers] if o]

        # 2. Charger toutes les pages puis parser les cartes
        if not all_offers:
            load_more(driver)
            time.sleep(2)
            all_offers = parse_cards(driver)

    except Exception as e:
        print(f"Erreur: {e}")
        import traceback; traceback.print_exc()
    finally:
        if driver:
            driver.quit()

    print(f"\n✅ Total: {len(all_offers)} offres")
    output = {"updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
              "total": len(all_offers), "offers": all_offers}
    with open("emplois.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("💾 emplois.json sauvegardé")
    if all_offers:
        for o in all_offers[:5]:
            print(f"  • {o['titre']} — {o['etab']} ({o['ville']}, {o['pays']})")

if __name__ == "__main__":
    main()
