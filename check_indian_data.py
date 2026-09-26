import pandas as pd

df = pd.read_csv("data/raw/indian_recipes_raw.csv")
print("Columns:", df.columns.tolist())
print("Number of rows:", len(df))
print(df.head(2))
