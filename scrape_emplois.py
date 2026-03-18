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
            # Bouton suivant : button.pagination__controls avec chevron_right
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
            if page > 40:
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
