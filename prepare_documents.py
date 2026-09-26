import pandas as pd
import json
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ---------- 1. Process US recipes ----------
us_recipes = pd.read_csv("data/raw/recipes_sample.csv")

recipe_chunks = []
for _, row in us_recipes.iterrows():
    text = f"""Recipe: {row['name']}
Ingredients: {row['ingredients']}
Steps: {row['steps']}
Description: {row['description']}
Time to make: {row['minutes']} minutes
Number of ingredients: {row['n_ingredients']}"""

    recipe_chunks.append({
        "text": text,
        "source": "recipe",
        "cuisine": "us",
        "recipe_name": row['name']
    })

print(f"Created {len(recipe_chunks)} US recipe chunks")

# ---------- 2. Process Indian recipes ----------
indian_recipes = pd.read_csv("data/raw/indian_recipes_sample.csv")

indian_chunks = []
for _, row in indian_recipes.iterrows():
    text = f"""Recipe: {row['name']}
Ingredients: {row['ingredients']}
Steps: {row['steps']}
Description: {row['description']}
Time to make: {row['minutes']} minutes
Number of ingredients: {row['n_ingredients']}"""

    indian_chunks.append({
        "text": text,
        "source": "recipe",
        "cuisine": "indian",
        "recipe_name": row['name']
    })

print(f"Created {len(indian_chunks)} Indian recipe chunks")

# ---------- 3. Process guideline text files ----------
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

guideline_chunks = []
guideline_dir = "data/guidelines"

for filename in os.listdir(guideline_dir):
    if filename.endswith(".txt"):
        filepath = os.path.join(guideline_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        chunks = splitter.split_text(content)
        for chunk in chunks:
            region = "indian" if filename.startswith("indian_") else "general"
            guideline_chunks.append({
                "text": chunk,
                "source": "guideline",
                "region": region,
                "source_file": filename
            })

print(f"Created {len(guideline_chunks)} guideline chunks")

# ---------- 4. Combine and save everything ----------
all_chunks = recipe_chunks + indian_chunks + guideline_chunks

with open("data/processed_chunks.json", "w", encoding="utf-8") as f:
    json.dump(all_chunks, f, indent=2)

print(f"Saved {len(all_chunks)} total chunks to data/processed_chunks.json")
