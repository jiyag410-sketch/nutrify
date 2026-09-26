import pandas as pd

recipes = pd.read_csv("data/raw/RAW_recipes.csv")
print("Number of recipes:", len(recipes))
print(recipes.head())
