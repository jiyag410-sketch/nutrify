import pandas as pd

# Load full dataset
recipes = pd.read_csv("data/raw/RAW_recipes.csv")

# Drop rows with missing critical fields
recipes = recipes.dropna(subset=["name", "ingredients", "steps", "description"])

# Take a random sample of 5,000 recipes (fixed seed = reproducible)
sample = recipes.sample(n=5000, random_state=42)

# Save the cleaned sample
sample.to_csv("data/raw/recipes_sample.csv", index=False)

print("Saved sample with", len(sample), "recipes")
print(sample[["name", "ingredients", "n_ingredients"]].head())
