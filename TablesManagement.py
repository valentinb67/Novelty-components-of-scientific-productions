import pandas as pd
import numpy as np
import ast
import requests
import time

DF_SDG_2 = pd.read_csv('DF_SDG.csv')

#Unlist the columns 'authors'
    #Convert string to list in column 'authors'
DF_SDG_2['authors'] = DF_SDG_2['authors'].apply(ast.literal_eval)
    #Separate authors (one per column)
authors_df = DF_SDG_2['authors'].apply(pd.Series)
    #Rename columns
authors_df.columns = [f'author_{i+1}' for i in range(authors_df.shape[1])]
    #Combine with the main df
DF_SDG_2 = pd.concat([DF_SDG_2, authors_df], axis=1)

#Unlist the columns 'institutions'
    #Convertir les chaînes de caractères en listes Python dans la colonne 'institutions'
DF_SDG_2['institutions'] = DF_SDG_2['institutions'].apply(ast.literal_eval)
    #Separate the institutions
institutions_df = DF_SDG_2['institutions'].apply(pd.Series)
    #Rename the columns
institutions_df.columns = [f'institution_{i+1}' for i in range(institutions_df.shape[1])]
    #Combine the df
DF_SDG_2 = pd.concat([DF_SDG_2, institutions_df], axis=1)


print(DF_SDG_2)

DF_SDG_2.to_csv("DF_SDG_2.csv", index=False)
########################################
############ DF_SDG_2_authors ############
    #Filter the following columns: PMID, num_authors, Auteur_1 à Auteur_100
#selected_columns = ['PMID', 'num_authors', 'log_num_authors_SDG_2', 'log_num_authors_squared_SDG_2'] + [f'author_{i+1}' for i in range(100)]
#DF_SDG_2_authors_authors = DF_SDG_2[selected_columns]
#DF_SDG_2_authors_authors

########################################
############ DF_SDG_2_metrics ############

#selected_columns_metrics = ['PMID', 'num_citations', 'Novelty']
#DF_SDG_2_metrics = DF_SDG_2[selected_columns_metrics]