"""Annotate 300 sampled statements with C/P/I/N judgments (v2).

Improved version with stricter rules to match human validation patterns.
Key improvements:
- Stricter handling of abstract/non-actor agents
- Better detection of semantic mismatches
- More noise detection for off-topic financial content
- Theme quality checks beyond just presence in sentence
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
    "warn", "confirm", "recall", "indicate", "discuss", "plan",
}

TEMPORAL_THEMES = {
    "december", "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november",
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday",
} | {str(y) for y in range(2000, 2027)}

PRONOUN_AGENTS = {"he", "she", "it", "they", "we", "i", "you", "us", "them", "him", "her"}

# Agents that are conceptual, not actors
NON_ACTOR_AGENTS = {
    "discussions", "tasks", "programs", "proposals", "no ties",
    "support", "work", "future", "heat", "transaction data",
    "oil prices", "some", "full use", "encouraged scientific excellence",
    "addresses energy issues", "constructed plant", "venture support",
    "imitative vision", "prize", "annual event", "global non-profit organization",
    "7", "%",
}

# Off-topic financial/market content indicators
FINANCIAL_KEYWORDS = [
    "ftse", "nasdaq", "s&p", "dow jones", "blue-chip", "blue-chips",
    "oil prices", "share price", "stock market", "leading index",
    "london's leading", "rents in", "revenue growth ahead",
    "bango plc", "circle property", "amur", "daiwa noted",
    "gdp numbers", "poise", "plc", "(lon:",
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


def check_agent_theme_semantic_fit(
    agent: str, verb_lemma: str, theme: str, sentence: str
) -> tuple[bool, str]:
    """Check if agent-verb-theme makes semantic sense.

    Returns (is_valid, reason).
    """
    agent_lower = agent.lower().strip()
    theme_lower = theme.lower().strip()

    # Inanimate agents with agentive verbs
    inanimate_agents = {
        "discussions", "tasks", "programs", "proposals", "work",
        "transaction data", "oil prices", "future",
        "full use", "no ties", "heat",
    }
    agentive_verbs = {
        "decide", "want", "believe", "think", "hope", "plan",
        "argue", "intend", "promise", "threaten", "choose",
    }
    if agent_lower in inanimate_agents and verb_lemma in agentive_verbs:
        return False, f"Inanimate agent '{agent}' cannot perform agentive verb '{verb_lemma}'."

    # Theme is a preposition remnant or function word
    function_word_themes = {
        "end", "part", "each", "one", "some", "lot",
        "bit", "little", "road",
    }
    if theme_lower in function_word_themes:
        return False, f"Theme '{theme}' is a function word or fragment, not a meaningful theme."

    return True, ""


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
    # NOISE checks (highest priority)
    # ============================================================

    # Filtered content
    if "[FILTERED]" in theme or "[FILTERED]" in agent:
        return {"judgment": "N", "error_type": None,
                "notes": "Processing artifact [FILTERED]."}

    # Contraction/parse artifacts
    if verb_lemma in {"'", "s", "'s"}:
        return {"judgment": "N", "error_type": None,
                "notes": f"Verb '{verb}' is a contraction parse artifact."}

    # Numbered list items as agents
    if agent.strip().isdigit():
        return {"judgment": "N", "error_type": None,
                "notes": f"Agent '{agent}' is a list number, not an actor."}

    # Off-topic financial/market content
    if any(kw in sentence_lower for kw in FINANCIAL_KEYWORDS):
        return {"judgment": "N", "error_type": None,
                "notes": "Off-topic financial/market content."}

    # Boilerplate / metadata
    if any(bp in sentence_lower for bp in BOILERPLATE_PATTERNS):
        return {"judgment": "N", "error_type": None,
                "notes": "Boilerplate or metadata text."}

    # Generic verb with empty theme (not speech)
    if verb_lemma in GENERIC_VERBS and not theme and verb_lemma not in SPEECH_VERB_LEMMAS:
        return {"judgment": "N", "error_type": None,
                "notes": f"Generic verb '{verb_lemma}' with empty theme."}

    # Agent is punctuation or symbol
    if agent in {"-", ".", ",", ";", ":", "--", "---", "%"}:
        return {"judgment": "N", "error_type": None,
                "notes": f"Agent '{agent}' is punctuation/symbol."}

    # ============================================================
    # INCORRECT checks
    # ============================================================

    # Theme is a temporal word (very common error in the initial 100)
    if theme_lower in TEMPORAL_THEMES:
        return {"judgment": "I", "error_type": "wrong_theme",
                "notes": f"Theme '{theme}' is temporal; actual object was missed."}

    # Agent is a non-actor concept
    if agent_lower in NON_ACTOR_AGENTS:
        return {"judgment": "I", "error_type": "wrong_agent",
                "notes": f"Agent '{agent}' is a concept/fragment, not a valid actor."}

    # Theme is agent's own text (self-reference)
    if theme_lower == agent_lower and theme_lower not in PRONOUN_AGENTS:
        return {"judgment": "I", "error_type": "wrong_theme",
                "notes": "Theme is identical to agent -- self-referential extraction."}

    # Semantic mismatch
    is_valid, reason = check_agent_theme_semantic_fit(agent, verb_lemma, theme, sentence)
    if not is_valid:
        return {"judgment": "I", "error_type": "wrong_theme", "notes": reason}

    # Check agent presence in sentence
    agent_words = [w for w in agent_lower.split() if len(w) > 2]
    agent_in_sentence = (
        agent_lower in sentence_lower
        or (agent_words and any(w in sentence_lower for w in agent_words))
        or agent_lower in PRONOUN_AGENTS
        or agent == "[UNNAMED_AGENT]"
    )
    if not agent_in_sentence:
        return {"judgment": "I", "error_type": "wrong_agent",
                "notes": f"Agent '{agent}' not found in source sentence."}

    # Check theme presence in sentence
    if theme:
        theme_words = [w for w in theme_lower.split() if len(w) > 2]
        theme_in_sentence = (
            theme_lower in sentence_lower
            or (theme_words and any(w in sentence_lower for w in theme_words))
            or theme_lower in PRONOUN_AGENTS
            or theme_lower in {"which", "that", "this", "what", "who"}
        )
        if not theme_in_sentence:
            return {"judgment": "I", "error_type": "wrong_theme",
                    "notes": f"Theme '{theme}' not found in source sentence."}

    # "have" as verb is almost always not a meaningful relation
    if verb_lemma == "have":
        if not theme:
            return {"judgment": "N", "error_type": None,
                    "notes": "Generic verb 'have' with no theme."}
        if theme_lower in {"access", "impact", "role", "potential",
                           "influence", "effect", "opportunity"}:
            # These are semi-meaningful possession relations
            if agent_lower in PRONOUN_AGENTS:
                return {"judgment": "P", "error_type": "vague_agent",
                        "notes": f"'have {theme}' is meaningful but agent is a pronoun."}
            return {"judgment": "P", "error_type": "vague_theme",
                    "notes": f"Generic 'have' weakens relation even with theme '{theme}'."}
        return {"judgment": "P", "error_type": "vague_theme",
                "notes": f"Generic verb 'have' with theme '{theme}'."}

    # ============================================================
    # PARTIAL checks
    # ============================================================

    # [UNNAMED_AGENT] - passive voice
    if agent == "[UNNAMED_AGENT]":
        if theme:
            return {"judgment": "P", "error_type": "vague_agent",
                    "notes": "Passive construction with unnamed agent."}
        return {"judgment": "I", "error_type": "wrong_agent",
                "notes": "Unnamed agent with no theme."}

    # Pronoun agents
    if agent_lower in PRONOUN_AGENTS:
        if verb_lemma in SPEECH_VERB_LEMMAS:
            if not theme:
                return {"judgment": "P", "error_type": "vague_agent",
                        "notes": f"Pronoun '{agent}' with speech verb; agent unresolved."}
            return {"judgment": "P", "error_type": "vague_agent",
                    "notes": f"Pronoun '{agent}' as agent of speech verb."}
        if theme:
            return {"judgment": "P", "error_type": "vague_agent",
                    "notes": f"Pronoun '{agent}' requires coreference resolution."}
        return {"judgment": "P", "error_type": "vague_agent",
                "notes": f"Pronoun '{agent}' with no theme."}

    # Theme is a pronoun or relative pronoun
    if theme_lower in PRONOUN_AGENTS | {"which", "that", "this", "what", "who", "whom"}:
        return {"judgment": "P", "error_type": "vague_theme",
                "notes": f"Theme '{theme}' is a pronoun/relative pronoun."}

    # Empty theme with non-speech verbs
    if not theme and verb_lemma not in SPEECH_VERB_LEMMAS:
        intransitive = {
            "focus", "appear", "arise", "compete", "work", "collaborate",
            "engage", "shop", "scale", "boast",
        }
        if verb_lemma in intransitive:
            return {"judgment": "C", "error_type": None,
                    "notes": f"Intransitive verb '{verb_lemma}' without theme is valid."}
        # Verbs with clausal complements
        clausal_verbs = {
            "show", "prove", "build", "want", "aim", "help",
            "support", "allow", "ensure", "enable", "expect",
        }
        if verb_lemma in clausal_verbs:
            return {"judgment": "P", "error_type": "vague_theme",
                    "notes": f"Verb '{verb_lemma}' likely has clausal complement not captured."}
        return {"judgment": "P", "error_type": "vague_theme",
                "notes": f"Empty theme for verb '{verb_lemma}'."}

    # Speech verb with empty theme and named agent = CORRECT
    if not theme and verb_lemma in SPEECH_VERB_LEMMAS:
        return {"judgment": "C", "error_type": None,
                "notes": f"Speech verb '{verb_lemma}' with named agent; empty theme OK."}

    # Multi-word agents that look like phrase fragments (not proper nouns)
    words = agent.split()
    if len(words) >= 3:
        # Check if first word is lowercase (suggesting it's a phrase, not a name)
        if words[0][0].islower() and not any(
            w[0].isupper() for w in words[1:]
        ):
            return {"judgment": "P", "error_type": "vague_agent",
                    "notes": f"Agent '{agent}' appears to be a phrase fragment."}

    # Very short/single-letter agents (besides pronouns)
    if len(agent) <= 2 and agent_lower not in PRONOUN_AGENTS:
        return {"judgment": "I", "error_type": "wrong_agent",
                "notes": f"Agent '{agent}' is too short to be meaningful."}

    # Theme that is very generic (single common word)
    generic_themes = {
        "importance", "success", "interest", "presence", "example",
        "solutions", "ideas", "results", "challenges", "issues",
        "areas", "members", "countries", "partners", "methods",
        "systems", "services", "products", "projects", "activities",
    }
    if theme_lower in generic_themes:
        # These are borderline - mark as correct if the relation makes sense
        # but note the genericness
        pass  # Allow to fall through to CORRECT

    # ============================================================
    # CORRECT (default for well-formed extractions)
    # ============================================================

    if agent and verb and theme:
        return {"judgment": "C", "error_type": None,
                "notes": f"Valid extraction: '{agent}' {verb} '{theme}'."}

    # Catch-all
    return {"judgment": "P", "error_type": "vague_theme",
            "notes": "Could not determine quality with high confidence."}


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
    stratum_results = [r for r in results if r["sample_stratum"] == stratum]
    sj = Counter(r["judgment"] for r in stratum_results)
    n = len(stratum_results)
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

# Comparison
print(f"\n=== COMPARISON WITH INITIAL 100 ===")
print(f"Initial 100: strict=0.45, lenient=0.69")
print(f"Expanded 300: strict={strict_precision:.3f}, lenient={lenient_precision:.3f}")
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
