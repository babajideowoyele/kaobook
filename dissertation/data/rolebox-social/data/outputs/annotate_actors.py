"""
Pseudo-annotate actor types based on handles and tweet content.
Stratified sample of ~200 actors from the rolefield network.
"""

import json
import pandas as pd
from pathlib import Path
from collections import Counter, defaultdict
import re

# Paths — resolved relative to this script's location
BASE_DIR = Path(__file__).parent.parent.parent  # rolebox-social root
NETWORK_FILE = BASE_DIR / "ui/network_data.json"
TWEETS_FILE = BASE_DIR / "data/processed/twitter_consolidated.parquet"
OUTPUT_FILE = BASE_DIR / "data/outputs/actor_type_annotations.json"

# Ensure output dir exists
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Load network data
print("Loading network data...")
with open(NETWORK_FILE, encoding='utf-8') as f:
    network = json.load(f)

nodes = network['nodes']
print(f"Total nodes: {len(nodes)}")

# Count by community
community_counts = Counter(n['communityLabel'] for n in nodes)
print("\nCommunity distribution:")
for comm, count in community_counts.most_common():
    print(f"  {comm}: {count}")

# Stratified sampling: proportional to community size, target ~200 total
TARGET_SAMPLE = 200
sample_fraction = TARGET_SAMPLE / len(nodes)
print(f"\nSample fraction: {sample_fraction:.2%}")

sampled_nodes = []
for comm, count in community_counts.items():
    comm_nodes = [n for n in nodes if n['communityLabel'] == comm]
    sample_size = max(1, int(count * sample_fraction))
    # Sort by degree (descending) and sample top actors
    comm_nodes_sorted = sorted(comm_nodes, key=lambda x: x['degree'], reverse=True)
    sampled = comm_nodes_sorted[:sample_size]
    sampled_nodes.extend(sampled)
    print(f"  {comm}: sampled {len(sampled)}/{count}")

print(f"\nTotal sampled: {len(sampled_nodes)}")

# Load tweets
print("\nLoading tweets...")
tweets_df = pd.read_parquet(TWEETS_FILE)
print(f"Total tweets: {len(tweets_df)}")
print(f"Columns: {list(tweets_df.columns)}")

# Normalize user handles in tweets (lowercase, remove @)
tweets_df['User_normalized'] = tweets_df['User'].str.lower().str.replace('@', '', regex=False)

# Sample tweets for each actor
print("\nSampling tweets for actors...")
actor_tweets = defaultdict(list)
for node in sampled_nodes:
    handle = node['label'].lower()  # network uses label without @
    user_tweets = tweets_df[tweets_df['User_normalized'] == handle]

    # Get up to 5 tweets, prefer longer ones
    if len(user_tweets) > 0:
        user_tweets_sorted = user_tweets.sort_values('Tweet value', ascending=False)
        sample_tweets = user_tweets_sorted.head(5)['Tweet'].tolist()
        actor_tweets[handle] = sample_tweets

print(f"Found tweets for {len(actor_tweets)}/{len(sampled_nodes)} actors")

# Classification heuristics
def classify_actor(handle: str, tweets: list[str], degree: int) -> tuple[str, str, str]:
    """
    Classify actor based on handle and tweets.
    Returns (actor_type, confidence, reasoning)
    """
    handle_lower = handle.lower()
    tweet_text = ' '.join(tweets).lower() if tweets else ''

    # Strong signals
    if any(kic in handle_lower for kic in ['eit', 'climatekit', 'eitdigital', 'eithealth',
                                              'eitfood', 'eitrawmaterials', 'eitmanufacturing',
                                              'eitculture', 'eiturban']):
        return ('KIC/EIT', 'high', 'EIT/KIC handle name')

    if any(term in handle_lower for term in ['eu_', 'european', 'ec_', 'europarl', 'eufunds']):
        return ('Government/Public Agency', 'high', 'EU/government handle')

    # Research signals
    research_terms = ['university', 'institut', 'research', 'lab', 'academy', 'college', 'univ']
    if any(term in handle_lower for term in research_terms):
        return ('Research Institution', 'high', 'Academic institution handle')

    # Check tweet patterns
    i_pronoun_count = len(re.findall(r'\bi\b', tweet_text))
    we_pronoun_count = len(re.findall(r'\bwe\b', tweet_text))

    # Individual signals
    personal_indicators = [
        'i think', 'i believe', 'my view', 'personally',
        'excited to', 'happy to', 'proud to'
    ]
    personal_score = sum(1 for p in personal_indicators if p in tweet_text)

    # Startup/SME signals
    startup_terms = ['our product', 'our startup', 'our company', 'we launch', 'we build',
                     'proud to announce', 'just launched', 'check out our', 'join our team']
    startup_score = sum(1 for s in startup_terms if s in tweet_text)

    # Investment fund signals
    invest_terms = ['portfolio', 'investment', 'fund', 'invest in', 'backed', 'funding']
    invest_score = sum(1 for i in invest_terms if i in tweet_text)

    # Media signals
    media_terms = ['breaking', 'just published', 'read our', 'our story', 'coverage']
    media_score = sum(1 for m in media_terms if m in tweet_text)

    # Corporation signals (large, established)
    corp_terms = ['global', 'worldwide', 'fortune', 'enterprise', 'solutions']
    corp_score = sum(1 for c in corp_terms if c in tweet_text)

    # NGO signals
    ngo_terms = ['mission', 'advocacy', 'campaign', 'nonprofit', 'charity', 'impact']
    ngo_score = sum(1 for n in ngo_terms if n in tweet_text)

    # Association signals
    assoc_terms = ['member', 'association', 'alliance', 'network', 'federation']
    assoc_score = sum(1 for a in assoc_terms if a in tweet_text)

    # Decision tree
    if i_pronoun_count > we_pronoun_count * 1.5 and personal_score > 0:
        return ('Individual', 'medium', f'Personal pronouns ({i_pronoun_count} "I" vs {we_pronoun_count} "we"), personal language')

    if invest_score >= 2:
        return ('Investment Fund', 'medium', f'Investment language ({invest_score} signals)')

    if media_score >= 2:
        return ('Media/Publication', 'medium', f'Media language ({media_score} signals)')

    if startup_score >= 2:
        return ('Startup/SME', 'medium', f'Startup language ({startup_score} signals)')

    if corp_score >= 2 and degree > 50:
        return ('Corporation', 'medium', f'Corporate language, high degree ({degree})')

    if ngo_score >= 2:
        return ('NGO/Nonprofit', 'medium', f'NGO language ({ngo_score} signals)')

    if assoc_score >= 2:
        return ('Industry Association', 'medium', f'Association language ({assoc_score} signals)')

    # Fallback: use pronouns and degree
    if we_pronoun_count > 0:
        if degree > 50:
            return ('Corporation', 'low', f'Organizational language, high degree ({degree})')
        else:
            return ('Startup/SME', 'low', f'Organizational language, moderate degree ({degree})')

    if not tweets:
        return ('Unknown', 'low', 'No tweets available')

    return ('Individual', 'low', 'Default classification based on personal tone')

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
        'sample_tweets': tweets[:3],  # Limit to 3 for readability
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

print("\nDone!")
