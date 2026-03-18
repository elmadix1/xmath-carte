#!/usr/bin/env python3
import json, time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

BASE = "https://talents.aefe.fr"

def make_driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--lang=fr-FR")
    return webdriver.Chrome(options=opts)

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
            ville = footer_items[0] if len(footer_items) > 0 else ""
            contrat = footer_items[1] if len(footer_items) > 1 else ""
            discipline = footer_items[2] if len(footer_items) > 2 else ""
            offers.append({"titre": titre, "etab": "", "ville": ville, "pays": "",
                           "contrat": contrat, "discipline": discipline, "date": "", "url": href})
        except:
            pass
    return offers

def scrape():
    driver = make_driver()
    all_offers = []
    page = 1
    try:
        print(f"Chargement {BASE}/fr/annonces ...")
        driver.get(f"{BASE}/fr/annonces")
        print("Attente chargement...")
        try:
            WebDriverWait(driver, 20).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "div.job-ad-card-wrapper")) > 0
            )
            print("  Cartes chargees")
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
            for btn in driver.find_elements(By.TAG_NAME, "button"):
                if btn.text.strip() in [">", "Suivant", "Next"] and btn.is_displayed() and btn.is_enabled():
                    next_btn = btn
                    break
            if not next_btn:
                for sel in ["button[aria-label*='uivant']", "button[aria-label*='ext']", ".pagination__next"]:
                    btns = [b for b in driver.find_elements(By.CSS_SELECTOR, sel) if b.is_displayed() and b.is_enabled()]
                    if btns:
                        next_btn = btns[0]
                        break
            if not next_btn:
                print("  Fin pagination")
                break
            driver.execute_script("arguments[0].click();", next_btn)
            page += 1
            if page > 30:
                break
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback; traceback.print_exc()
    finally:
        driver.quit()
    return all_offers

def main():
    print(f"=== Scraping talents.aefe.fr - {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    all_offers = scrape()
    print(f"Total: {len(all_offers)} offres")
    output = {"updated": datetime.now().strftime("%Y-%m-%d %H:%M"), "total": len(all_offers), "offers": all_offers}
    with open("emplois.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("Sauvegarde emplois.json")
    for o in all_offers[:5]:
        print(f"  - {o['titre']} ({o['ville']})")

if __name__ == "__main__":
    main()
