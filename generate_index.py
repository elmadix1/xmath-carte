#!/usr/bin/env python3
"""
generate_index.py — Régénère index.html avec les données fraîches de etablissements.json
"""
import json, re

PAYS_MAP = {
    "ALBANIE": "Albania", "ALGÉRIE": "Algeria", "ANGOLA": "Angola",
    "ARABIE SAOUDITE": "Saudi Arabia", "ARGENTINE": "Argentina",
    "ARMÉNIE": "Armenia", "AUSTRALIE": "Australia", "AUTRICHE": "Austria",
    "BAHREÏN": "Bahrain", "BANGLADESH": "Bangladesh", "BELGIQUE": "Belgium",
    "BÉNIN": "Benin", "BIRMANIE (MYANMAR)": "Myanmar", "BOLIVIE": "Bolivia",
    "BOSNIE-HERZÉGOVINE": "Bosnia and Herzegovina", "BRÉSIL": "Brazil",
    "BULGARIE": "Bulgaria", "BURKINA FASO": "Burkina Faso", "BURUNDI": "Burundi",
    "CAMBODGE": "Cambodia", "CAMEROUN": "Cameroon", "CANADA": "Canada",
    "CAP-VERT": "Cape Verde", "CHILI": "Chile", "CHINE": "China",
    "CHYPRE": "Cyprus", "COLOMBIE": "Colombia", "COMORES": "Comoros",
    "CONGO": "Republic of the Congo", "CORÉE DU SUD": "South Korea",
    "COSTA RICA": "Costa Rica", "CÔTE D'IVOIRE": "Ivory Coast",
    "CROATIE": "Croatia", "CUBA": "Cuba", "DANEMARK": "Denmark",
    "DJIBOUTI": "Djibouti", "ÉGYPTE": "Egypt", "ÉMIRATS ARABES UNIS": "United Arab Emirates",
    "ÉQUATEUR": "Ecuador", "ESPAGNE": "Spain", "ESTONIE": "Estonia",
    "ÉTATS-UNIS": "United States of America", "ÉTHIOPIE": "Ethiopia",
    "FINLANDE": "Finland", "GABON": "Gabon", "GAMBIE": "Gambia",
    "GÉORGIE": "Georgia", "GHANA": "Ghana", "GRÈCE": "Greece",
    "GUATEMALA": "Guatemala", "GUINÉE": "Guinea", "GUINÉE ÉQUATORIALE": "Equatorial Guinea",
    "GUINÉE-BISSAU": "Guinea-Bissau", "HAÏTI": "Haiti", "HONDURAS": "Honduras",
    "HONGRIE": "Hungary", "INDE": "India", "INDONÉSIE": "Indonesia",
    "IRAK": "Iraq", "IRAN": "Iran", "IRLANDE": "Ireland", "ISRAËL": "Israel",
    "ITALIE": "Italy", "JAPON": "Japan", "JÉRUSALEM": "Israel",
    "JORDANIE": "Jordan", "KAZAKHSTAN": "Kazakhstan", "KENYA": "Kenya",
    "KOSOVO": "Kosovo", "KOWEÏT": "Kuwait", "LAOS": "Laos",
    "LIBAN": "Lebanon", "LITUANIE": "Lithuania", "LETTONIE": "Latvia",
    "LUXEMBOURG": "Luxembourg", "MACÉDOINE DU NORD": "Macedonia",
    "MADAGASCAR": "Madagascar", "MALAISIE": "Malaysia", "MALI": "Mali",
    "MAROC": "Morocco", "MAURITANIE": "Mauritania", "MAURICE": "Mauritius",
    "MEXIQUE": "Mexico", "MONACO": "Monaco", "MONGOLIE": "Mongolia",
    "MONTÉNÉGRO": "Montenegro", "MOZAMBIQUE": "Mozambique",
    "NÉPAL": "Nepal", "NICARAGUA": "Nicaragua", "NIGER": "Niger",
    "NIGÉRIA": "Nigeria", "NORVÈGE": "Norway", "OMAN": "Oman",
    "OUGANDA": "Uganda", "OUZBÉKISTAN": "Uzbekistan",
    "PAKISTAN": "Pakistan", "PALESTINE": "Palestine", "PANAMA": "Panama",
    "PARAGUAY": "Paraguay", "PAYS-BAS": "Netherlands", "PÉROU": "Peru",
    "PHILIPPINES": "Philippines", "POLOGNE": "Poland", "PORTUGAL": "Portugal",
    "QATAR": "Qatar", "RÉPUBLIQUE CENTRAFRICAINE": "Central African Republic",
    "RÉPUBLIQUE DÉMOCRATIQUE DU CONGO": "Democratic Republic of the Congo",
    "RÉPUBLIQUE DOMINICAINE": "Dominican Republic", "RÉPUBLIQUE TCHÈQUE": "Czech Republic",
    "ROUMANIE": "Romania", "ROYAUME-UNI": "United Kingdom", "RUSSIE": "Russia",
    "RWANDA": "Rwanda", "SALVADOR": "El Salvador", "SÉNÉGAL": "Senegal",
    "SERBIE": "Serbia", "SEYCHELLES": "Seychelles", "SINGAPOUR": "Singapore",
    "SLOVAQUIE": "Slovakia", "SLOVÉNIE": "Slovenia", "SRI LANKA": "Sri Lanka",
    "SUÈDE": "Sweden", "SUISSE": "Switzerland", "TAIWAN": "Taiwan",
    "TANZANIE": "Tanzania", "TCHAD": "Chad", "THAÏLANDE": "Thailand",
    "TOGO": "Togo", "TUNISIE": "Tunisia", "TURKMÉNISTAN": "Turkmenistan",
    "TURQUIE": "Turkey", "UKRAINE": "Ukraine", "URUGUAY": "Uruguay",
    "VANUATU": "Vanuatu", "VÉNÉZUÉLA": "Venezuela", "VIETNAM": "Vietnam",
    "ZAMBIE": "Zambia", "ZIMBABWE": "Zimbabwe",
    "ALLEMAGNE": "Germany", "AFRIQUE DU SUD": "South Africa",
    "AMPEFILOHA": "Madagascar",
}

def main():
    # Charger les données
    with open('etablissements.json', encoding='utf-8') as f:
        data = json.load(f)
    with open('pays_info.json', encoding='utf-8') as f:
        pays_info = json.load(f)

    # Construire la nouvelle DB
    new_db = {}
    for country_key, info in pays_info.items():
        new_db[country_key] = {
            "zone": info["zone"], "nom": info["nom"], "acad": info["acad"],
            "centre": info["centre"], "sujet": info["sujet"],
            "date": info["date"], "pack": info["pack"], "etabs": []
        }

    for e in data['etablissements']:
        pays_fr = e.get('pays', '').upper()
        country_key = PAYS_MAP.get(pays_fr)
        if not country_key or country_key not in new_db:
            continue
        coords = e.get('coords')
        if not coords:
            continue
        etab = {
            "n": e.get('nom', ''),
            "v": e.get('ville', '').title(),
            "s": e.get('statut', 'Part'),
            "w": e.get('site', ''),
            "aefe": e.get('url_aefe', ''),
            "brevet": e.get('brevet', False),
            "bac": e.get('bac', False),
            "c": [round(coords[0], 5), round(coords[1], 5)]
        }
        new_db[country_key]["etabs"].append(etab)

    # Générer le JS de la DB
    db_js = "const DB={\n"
    for key, val in new_db.items():
        etabs_json = json.dumps(val["etabs"], ensure_ascii=False, separators=(',', ':'))
        db_js += f'"{key}":{{'
        db_js += f'zone:"{val["zone"]}",'
        db_js += f'nom:"{val["nom"]}",'
        db_js += f'acad:"{val["acad"]}",'
        db_js += f'centre:"{val["centre"]}",'
        db_js += f'sujet:"{val["sujet"]}",'
        db_js += f'date:"{val["date"]}",'
        db_js += f'pack:"{val["pack"]}",'
        db_js += f'etabs:{etabs_json}}},'
        db_js += "\n"
    db_js = db_js.rstrip(",\n") + "\n};"

    # Lire index.html.backup
    with open('index.html.backup', encoding='utf-8') as f:
        content = f.read()

    # Remplacer la DB
    start = content.find('const DB={')
    end = content.find('\nconst SPECIFICITES=')
    if start == -1 or end == -1:
        print(f"ERREUR: DB non trouvée start={start} end={end}")
        return

    new_content = content[:start] + db_js + content[end:]

    # Corriger le loader
    new_content = new_content.replace(
        "document.getElementById('loader').remove();",
        "var _l=document.getElementById('loader');if(_l)_l.remove();")
    new_content = new_content.replace(
        ".catch(function(){document.getElementById('loader').textContent='Erreur de chargement — vérifiez votre connexion.';})",
        ".catch(function(){var l=document.getElementById('loader');if(l)l.textContent='Erreur de chargement — vérifiez votre connexion.';})")

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)

    total = sum(len(v["etabs"]) for v in new_db.values())
    print(f"index.html généré ✓ — {total} établissements dans {len([v for v in new_db.values() if v['etabs']])} pays")

if __name__ == "__main__":
    main()
