import os
import requests
import pandas as pd
import pycountry_convert as pc
from geopy.geocoders import Nominatim

API_KEY = ''

def get_city_state(place_name):

    """
    Fetches the city, region, state, latitude, and longitude for a given place name using Google Maps Geocoding API.

    Args:
        place_name (str): The name of the place to geocode.
        api_key (str): Your Google Maps API key.

    Returns:
        tuple: A tuple containing city (str), region (str), state (str), latitude (float), longitude (float).
               Returns (None, None, None, None, None) if the place is not found or an error occurs.
    """

    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": place_name, "key": API_KEY}
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            city = None
            region = None
            state = None
            latitude = None
            longitude = None
            for component in data['results'][0]['address_components']:
                if "locality" in component['types']:
                    city = component['long_name']
                if not city and "postal_town" in component['types']:
                    city = component['long_name']
                if "administrative_area_level_1" in component['types']:
                    region = component['long_name']
                if "country" in component['types']:
                    state = component['long_name']
                latitude = data["results"][0]["geometry"]["location"]["lat"]
                longitude = data["results"][0]["geometry"]["location"]["lng"]
            return city, region, state, latitude, longitude
    return None, None, None, None, None

def get_city_from_coordinates(lat, lng):

    """
    Fetches the city, region, and state for given latitude and longitude coordinates using Google Maps Geocoding API.

    Args:
        lat (float): The latitude of the location.
        lng (float): The longitude of the location.
        api_key (str): Your Google Maps API key.

    Returns:
        tuple: A tuple containing city (str), region (str), and state (str).
            Returns (None, None, None) if the location is not found or an error occurs.
    """

    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"latlng": f"{lat},{lng}", "key": API_KEY}  # Latitudine e Longitudine
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            city = None
            region = None
            state = None
            for result in data['results']:
                for component in result['address_components']:
                    if "locality" in component['types']:
                        city = component['long_name']
                    if not city and "postal_town" in component['types']:
                        city = component['long_name']
                    if "administrative_area_level_1" in component['types']:
                        region = component['long_name']
                    if "country" in component['types']:
                        state = component['long_name']
                return city, region, state
    return None, None, None

def get_continent_from_country(country_name):

    """
    Fetches the continent name for a given country name.

    Args:
        country_name (str): The name of the country.

    Returns:
        str: The name of the continent (e.g., "Africa", "Asia", "Europe").
            Returns None if the country name is invalid or an error occurs.
    """

    try:
        country_code = pc.country_name_to_country_alpha2(country_name)
        continent_code = pc.country_alpha2_to_continent_code(country_code)
        continent_name = {
            "AF": "Africa",
            "AS": "Asia",
            "EU": "Europe",
            "NA": "North America",
            "SA": "South America",
            "OC": "Oceania",
            "AN": "Antarctica"
        }
        return continent_name.get(continent_code, None)
    except Exception as e:
        return None

##################
##################

source_folder = "Novelty-components-of-scientific-productions/DataFrames/"
destination_folder = "Novelty-components-of-scientific-productions/DataFrames_to_PBI/"

# Take the .csv files from the DataFrame folder.
for filename in os.listdir(source_folder):
    if filename.endswith(".csv"):
        file_path = os.path.join(source_folder, filename)
        df = pd.read_csv(file_path)

        # Convert 'authors' and 'institutions' columns from strings to lists.
        # The columns are stored as string representations of lists; 'eval' is used to parse them into actual lists.
        df['authors'] = df['authors'].apply(lambda x: eval(x))
        df['institutions'] = df['institutions'].apply(lambda x: eval(x))
        
        # Flatten the authors and their institutions into a row-wise format.
        # Each author-institution pair is extracted into a separate row in the new dataframe.
        rows = []
        for _, row in df.iterrows():
            authors = row['authors']
            institutions = row['institutions'] if row['institutions'] else [None] * len(authors)
            for author, institution in zip(authors, institutions):
                rows.append({
                    'PMID': row['PMID'],
                    'Year': row['year'],
                    'Author': author.strip(),
                    'Institution': institution.strip() if institution else None
                })
        df_authors = pd.DataFrame(rows)
        
        # Add placeholder columns for location information.
        # These columns will store the city, region, state, latitude, and longitude based on the institution's address.
        df_authors['City'] = None
        df_authors['Region'] = None
        df_authors['State'] = None
        df_authors['Latitude'] = None
        df_authors['Longitude'] = None
        
        # Populate location data for each institution using the `get_city_state` function.
        # If an institution address exists, fetch its location details and update the corresponding columns.
        for i in range(len(df_authors)):
            if df_authors.loc[i, 'Institution']:
                place_name = df_authors.loc[i, 'Institution']
                city, region, state, latitude, longitude = get_city_state(place_name)
                df_authors.loc[i, 'City'] = city
                df_authors.loc[i, 'Region'] = region
                df_authors.loc[i, 'State'] = state
                df_authors.loc[i, 'Latitude'] = latitude
                df_authors.loc[i, 'Longitude'] = longitude
        
        # Validate and enrich location data using the `get_city_from_coordinates` function.
        # For rows with valid latitude and longitude, fetch additional location details if missing.
        for i in range(len(df_authors)):
            lat = df_authors.loc[i, 'Latitude']
            lng = df_authors.loc[i, 'Longitude']
            if pd.notna(lat) and pd.notna(lng):
                city, region, state = get_city_from_coordinates(lat, lng)
                if not df_authors.loc[i, 'City']:
                    df_authors.loc[i, 'City'] = city
                if not df_authors.loc[i, 'Region']:
                    df_authors.loc[i, 'Region'] = region
                if not df_authors.loc[i, 'State']:
                    df_authors.loc[i, 'State'] = state
        
        # Save the updated dataframe to the destination folder.
        # Export the dataframe to a CSV file after processing and print a preview of the first row.
        dest_path = os.path.join(destination_folder, filename)
        df_authors.to_csv(dest_path, encoding='utf-8', index=False)
        print(f"File {filename} elaborated and saved in {destination_folder}")

print("Complete!")
