import pandas as pd

# Load Indian recipes dataset
indian = pd.read_csv("data/raw/indian_recipes_raw.csv")

# Drop rows missing critical fields
indian = indian.dropna(subset=["TranslatedRecipeName", "Cleaned-Ingredients", "TranslatedInstructions"])

# Take a sample of 3000 (or fewer if dataset is smaller)
sample_size = min(3000, len(indian))
sample = indian.sample(n=sample_size, random_state=42)

# Rename columns to match our existing recipe structure
sample = sample.rename(columns={
    "TranslatedRecipeName": "name",
    "Cleaned-Ingredients": "ingredients",
    "TranslatedInstructions": "steps",
    "TotalTimeInMins": "minutes",
    "Ingredient-count": "n_ingredients"
})

# Add a description column (Indian dataset doesn't have one, so build one from cuisine)
sample["description"] = "A " + sample["Cuisine"].fillna("Indian") + " dish."

# Keep only the columns we need, matching our pipeline
final = sample[["name", "ingredients", "steps", "description", "minutes", "n_ingredients"]]

final.to_csv("data/raw/indian_recipes_sample.csv", index=False)

print(f"Saved {len(final)} Indian recipes")
print(final.head(3))
