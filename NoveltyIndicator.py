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

def get_openalex_data(query, num_results=1000):
    base_url = "https://api.openalex.org/works"
    results = []
    per_page = 15
    
    for offset in range(0, num_results, per_page):
        response = requests.get(f"{base_url}?filter=title.search:{query},from_publication_date:2007-01-01,to_publication_date:2024-12-31&per-page={per_page}&page={offset // per_page + 1}")
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
            if year is None or not (2007 <= year <= 2024):
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
                
                # Variables supplémentaires
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

#Query Launch
query = "sustainable development goals"
data = get_openalex_data(query, num_results=1000)
prepared_data = prepare_data_for_novelpy(data)
save_data_by_year(prepared_data)

#Calculating the co-occurrence matrix and Lee et al. (2015) indicator
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
    

#Retrieve commonness in csv format
def convert_to_dataframe(data):
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

def convert_to_dataframe(data):
    records = []
    for item in data:
        pmid = item.get('PMID', None)
        novelty_score = item.get('c04_referencelist_lee', {}).get('score', {}).get('novelty', None)
        records.append({
            'PMID': pmid,
            'Novelty': novelty_score
        })
    return pd.DataFrame(records)

#Load data for Lee
start_year = 2012
end_year = 2024
directory = 'Result/lee/c04_referencelist/'
data_lee = load_data_from_files(start_year, end_year, directory)
print(f"Total records loaded: {len(data_lee)}")

lee_df = convert_to_dataframe(data_lee)
lee_df.describe()

#Retrieve paper data in CSV format
def convert_to_dataframe(data):
    return pd.DataFrame(data)

query = "sustainable development goals"
data = get_openalex_data(query, 1000)
prepared_data = prepare_data_for_novelpy(data)
save_data_by_year(prepared_data)

#Load saved data for a given period
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

start_year = 2012
end_year = 2024
directory = 'Data/docs/references_sample/'
data = load_data_from_files(start_year, end_year, directory)

df_articles = convert_to_dataframe(data)
df_articles.describe()

df = df_articles.merge(lee_df, on='PMID', how='left').dropna(subset=['Novelty'])
df.describe()

#Number of authors and creation of a quadratic term for the U-inversed relationship
df['log_num_authors_SDG'] = np.log(df['num_authors'] + 1)
df['log_num_authors_squared_SDG'] = df['log_num_authors_SDG']**2

#Add a dummy for articles that refer to a digital technology


#DL the DF
df.describe()
df.to_csv("DF_SDG.csv", index=False)