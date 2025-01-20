# Novelty-components-of-scientific-productions
As part of our Master Data Science for Economy and Business, we want to develop our skills in Data Vizualisation by proposing a Dashboard that will present different components of the novelty of scientific productions from the OpenAlex database.

We'll start with a sample of 1,000 articles from OpenAlex Database based on the keyword “Substainable Development Goal”, the aim is to identify a scientific subfield to define whether the method of the article employs/discusses digital technologies. We will explain the novelty potential of scientific productions talking about SDGs through the use of digital technologies, and to bring out evidence linked to the characteristics of the articles and their production conditions.

# get_location.py

`get_location.py` is a Python script for processing scientific publication data to extract geographic information about authors and their affiliated institutions. It uses the Google Maps Geocoding API and other libraries to map institution names to their respective cities, regions, states, and coordinates.

## Features

- Converts institution names into geographic details (city, region, state, latitude, longitude).
- Maps countries to their continents.
- Processes `.csv` files to normalize and flatten author-institution data.
- Enriches the dataset with geographic information.
- Saves the processed data as new `.csv` files for further analysis.

This script is ideal for adding geographic context to publication datasets for research or visualization purposes.