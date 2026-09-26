import pandas as pd

# Load Indian recipes dataset
indian = pd.read_csv("data/raw/indian_recipes_raw.csv")
indian = indian.dropna(subset=["TranslatedRecipeName", "Cleaned-Ingredients", "TranslatedInstructions"])

# Keywords covering North Indian states/regions you asked for
north_indian_keywords = [
    "punjabi", "rajasthani", "kashmiri", "mughlai", "awadhi", "lucknowi",
    "north indian", "bihari", "uttar pradesh", "delhi", "himachal",
    "uttarakhand", "chandigarh"
]

pattern = "|".join(north_indian_keywords)
is_north = indian["Cuisine"].str.lower().str.contains(pattern, na=False)

north_subset = indian[is_north]
other_subset = indian[~is_north]

print(f"North Indian-matching recipes available: {len(north_subset)}")
print(f"Other recipes available: {len(other_subset)}")

# Take ALL north Indian matches (up to 1500), fill rest with a broader sample
north_sample_size = min(1500, len(north_subset))
north_sample = north_subset.sample(n=north_sample_size, random_state=42)

remaining_needed = 3000 - north_sample_size
other_sample_size = min(remaining_needed, len(other_subset))
other_sample = other_subset.sample(n=other_sample_size, random_state=42)

sample = pd.concat([north_sample, other_sample])

# Rename columns to match our pipeline structure
sample = sample.rename(columns={
    "TranslatedRecipeName": "name",
    "Cleaned-Ingredients": "ingredients",
    "TranslatedInstructions": "steps",
    "TotalTimeInMins": "minutes",
    "Ingredient-count": "n_ingredients"
})

sample["description"] = "A " + sample["Cuisine"].fillna("Indian") + " dish."

final = sample[["name", "ingredients", "steps", "description", "minutes", "n_ingredients"]]
final.to_csv("data/raw/indian_recipes_sample.csv", index=False)

print(f"\nSaved {len(final)} total Indian recipes ({north_sample_size} North Indian-focused)")
print(final.head(3))
