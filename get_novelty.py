# Import packages for Lee Commonness and data manipulation
import pandas as pd
import numpy as np
import json
import os
import requests
import hashlib
import novelpy
import tqdm
import csv
import shutil

# Function to retrieve top-cited articles from OpenAlex API
def get_top_cited_openalex_data(query, num_results=800):
    """
    Récupère les articles OpenAlex les plus cités pour une requête donnée.

    Args:
        query (str): La requête de recherche.
        num_results (int): Nombre total d'articles à récupérer.

    Returns:
        list: Liste des articles triés par nombre de citations décroissant.
    """
    # Base URL of the OpenAlex API endpoint
    base_url = "https://api.openalex.org/works"
    results = []
    per_page = 200 # Number of results per API page

    # Loop through pages to collect data until the desired count is reached
    for offset in range(0, num_results, per_page):
        response = requests.get(
            f"{base_url}?filter=title.search:{query},from_publication_date:2016-01-01,to_publication_date:2024-12-31"
            f"&sort=cited_by_count:desc&per-page={per_page}&page={offset // per_page + 1}"
        )
        
        if response.status_code == 200:
            # Add results from this page to the cumulative results list
            data = response.json().get('results', [])
            results.extend(data)
        else:
            # Print an error message if the API request fails and stop the loop
            print(f"Erreur : {response.status_code}")
            break

        if len(data) < per_page:
            # If fewer results than expected are returned, stop fetching more
            break

    return results[:num_results]

def generate_int_id(string_id):
    """Generate a unique integer ID from a string ID using hashing"""
    return int(hashlib.sha256(string_id.encode('utf-8')).hexdigest(), 16) % (10**8)

def prepare_data_for_novelpy(data):
    """
    Prepare OpenAlex data for analysis by extracting relevant fields.
    
    Args:
        data (list): List of OpenAlex works data.
    
    Returns:
        list: Processed data entries with standardized fields.
    """
    prepared_data = []

    for item in data:
        try:
            # Ensure the item contains a unique identifier
            if 'id' not in item:
                print(f"Skipping item without id: {item}")
                continue
            
            # Filter out items outside the date range
            year = item.get('publication_year', None)
            if year is None or not (2016 <= year <= 2024):
                print(f"Skipping item outside date range: {item['id']}")
                continue
            
            # Extract authors and institutions
            authorships = item.get('authorships', [])
            authors = [author['author']['display_name'] for author in authorships]
            institutions = []
            for author in authorships:
                if 'institutions' in author:
                    for inst in author['institutions']:
                        institutions.append(inst.get('display_name', ''))

            # Extract additional optional fields, with a default for missing data
            keyword_analysis = item.get('keyword_analysis', 'Missing')
            collaborative_index = item.get('collaborative_index', 'Missing')
            license_info = item.get('license', 'Missing')
            journal_impact_factor = item.get('journal_impact_factor', 'Missing')
            citations_geographical = item.get('citations_geographical', 'Missing')
            page_count = item.get('page_count', 'Missing')
            publisher = item.get('host_venue', {}).get('publisher', 'Missing')
            apc_paid = item.get('apc_paid', 'Missing')
            open_access_status = item.get('open_access', {}).get('status', 'Missing')

            # Construct the processed data entry
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
            # Log KeyErrors to help identify issues with missing fields
            print(f"KeyError: {e} in item {item.get('id', 'unknown')}")
            continue

    return prepared_data

def save_data_by_year(prepared_data, base_dir='Data/docs/references_sample'):
    """
    Save the prepared data into separate files for each year.
    
    Args:
        prepared_data (list): List of processed data entries, each containing a 'year' field.
        base_dir (str): Directory where the year-specific files will be stored.

    The function organizes the data by year and writes it into JSON files,
    creating a separate file for each year.
    """
    data_by_year = {}
    for item in prepared_data:
        year = item['year']
        # Initialize a list for each year if not already present
        if year not in data_by_year:
            data_by_year[year] = []
        # Append the item to the corresponding year list
        data_by_year[year].append(item)
    
    # Ensure the target directory exists
    os.makedirs(base_dir, exist_ok=True)
    # Write each year's data to a JSON file
    for year, data in data_by_year.items():
        with open(os.path.join(base_dir, f"{year}.json"), 'w') as f:
            json.dump(data, f, indent=4)

def validate_data(prepared_data):
    """
    Validate that all referenced items exist within the dataset.

    Args:
        prepared_data (list): List of data entries, each containing a 'PMID' field and a 
                              'c04_referencelist' field with references.

    Returns:
        bool: True if all references are valid, False if any references are missing.
    """
    # Collect all known PMIDs in a set
    all_ids = set(item['PMID'] for item in prepared_data)
    valid = True
    
    # Check each item's references
    for item in prepared_data:
        for ref in item['c04_referencelist']:
            if ref['item'] not in all_ids:
                # Print a message for missing references
                print(f"Reference {ref['item']} in document {item['PMID']} does not exist in the dataset.")
                valid = False
    return valid

def convert_to_dataframe_1(data):
    """
    Convert a dataset into a DataFrame with specific columns.

    Args:
        data (list): List of data entries, each containing 'PMID', 'year', and nested
                     fields for novelty scores.

    Returns:
        pandas.DataFrame: DataFrame with 'PMID', 'Year', and 'Novelty' columns.
    """
    records = []
    # Iterate through each entry and extract relevant fields
    for item in data:
        pmid = item.get('PMID', None)
        year = item.get('year', None)
        novelty_score = item.get('c04_referencelist_lee', {}).get('score', {}).get('novelty', None)
        records.append({
            'PMID': pmid,
            'Year': year,
            'Novelty': novelty_score
        })
    # Create a DataFrame from the extracted records
    return pd.DataFrame(records)

def load_data_from_files(start_year, end_year, directory):
    """
    Load data from a range of yearly JSON files.

    Args:
        start_year (int): Start year of the range to load.
        end_year (int): End year of the range to load.
        directory (str): Directory containing the yearly JSON files.

    Returns:
        list: Combined list of data entries from all specified year files.
    """
    all_data = []
    # Loop through the specified years
    for year in range(start_year, end_year + 1):
        file_path = os.path.join(directory, f"{year}.json")
        if os.path.exists(file_path):
            # Load data if the file exists
            with open(file_path, 'r') as f:
                data = json.load(f)
                all_data.extend(data)
                print(f"Data from {year}.json loaded successfully")
        else:
            print(f"File {file_path} does not exist")
    return all_data

def convert_to_dataframe_2(data):
    """
    Convert a dataset into a DataFrame focused on novelty scores.

    Args:
        data (list): List of data entries, each containing 'PMID' and nested novelty score fields.

    Returns:
        pandas.DataFrame: DataFrame with 'PMID' and 'Novelty' columns.
    """
    records = []
    # Extract 'PMID' and 'Novelty' from each entry
    for item in data:
        pmid = item.get('PMID', None)
        novelty_score = item.get('c04_referencelist_lee', {}).get('score', {}).get('novelty', None)
        records.append({
            'PMID': pmid,
            'Novelty': novelty_score
        })
    return pd.DataFrame(records)

def convert_to_dataframe_3(data):
    # Convert a list of data entries directly into a DataFrame 
    return pd.DataFrame(data)

# Define a list of queries representing Sustainable Development Goals (SDGs)
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

# Process each query
for query in queries:
    print(f"Processing query: {query}")
    # Retrieve data for the current query
    data = get_top_cited_openalex_data(query, num_results=800)
    # Prepare the data for Novelty
    prepared_data = prepare_data_for_novelpy(data)
    # Save the prepared data grouped by publication year
    save_data_by_year(prepared_data, base_dir=f"Data/docs/references_sample")
    # Validate the prepared data to ensure consistency
    validate_data(prepared_data)
    
    # Calculating the co-occurrence matrix and Lee et al. (2015) indicator
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

    # Define parameters for the Lee indicator calculation
    focal_years = range(2016, 2025)
    collection_name = 'references_sample'
    id_variable = 'PMID'
    year_variable = 'year'
    variable = 'c04_referencelist'
    sub_variable = 'item'

    # Compute the Lee indicator for each focal year
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

    # Load the computed Lee data
    start_year = 2016
    end_year = 2024
    directory = 'Result/lee/c04_referencelist/'
    data_lee = load_data_from_files(start_year, end_year, directory)
    print(f"Total records loaded: {len(data_lee)}")

    # Convert Lee data into a DataFrame and summarize it
    lee_df = convert_to_dataframe_2(data_lee)
    lee_df.describe()
    
    # Reprocess the query data, prepare it, and save it by year
    data = get_top_cited_openalex_data(query, 800)
    prepared_data = prepare_data_for_novelpy(data)
    save_data_by_year(prepared_data)
    
    # Load all yearly data into a single list
    start_year = 2016
    end_year = 2024
    directory = 'Data/docs/references_sample/'
    data = load_data_from_files(start_year, end_year, directory)
    
    # Convert the loaded data into a DataFrame and summarize it
    df_articles = convert_to_dataframe_3(data)
    df_articles.describe()
    
    # Merge the Lee data with the article data and filter out rows without novelty scores
    df = df_articles.merge(lee_df, on='PMID', how='left').dropna(subset=['Novelty'])
    df.describe()
    
    # Save the final DataFrame to a CSV file
    df.to_csv(f"DataFrames/DF_{query}.csv", index=False)
    print(df.describe())
    print(f"Data for query '{query}' saved to DF_{query}.csv")
    
    # Clean up temporary data and results folders
    folders_to_delete = ['Data', 'Result']
    for folder in folders_to_delete:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"Folder '{folder}' successfully deleted.")
            except Exception as e:
                print(f"Error deleting folder '{folder}': {e}")

print("All queries processed successfully.")
