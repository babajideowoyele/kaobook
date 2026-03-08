"""
Improved pseudo-annotation with better heuristics.
Key improvements:
1. Handle-based classification for actors without tweets
2. Better startup/SME detection
3. Multi-signal scoring system
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
OUTPUT_FILE = BASE_DIR / "data/outputs/actor_type_annotations_v2.json"

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
    # Personal names often have 2-3 parts, no org terms
    parts = handle_clean.split()
    org_terms = ['lab', 'tech', 'group', 'company', 'inc', 'co', 'eu', 'official',
                 'platform', 'network', 'project', 'innovation', 'startup', 'ventures']
    has_org = any(term in handle_clean for term in org_terms)
    # Length heuristic: personal names typically 2-3 words, 10-25 chars
    return (not has_org and
            2 <= len(parts) <= 3 and
            6 <= len(handle_clean.replace(' ', '')) <= 25)

def classify_actor(handle: str, tweets: list[str], degree: int) -> tuple[str, str, str]:
    """Improved classification with handle + tweet signals."""
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
                 'europa', 'govt', 'ministry']
    if any(term in handle_lower for term in gov_terms):
        return ('Government/Public Agency', 'high', 'EU/government handle')

    # Research
    research_terms = ['university', 'institut', 'research', 'lab', 'academy',
                      'college', 'univ', 'campus', 'school']
    if any(term in handle_lower for term in research_terms):
        return ('Research Institution', 'high', 'Academic institution handle')

    # === TIER 2: Tweet content analysis (if tweets available) ===
    if tweets:
        # Count key patterns
        i_count = len(re.findall(r'\bi\b', tweet_text))
        we_count = len(re.findall(r'\bwe\b', tweet_text))
        our_count = len(re.findall(r'\bour\b', tweet_text))

        # Individual signals
        individual_patterns = [
            r'\bi think\b', r'\bi believe\b', r'\bmy view\b', r'\bpersonally\b',
            r'\bexcited to\b', r'\bhappy to\b', r'\bproud to\b', r'\bi\'m\b',
            r'\bi am\b', r'\bmy work\b', r'\bmy research\b'
        ]
        individual_score = sum(1 for p in individual_patterns if re.search(p, tweet_text))

        # Startup/SME signals
        startup_patterns = [
            r'\bour product\b', r'\bour startup\b', r'\bour company\b', r'\bwe launch\b',
            r'\bwe build\b', r'\bwe develop\b', r'\bour team\b', r'\bjoin us\b',
            r'\bwe are hiring\b', r'\bcheck out our\b', r'\bour solution\b',
            r'\bfounded\b', r'\bco-founder\b', r'\bstartup\b', r'\bour app\b',
            r'\bour platform\b', r'\bwe help\b', r'\bwe create\b'
        ]
        startup_score = sum(1 for p in startup_patterns if re.search(p, tweet_text))

        # Investment fund signals
        invest_patterns = [
            r'\bportfolio\b', r'\binvestment\b', r'\bfund\b', r'\binvest in\b',
            r'\bbacked\b', r'\bfunding\b', r'\bventure\b', r'\bcapital\b',
            r'\binvestor\b', r'\bequity\b'
        ]
        invest_score = sum(1 for p in invest_patterns if re.search(p, tweet_text))

        # Media signals
        media_patterns = [
            r'\bbreaking\b', r'\bjust published\b', r'\bread our\b', r'\bour story\b',
            r'\bcoverage\b', r'\bjournalism\b', r'\breport\b', r'\barticle\b'
        ]
        media_score = sum(1 for p in media_patterns if re.search(p, tweet_text))

        # Corporation signals
        corp_patterns = [
            r'\bglobal\b', r'\bworldwide\b', r'\benterprise\b', r'\bsolutions\b',
            r'\bindustry leader\b', r'\bmarket leader\b', r'\bfortune\b'
        ]
        corp_score = sum(1 for p in corp_patterns if re.search(p, tweet_text))

        # NGO signals
        ngo_patterns = [
            r'\bmission\b', r'\badvocacy\b', r'\bcampaign\b', r'\bnonprofit\b',
            r'\bcharity\b', r'\bimpact\b', r'\bcause\b'
        ]
        ngo_score = sum(1 for p in ngo_patterns if re.search(p, tweet_text))

        # Association signals
        assoc_patterns = [
            r'\bmember\b', r'\bassociation\b', r'\balliance\b', r'\bnetwork\b',
            r'\bfederation\b', r'\bconsortium\b', r'\bpartnership\b'
        ]
        assoc_score = sum(1 for p in assoc_patterns if re.search(p, tweet_text))

        # Decision tree based on scores
        if invest_score >= 2:
            return ('Investment Fund', 'medium', f'Investment language ({invest_score} signals)')

        if media_score >= 2:
            return ('Media/Publication', 'medium', f'Media language ({media_score} signals)')

        if ngo_score >= 2:
            return ('NGO/Nonprofit', 'medium', f'NGO language ({ngo_score} signals)')

        if assoc_score >= 2:
            return ('Industry Association', 'medium', f'Association language ({assoc_score} signals)')

        # Startup vs Corporation vs Individual
        if startup_score >= 2:
            return ('Startup/SME', 'medium', f'Startup language ({startup_score} signals, we={we_count}, our={our_count})')

        if corp_score >= 2 and degree > 50:
            return ('Corporation', 'medium', f'Corporate language ({corp_score} signals), high degree ({degree})')

        # Pronoun-based classification
        if i_count > we_count * 2 and individual_score >= 1:
            return ('Individual', 'medium', f'Personal pronouns (I={i_count} vs we={we_count}), individual_score={individual_score}')

        # Organizational language (we/our dominant)
        if (we_count + our_count) > i_count * 1.5:
            if degree > 60:
                return ('Corporation', 'low', f'Organizational language (we={we_count}, our={our_count}), high degree')
            else:
                return ('Startup/SME', 'low', f'Organizational language (we={we_count}, our={our_count}), moderate degree')

        # Personal tone default
        if i_count > 0:
            return ('Individual', 'low', f'Personal tone (I={i_count})')

    # === TIER 3: No tweets - handle heuristics ===
    # Check if handle looks like personal name
    if has_personal_name(handle):
        return ('Individual', 'low', 'Personal name handle pattern (no tweets)')

    # Organizational handle patterns
    org_indicators = ['tech', 'lab', 'inc', 'group', 'ventures', 'solutions',
                      'platform', 'network', 'innovation', 'startup', 'co']
    if any(ind in handle_lower for ind in org_indicators):
        if degree > 50:
            return ('Corporation', 'low', f'Organizational handle pattern, high degree ({degree})')
        else:
            return ('Startup/SME', 'low', f'Organizational handle pattern, moderate degree ({degree})')

    # Fallback based on degree
    if degree > 70:
        return ('Corporation', 'low', f'High degree ({degree}), no other signals')
    elif degree > 40:
        return ('Startup/SME', 'low', f'Moderate-high degree ({degree}), no other signals')
    else:
        return ('Individual', 'low', f'Low degree ({degree}), default to individual')

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
        'sample_tweets': tweets[:3],
        'actor_type': actor_type,
        'confidence': confidence,
        'reasoning': reasoning
    })

# Save results
print(f"\nSaving {len(annotations)} annotations to {OUTPUT_FILE}")
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(annotations, f, indent=2, ensure_ascii=False)

# Compute distribution
type_counts = Counter(a['actor_type'] for a in annotations)
print("\nActor Type Distribution:")
print(f"{'Actor Type':<30} {'Count':<8} {'Percentage'}")
print("-" * 55)
total = len(annotations)
for actor_type, count in type_counts.most_common():
    pct = 100 * count / total
    print(f"{actor_type:<30} {count:<8} {pct:>5.1f}%")

print(f"\nTotal: {total}")

# Compare to chapter claims
print("\nComparison to Chapter 6 claims:")
print(f"  Chapter claim: 33% individuals, 22% startups")
individual_pct = 100 * type_counts.get('Individual', 0) / total
startup_pct = 100 * type_counts.get('Startup/SME', 0) / total
print(f"  Our data:      {individual_pct:.1f}% individuals, {startup_pct:.1f}% startups")

# Confidence breakdown
conf_counts = Counter(a['confidence'] for a in annotations)
print("\nConfidence Distribution:")
for conf, count in conf_counts.most_common():
    pct = 100 * count / total
    print(f"  {conf}: {count} ({pct:.1f}%)")

# Tweet availability
tweet_counts = Counter(a['has_tweets'] for a in annotations)
print("\nTweet Availability:")
print(f"  With tweets: {tweet_counts[True]} ({100*tweet_counts[True]/total:.1f}%)")
print(f"  No tweets: {tweet_counts[False]} ({100*tweet_counts[False]/total:.1f}%)")

# Breakdown by confidence and tweet availability
print("\nDetailed Breakdown:")
with_tweets = [a for a in annotations if a['has_tweets']]
without_tweets = [a for a in annotations if not a['has_tweets']]

print(f"\nWith tweets (n={len(with_tweets)}):")
wt_counts = Counter(a['actor_type'] for a in with_tweets)
for actor_type, count in wt_counts.most_common():
    pct = 100 * count / len(with_tweets)
    print(f"  {actor_type:<30} {count:<8} {pct:>5.1f}%")

print(f"\nWithout tweets (n={len(without_tweets)}):")
nt_counts = Counter(a['actor_type'] for a in without_tweets)
for actor_type, count in nt_counts.most_common():
    pct = 100 * count / len(without_tweets)
    print(f"  {actor_type:<30} {count:<8} {pct:>5.1f}%")

print("\nDone!")
