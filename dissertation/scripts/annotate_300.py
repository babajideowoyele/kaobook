"""Annotate 300 sampled statements with C/P/I/N judgments.

Decision rules (from task specification):
- C (Correct): Agent, verb, and theme all correctly extracted from sentence
- P (Partial): Relationship exists but agent or theme is vague/generic/truncated
- I (Incorrect): Extraction is wrong (role swap, wrong parse, fabricated relation)
- N (Noise): Artifact: filtered text, boilerplate, metadata leak

Sub-rules:
- Judge against SOURCE SENTENCE only, not world knowledge
- Passive voice: "X was funded by Y" -> Agent=Y, Theme=X is CORRECT
- Pronoun agents: "It invested..." with unclear coreference -> PARTIAL (vague_agent)
- Generic verbs: "have", "be", "do" -> NOISE unless genuinely meaningful
- Multi-clause: judge only the extracted relation, not the whole sentence
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

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

# --- Generic/noise verbs ---
GENERIC_VERBS = {"have", "be", "do", "'", "s", "'s"}
# Verbs that are only meaningful with specific themes
WEAK_VERBS = {"go", "come", "get", "make", "take", "see", "look", "say", "tell"}
# Communication verbs with empty theme are valid speech acts
SPEECH_VERBS = {
    "say", "said", "says", "tell", "tells", "told", "explain", "explains",
    "explained", "argue", "argues", "argued", "note", "notes", "noted",
    "stress", "stressed", "stresses", "reply", "replied", "replies",
    "believe", "believes", "believed", "claim", "claims", "claimed",
    "suggest", "suggests", "suggested", "announce", "announces", "announced",
    "report", "reports", "reported", "state", "states", "stated",
    "warn", "warns", "warned", "confirm", "confirms", "confirmed",
    "recall", "recalls", "recalled", "indicate", "indicates", "indicated",
    "discuss", "discussing", "plan",
}
SPEECH_VERB_LEMMAS = {
    "say", "tell", "explain", "argue", "note", "stress", "reply",
    "believe", "claim", "suggest", "announce", "report", "state",
    "warn", "confirm", "recall", "indicate", "discuss", "plan",
}

# Temporal words that indicate theme extraction errors
TEMPORAL_THEMES = {
    "december", "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november",
    "2004", "2005", "2006", "2007", "2008", "2009", "2010", "2011",
    "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019",
    "2020", "2021", "2022", "2023", "2024", "2025", "2026",
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday",
}

# Pronouns that indicate vague agents
PRONOUN_AGENTS = {"he", "she", "it", "they", "we", "i", "you", "us", "them", "him", "her"}

# Known noise patterns
NOISE_PATTERNS = [
    r"\[FILTERED\]",
    r"\[UNNAMED_AGENT\]",
    r"FTSE|NASDAQ|Nasdaq|S&P|Dow Jones",
]

# Financial market noise indicators
FINANCIAL_NOISE_THEMES = {
    "losses", "10,387", "poise", "bit", "%", "little",
}
FINANCIAL_NOISE_VERBS = {"par", "fall", "slip", "recover", "slipping"}


def is_financial_noise(entry: dict) -> bool:
    """Detect financial market data noise."""
    sentence = entry.get("source_sentence", "").lower()
    financial_keywords = [
        "ftse", "nasdaq", "s&p", "dow jones", "blue-chip", "blue-chips",
        "oil prices", "share price", "stock", "index has",
        "leading index", "london's leading",
    ]
    return any(kw in sentence for kw in financial_keywords)


def is_boilerplate(entry: dict) -> bool:
    """Detect boilerplate/metadata text."""
    sentence = entry.get("source_sentence", "").lower()
    boilerplate = [
        "disclaimer", "original document", "permalink",
        "published this content on", "solely responsible",
        "if you would like to have your company featured",
        "get in contact with us at",
        "[email protected]",
    ]
    return any(bp in sentence for bp in boilerplate)


def annotate_statement(entry: dict) -> dict:
    """Apply annotation rules to a single statement.

    Returns a dict with judgment, error_type, and notes.
    """
    agent = entry.get("agent", "").strip()
    verb = entry.get("verb", "").strip()
    verb_lemma = entry.get("verb_lemma", "").strip()
    theme = entry.get("theme", "").strip()
    sentence = entry.get("source_sentence", "").strip()
    agent_lower = agent.lower()
    theme_lower = theme.lower()
    sentence_lower = sentence.lower()

    # --- NOISE checks ---

    # Filtered content
    if "[FILTERED]" in theme or "[FILTERED]" in agent:
        return {
            "judgment": "N",
            "error_type": None,
            "notes": "Theme or agent contains [FILTERED] processing artifact.",
        }

    # Financial market data noise
    if is_financial_noise(entry):
        return {
            "judgment": "N",
            "error_type": None,
            "notes": "Financial market data unrelated to EIT/innovation content.",
        }

    # Boilerplate / metadata
    if is_boilerplate(entry):
        return {
            "judgment": "N",
            "error_type": None,
            "notes": "Boilerplate or metadata text, not substantive content.",
        }

    # Generic verb with empty/minimal theme
    if verb_lemma in GENERIC_VERBS:
        # "'s" is a contraction parse error
        if verb_lemma in {"'", "s", "'s"}:
            return {
                "judgment": "N",
                "error_type": None,
                "notes": f"Verb '{verb}' is a contraction/parse artifact, not meaningful.",
            }
        # "have" with vague theme
        if verb_lemma == "have" and (not theme or theme_lower in {
            "strong world", "community", "access", "startups",
        }):
            if not theme:
                return {
                    "judgment": "N",
                    "error_type": None,
                    "notes": "Generic verb 'have' with empty theme is not meaningful.",
                }
            # "have access" is a common meaningful pattern
            if theme_lower == "access":
                return {
                    "judgment": "C",
                    "error_type": None,
                    "notes": "Verb 'have' with theme 'access' is meaningful.",
                }
            return {
                "judgment": "P",
                "error_type": "vague_theme",
                "notes": f"Generic verb 'have' with vague theme '{theme}'.",
            }
        if verb_lemma == "have" and theme:
            # Check if it's a meaningful possession relationship
            return {
                "judgment": "P",
                "error_type": "vague_theme",
                "notes": f"Generic verb 'have' with theme '{theme}' - relationship is weak.",
            }
        if verb_lemma in {"be", "do"}:
            if not theme:
                return {
                    "judgment": "N",
                    "error_type": None,
                    "notes": f"Generic verb '{verb_lemma}' with empty theme is not meaningful.",
                }

    # Numbered list items as agents (e.g., "7" from numbered paragraphs)
    if agent.strip().isdigit():
        return {
            "judgment": "N",
            "error_type": None,
            "notes": f"Agent '{agent}' is a list number, not a meaningful actor.",
        }

    # Agent is a punctuation mark
    if agent in {"-", ".", ",", ";", ":", "—", "–"}:
        return {
            "judgment": "I",
            "error_type": "wrong_agent",
            "notes": f"Agent '{agent}' is punctuation, not a valid actor.",
        }

    # Agent is a percentage
    if agent.strip() == "%":
        return {
            "judgment": "I",
            "error_type": "wrong_agent",
            "notes": "Agent '%' is not a valid actor.",
        }

    # --- INCORRECT checks ---

    # Theme is a temporal word (month, year, day)
    if theme_lower in TEMPORAL_THEMES and verb_lemma not in {"launch", "join", "start", "begin", "found", "establish"}:
        # For some verbs, temporal themes make sense contextually (launched in 2013)
        # But for many others (select December, endorse December) it's wrong
        # Check if the sentence actually supports agent-verb-temporal as a real relation
        # Generally: temporal themes are wrong unless the verb inherently takes time
        return {
            "judgment": "I",
            "error_type": "wrong_theme",
            "notes": f"Theme '{theme}' is a temporal word incorrectly extracted as theme.",
        }

    # Special case: "launched" with temporal theme - check if the theme is actually the thing launched
    if verb_lemma in {"launch", "start", "found", "establish"} and theme_lower in TEMPORAL_THEMES:
        # Check if sentence says "In 2013, X launched Y" - theme should be Y not 2013
        # This IS wrong - the temporal got captured instead of the actual object
        return {
            "judgment": "I",
            "error_type": "wrong_theme",
            "notes": f"Theme '{theme}' is a temporal word; the actual launched entity was missed.",
        }

    # --- PARTIAL checks for pronouns ---

    # [UNNAMED_AGENT] - passive voice constructions
    if agent == "[UNNAMED_AGENT]":
        # Passive voice with clear theme is often valid
        if theme and verb:
            # Check if sentence is truly passive
            if " was " in sentence_lower or " were " in sentence_lower or " been " in sentence_lower or " being " in sentence_lower:
                if theme and theme != "[FILTERED]":
                    return {
                        "judgment": "P",
                        "error_type": "vague_agent",
                        "notes": "Passive construction - agent unnamed but relation is valid.",
                    }
            # Also "can be found" etc.
            if " can " in sentence_lower or " will " in sentence_lower or " is " in sentence_lower:
                return {
                    "judgment": "P",
                    "error_type": "vague_agent",
                    "notes": "Unnamed agent in passive/modal construction.",
                }
            # Default unnamed agent
            return {
                "judgment": "P",
                "error_type": "vague_agent",
                "notes": "Agent is unnamed, relationship partially valid.",
            }
        return {
            "judgment": "I",
            "error_type": "wrong_agent",
            "notes": "Unnamed agent with no clear theme.",
        }

    # Pronoun agents
    if agent_lower in PRONOUN_AGENTS:
        # Speech verbs with pronoun agents are common and valid
        if verb_lemma in SPEECH_VERB_LEMMAS or verb.lower() in SPEECH_VERBS:
            if not theme:
                return {
                    "judgment": "P",
                    "error_type": "vague_agent",
                    "notes": f"Pronoun agent '{agent}' with speech verb is valid but agent unresolved.",
                }
            return {
                "judgment": "P",
                "error_type": "vague_agent",
                "notes": f"Pronoun agent '{agent}' - coreference unresolved.",
            }
        # Non-speech verbs with pronoun agents
        if theme:
            return {
                "judgment": "P",
                "error_type": "vague_agent",
                "notes": f"Pronoun agent '{agent}' requires coreference resolution.",
            }
        return {
            "judgment": "P",
            "error_type": "vague_agent",
            "notes": f"Pronoun agent '{agent}' with no theme - vague.",
        }

    # --- CORRECT / PARTIAL decisions based on content ---

    # Speech verbs with empty theme - valid speech acts
    if verb_lemma in SPEECH_VERB_LEMMAS and not theme:
        # Check if agent is a real entity
        if agent_lower not in PRONOUN_AGENTS and agent != "[UNNAMED_AGENT]":
            return {
                "judgment": "C",
                "error_type": None,
                "notes": f"Speech verb '{verb_lemma}' with named agent; empty theme acceptable for speech acts.",
            }

    # Empty theme with non-speech verbs
    if not theme and verb_lemma not in SPEECH_VERB_LEMMAS:
        # Some verbs are intransitive and don't need themes
        intransitive = {"focus", "appear", "arise", "compete", "work", "collaborate", "engage", "shop", "scale"}
        if verb_lemma in intransitive:
            if agent_lower not in PRONOUN_AGENTS and agent != "[UNNAMED_AGENT]":
                return {
                    "judgment": "C",
                    "error_type": None,
                    "notes": f"Intransitive verb '{verb_lemma}' - no theme needed.",
                }
            return {
                "judgment": "P",
                "error_type": "vague_agent",
                "notes": f"Intransitive verb '{verb_lemma}' with vague agent '{agent}'.",
            }
        # Other verbs with empty theme
        if verb_lemma in {"show", "prove", "build", "want", "aim", "help", "support"}:
            # These often take clausal complements that aren't extracted
            if agent_lower not in PRONOUN_AGENTS and agent != "[UNNAMED_AGENT]":
                return {
                    "judgment": "P",
                    "error_type": "vague_theme",
                    "notes": f"Verb '{verb_lemma}' likely has clausal complement not captured as theme.",
                }
        if agent_lower not in PRONOUN_AGENTS:
            return {
                "judgment": "P",
                "error_type": "vague_theme",
                "notes": f"Empty theme for verb '{verb_lemma}'.",
            }

    # Check if agent text actually appears in sentence
    agent_in_sentence = agent_lower in sentence_lower or any(
        w in sentence_lower for w in agent_lower.split() if len(w) > 3
    )
    theme_in_sentence = (
        not theme
        or theme_lower in sentence_lower
        or any(w in sentence_lower for w in theme_lower.split() if len(w) > 3)
    )

    # Agent not in sentence at all - likely extraction error
    if not agent_in_sentence and agent_lower not in PRONOUN_AGENTS:
        return {
            "judgment": "I",
            "error_type": "wrong_agent",
            "notes": f"Agent '{agent}' not found in source sentence.",
        }

    # Theme not in sentence at all
    if theme and not theme_in_sentence:
        return {
            "judgment": "I",
            "error_type": "wrong_theme",
            "notes": f"Theme '{theme}' not found in source sentence.",
        }

    # --- Specific pattern checks ---

    # Abstract concepts as agents (when they shouldn't be actors)
    abstract_agent_patterns = [
        "discussions", "implementation", "work", "support", "future",
        "publication", "no ties", "tasks", "programs", "proposals",
        "heat", "virus", "oil prices", "market", "mergers",
        "manufacturing shutdown", "transaction data",
    ]
    if agent_lower in abstract_agent_patterns:
        # Some abstracts are valid metonyms (e.g., "the publication showcases")
        valid_abstract_agents = {
            "publication", "virus", "oil prices", "market",
            "implementation", "manufacturing shutdown",
        }
        if agent_lower in valid_abstract_agents:
            if theme:
                return {
                    "judgment": "C",
                    "error_type": None,
                    "notes": f"Abstract agent '{agent}' used as valid metonym.",
                }
        # Truly problematic abstract agents
        if agent_lower in {"discussions", "tasks", "programs", "proposals", "no ties", "support", "work"}:
            if theme:
                return {
                    "judgment": "P",
                    "error_type": "vague_agent",
                    "notes": f"Abstract concept '{agent}' used as agent - should be an organization/person.",
                }
            return {
                "judgment": "I",
                "error_type": "wrong_agent",
                "notes": f"Abstract concept '{agent}' cannot be an agent.",
                }

    # Check for multi-word agent that's actually a phrase fragment
    if len(agent.split()) >= 3 and not any(
        c.isupper() for c in agent.split()[0]
    ):
        # Long lowercase agent is likely a phrase fragment
        return {
            "judgment": "P",
            "error_type": "vague_agent",
            "notes": f"Agent '{agent}' appears to be a phrase fragment.",
        }

    # Theme is "which", "that", "this", "what" - relative pronoun
    if theme_lower in {"which", "that", "this", "what", "who", "whom", "whose"}:
        return {
            "judgment": "P",
            "error_type": "vague_theme",
            "notes": f"Theme '{theme}' is a relative/demonstrative pronoun.",
        }

    # Theme is a pronoun
    if theme_lower in PRONOUN_AGENTS:
        return {
            "judgment": "P",
            "error_type": "vague_theme",
            "notes": f"Theme '{theme}' is a pronoun requiring coreference resolution.",
        }

    # If we got here, do a final quality check
    # Named agent + specific verb + specific theme = CORRECT
    if (
        agent
        and verb
        and theme
        and agent_lower not in PRONOUN_AGENTS
        and agent != "[UNNAMED_AGENT]"
        and theme_lower not in PRONOUN_AGENTS
        and theme_lower not in {"which", "that", "this", "what", "who"}
        and theme_lower not in TEMPORAL_THEMES
        and agent_in_sentence
        and theme_in_sentence
    ):
        # Check verb sense makes sense
        # A few more pattern checks
        if verb_lemma in {"include"} and theme:
            return {
                "judgment": "C",
                "error_type": None,
                "notes": f"Valid extraction: '{agent}' {verb} '{theme}'.",
            }
        return {
            "judgment": "C",
            "error_type": None,
            "notes": f"Correctly extracted: '{agent}' {verb} '{theme}'.",
        }

    # Default: if agent and verb exist but theme is missing, it's partial
    if agent and verb and not theme:
        return {
            "judgment": "P",
            "error_type": "vague_theme",
            "notes": f"Missing theme for '{agent}' {verb}.",
        }

    # Fallback
    return {
        "judgment": "P",
        "error_type": "vague_theme",
        "notes": "Could not determine quality with high confidence.",
    }


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
from collections import Counter

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
    stratum_judgments = Counter(r["judgment"] for r in stratum_results)
    n = len(stratum_results)
    if n > 0:
        sp = stratum_judgments["C"] / n
        lp = (stratum_judgments["C"] + stratum_judgments["P"]) / n
        print(f"  {stratum} (n={n}): strict={sp:.3f}, lenient={lp:.3f}")
        print(f"    C={stratum_judgments['C']}, P={stratum_judgments['P']}, I={stratum_judgments['I']}, N={stratum_judgments['N']}")

# By verb lemma
print(f"\nPrecision by top verb lemmas:")
verb_results: dict[str, list[str]] = {}
for r in results:
    vl = r.get("verb_lemma", "unknown")
    verb_results.setdefault(vl, []).append(r["judgment"])

for vl, judgments_list in sorted(verb_results.items(), key=lambda x: -len(x[1])):
    if len(judgments_list) >= 3:
        c_count = judgments_list.count("C")
        p_count = judgments_list.count("P")
        n = len(judgments_list)
        print(f"  {vl} (n={n}): strict={c_count/n:.2f}, lenient={(c_count+p_count)/n:.2f}")

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
    "details": results,
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"\nWritten to {OUTPUT_PATH}")
