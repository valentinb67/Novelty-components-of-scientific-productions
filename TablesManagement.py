import pandas as pd
import numpy as np
import ast
import requests
import time

# Charger le fichier CSV
DF_SDG_2 = pd.read_csv('DF_SDG.csv')

#Unlist the columns 'authors'
    #Convertir les chaînes de caractères en listes Python dans la colonne 'authors'
DF_SDG_2['authors'] = DF_SDG_2['authors'].apply(ast.literal_eval)
    #Séparer les auteurs dans plusieurs colonnes
authors_df = DF_SDG_2['authors'].apply(pd.Series)
    #Renommer les colonnes de façon appropriée
authors_df.columns = [f'author_{i+1}' for i in range(authors_df.shape[1])]
    #Combiner avec le dataframe original
DF_SDG_2 = pd.concat([DF_SDG_2, authors_df], axis=1)

#Unlist the columns 'institutions'
    # Convertir les chaînes de caractères en listes Python dans la colonne 'institutions'
DF_SDG_2['institutions'] = DF_SDG_2['institutions'].apply(ast.literal_eval)
    # Séparer les institutions dans plusieurs colonnes
institutions_df = DF_SDG_2['institutions'].apply(pd.Series)
    # Renommer les colonnes de façon appropriée
institutions_df.columns = [f'institution_{i+1}' for i in range(institutions_df.shape[1])]
    # Combiner avec le dataframe original
DF_SDG_2 = pd.concat([DF_SDG_2, institutions_df], axis=1)

########################################
############ DF_SDG_2_authors ############
    #Filtrer les colonnes nécessaires : PMID, num_authors, Auteur_1 à Auteur_100
selected_columns = ['PMID', 'num_authors', 'log_num_authors_SDG_2', 'log_num_authors_squared_SDG_2'] + [f'author_{i+1}' for i in range(100)]
DF_SDG_2_authors_authors = DF_SDG_2[selected_columns]
DF_SDG_2_authors_authors

########################################
############ DF_SDG_2_metrics ############

selected_columns_metrics = ['PMID', 'num_citations', 'Novelty']
DF_SDG_2_metrics = DF_SDG_2[selected_columns_metrics]