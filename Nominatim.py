#from geopy.geocoders import Nominatim
#import pandas as pd

# Charger le fichier CSV
#DF_SDG_3 = pd.read_csv('DF_SDG_2.csv')

# Initialiser le géolocaliseur
#geolocator = Nominatim(user_agent="institution_lookup")

# Fonction pour récupérer la ville via Nominatim
#def get_city_from_institution(institution_name):
    #try:
        #location = geolocator.geocode(institution_name)
        #if location:
            #return location.address.split(',')[-4].strip()  # Récupérer la ville
        #return None
    #except:
        #return None

# Liste des colonnes d'institutions
#institution_columns = [f'institution_{i}' for i in range(1, 63)]  # institution_1 à institution_62

# Appliquer la fonction pour chaque colonne d'institutions et créer des colonnes de ville correspondantes
#for col in institution_columns:
#    DF_SDG_3[f'city_{col}'] = DF_SDG_3[col].apply(get_city_from_institution)

#DF_SDG_3['city_1'] = DF_SDG_3['institution_1'].apply(get_city_from_institution)
#DF_SDG_3['city_1'].head()


from geopy.geocoders import Nominatim
import pandas as pd

# Charger le fichier CSV
DF_SDG_3 = pd.read_csv('DF_SDG_2.csv')

geolocator = Nominatim(user_agent="institution_lookup")

# Fonction pour récupérer la ville via Nominatim
def get_city_from_institution(institution_name):
    try:
        location = geolocator.geocode(institution_name)
        if location:
            # Essayons de récupérer la deuxième ou troisième partie de l'adresse pour isoler la ville
            address_parts = location.address.split(',')
            # Tenter d'extraire une partie raisonnable (ajuster si nécessaire)
            if len(address_parts) >= 3:
                return address_parts[-3].strip()
            elif len(address_parts) >= 2:
                return address_parts[-2].strip()
            else:
                return address_parts[-1].strip()
        return None
    except:
        return None

#Apply the function on 'institution_1'
DF_SDG_3['city_1'] = DF_SDG_3['institution_1'].apply(get_city_from_institution)
DF_SDG_3['city_1'].head()

valeurs_manquantes = DF_SDG_3['city_1'].isna().sum()
print(valeurs_manquantes)

DF_SDG_3.to_csv("DF_SDG_3.csv", index=False)
