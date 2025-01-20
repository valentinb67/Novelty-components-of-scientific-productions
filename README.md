# Novelty-components-of-scientific-productions
As part of our Master Data Science for Economy and Business, we want to develop our skills in Data Vizualisation by proposing a Dashboard that will present different components of the novelty of scientific productions from the OpenAlex database.

We'll start with a sample of 1,000 articles from OpenAlex Database based on the keyword “Substainable Development Goal”, the aim is to identify a scientific subfield to define whether the method of the article employs/discusses digital technologies. We will explain the novelty potential of scientific productions talking about SDGs through the use of digital technologies, and to bring out evidence linked to the characteristics of the articles and their production conditions.

# get_location.py

`get_location.py` is a Python script designed to process scientific publication data and determine the geographic location of institutions associated with each author. Using the Google Maps Geocoding API, the script extracts detailed location information, such as city, region, state, latitude, and longitude, for every institution listed in the dataset.

## Main Purpose

This script processes `.csv` files containing metadata about publications, including authors and their institutions. For each institution, it identifies its geographic location and enriches the dataset with detailed positional information, making it easier to analyze the geographic distribution of scientific collaborations.

## Key Features

- Extracts geographic details (city, region, state, latitude, longitude) for each institution using the Google Maps Geocoding API.
- Associates each author with their respective institution in a row-wise format.
- Adds missing geographic details by validating latitude and longitude data.
- Determines the continent of each institution's country for additional context.
- Saves enriched data to `.csv` files for further analysis or visualization.

This script is particularly useful for researchers and analysts seeking to map the institutional affiliations of authors in scientific datasets and analyze the geographic distribution of their research outputs.
