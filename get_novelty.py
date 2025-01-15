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
import shutil

def get_top_cited_openalex_data(query, num_results=800):
    """
    Récupère les articles OpenAlex les plus cités pour une requête donnée.

    Args:
        query (str): La requête de recherche.
        num_results (int): Nombre total d'articles à récupérer.

    Returns:
        list: Liste des articles triés par nombre de citations décroissant.
    """
    base_url = "https://api.openalex.org/works"
    results = []
    per_page = 200

    for offset in range(0, num_results, per_page):
        response = requests.get(
            f"{base_url}?filter=title.search:{query},from_publication_date:2016-01-01,to_publication_date:2024-12-31"
            f"&sort=cited_by_count:desc&per-page={per_page}&page={offset // per_page + 1}"
        )
        
        if response.status_code == 200:
            data = response.json().get('results', [])
            results.extend(data)
        else:
            print(f"Erreur : {response.status_code}")
            break

        if len(data) < per_page:
            # Si moins de résultats que prévu, on arrête
            break

    return results[:num_results]

def generate_int_id(string_id):
    """Generate a unique integer ID from a string ID using hashing"""
    return int(hashlib.sha256(string_id.encode('utf-8')).hexdigest(), 16) % (10**8)

def prepare_data_for_novelpy(data):
    prepared_data = []

    for item in data:
        try:
            if 'id' not in item:
                print(f"Skipping item without id: {item}")
                continue

            year = item.get('publication_year', None)
            if year is None or not (2016 <= year <= 2024):
                print(f"Skipping item outside date range: {item['id']}")
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

            # Création de l'entrée
            entry = {
                "PMID": generate_int_id(item['id']),
                "year": year,
                "type": item.get('type', ''),
                "num_citations": item.get('cited_by_count', 0),
                "num_authors": len(authorships),
                "authors": authors,
                "institutions": institutions,
                "c04_referencelist": [{"item": generate_int_id(ref)} for ref in item.get('referenced_works', [])],
                "subfield": item.get('concepts', [{}])[0].get('display_name', '') if item.get('concepts') else '',
                "field": item.get('concepts', [{}])[1].get('display_name', '') if len(item.get('concepts', [])) > 1 else '',
                "domain": item.get('concepts', [{}])[2].get('display_name', '') if len(item.get('concepts', [])) > 2 else '',
                "sustainable_development_goals": item.get('sustainable_development_goals', []),
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

def convert_to_dataframe_1(data):
    records = []
    for item in data:
        pmid = item.get('PMID', None)
        year = item.get('year', None)
        novelty_score = item.get('c04_referencelist_lee', {}).get('score', {}).get('novelty', None)
        records.append({
            'PMID': pmid,
            'Year': year,
            'Novelty': novelty_score
        })
    return pd.DataFrame(records)

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

def convert_to_dataframe_2(data):
    records = []
    for item in data:
        pmid = item.get('PMID', None)
        novelty_score = item.get('c04_referencelist_lee', {}).get('score', {}).get('novelty', None)
        records.append({
            'PMID': pmid,
            'Novelty': novelty_score
        })
    return pd.DataFrame(records)

def convert_to_dataframe_3(data):
    return pd.DataFrame(data)

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

# Liste des requêtes
#queries = ["SDG 1", "SDG 2", "SDG 3", "SDG 4", "SDG 5", "SDG 6", "SDG 7", "SDG 8", "SDG 9", "SDG 10",
#           "SDG 11", "SDG 12", "SDG 13", "SDG 14", "SDG 15", "SDG 16", "SDG 17"]
queries = [
    "No Poverty", # SDG 1
    "Zero Hunger", # SDG 2
    "SDG 3", # SDG 3
    "Quality Education", # SDG 4
    "Gender Equality", # SDG 5
    "SDG 6", # SDG 6
    "SDG 7", # SDG 7
    "SDG 8", # SDG 8
    "SDG 9", # SDG 9
    "Reduced Inequality", # SDG 10
    "Sustainable Cities and Communities", # SDG 11
    "Responsible Consumption and Production", # SDG 12
    "Climate Action", # SDG 13
    "SDG 14", # SDG 14
    "Life on Land", # SDG 15
    "SDG 16", # SDG 16
    "Partnerships for the Goals" # SDG 17
    ]

for query in queries:
    print(f"Processing query: {query}")
    data = get_top_cited_openalex_data(query, num_results=800)
    prepared_data = prepare_data_for_novelpy(data)
    save_data_by_year(prepared_data, base_dir=f"Data/docs/references_sample")
    validate_data(prepared_data)
    
    #Calculating the co-occurrence matrix and Lee et al. (2015) indicator
    ref_cooc = novelpy.utils.cooc_utils.create_cooc(
        collection_name="references_sample",
        year_var="year",
        var="c04_referencelist",
        sub_var="item",
        time_window=range(2016, 2025),
        weighted_network=True, 
        self_loop=True
    )
    ref_cooc.main()

    focal_years = range(2016, 2025)
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

    #Load data for Lee
    start_year = 2016
    end_year = 2024
    directory = 'Result/lee/c04_referencelist/'
    data_lee = load_data_from_files(start_year, end_year, directory)
    print(f"Total records loaded: {len(data_lee)}")

    lee_df = convert_to_dataframe_2(data_lee)
    lee_df.describe()
    
    data = get_top_cited_openalex_data(query, 800)
    prepared_data = prepare_data_for_novelpy(data)
    save_data_by_year(prepared_data)
    
    start_year = 2016
    end_year = 2024
    directory = 'Data/docs/references_sample/'
    data = load_data_from_files(start_year, end_year, directory)
    
    df_articles = convert_to_dataframe_3(data)
    df_articles.describe()
    
    df = df_articles.merge(lee_df, on='PMID', how='left').dropna(subset=['Novelty'])
    df.describe()
    
    # Conversion en DataFrame et sauvegarde
    df.to_csv(f"DataFrames/DF_{query}.csv", index=False)
    print(df.describe())
    print(f"Data for query '{query}' saved to DF_{query}.csv")
    
    folders_to_delete = ['Data', 'Result']
    for folder in folders_to_delete:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"Dossier '{folder}' supprimé avec succès.")
            except Exception as e:
                print(f"Erreur lors de la suppression du dossier '{folder}': {e}")

print("All queries processed successfully.")