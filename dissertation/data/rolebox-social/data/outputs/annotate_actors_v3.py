"""
Final refined pseudo-annotation.
Key improvements over v2:
1. Less aggressive degree-based fallback
2. Better startup vs corporation distinction
3. More conservative "Unknown" category
4. Handle suffixes (Inc, Ltd, GmbH, etc) for organizational type
"""

import json
import pandas as pd
from pathlib import Path
from collections import Counter, defaultdict
import re

# Paths
BASE_DIR = Path(__file__).parent.parent.parent  # rolebox-social root
NETWORK_FILE = BASE_DIR / "ui/network_data.json"
TWEETS_FILE = BASE_DIR / "data/processed/twitter_consolidated.parquet"
OUTPUT_FILE = BASE_DIR / "data/outputs/actor_type_annotations.json"  # Final output

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Load network data
print("Loading network data...")
with open(NETWORK_FILE, encoding='utf-8') as f:
    network = json.load(f)

nodes = network['nodes']
print(f"Total nodes: {len(nodes)}")

# Stratified sampling
community_counts = Counter(n['communityLabel'] for n in nodes)
TARGET_SAMPLE = 200
sample_fraction = TARGET_SAMPLE / len(nodes)

sampled_nodes = []
for comm, count in community_counts.items():
    comm_nodes = [n for n in nodes if n['communityLabel'] == comm]
    sample_size = max(1, int(count * sample_fraction))
    comm_nodes_sorted = sorted(comm_nodes, key=lambda x: x['degree'], reverse=True)
    sampled_nodes.extend(comm_nodes_sorted[:sample_size])

print(f"Total sampled: {len(sampled_nodes)}")

# Load tweets
print("Loading tweets...")
tweets_df = pd.read_parquet(TWEETS_FILE)
tweets_df['User_normalized'] = tweets_df['User'].str.lower().str.replace('@', '', regex=False)

# Sample tweets for each actor
actor_tweets = defaultdict(list)
for node in sampled_nodes:
    handle = node['label'].lower()
    user_tweets = tweets_df[tweets_df['User_normalized'] == handle]
    if len(user_tweets) > 0:
        sample_tweets = user_tweets.sort_values('Tweet value', ascending=False).head(5)['Tweet'].tolist()
        actor_tweets[handle] = sample_tweets

print(f"Found tweets for {len(actor_tweets)}/{len(sampled_nodes)} actors")

def has_personal_name(handle: str) -> bool:
    """Check if handle looks like a personal name."""
    handle_clean = handle.lower().replace('_', ' ').replace('.', ' ')
    parts = handle_clean.split()

    # Exclude organizational terms
    org_terms = ['lab', 'tech', 'group', 'company', 'inc', 'ltd', 'gmbh', 'co',
                 'eu', 'official', 'platform', 'network', 'project', 'innovation',
                 'startup', 'ventures', 'capital', 'fund', 'global', 'institute',
                 'university', 'research', 'news', 'media']
    has_org = any(term in handle_clean for term in org_terms)

    # Personal name patterns: 2-3 words, reasonable length
    return (not has_org and
            2 <= len(parts) <= 3 and
            6 <= len(handle_clean.replace(' ', '')) <= 30)

def get_org_type_from_handle(handle: str) -> str | None:
    """Detect organization type from handle suffix or keywords."""
    handle_lower = handle.lower()

    # Startup/SME indicators
    startup_terms = ['startup', 'ventures', 'labs', 'technologies', 'solutions',
                     'innovation', 'tech', 'app', 'software', 'platform']
    if any(term in handle_lower for term in startup_terms):
        return 'startup'

    # Corporation indicators
    corp_suffixes = ['inc', 'ltd', 'gmbh', 'corp', 'corporation', 'plc', 'ag', 'sa']
    corp_terms = ['global', 'international', 'worldwide', 'group', 'industries']
    if (any(suf in handle_lower for suf in corp_suffixes) or
        any(term in handle_lower for term in corp_terms)):
        return 'corporation'

    # Investment fund
    invest_terms = ['capital', 'fund', 'ventures', 'partners', 'equity']
    if any(term in handle_lower for term in invest_terms):
        return 'investment'

    return None

def classify_actor(handle: str, tweets: list[str], degree: int) -> tuple[str, str, str]:
    """Final classification with balanced heuristics."""
    handle_lower = handle.lower()
    tweet_text = ' '.join(tweets).lower() if tweets else ''

    # === TIER 1: High-confidence handle-based ===
    # KIC/EIT
    kic_terms = ['eit', 'climatekit', 'eitdigital', 'eithealth', 'eitfood',
                 'eitrawmaterials', 'eitmanufacturing', 'eitculture', 'eiturban']
    if any(kic in handle_lower for kic in kic_terms):
        return ('KIC/EIT', 'high', 'EIT/KIC handle name')

    # Government/EU
    gov_terms = ['eu_', 'european', 'ec_', 'europarl', 'eufunds', 'commission',
                 'europa', 'govt', 'ministry', 'parliament']
    if any(term in handle_lower for term in gov_terms):
        return ('Government/Public Agency', 'high', 'EU/government handle')

    # Research
    research_terms = ['university', 'institut', 'research', 'academy',
                      'college', 'univ', 'campus', 'school']
    if any(term in handle_lower for term in research_terms):
        return ('Research Institution', 'high', 'Academic institution handle')

    # === TIER 2: Tweet content analysis ===
    if tweets and len(tweet_text) > 100:  # Require substantial tweet content
        # Count patterns
        i_count = len(re.findall(r'\bi\b', tweet_text))
        we_count = len(re.findall(r'\bwe\b', tweet_text))
        our_count = len(re.findall(r'\bour\b', tweet_text))

        # Individual signals
        individual_patterns = [
            r'\bi think\b', r'\bi believe\b', r'\bmy view\b', r'\bpersonally\b',
            r'\bexcited to\b', r'\bhappy to\b', r'\bproud to\b', r'\bi\'m\b',
            r'\bi am\b', r'\bmy work\b', r'\bmy research\b', r'\bmy opinion\b'
        ]
        individual_score = sum(1 for p in individual_patterns if re.search(p, tweet_text))

        # Startup/SME signals (enhanced)
        startup_patterns = [
            r'\bour product\b', r'\bour startup\b', r'\bour company\b', r'\bwe launch\b',
            r'\bwe build\b', r'\bwe develop\b', r'\bour team\b', r'\bjoin us\b',
            r'\bwe are hiring\b', r'\bcheck out our\b', r'\bour solution\b',
            r'\bfounded\b', r'\bco-founder\b', r'\bstartup\b', r'\bour app\b',
            r'\bour platform\b', r'\bwe help\b', r'\bwe create\b', r'\bwe\'re building\b',
            r'\bnew feature\b', r'\bproduct update\b', r'\bearly stage\b', r'\bseed\b',
            r'\bpre-seed\b', r'\bseries a\b', r'\bMVP\b'
        ]
        startup_score = sum(1 for p in startup_patterns if re.search(p, tweet_text))

        # Investment fund
        invest_patterns = [
            r'\bportfolio\b', r'\binvestment\b', r'\bfund\b', r'\binvest in\b',
            r'\bbacked\b', r'\bfunding round\b', r'\bventure\b', r'\bcapital\b',
            r'\binvestor\b', r'\bequity\b', r'\bour portfolio\b'
        ]
        invest_score = sum(1 for p in invest_patterns if re.search(p, tweet_text))

        # Media
        media_patterns = [
            r'\bbreaking\b', r'\bjust published\b', r'\bread our\b', r'\bcoverage\b',
            r'\bjournalism\b', r'\breporting\b', r'\beditor\b'
        ]
        media_score = sum(1 for p in media_patterns if re.search(p, tweet_text))

        # Corporation (large, established)
        corp_patterns = [
            r'\bglobal leader\b', r'\bindustry leader\b', r'\bmarket leader\b',
            r'\bfortune 500\b', r'\benterprise\b', r'\bmultinational\b'
        ]
        corp_score = sum(1 for p in corp_patterns if re.search(p, tweet_text))

        # NGO
        ngo_patterns = [
            r'\bmission\b', r'\badvocacy\b', r'\bcampaign\b', r'\bnonprofit\b',
            r'\bcharity\b', r'\bsocial impact\b'
        ]
        ngo_score = sum(1 for p in ngo_patterns if re.search(p, tweet_text))

        # Association
        assoc_patterns = [
            r'\bmember\b', r'\bmembership\b', r'\bassociation\b', r'\balliance\b',
            r'\bfederation\b', r'\bconsortium\b'
        ]
        assoc_score = sum(1 for p in assoc_patterns if re.search(p, tweet_text))

        # === Decision tree ===
        # Specialized categories first
        if invest_score >= 2:
            return ('Investment Fund', 'medium', f'Investment language ({invest_score} signals)')

        if media_score >= 2:
            return ('Media/Publication', 'medium', f'Media language ({media_score} signals)')

        if ngo_score >= 2:
            return ('NGO/Nonprofit', 'medium', f'NGO language ({ngo_score} signals)')

        if assoc_score >= 2:
            return ('Industry Association', 'medium', f'Association language ({assoc_score} signals)')

        # Startup detection (strong signal)
        if startup_score >= 3:
            return ('Startup/SME', 'medium', f'Strong startup signals ({startup_score})')

        # Corporation (strong signal)
        if corp_score >= 2 and degree > 60:
            return ('Corporation', 'medium', f'Corporate language ({corp_score}), high degree ({degree})')

        # Individual (strong signal)
        if i_count >= 5 and individual_score >= 2:
            return ('Individual', 'medium', f'Strong personal voice (I={i_count}, signals={individual_score})')

        # Pronoun-based with thresholds
        total_pronouns = i_count + we_count + our_count
        if total_pronouns >= 5:
            if i_count > (we_count + our_count) * 2:
                return ('Individual', 'low', f'Personal pronouns (I={i_count} vs we={we_count}+our={our_count})')

            if (we_count + our_count) > i_count * 2:
                # Startup vs Corporation based on degree and language
                if startup_score >= 1 or degree < 60:
                    return ('Startup/SME', 'low', f'Organizational language (we={we_count}+our={our_count}), startup signals')
                else:
                    return ('Corporation', 'low', f'Organizational language, high degree ({degree})')

    # === TIER 3: Handle-based classification (no/weak tweets) ===
    # Check organizational type from handle
    org_type = get_org_type_from_handle(handle)
    if org_type == 'startup':
        return ('Startup/SME', 'low', f'Startup handle pattern (degree={degree})')
    elif org_type == 'corporation':
        return ('Corporation', 'low', f'Corporation handle pattern (degree={degree})')
    elif org_type == 'investment':
        return ('Investment Fund', 'low', f'Investment fund handle pattern (degree={degree})')

    # Check if handle looks like personal name
    if has_personal_name(handle):
        return ('Individual', 'low', 'Personal name handle pattern')

    # === TIER 4: Degree-based fallback (very conservative) ===
    if not tweets:
        # No tweets, no strong handle signals - degree-based guess
        if degree > 80:
            return ('Corporation', 'low', f'Very high degree ({degree}), likely established org')
        elif degree > 50:
            return ('Startup/SME', 'low', f'Moderate-high degree ({degree}), likely SME/startup')
        elif degree < 20:
            return ('Individual', 'low', f'Low degree ({degree}), likely individual')
        else:
            # Ambiguous case
            return ('Startup/SME', 'low', f'Medium degree ({degree}), default to SME')

    # Tweets exist but insufficient signals
    return ('Individual', 'low', 'Insufficient signals, default to individual')

# Annotate actors
print("\nClassifying actors...")
annotations = []
for node in sampled_nodes:
    handle = node['label']
    tweets = actor_tweets.get(handle.lower(), [])
    degree = node['degree']
    community = node['communityLabel']

    actor_type, confidence, reasoning = classify_actor(handle, tweets, degree)

    annotations.append({
        'handle': f"@{handle}",
        'community_label': community,
        'degree': degree,
        'has_tweets': len(tweets) > 0,
        'num_tweets_sampled': len(tweets),
        'sample_tweets': tweets[:3],
        'actor_type': actor_type,
        'confidence': confidence,
        'reasoning': reasoning
    })

# Save results
print(f"\nSaving {len(annotations)} annotations to {OUTPUT_FILE}")
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(annotations, f, indent=2, ensure_ascii=False)

# === ANALYSIS & REPORTING ===
type_counts = Counter(a['actor_type'] for a in annotations)
print("\n" + "="*60)
print("ACTOR TYPE DISTRIBUTION")
print("="*60)
print(f"{'Actor Type':<30} {'Count':<8} {'Percentage'}")
print("-" * 60)
total = len(annotations)
for actor_type, count in type_counts.most_common():
    pct = 100 * count / total
    print(f"{actor_type:<30} {count:<8} {pct:>5.1f}%")

print(f"\nTotal: {total}")

# Compare to chapter claims
print("\n" + "="*60)
print("COMPARISON TO CHAPTER 6 CLAIMS")
print("="*60)
individual_pct = 100 * type_counts.get('Individual', 0) / total
startup_pct = 100 * type_counts.get('Startup/SME', 0) / total
print(f"Chapter claim:  33.0% individuals, 22.0% startups")
print(f"Our annotation: {individual_pct:>4.1f}% individuals, {startup_pct:>4.1f}% startups")
print(f"Difference:     {individual_pct-33:+5.1f}pp individuals, {startup_pct-22:+5.1f}pp startups")

# Confidence breakdown
print("\n" + "="*60)
print("CONFIDENCE DISTRIBUTION")
print("="*60)
conf_counts = Counter(a['confidence'] for a in annotations)
for conf in ['high', 'medium', 'low']:
    count = conf_counts.get(conf, 0)
    pct = 100 * count / total
    print(f"{conf:>10}: {count:>3} ({pct:>5.1f}%)")

# Tweet availability
print("\n" + "="*60)
print("TWEET AVAILABILITY")
print("="*60)
tweet_counts = Counter(a['has_tweets'] for a in annotations)
print(f"With tweets:    {tweet_counts.get(True, 0):>3} ({100*tweet_counts.get(True, 0)/total:>5.1f}%)")
print(f"Without tweets: {tweet_counts.get(False, 0):>3} ({100*tweet_counts.get(False, 0)/total:>5.1f}%)")

# Stratified by tweet availability
print("\n" + "="*60)
print("ACTOR TYPES BY TWEET AVAILABILITY")
print("="*60)

with_tweets = [a for a in annotations if a['has_tweets']]
without_tweets = [a for a in annotations if not a['has_tweets']]

print(f"\nWith tweets (n={len(with_tweets)}):")
wt_counts = Counter(a['actor_type'] for a in with_tweets)
for actor_type in sorted(wt_counts.keys()):
    count = wt_counts[actor_type]
    pct = 100 * count / len(with_tweets)
    print(f"  {actor_type:<30} {count:>3} ({pct:>5.1f}%)")

print(f"\nWithout tweets (n={len(without_tweets)}):")
nt_counts = Counter(a['actor_type'] for a in without_tweets)
for actor_type in sorted(nt_counts.keys()):
    count = nt_counts[actor_type]
    pct = 100 * count / len(without_tweets)
    print(f"  {actor_type:<30} {count:>3} ({pct:>5.1f}%)")

# High confidence only
print("\n" + "="*60)
print("HIGH CONFIDENCE ANNOTATIONS ONLY")
print("="*60)
high_conf = [a for a in annotations if a['confidence'] == 'high']
print(f"Total high-confidence: {len(high_conf)}")
hc_counts = Counter(a['actor_type'] for a in high_conf)
for actor_type, count in hc_counts.most_common():
    pct = 100 * count / len(high_conf)
    print(f"  {actor_type:<30} {count:>3} ({pct:>5.1f}%)")

print("\nDone!")
