#!/usr/bin/env python3
"""
scrape_etabs.py — Scrape tous les établissements AEFE depuis aefe.gouv.fr
Produit : etablissements.json

Phase 1 : liste des URLs depuis /fr/etablissements (pagination Selenium)
Phase 2 : visite chaque fiche en parallèle (5 workers) pour extraire :
          nom, ville, pays, statut, site web, brevet, bac, niveaux, adresse
Phase 3 : géocodage via Nominatim (OpenStreetMap, gratuit, sans clé API)
"""

import json, time, re, requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

BASE = "https://aefe.gouv.fr"
NOMINATIM = "https://nominatim.openstreetmap.org/search"

def make_driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--lang=fr-FR")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)

# ── PHASE 1 : récupérer toutes les URLs d'établissements ──────────────────────

def get_all_etab_urls():
    """Scrape la liste paginée des établissements et retourne leurs URLs."""
    driver = make_driver()
    urls = []
    seen = set()
    page = 1

    try:
        print(f"Chargement de la liste des établissements...")
        driver.get(f"{BASE}/fr/etablissements")

        # Attendre que les cards apparaissent
        try:
            WebDriverWait(driver, 20).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "article.node--type-etablissement, div.views-row, h3.node__title a, .etablissement-card")) > 0
            )
        except:
            pass

        # Cliquer sur "Tout" pour afficher tous les résultats d'un coup
        try:
            tout_btn = driver.find_element(By.XPATH, "//a[text()='Tout'] | //button[text()='Tout']")
            driver.execute_script("arguments[0].click();", tout_btn)
            time.sleep(3)
            print("  Affichage 'Tout' activé")
        except:
            print("  Bouton 'Tout' non trouvé, pagination manuelle")

        while True:
            time.sleep(2)

            # Chercher tous les liens vers des fiches d'établissements
            links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/fr/etablissements/']")
            new_count = 0
            for link in links:
                href = link.get_attribute("href") or ""
                # Filtrer : seulement les fiches (pas la page liste elle-même)
                if (href and
                    "/fr/etablissements/" in href and
                    href != f"{BASE}/fr/etablissements" and
                    not href.endswith("/fr/etablissements") and
                    "?" not in href and
                    href not in seen):
                    seen.add(href)
                    urls.append(href)
                    new_count += 1

            print(f"  Page {page}: +{new_count} URLs (total: {len(urls)})")

            # Chercher le bouton "page suivante"
            next_btn = None
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, "li.pager__item--next a, a[rel='next'], .pager-next a")
                if not next_btn.is_displayed():
                    next_btn = None
            except:
                pass

            if not next_btn or new_count == 0:
                print("  Fin de la liste")
                break

            driver.execute_script("arguments[0].click();", next_btn)
            page += 1
            if page > 50:
                break

    except Exception as e:
        print(f"Erreur phase 1: {e}")
        import traceback; traceback.print_exc()
    finally:
        driver.quit()

    return list(set(urls))  # dédoublonner


# ── PHASE 2 : scraper chaque fiche ───────────────────────────────────────────

def scrape_fiche(url):
    """Visite une fiche d'établissement et extrait toutes les infos."""
    driver = make_driver()
    result = {
        "url_aefe": url,
        "nom": "",
        "ville": "",
        "pays": "",
        "statut": "",   # EGD, Conv, Part
        "site": "",
        "adresse": "",
        "telephone": "",
        "email": "",
        "brevet": False,
        "bac": False,
        "niveaux": [],
        "nb_eleves": "",
    }
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "h1")) > 0
        )
        time.sleep(1)

        # Nom
        try:
            result["nom"] = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
        except: pass

        # Ville + Pays (sous le h1)
        try:
            loc = driver.find_element(By.CSS_SELECTOR, "h1 + p, .field--name-field-ville, .localisation-etablissement").text.strip()
            parts = [p.strip() for p in loc.split(",")]
            if len(parts) >= 2:
                result["ville"] = parts[0]
                result["pays"] = parts[-1]
            elif len(parts) == 1:
                result["ville"] = parts[0]
        except:
            # Essai alternatif
            try:
                page_text = driver.find_element(By.CSS_SELECTOR, ".node__content, main").text
                m = re.search(r'\n([^\n,]+)\s*,\s*([^\n]+)\n', page_text)
                if m:
                    result["ville"] = m.group(1).strip()
                    result["pays"] = m.group(2).strip()
            except: pass

        # Statut — logo EGD/Conv/Part
        try:
            img = driver.find_element(By.CSS_SELECTOR, "img[src*='logo_egd'], img[src*='logo_conv'], img[src*='logo_part'], img[alt*='egd'], img[alt*='conv'], img[alt*='part']")
            src = img.get_attribute("src") or img.get_attribute("alt") or ""
            if "egd" in src.lower():
                result["statut"] = "EGD"
            elif "conv" in src.lower():
                result["statut"] = "Conv"
            else:
                result["statut"] = "Part"
        except:
            result["statut"] = "Part"

        # Nombre d'élèves
        try:
            nb = driver.find_element(By.CSS_SELECTOR, ".field--name-field-nombre-eleves, .nb-eleves").text.strip()
            result["nb_eleves"] = nb
        except: pass

        # Niveaux + brevet + bac
        try:
            rows = driver.find_elements(By.CSS_SELECTOR, "table tr, .niveau-row")
            niveaux = []
            for row in rows:
                cells = row.find_elements(By.CSS_SELECTOR, "td")
                if len(cells) >= 2:
                    niveau = cells[0].text.strip()
                    homologue = cells[1].text.strip().lower()
                    if niveau and "oui" in homologue:
                        niveaux.append(niveau)
                        if niveau.lower() == "troisième":
                            result["brevet"] = True
                        if niveau.lower() == "terminale":
                            result["bac"] = True
            result["niveaux"] = niveaux
        except: pass

        # Site web
        try:
            site_links = driver.find_elements(By.CSS_SELECTOR, "a[href^='http']")
            for link in site_links:
                href = link.get_attribute("href") or ""
                if ("aefe.gouv.fr" not in href and
                    "facebook" not in href and
                    "twitter" not in href and
                    "linkedin" not in href and
                    "bsky.app" not in href and
                    "instagram" not in href and
                    "youtube" not in href and
                    "legifrance" not in href and
                    "gouvernement" not in href and
                    "service-public" not in href and
                    "data.gouv" not in href and
                    len(href) > 10):
                    result["site"] = href
                    break
        except: pass

        # Adresse
        try:
            adresse_el = driver.find_element(By.XPATH, "//*[contains(text(),'Adresse')]/following-sibling::*[1] | //*[contains(@class,'adresse')]")
            result["adresse"] = adresse_el.text.strip()
        except: pass

        # Téléphone
        try:
            tel_el = driver.find_element(By.XPATH, "//*[contains(text(),'Contact')]/following-sibling::*[1]")
            text = tel_el.text.strip()
            m = re.search(r'[\d\s\+\-\.]{8,}', text)
            if m:
                result["telephone"] = m.group(0).strip()
        except: pass

        # Email
        try:
            email_link = driver.find_element(By.CSS_SELECTOR, "a[href^='mailto:']")
            result["email"] = email_link.get_attribute("href").replace("mailto:", "")
        except: pass

    except Exception as e:
        print(f"  Erreur sur {url}: {e}")
    finally:
        driver.quit()

    return result


def scrape_all_fiches_parallel(urls, workers=15):
    """Phase 2 : visite toutes les fiches en parallèle."""
    print(f"\nScraping de {len(urls)} fiches en parallèle ({workers} workers)...")
    results = []
    completed = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_url = {executor.submit(scrape_fiche, url): url for url in urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                data = future.result()
                results.append(data)
            except Exception as e:
                print(f"  Échec {url}: {e}")
                results.append({"url_aefe": url, "nom": "", "statut": "Part"})
            completed += 1
            if completed % 50 == 0:
                print(f"  {completed}/{len(urls)} fiches traitées...")

    print("  Toutes les fiches traitées.")
    return results


# ── PHASE 3 : géocodage via Nominatim (OpenStreetMap, gratuit) ───────────────

def geocode(nom, ville, pays):
    """Retourne [lon, lat] ou None via Nominatim."""
    headers = {"User-Agent": "xmath-academy-scraper/1.0 (contact@xmath.academy)"}
    queries = [
        f"{nom}, {ville}, {pays}",
        f"{ville}, {pays}",
        f"{pays}",
    ]
    for q in queries:
        try:
            r = requests.get(NOMINATIM, params={"q": q, "format": "json", "limit": 1}, headers=headers, timeout=5)
            data = r.json()
            if data:
                return [float(data[0]["lon"]), float(data[0]["lat"])]
        except: pass
        time.sleep(1)  # Respecter la limite Nominatim (1 req/sec)
    return None

def geocode_all(etabs):
    """Phase 3 : géocode tous les établissements sans coordonnées."""
    print(f"\nGéocodage de {len(etabs)} établissements...")
    for i, e in enumerate(etabs):
        if not e.get("coords"):
            coords = geocode(e.get("nom",""), e.get("ville",""), e.get("pays",""))
            e["coords"] = coords
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(etabs)} géocodés...")
    print("  Géocodage terminé.")
    return etabs


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    start = datetime.now()
    print(f"=== Scraping établissements AEFE - {start.strftime('%Y-%m-%d %H:%M')} ===")

    # Phase 1 : liste des URLs (TEST : limité à 2 pages, retirer pour prod)
    urls = get_all_etab_urls()
    print(f"\nTotal URLs trouvées : {len(urls)}")

    # Commenter ces 2 lignes pour la prod
    # ────────────────────────────────────

    # Phase 2 : scraper les fiches en parallèle
    etabs = scrape_all_fiches_parallel(urls, workers=15)

    # Phase 3 : géocodage
    etabs = geocode_all(etabs)

    # Stats
    avec_brevet = sum(1 for e in etabs if e.get("brevet"))
    avec_bac    = sum(1 for e in etabs if e.get("bac"))
    avec_coords = sum(1 for e in etabs if e.get("coords"))
    duree = (datetime.now() - start).seconds // 60
    print(f"\nAvec Brevet: {avec_brevet} | Avec Bac: {avec_bac} | Avec GPS: {avec_coords}/{len(etabs)} | Durée: {duree} min")

    output = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": len(etabs),
        "etablissements": etabs
    }
    with open("etablissements.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("Sauvegarde etablissements.json ✓")

    for e in etabs[:3]:
        print(f"  - {e['nom']} | {e['ville']}, {e['pays']} | {e['statut']} | GPS:{e.get('coords')} | Brevet:{e['brevet']} Bac:{e['bac']}")

if __name__ == "__main__":
    main()
