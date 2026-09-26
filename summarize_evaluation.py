import json

with open("evaluation_results.json", "r", encoding="utf-8") as f:
    results = json.load(f)

print(f"{'#':<3} {'Category':<30} {'Question':<45}")
print("=" * 100)

for i, r in enumerate(results, 1):
    q = r["question"]
    q_short = (q[:42] + "...") if len(q) > 45 else q
    print(f"{i:<3} {r['category']:<30} {q_short:<45}")

print("\n\nFull answers are in evaluation_results.json for detailed review.")
print(f"Total test cases: {len(results)}")

# Group by category for a quick coverage check
categories = {}
for r in results:
    categories[r["category"]] = categories.get(r["category"], 0) + 1

print("\nCoverage by category:")
for cat, count in categories.items():
    print(f"  - {cat}: {count} test(s)")