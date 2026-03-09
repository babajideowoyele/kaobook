"""Sample 300 statements from the news_statements.json for annotation.

Stratification:
- 100 stratified by KIC (~10 per KIC)
- 50 high-power/agency verbs
- 150 from remaining pool (systematic every-Nth)
"""

import json
from pathlib import Path
from collections import Counter
import random

random.seed(42)

STATEMENTS_PATH = Path(
    r"C:\Users\babaj\Documents\GitHub\kaobook\dissertation"
    r"\data\rolebox-news\data\outputs\annotations\news_statements.json"
)

OUTPUT_PATH = Path(
    r"C:\Users\babaj\Documents\GitHub\kaobook\dissertation"
    r"\scripts\sampled_300.json"
)

HIGH_POWER_VERBS = {
    "publish", "develop", "fund", "create", "launch", "support",
    "accelerate", "invest", "transform", "disrupt", "enable",
    "establish", "build", "lead", "drive", "promote", "implement",
    "deliver", "expand", "scale"
}

with open(STATEMENTS_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

statements = data["statements"]
print(f"Total statements: {len(statements)}")

# --- Understand the data ---
kics = Counter()
verbs = Counter()
agent_types = Counter()
for s in statements:
    p = s.get("provenance", {})
    kics[p.get("kic", "UNKNOWN")] += 1
    verbs[p.get("verb_lemma", "UNKNOWN")] += 1
    agent_types[p.get("agent_type", "UNKNOWN")] += 1

print("\n--- KIC distribution ---")
for k, v in kics.most_common():
    print(f"  {k}: {v}")

print("\n--- Agent type distribution ---")
for k, v in agent_types.most_common():
    print(f"  {k}: {v}")

print(f"\n--- Top 30 verbs ---")
for k, v in verbs.most_common(30):
    print(f"  {k}: {v}")

# --- Check for needs_review flag ---
flagged = [s for s in statements if s.get("needs_review", False)]
print(f"\n--- Flagged needs_review: {len(flagged)} ---")

# --- Sampling ---
selected_ids: set[int] = set()

# 1) KIC-stratified: ~10 per KIC
kic_groups: dict[str, list[int]] = {}
for i, s in enumerate(statements):
    kic = s.get("provenance", {}).get("kic", "UNKNOWN")
    kic_groups.setdefault(kic, []).append(i)

kic_sample: list[int] = []
for kic, indices in sorted(kic_groups.items()):
    n_sample = min(10, len(indices))
    sampled = random.sample(indices, n_sample)
    kic_sample.extend(sampled)
    print(f"  KIC '{kic}': sampled {n_sample} from {len(indices)}")

selected_ids.update(kic_sample)
print(f"After KIC stratification: {len(selected_ids)} unique")

# 2) High-power/agency verbs: 50
high_power_pool = [
    i for i, s in enumerate(statements)
    if s.get("provenance", {}).get("verb_lemma", "") in HIGH_POWER_VERBS
    and i not in selected_ids
]
print(f"\nHigh-power verb pool: {len(high_power_pool)}")
hp_sample = random.sample(high_power_pool, min(50, len(high_power_pool)))
selected_ids.update(hp_sample)
print(f"After high-power sampling: {len(selected_ids)} unique")

# 3) Fill remaining to 300 with systematic sampling
remaining_needed = 300 - len(selected_ids)
remaining_pool = [i for i in range(len(statements)) if i not in selected_ids]
step = max(1, len(remaining_pool) // remaining_needed)
systematic_sample = remaining_pool[::step][:remaining_needed]
selected_ids.update(systematic_sample)
print(f"\nAfter systematic fill: {len(selected_ids)} unique")

# --- Build output ---
sampled = []
for idx in sorted(selected_ids):
    s = statements[idx]
    p = s.get("provenance", {})
    sampled.append({
        "statement_id": s["id"],
        "index_in_file": idx,
        "agent": p.get("agent_text", s.get("actor", "")),
        "verb": p.get("verb", ""),
        "verb_lemma": p.get("verb_lemma", ""),
        "theme": p.get("theme_text", ""),
        "source_sentence": s.get("text", ""),
        "kic": p.get("kic", ""),
        "year": p.get("year", ""),
        "agent_type": p.get("agent_type", ""),
        "power_agent": p.get("power_agent", 0.0),
        "agency_agent": p.get("agency_agent", 0.0),
        "sample_stratum": (
            "kic_stratified" if idx in set(kic_sample)
            else "high_power_verb" if idx in set(hp_sample)
            else "systematic"
        ),
    })

print(f"\nFinal sample: {len(sampled)} statements")
print(f"Strata: {Counter(s['sample_stratum'] for s in sampled)}")

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(sampled, f, indent=2, ensure_ascii=False)

print(f"\nWritten to {OUTPUT_PATH}")
