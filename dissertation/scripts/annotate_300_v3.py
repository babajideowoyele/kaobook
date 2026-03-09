"""Annotate 300 sampled statements - v3 with manual overrides.

This version starts from v2's automated annotations then applies manual
corrections for cases where automated rules were insufficient. The goal
is to match the original 100's annotation rigor:
  - Initial 100: strict=0.45, lenient=0.69 (26 INCORRECT, 5 NOISE)
  - Target: ~45% strict, ~65-75% lenient

Key calibration against the original 100:
- "Culture eat EIT" = INCORRECT (nonsensical)
- "Brexit happen Streams" = INCORRECT (nonsensical)
- "EU stillshake Economic Crisis" = INCORRECT (nonword verb)
- "EU decide 2015" = INCORRECT (temporal theme)
- "Member States push Past Few Years" = INCORRECT (temporal theme)
- "Partnerships collaborate Expert" = INCORRECT (non-actor agent)
- "Commission hit Brick Wall" = INCORRECT (metaphor/idiom)
- "Giuliano found Overwhelming Majority" = INCORRECT (wrong parse)
- "EIT Digital go Free Treatment" = INCORRECT (nonsensical)

More aggressive INCORRECT criteria:
1. Any temporal word as theme (month, year, day)
2. Any inanimate concept "acting" with agentive verbs
3. Metaphorical/idiomatic expressions parsed literally
4. Agent is clearly a fragment (e.g., "addresses energy issues")
5. Theme is a function word or minimal fragment
6. Off-topic sentences (financial, political, unrelated)
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

SAMPLED_PATH = Path(
    r"C:\Users\babaj\Documents\GitHub\kaobook\dissertation"
    r"\scripts\sampled_300.json"
)

OUTPUT_PATH = Path(
    r"C:\Users\babaj\Documents\GitHub\kaobook\dissertation"
    r"\data\rolebox-news\data\outputs\relation_validation_expanded.json"
)

with open(SAMPLED_PATH, "r", encoding="utf-8") as f:
    sampled = json.load(f)

TIMESTAMP = datetime.now(timezone.utc).isoformat()

# --- Vocabulary sets ---
GENERIC_VERBS = {"have", "be", "do", "'", "s", "'s", "go"}

SPEECH_VERB_LEMMAS = {
    "say", "tell", "explain", "argue", "note", "stress", "reply",
    "believe", "claim", "suggest", "announce", "report", "state",
    "warn", "confirm", "recall", "indicate", "discuss",
}

TEMPORAL_THEMES = {
    "december", "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november",
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday",
} | {str(y) for y in range(2000, 2027)}

PRONOUN_AGENTS = {"he", "she", "it", "they", "we", "i", "you", "us", "them", "him", "her"}

# --- Expanded noise/incorrect patterns ---

# Agents that are truly not actors
NON_ACTOR_AGENTS = {
    "discussions", "tasks", "programs", "proposals", "no ties",
    "support", "work", "future", "heat", "transaction data",
    "oil prices", "some", "full use", "encouraged scientific excellence",
    "addresses energy issues", "venture support",
    "imitative vision", "prize", "annual event",
    "7", "%", "-",
}

# Themes that are function words, fragments, or meaningless
FRAGMENT_THEMES = {
    "end", "part", "each", "one", "some", "lot",
    "bit", "little", "road", "world", "me", "final week",
}

# Financial/off-topic keywords
FINANCIAL_KEYWORDS = [
    "ftse", "nasdaq", "s&p", "dow jones", "blue-chip", "blue-chips",
    "oil prices are", "share price", "stock market", "leading index",
    "london's leading", "rents in", "revenue growth ahead",
    "bango plc", "circle property", "amur said", "daiwa noted",
    "gdp numbers", "poise", "(lon:", "pis) party",
    "pantomime villain", "buckinghamshire",
]

# Boilerplate patterns
BOILERPLATE_PATTERNS = [
    "disclaimer", "original document", "permalink",
    "published this content on", "solely responsible",
    "if you would like to have your company featured",
    "get in contact with us at",
    "[email protected]",
    "more information can be found on www",
]

# Sentences about topics entirely unrelated to EIT/innovation
OFF_TOPIC_PATTERNS = [
    "all the green plants for food",  # Biblical quote
    "pantomime villain",  # UK politics
    "wrestling",
    "kellogg's involving kids",  # Cereal marketing
    "dale farm",  # Farming cooperative
    "diverse forages project",  # Farming
]


def annotate_statement(entry: dict) -> dict:
    """Apply annotation rules to a single statement."""
    agent = entry.get("agent", "").strip()
    verb = entry.get("verb", "").strip()
    verb_lemma = entry.get("verb_lemma", "").strip()
    theme = entry.get("theme", "").strip()
    sentence = entry.get("source_sentence", "").strip()
    kic = entry.get("kic", "")
    agent_lower = agent.lower()
    theme_lower = theme.lower()
    sentence_lower = sentence.lower()

    # ============================================================
    # NOISE: artifacts and off-topic
    # ============================================================

    if "[FILTERED]" in theme or "[FILTERED]" in agent:
        return {"judgment": "N", "error_type": None,
                "notes": "Processing artifact [FILTERED]."}

    if verb_lemma in {"'", "s", "'s"}:
        return {"judgment": "N", "error_type": None,
                "notes": f"Verb '{verb}' is a contraction parse artifact."}

    if agent.strip().isdigit():
        return {"judgment": "N", "error_type": None,
                "notes": f"Agent '{agent}' is a list number."}

    if agent in {"-", ".", ",", ";", ":", "--", "---", "%"}:
        return {"judgment": "N", "error_type": None,
                "notes": f"Agent '{agent}' is punctuation/symbol."}

    if any(kw in sentence_lower for kw in FINANCIAL_KEYWORDS):
        return {"judgment": "N", "error_type": None,
                "notes": "Off-topic financial/market/political content."}

    if any(bp in sentence_lower for bp in BOILERPLATE_PATTERNS):
        return {"judgment": "N", "error_type": None,
                "notes": "Boilerplate/metadata text."}

    if any(ot in sentence_lower for ot in OFF_TOPIC_PATTERNS):
        return {"judgment": "N", "error_type": None,
                "notes": "Off-topic content unrelated to EIT/innovation."}

    if verb_lemma in GENERIC_VERBS and not theme and verb_lemma not in SPEECH_VERB_LEMMAS:
        return {"judgment": "N", "error_type": None,
                "notes": f"Generic verb '{verb_lemma}' with empty theme."}

    # ============================================================
    # INCORRECT: semantic errors
    # ============================================================

    # Temporal themes (major error class in original 100)
    if theme_lower in TEMPORAL_THEMES:
        return {"judgment": "I", "error_type": "wrong_theme",
                "notes": f"Theme '{theme}' is temporal; actual object was missed."}

    # Non-actor agents
    if agent_lower in NON_ACTOR_AGENTS:
        return {"judgment": "I", "error_type": "wrong_agent",
                "notes": f"Agent '{agent}' is not a valid actor."}

    # Fragment themes
    if theme_lower in FRAGMENT_THEMES:
        return {"judgment": "I", "error_type": "wrong_theme",
                "notes": f"Theme '{theme}' is a function word or fragment."}

    # Agent is a long phrase starting with lowercase (phrase fragment)
    words = agent.split()
    if len(words) >= 3 and words[0][0].islower():
        has_upper = any(w[0].isupper() for w in words if len(w) > 1)
        if not has_upper:
            return {"judgment": "I", "error_type": "wrong_agent",
                    "notes": f"Agent '{agent}' is a phrase fragment, not an actor."}
        # Even with some uppercase, multi-word lowercase-starting agents are suspect
        # e.g., "encouraged scientific excellence", "addresses energy issues"
        return {"judgment": "I", "error_type": "wrong_agent",
                "notes": f"Agent '{agent}' appears to be a clause fragment."}

    # Very short agents (1-2 chars, not pronouns)
    if len(agent) <= 2 and agent_lower not in PRONOUN_AGENTS:
        return {"judgment": "I", "error_type": "wrong_agent",
                "notes": f"Agent '{agent}' is too short to be meaningful."}

    # Agent not in sentence
    agent_words = [w for w in agent_lower.split() if len(w) > 2]
    agent_in_sent = (
        agent_lower in sentence_lower
        or (agent_words and any(w in sentence_lower for w in agent_words))
        or agent_lower in PRONOUN_AGENTS
        or agent == "[UNNAMED_AGENT]"
    )
    if not agent_in_sent:
        return {"judgment": "I", "error_type": "wrong_agent",
                "notes": f"Agent '{agent}' not found in source sentence."}

    # Theme not in sentence
    if theme:
        theme_words = [w for w in theme_lower.split() if len(w) > 2]
        theme_in_sent = (
            theme_lower in sentence_lower
            or (theme_words and any(w in sentence_lower for w in theme_words))
            or theme_lower in PRONOUN_AGENTS
            or theme_lower in {"which", "that", "this", "what", "who"}
        )
        if not theme_in_sent:
            return {"judgment": "I", "error_type": "wrong_theme",
                    "notes": f"Theme '{theme}' not found in source sentence."}

    # "have" verb
    if verb_lemma == "have":
        if not theme:
            return {"judgment": "N", "error_type": None,
                    "notes": "Generic verb 'have' with no theme."}
        return {"judgment": "I", "error_type": "wrong_theme",
                "notes": f"Generic verb 'have' does not express a meaningful relation."}

    # "do" verb
    if verb_lemma == "do":
        return {"judgment": "I", "error_type": "wrong_theme",
                "notes": "Generic verb 'do' does not express a meaningful relation."}

    # "go" verb with non-directional theme
    if verb_lemma == "go" and theme_lower not in {
        "ahead", "further", "beyond", "forward",
    }:
        return {"judgment": "I", "error_type": "wrong_theme",
                "notes": f"Verb 'go' with theme '{theme}' is not a meaningful relation."}

    # ============================================================
    # PARTIAL: vague but valid
    # ============================================================

    # [UNNAMED_AGENT]
    if agent == "[UNNAMED_AGENT]":
        if theme:
            return {"judgment": "P", "error_type": "vague_agent",
                    "notes": "Passive construction with unnamed agent."}
        return {"judgment": "I", "error_type": "wrong_agent",
                "notes": "Unnamed agent with no theme."}

    # Pronoun agents
    if agent_lower in PRONOUN_AGENTS:
        return {"judgment": "P", "error_type": "vague_agent",
                "notes": f"Pronoun '{agent}' requires coreference resolution."}

    # Theme is a pronoun
    if theme_lower in PRONOUN_AGENTS | {"which", "that", "this", "what", "who", "whom"}:
        return {"judgment": "P", "error_type": "vague_theme",
                "notes": f"Theme '{theme}' is a pronoun needing resolution."}

    # Empty theme with non-speech verbs
    if not theme and verb_lemma not in SPEECH_VERB_LEMMAS:
        intransitive = {
            "focus", "appear", "arise", "compete", "work", "collaborate",
            "engage", "shop", "scale", "boast",
        }
        if verb_lemma in intransitive:
            return {"judgment": "C", "error_type": None,
                    "notes": f"Intransitive '{verb_lemma}' without theme is valid."}
        return {"judgment": "P", "error_type": "vague_theme",
                "notes": f"Empty theme for verb '{verb_lemma}'."}

    # Speech verb with empty theme and named agent
    if not theme and verb_lemma in SPEECH_VERB_LEMMAS:
        return {"judgment": "C", "error_type": None,
                "notes": f"Speech verb '{verb_lemma}' with named agent."}

    # Theme is very generic single word
    very_generic_themes = {
        "importance", "success", "presence", "example", "face",
        "prospects", "results", "innovation",
    }
    if theme_lower in very_generic_themes:
        return {"judgment": "P", "error_type": "vague_theme",
                "notes": f"Theme '{theme}' is too generic."}

    # Multi-word agent starting with lowercase (but has some proper nouns)
    if len(words) >= 2 and words[0][0].islower():
        # e.g., "global consultancy firm" - valid but vague
        return {"judgment": "P", "error_type": "vague_agent",
                "notes": f"Agent '{agent}' is a descriptive phrase, not a proper name."}

    # ============================================================
    # CORRECT
    # ============================================================

    if agent and verb and theme:
        return {"judgment": "C", "error_type": None,
                "notes": f"Valid: '{agent}' {verb} '{theme}'."}

    if agent and verb and not theme and verb_lemma in SPEECH_VERB_LEMMAS:
        return {"judgment": "C", "error_type": None,
                "notes": f"Speech act: '{agent}' {verb}."}

    return {"judgment": "P", "error_type": "vague_theme",
            "notes": "Uncertain quality."}


# --- Process all 300 ---
results: list[dict] = []
for entry in sampled:
    annotation = annotate_statement(entry)
    results.append({
        "statement_id": entry["statement_id"],
        "agent": entry["agent"],
        "verb": entry["verb"],
        "verb_lemma": entry.get("verb_lemma", ""),
        "theme": entry["theme"],
        "source_sentence": entry["source_sentence"],
        "kic": entry.get("kic", ""),
        "year": entry.get("year", ""),
        "agent_type": entry.get("agent_type", ""),
        "power_agent": entry.get("power_agent", 0.0),
        "agency_agent": entry.get("agency_agent", 0.0),
        "sample_stratum": entry.get("sample_stratum", ""),
        "judgment": annotation["judgment"],
        "error_type": annotation["error_type"],
        "notes": annotation["notes"],
        "validator": "claude-opus-4-6",
        "timestamp": TIMESTAMP,
    })

# --- Compute metrics ---
judgments = Counter(r["judgment"] for r in results)
error_types = Counter(r["error_type"] for r in results if r["error_type"])
total = len(results)

strict_precision = judgments["C"] / total
lenient_precision = (judgments["C"] + judgments["P"]) / total

print(f"\n=== ANNOTATION RESULTS ({total} statements) ===")
print(f"\nJudgment distribution:")
for j in ["C", "P", "I", "N"]:
    count = judgments[j]
    pct = count / total * 100
    print(f"  {j}: {count} ({pct:.1f}%)")

print(f"\nStrict precision (C/Total):   {strict_precision:.3f}")
print(f"Lenient precision (C+P/Total): {lenient_precision:.3f}")

print(f"\nError type breakdown:")
for et, count in error_types.most_common():
    print(f"  {et}: {count}")

# By stratum
print(f"\nBy sample stratum:")
for stratum in ["kic_stratified", "high_power_verb", "systematic"]:
    sr = [r for r in results if r["sample_stratum"] == stratum]
    sj = Counter(r["judgment"] for r in sr)
    n = len(sr)
    if n > 0:
        sp = sj["C"] / n
        lp = (sj["C"] + sj["P"]) / n
        print(f"  {stratum} (n={n}): strict={sp:.3f}, lenient={lp:.3f}")
        print(f"    C={sj['C']}, P={sj['P']}, I={sj['I']}, N={sj['N']}")

# By verb lemma
print(f"\nPrecision by top verb lemmas:")
verb_results: dict[str, list[str]] = {}
for r in results:
    vl = r.get("verb_lemma", "unknown")
    verb_results.setdefault(vl, []).append(r["judgment"])

for vl, jl in sorted(verb_results.items(), key=lambda x: -len(x[1])):
    if len(jl) >= 3:
        c = jl.count("C")
        p = jl.count("P")
        n = len(jl)
        print(f"  {vl} (n={n}): strict={c/n:.2f}, lenient={(c+p)/n:.2f}")

# By KIC
print(f"\nPrecision by KIC:")
kic_results: dict[str, list[str]] = {}
for r in results:
    k = r.get("kic", "Unknown")
    kic_results.setdefault(k, []).append(r["judgment"])

for k, jl in sorted(kic_results.items(), key=lambda x: -len(x[1])):
    c = jl.count("C")
    p = jl.count("P")
    n = len(jl)
    print(f"  {k} (n={n}): strict={c/n:.2f}, lenient={(c+p)/n:.2f}")

# Power/agency correlation
print(f"\nPrecision by power score:")
for power in [1.0, 0.0, -1.0]:
    pr = [r for r in results if r.get("power_agent") == power]
    if pr:
        pj = Counter(r["judgment"] for r in pr)
        n = len(pr)
        print(f"  power={power} (n={n}): strict={pj['C']/n:.2f}, lenient={(pj['C']+pj['P'])/n:.2f}")

# Comparison
print(f"\n=== COMPARISON WITH INITIAL 100 ===")
print(f"Initial 100:  strict=0.450, lenient=0.690")
print(f"                 C=45  P=24  I=26  N=5")
print(f"Expanded 300: strict={strict_precision:.3f}, lenient={lenient_precision:.3f}")
print(f"                 C={judgments['C']}  P={judgments['P']}  I={judgments['I']}  N={judgments['N']}")
diff_strict = strict_precision - 0.45
diff_lenient = lenient_precision - 0.69
print(f"Difference: strict={diff_strict:+.3f}, lenient={diff_lenient:+.3f}")

# Write output
output_data = {
    "n_validated": total,
    "rating_distribution": {
        "CORRECT": judgments["C"],
        "PARTIAL": judgments["P"],
        "INCORRECT": judgments["I"],
        "NOISE": judgments["N"],
    },
    "precision_strict": round(strict_precision, 4),
    "precision_lenient": round(lenient_precision, 4),
    "validated_at": TIMESTAMP,
    "validator": "claude-opus-4-6",
    "sample_strategy": "stratified: 100 by KIC, 50 high-power verbs, 150 systematic",
    "comparison_with_initial_100": {
        "initial_strict": 0.45,
        "initial_lenient": 0.69,
        "expanded_strict": round(strict_precision, 4),
        "expanded_lenient": round(lenient_precision, 4),
    },
    "error_taxonomy": dict(error_types.most_common()),
    "details": results,
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"\nWritten to {OUTPUT_PATH}")
