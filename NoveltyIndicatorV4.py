import pandas as pd
import json
import os
import hashlib
import matplotlib.pyplot as plt
import seaborn as sns
import novelpy
import requests
import tqdm
import numpy as np
import csv

def get_openalex_data(query, num_results=3000):
    """
    Récupère des données OpenAlex selon un mot-clé (query) avec filtre de date,
    en paginant par pas de 15.
    Retourne la liste brute 'results' renvoyée par l'API.
    """
    base_url = "https://api.openalex.org/works"
    results = []
    per_page = 20
    
    # On peut éventuellement forcer le tri par nombre de citations dès l'API 
    # en ajoutant &sort=cited_by_count:desc dans l'URL.
    for offset in range(0, num_results, per_page):
        response = requests.get(
            f"{base_url}"
            f"?filter=title.search:{query},"
            f"from_publication_date:2007-01-01,"
            f"to_publication_date:2024-12-31"
            f"&sort=cited_by_count:desc"
            f"&per-page={per_page}"
            f"&page={offset // per_page + 1}"
        )
        if response.status_code == 200:
            data = response.json()['results']
            results.extend(data)
        else:
            print(f"Erreur : {response.status_code}")
            break
        if len(data) < per_page:
            break

    return results

def generate_int_id(string_id):
    """Génère un identifiant entier unique à partir d'une chaîne (string_id) via hashing."""
    return int(hashlib.sha256(string_id.encode('utf-8')).hexdigest(), 16) % (10**8)

def prepare_data_for_novelpy(data):
    """
    Prépare les données pour Novelpy en créant un dictionnaire contenant
    les champs essentiels, ainsi que la nouvelle colonne 'sdg_query_source'.
    """
    prepared_data = []

    for item in data:
        try:
            if 'id' not in item:
                print(f"Skipping item without id: {item}")
                continue

            year = item.get('publication_year', None)
            if year is None or not (2007 <= year <= 2024):
                # Si on souhaite vraiment ignorer les papiers hors 2007-2024
                print(f"Skipping item outside date range: {item.get('id', 'inconnu')}")
                continue

            authorships = item.get('authorships', [])
            authors = [author['author']['display_name'] for author in authorships]
            institutions = []
            for author in authorships:
                if 'institutions' in author:
                    for inst in author['institutions']:
                        institutions.append(inst.get('display_name', ''))

            # Extraction des variables supplémentaires avec prise en compte des exceptions
            keyword_analysis = item.get('keyword_analysis', 'Missing')
            collaborative_index = item.get('collaborative_index', 'Missing')
            license_info = item.get('license', 'Missing')
            journal_impact_factor = item.get('journal_impact_factor', 'Missing')
            citations_geographical = item.get('citations_geographical', 'Missing')
            page_count = item.get('page_count', 'Missing')
            publisher = item.get('host_venue', {}).get('publisher', 'Missing')
            apc_paid = item.get('apc_paid', 'Missing')
            open_access_status = item.get('open_access', {}).get('status', 'Missing')

            # ---- NOUVELLE COLONNE : on récupère la source du SDG ----
            sdg_query_source = item.get('sdg_query_source', 'Unknown')

            entry = {
                "PMID": generate_int_id(item['id']),
                "year": year,
                "type": item.get('type', ''),
                "num_citations": item.get('cited_by_count', 0),
                "num_authors": len(authorships),
                "authors": authors,
                "institutions": institutions,
                "c04_referencelist": [
                    {"item": generate_int_id(ref)} for ref in item.get('referenced_works', [])
                ],
                # Exemple d'affectation de trois concepts à subfield/field/domain
                "subfield": (item.get('concepts') or [{}])[0].get('display_name', ''),
                "field": (item.get('concepts') or [{}])[1].get('display_name', '')
                         if len(item.get('concepts') or []) > 1 else '',
                "domain": (item.get('concepts') or [{}])[2].get('display_name', '')
                          if len(item.get('concepts') or []) > 2 else '',

                # Champ SDG + la nouvelle colonne
                "sustainable_development_goals": item.get('sustainable_development_goals', []),
                "sdg_query_source": sdg_query_source,

                "keyword_analysis": keyword_analysis,
                "collaborative_index": collaborative_index,
                "license": license_info,
                "journal_impact_factor": journal_impact_factor,
                "citations_geographical": citations_geographical,
                "page_count": page_count,
                "publisher": publisher,
                "apc_paid": apc_paid,
                "open_access_status": open_access_status
            }

            prepared_data.append(entry)

        except KeyError as e:
            print(f"KeyError: {e} in item {item.get('id', 'unknown')}")
            continue

    return prepared_data

def save_data_by_year(prepared_data, base_dir='Data/docs/references_sample'):
    data_by_year = {}
    for item in prepared_data:
        year = item['year']
        if year not in data_by_year:
            data_by_year[year] = []
        data_by_year[year].append(item)
    
    os.makedirs(base_dir, exist_ok=True)
    for year, data in data_by_year.items():
        with open(os.path.join(base_dir, f"{year}.json"), 'w') as f:
            json.dump(data, f, indent=4)

def validate_data(prepared_data):
    all_ids = set(item['PMID'] for item in prepared_data)
    valid = True
    for item in prepared_data:
        for ref in item['c04_referencelist']:
            if ref['item'] not in all_ids:
                print(f"Reference {ref['item']} in document {item['PMID']} does not exist in the dataset.")
                valid = False
    return valid


# ---------------------------------------------------------------------
# NOUVELLE PARTIE : récupérer 60 articles les plus cités pour chaque SDG
# ---------------------------------------------------------------------
sdg_queries = [
    "No Poverty",                     # SDG1
    "Zero Hunger",                    # SDG2
    "Good Health and Well Being",     # SDG3
    "Quality Education",              # SDG4
    "Gender Equality",                # SDG5
    "Clean Water and Sanitation",     # SDG6
    "Affordable and Clean Energy",    # SDG7
    "Decent Work and Economic Growth",# SDG8
    "Industry Innovation and Infrastructure", # SDG9
    "Reduced Inequalities",           # SDG10
    "Sustainable Cities and Communities",      # SDG11
    "Responsible Consumption and Production",  # SDG12
    "Climate Action",                 # SDG13
    "Life Below Water",               # SDG14
    "Life On Land",                   # SDG15
    "Peace Justice and Strong Institutions"     # SDG16
]

all_sdg_data = []

# Pour chaque SDG, on récupère par exemple jusqu'à 300 articles via get_openalex_data
# triés par nombre de citations (desc). Puis on ne garde que les 60 premiers.
for sdg_query in sdg_queries:
    data_sdg = get_openalex_data(query=sdg_query, num_results=300)
    print(f"Récupération des articles pour: {sdg_query} -> {len(data_sdg)} articles récupérés")

    # Trier localement par le nombre de citations décroissant
    data_sdg_sorted = sorted(data_sdg, key=lambda x: x.get('cited_by_count', 0), reverse=True)

    # Ne prendre que les 60 premiers
    data_sdg_top60 = data_sdg_sorted[:60]

    # Ajouter l'info du SDG et la nouvelle clé 'sdg_query_source' dans chaque enregistrement
    for item in data_sdg_top60:
        item['sustainable_development_goals'] = [sdg_query]
        # >>> NOUVELLE COLONNE <<<
        item['sdg_query_source'] = sdg_query

    # Ajouter à la liste globale
    all_sdg_data.extend(data_sdg_top60)

print(f"Nombre total d'articles combinés : {len(all_sdg_data)}")

# On prépare ces articles pour Novelpy
prepared_data = prepare_data_for_novelpy(all_sdg_data)

# Optionnel : vous pouvez valider l'existence de toutes les références
valid = validate_data(prepared_data)
print(f"Toutes les références sont-elles valides ? {valid}")

# Sauvegarder par année
save_data_by_year(prepared_data)

# ---------------------------------------------------------------------
# Exemple de calcul de co-occurrence et Lee indicator via Novelpy
# ---------------------------------------------------------------------
ref_cooc = novelpy.utils.cooc_utils.create_cooc(
    collection_name="references_sample",
    year_var="year",
    var="c04_referencelist",
    sub_var="item",
    time_window=range(2012, 2024),
    weighted_network=True, 
    self_loop=True
)
ref_cooc.main()

focal_years = range(2012, 2024)
collection_name = 'references_sample'
id_variable = 'PMID'
year_variable = 'year'
variable = 'c04_referencelist'
sub_variable = 'item'

for focal_year in tqdm.tqdm(focal_years, desc="Computing Lee indicator for window of time"):
    Lee = novelpy.indicators.Lee2015(
        collection_name=collection_name,
        id_variable=id_variable,
        year_variable=year_variable,
        variable=variable,
        sub_variable=sub_variable,
        focal_year=focal_year,
        density=True
    )
    Lee.get_indicator()

# ---------------------------------------------------------------------
# Exemple : ensuite on charge les résultats annuels, on fusionne, etc.
# ---------------------------------------------------------------------
def load_data_from_files(start_year, end_year, directory):
    all_data = []
    for year in range(start_year, end_year + 1):
        file_path = os.path.join(directory, f"{year}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                all_data.extend(data)
                print(f"Data from {year}.json loaded successfully")
        else:
            print(f"File {file_path} does not exist")
    return all_data

def convert_lee_to_dataframe(data):
    records = []
    for item in data:
        pmid = item.get('PMID', None)
        novelty_score = item.get('c04_referencelist_lee', {}).get('score', {}).get('novelty', None)
        records.append({
            'PMID': pmid,
            'Novelty': novelty_score
        })
    return pd.DataFrame(records)

# Charger les données calculées par Lee
start_year = 2012
end_year = 2024
directory_lee = 'Result/lee/c04_referencelist/'
data_lee = load_data_from_files(start_year, end_year, directory_lee)
print(f"Total records loaded from Lee: {len(data_lee)}")

lee_df = convert_lee_to_dataframe(data_lee)
lee_df.describe()

# Charger les données de base pour articles (qui contiennent 'sdg_query_source')
directory_data = 'Data/docs/references_sample/'
data_articles = load_data_from_files(start_year, end_year, directory_data)
df_articles = pd.DataFrame(data_articles)
df_articles.describe()

# Fusion sur 'PMID'
df = df_articles.merge(lee_df, on='PMID', how='left').dropna(subset=['Novelty'])
df.describe()

# Sauvegarde finale (le CSV contiendra alors la colonne 'sdg_query_source')
df.to_csv("df_Lee12-24.csv", index=False)
print("Fichier df_Lee.csv sauvegardé.")
