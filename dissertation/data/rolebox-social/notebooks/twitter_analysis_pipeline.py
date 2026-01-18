"""
Twitter Data Analysis Pipeline for EIT Ecosystem
=================================================

Comprehensive analysis of 268K tweets from TweetBinder exports.
Produces:
1. Mention networks (who mentions whom)
2. Hashtag co-occurrence networks
3. Community detection via Louvain algorithm
4. Bridging actors analysis
5. Temporal dynamics
6. KIC-specific sub-networks

Author: RoleBox Analysis Pipeline
Data: TweetBinder exports (2015-2020)
"""

import pandas as pd
import numpy as np
import re
import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Ensure proper encoding for Unicode output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# NetworkX for graph analysis
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    print("Warning: networkx not installed. Install with: pip install networkx")

# =============================================================================
# CONFIGURATION
# =============================================================================

DATA_DIR = Path(__file__).parent.parent / "data" / "raw" / "twitter_extracted" / "Raw_Twitter_Data (TweetBinder)"
TWEETBINDER_DIR = DATA_DIR / "Tweetbinder"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# EIT KIC Twitter handles mapping (for community labeling)
KIC_HANDLES = {
    '@ClimateKIC': 'Climate-KIC',
    '@CKICNordic': 'Climate-KIC',
    '@ClimateKIC_UKI': 'Climate-KIC',
    '@ClimateKICspain': 'Climate-KIC',
    '@ClimateKICItaly': 'Climate-KIC',
    '@cKIC_Alumni': 'Climate-KIC',
    '@ClimateLaunch': 'Climate-KIC',
    '@GlobalClimathon': 'Climate-KIC',
    '@EdCentreCC': 'Climate-KIC',
    '@EIT_Digital': 'EIT Digital',
    '@EITDigitalAccel': 'EIT Digital',
    '@EITDigitalAcad': 'EIT Digital',
    '@EITalumni': 'EIT Digital',
    '@EITRawMaterials': 'EIT RawMaterials',
    '@InnoEnergyEU': 'InnoEnergy',
    '@EITHealth': 'EIT Health',
    '@EIT_Food': 'EIT Food',
    '@EITUrbanMob': 'EIT Urban Mobility',
    '@EITeu': 'EIT Central',
}

# Minimum thresholds
MIN_MENTIONS = 3  # Minimum mentions to include in network
MIN_HASHTAG_COOCCUR = 5  # Minimum co-occurrences for hashtag network
MIN_TWEETS_FOR_ACTOR = 10  # Minimum tweets to be considered active actor


# =============================================================================
# DATA LOADING
# =============================================================================

def load_all_tweets():
    """Load all TweetBinder Excel files into a single DataFrame."""
    print("Loading TweetBinder data...")

    all_tweets = []

    # List all Excel files
    excel_files = list(TWEETBINDER_DIR.glob("*.xlsx"))
    excel_files = [f for f in excel_files if not f.name.startswith("~$")]

    print(f"Found {len(excel_files)} Excel files")

    for excel_file in excel_files:
        try:
            xlsx = pd.ExcelFile(excel_file)

            # Try to read Tweets sheet
            if 'Tweets' in xlsx.sheet_names:
                df = pd.read_excel(xlsx, sheet_name='Tweets')
                df['source_file'] = excel_file.name
                all_tweets.append(df)
                print(f"  Loaded {len(df)} tweets from {excel_file.name}")
            else:
                print(f"  Skipping {excel_file.name} - no Tweets sheet")

        except Exception as e:
            print(f"  Error loading {excel_file.name}: {e}")

    if not all_tweets:
        print("No tweets loaded!")
        return pd.DataFrame()

    # Combine all tweets
    tweets_df = pd.concat(all_tweets, ignore_index=True)

    # Standardize column names
    tweets_df.columns = tweets_df.columns.str.strip()

    # Parse dates
    if 'Date' in tweets_df.columns:
        tweets_df['Date'] = pd.to_datetime(tweets_df['Date'], errors='coerce')

    print(f"\nTotal tweets loaded: {len(tweets_df):,}")
    print(f"Date range: {tweets_df['Date'].min()} to {tweets_df['Date'].max()}")

    return tweets_df


# =============================================================================
# TEXT EXTRACTION
# =============================================================================

def extract_mentions(text):
    """Extract @mentions from tweet text."""
    if pd.isna(text):
        return []
    mentions = re.findall(r'@(\w+)', str(text))
    return ['@' + m.lower() for m in mentions]


def extract_hashtags(text):
    """Extract #hashtags from tweet text."""
    if pd.isna(text):
        return []
    hashtags = re.findall(r'#(\w+)', str(text))
    return ['#' + h.lower() for h in hashtags]


def extract_retweet_source(text):
    """Extract original author from RT pattern."""
    if pd.isna(text):
        return None
    match = re.match(r'^RT @(\w+):', str(text))
    if match:
        return '@' + match.group(1).lower()
    return None


def standardize_handle(handle):
    """Standardize Twitter handle format."""
    if pd.isna(handle):
        return None
    handle = str(handle).strip().lower()
    if not handle.startswith('@'):
        handle = '@' + handle
    return handle


# =============================================================================
# MENTION NETWORK CONSTRUCTION
# =============================================================================

def build_mention_network(tweets_df, min_weight=MIN_MENTIONS):
    """
    Build directed mention network from tweets.

    Edge (A, B) with weight W means A mentioned B in W tweets.
    """
    print("\nBuilding mention network...")

    mention_counts = defaultdict(lambda: defaultdict(int))
    author_tweets = defaultdict(int)

    for idx, row in tweets_df.iterrows():
        # Get author
        author = row.get('User', row.get('user', None))
        if pd.isna(author):
            continue

        # Try to get username/handle
        author_handle = standardize_handle(author)
        if not author_handle:
            continue

        author_tweets[author_handle] += 1

        # Extract mentions from tweet text
        tweet_text = row.get('Tweet', row.get('text', ''))
        mentions = extract_mentions(tweet_text)

        # Check for retweet
        rt_source = extract_retweet_source(tweet_text)
        if rt_source:
            mention_counts[author_handle][rt_source] += 1

        # Count mentions
        for mention in mentions:
            if mention != author_handle:  # No self-mentions
                mention_counts[author_handle][mention] += 1

    # Build NetworkX graph
    if not HAS_NETWORKX:
        print("NetworkX not available. Returning raw data.")
        return mention_counts, author_tweets

    G = nx.DiGraph()

    # Add nodes with tweet count attribute
    active_authors = {a for a, count in author_tweets.items() if count >= MIN_TWEETS_FOR_ACTOR}
    for author, count in author_tweets.items():
        G.add_node(author, tweets=count)

    # Add edges with weight
    edge_count = 0
    for source, targets in mention_counts.items():
        for target, weight in targets.items():
            if weight >= min_weight:
                G.add_edge(source, target, weight=weight)
                edge_count += 1

    print(f"Mention network: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges")
    print(f"  Active authors (>={MIN_TWEETS_FOR_ACTOR} tweets): {len(active_authors):,}")

    return G


def compute_mention_network_metrics(G):
    """Compute key metrics for mention network."""
    if not HAS_NETWORKX or G is None:
        return {}

    print("\nComputing network metrics...")

    metrics = {
        'n_nodes': G.number_of_nodes(),
        'n_edges': G.number_of_edges(),
        'density': nx.density(G),
    }

    # In-degree (how often mentioned)
    in_degrees = dict(G.in_degree(weight='weight'))
    top_mentioned = sorted(in_degrees.items(), key=lambda x: -x[1])[:30]
    metrics['top_mentioned'] = top_mentioned

    # Out-degree (how often mentioning others)
    out_degrees = dict(G.out_degree(weight='weight'))
    top_mentioners = sorted(out_degrees.items(), key=lambda x: -x[1])[:30]
    metrics['top_mentioners'] = top_mentioners

    # Reciprocity
    metrics['reciprocity'] = nx.reciprocity(G)

    # Weakly connected components
    wccs = list(nx.weakly_connected_components(G))
    metrics['n_components'] = len(wccs)
    metrics['largest_component_size'] = len(max(wccs, key=len)) if wccs else 0
    metrics['largest_component_pct'] = metrics['largest_component_size'] / G.number_of_nodes() * 100

    print(f"  Density: {metrics['density']:.4f}")
    print(f"  Reciprocity: {metrics['reciprocity']:.4f}")
    print(f"  Components: {metrics['n_components']}")
    print(f"  Largest component: {metrics['largest_component_pct']:.1f}%")

    return metrics


# =============================================================================
# HASHTAG CO-OCCURRENCE NETWORK
# =============================================================================

def build_hashtag_network(tweets_df, min_cooccur=MIN_HASHTAG_COOCCUR, top_n=500):
    """
    Build hashtag co-occurrence network.

    Edge (A, B) with weight W means hashtags A and B appeared together in W tweets.
    """
    print("\nBuilding hashtag co-occurrence network...")

    hashtag_counts = Counter()
    cooccurrence_counts = defaultdict(int)

    for idx, row in tweets_df.iterrows():
        tweet_text = row.get('Tweet', row.get('text', ''))
        hashtags = extract_hashtags(tweet_text)

        # Count individual hashtags
        for h in hashtags:
            hashtag_counts[h] += 1

        # Count co-occurrences
        hashtags_sorted = sorted(set(hashtags))
        for i, h1 in enumerate(hashtags_sorted):
            for h2 in hashtags_sorted[i+1:]:
                cooccurrence_counts[(h1, h2)] += 1

    print(f"Total unique hashtags: {len(hashtag_counts):,}")
    print(f"Total co-occurrence pairs: {len(cooccurrence_counts):,}")

    # Filter to top hashtags
    top_hashtags = set(h for h, _ in hashtag_counts.most_common(top_n))

    # Build network
    if not HAS_NETWORKX:
        return cooccurrence_counts, hashtag_counts

    G = nx.Graph()

    # Add nodes
    for hashtag, count in hashtag_counts.most_common(top_n):
        G.add_node(hashtag, count=count)

    # Add edges
    for (h1, h2), weight in cooccurrence_counts.items():
        if h1 in top_hashtags and h2 in top_hashtags and weight >= min_cooccur:
            G.add_edge(h1, h2, weight=weight)

    print(f"Hashtag network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    return G


# =============================================================================
# COMMUNITY DETECTION
# =============================================================================

def detect_communities_louvain(G, resolution=1.0):
    """
    Detect communities using Louvain algorithm.
    Returns community assignments and modularity.
    """
    if not HAS_NETWORKX:
        return {}, 0

    print("\nRunning Louvain community detection...")

    # For directed graphs, convert to undirected for community detection
    if G.is_directed():
        G_undirected = G.to_undirected()
    else:
        G_undirected = G

    # Get largest connected component
    if nx.is_connected(G_undirected):
        G_lcc = G_undirected
    else:
        lcc = max(nx.connected_components(G_undirected), key=len)
        G_lcc = G_undirected.subgraph(lcc)

    print(f"  Analyzing largest connected component: {G_lcc.number_of_nodes()} nodes")

    try:
        from networkx.algorithms.community import louvain_communities
        communities = louvain_communities(G_lcc, weight='weight', resolution=resolution, seed=42)

        # Convert to node->community mapping
        community_map = {}
        for i, comm in enumerate(communities):
            for node in comm:
                community_map[node] = i

        # Compute modularity
        modularity = nx.algorithms.community.modularity(G_lcc, communities, weight='weight')

        print(f"  Found {len(communities)} communities")
        print(f"  Modularity: {modularity:.4f}")

        # Community sizes
        comm_sizes = sorted([len(c) for c in communities], reverse=True)
        print(f"  Largest communities: {comm_sizes[:10]}")

        return community_map, modularity, communities

    except Exception as e:
        print(f"  Error in community detection: {e}")
        return {}, 0, []


def label_communities_by_kic(community_map, communities):
    """
    Attempt to label communities by dominant KIC affiliation.
    """
    community_labels = {}

    for i, comm in enumerate(communities):
        kic_counts = defaultdict(int)
        for node in comm:
            # Check if node is a known KIC handle
            for handle, kic in KIC_HANDLES.items():
                if node.lower() == handle.lower():
                    kic_counts[kic] += 10  # Boost weight for official accounts
                    break
            # Also check partial matches
            for handle, kic in KIC_HANDLES.items():
                if handle.lower()[1:] in node.lower():  # Remove @ and check
                    kic_counts[kic] += 1

        if kic_counts:
            dominant_kic = max(kic_counts.items(), key=lambda x: x[1])[0]
            community_labels[i] = dominant_kic
        else:
            community_labels[i] = f"Community_{i}"

    return community_labels


# =============================================================================
# BRIDGING ANALYSIS
# =============================================================================

def compute_bridging_scores(G, community_map):
    """
    Compute bridging scores for actors.
    Bridging score = proportion of ties that cross community boundaries.
    """
    if not HAS_NETWORKX:
        return {}

    print("\nComputing bridging scores...")

    bridging_scores = {}

    # Convert to undirected for bridging analysis
    G_undirected = G.to_undirected() if G.is_directed() else G

    for node in G_undirected.nodes():
        if node not in community_map:
            continue

        node_comm = community_map[node]
        neighbors = list(G_undirected.neighbors(node))

        if len(neighbors) == 0:
            bridging_scores[node] = 0
            continue

        cross_community = 0
        for neighbor in neighbors:
            if neighbor in community_map and community_map[neighbor] != node_comm:
                cross_community += 1

        bridging_scores[node] = cross_community / len(neighbors)

    # Get top bridging actors
    top_bridgers = sorted(bridging_scores.items(), key=lambda x: -x[1])[:50]

    # Filter to actors with significant degree (avoid noise)
    min_degree = 10
    significant_bridgers = [
        (node, score) for node, score in top_bridgers
        if G_undirected.degree(node) >= min_degree
    ]

    print(f"  Top bridging actors (degree >= {min_degree}):")
    for node, score in significant_bridgers[:15]:
        degree = G_undirected.degree(node)
        print(f"    {node}: {score:.3f} (degree={degree})")

    return bridging_scores, significant_bridgers


# =============================================================================
# TEMPORAL ANALYSIS
# =============================================================================

def analyze_temporal_dynamics(tweets_df):
    """Analyze temporal patterns in the data."""
    print("\nAnalyzing temporal dynamics...")

    if 'Date' not in tweets_df.columns:
        print("  No Date column found")
        return {}

    tweets_df['Date'] = pd.to_datetime(tweets_df['Date'], errors='coerce')
    tweets_df = tweets_df.dropna(subset=['Date'])

    # Monthly tweet counts
    monthly = tweets_df.set_index('Date').resample('M').size()

    # Yearly summary
    yearly = tweets_df.set_index('Date').resample('Y').size()

    print("\nYearly tweet counts:")
    for date, count in yearly.items():
        print(f"  {date.year}: {count:,}")

    # Extract mentions per year to see network evolution
    yearly_mentions = {}
    for year in range(2015, 2021):
        year_tweets = tweets_df[tweets_df['Date'].dt.year == year]
        all_mentions = []
        for text in year_tweets.get('Tweet', year_tweets.get('text', pd.Series())):
            all_mentions.extend(extract_mentions(text))
        mention_counts = Counter(all_mentions)
        yearly_mentions[year] = mention_counts.most_common(20)

    return {
        'monthly': monthly.to_dict(),
        'yearly': yearly.to_dict(),
        'yearly_top_mentions': yearly_mentions
    }


# =============================================================================
# KIC-SPECIFIC ANALYSIS
# =============================================================================

def extract_kic_subnetworks(G, community_map, community_labels):
    """Extract subnetworks for each EIT KIC."""
    print("\nExtracting KIC-specific subnetworks...")

    kic_subnetworks = {}

    # Group communities by KIC label
    kic_communities = defaultdict(list)
    for comm_id, label in community_labels.items():
        if label != f"Community_{comm_id}":  # Only labeled communities
            kic_communities[label].append(comm_id)

    for kic, comm_ids in kic_communities.items():
        # Get all nodes in these communities
        kic_nodes = [node for node, comm in community_map.items() if comm in comm_ids]

        if len(kic_nodes) < 10:
            continue

        # Extract subgraph
        subgraph = G.subgraph(kic_nodes)

        kic_subnetworks[kic] = {
            'n_nodes': subgraph.number_of_nodes(),
            'n_edges': subgraph.number_of_edges(),
            'density': nx.density(subgraph) if subgraph.number_of_nodes() > 1 else 0,
            'nodes': list(kic_nodes)[:100],  # Sample
        }

        print(f"  {kic}: {subgraph.number_of_nodes()} nodes, {subgraph.number_of_edges()} edges")

    return kic_subnetworks


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

def export_results(results, output_dir):
    """Export analysis results to JSON files."""
    print("\nExporting results...")

    # Network statistics
    with open(output_dir / 'mention_network_stats.json', 'w', encoding='utf-8') as f:
        # Convert non-serializable items
        stats = {k: v for k, v in results.get('mention_metrics', {}).items()
                if not isinstance(v, (list,)) or k in ['top_mentioned', 'top_mentioners']}
        json.dump(stats, f, indent=2, default=str)

    # Community structure
    if 'communities' in results:
        comm_data = {
            'n_communities': len(results['communities']),
            'modularity': results.get('modularity', 0),
            'community_sizes': [len(c) for c in results['communities']],
            'community_labels': results.get('community_labels', {}),
        }
        with open(output_dir / 'community_structure.json', 'w', encoding='utf-8') as f:
            json.dump(comm_data, f, indent=2)

    # Top actors
    if 'mention_metrics' in results:
        top_actors = {
            'most_mentioned': results['mention_metrics'].get('top_mentioned', [])[:50],
            'most_active': results['mention_metrics'].get('top_mentioners', [])[:50],
            'top_bridgers': results.get('top_bridgers', [])[:50],
        }
        with open(output_dir / 'top_actors.json', 'w', encoding='utf-8') as f:
            json.dump(top_actors, f, indent=2, default=str)

    # Temporal analysis
    if 'temporal' in results:
        # Convert timestamp keys to strings
        temporal_data = {}
        for key, value in results['temporal'].items():
            if isinstance(value, dict):
                temporal_data[key] = {str(k): v for k, v in value.items()}
            else:
                temporal_data[key] = value
        with open(output_dir / 'temporal_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(temporal_data, f, indent=2, default=str)

    # KIC subnetworks
    if 'kic_subnetworks' in results:
        with open(output_dir / 'kic_subnetworks.json', 'w', encoding='utf-8') as f:
            json.dump(results['kic_subnetworks'], f, indent=2)

    print(f"Results exported to {output_dir}")


def export_network_for_visualization(G, community_map, output_dir, filename='mention_network'):
    """Export network in formats suitable for visualization."""
    if not HAS_NETWORKX:
        return

    print(f"\nExporting network for visualization...")

    # Get largest connected component for cleaner visualization
    if G.is_directed():
        G_undirected = G.to_undirected()
    else:
        G_undirected = G

    lcc_nodes = max(nx.connected_components(G_undirected), key=len)
    G_lcc = G.subgraph(lcc_nodes)

    # Filter to top nodes by degree for manageable visualization
    degrees = dict(G_lcc.degree())
    top_nodes = sorted(degrees.keys(), key=lambda x: degrees[x], reverse=True)[:500]
    G_viz = G_lcc.subgraph(top_nodes)

    # Export as node/edge lists
    nodes_data = []
    for node in G_viz.nodes():
        node_data = {
            'id': node,
            'degree': degrees.get(node, 0),
            'community': community_map.get(node, -1),
        }
        # Add KIC label if known
        for handle, kic in KIC_HANDLES.items():
            if node.lower() == handle.lower():
                node_data['kic'] = kic
                break
        nodes_data.append(node_data)

    edges_data = [
        {'source': u, 'target': v, 'weight': d.get('weight', 1)}
        for u, v, d in G_viz.edges(data=True)
    ]

    network_data = {
        'nodes': nodes_data,
        'edges': edges_data,
        'statistics': {
            'n_nodes': len(nodes_data),
            'n_edges': len(edges_data),
        }
    }

    with open(output_dir / f'{filename}_viz.json', 'w', encoding='utf-8') as f:
        json.dump(network_data, f, indent=2)

    # Also export as GraphML for Gephi
    try:
        nx.write_graphml(G_viz, output_dir / f'{filename}.graphml')
        print(f"  Exported GraphML: {filename}.graphml")
    except Exception as e:
        print(f"  Could not export GraphML: {e}")

    print(f"  Network visualization data: {len(nodes_data)} nodes, {len(edges_data)} edges")


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_full_analysis():
    """Run the complete Twitter analysis pipeline."""
    print("=" * 70)
    print("EIT ECOSYSTEM TWITTER ANALYSIS PIPELINE")
    print("=" * 70)

    results = {}

    # 1. Load data
    tweets_df = load_all_tweets()
    if tweets_df.empty:
        print("No data loaded. Exiting.")
        return

    results['n_tweets'] = len(tweets_df)

    # 2. Build mention network
    mention_network = build_mention_network(tweets_df)
    if HAS_NETWORKX and isinstance(mention_network, nx.DiGraph):
        results['mention_metrics'] = compute_mention_network_metrics(mention_network)

    # 3. Build hashtag network
    hashtag_network = build_hashtag_network(tweets_df)

    # 4. Community detection on mention network
    if HAS_NETWORKX and isinstance(mention_network, nx.DiGraph):
        community_map, modularity, communities = detect_communities_louvain(mention_network)
        results['community_map'] = community_map
        results['modularity'] = modularity
        results['communities'] = communities

        # Label communities
        community_labels = label_communities_by_kic(community_map, communities)
        results['community_labels'] = community_labels

        # 5. Bridging analysis
        bridging_scores, top_bridgers = compute_bridging_scores(mention_network, community_map)
        results['bridging_scores'] = bridging_scores
        results['top_bridgers'] = top_bridgers

        # 6. KIC subnetworks
        kic_subnetworks = extract_kic_subnetworks(mention_network, community_map, community_labels)
        results['kic_subnetworks'] = kic_subnetworks

        # 7. Export network for visualization
        export_network_for_visualization(mention_network, community_map, OUTPUT_DIR)

    # 8. Temporal analysis
    temporal_results = analyze_temporal_dynamics(tweets_df)
    results['temporal'] = temporal_results

    # 9. Export results
    export_results(results, OUTPUT_DIR)

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)

    # Summary statistics
    print("\nSUMMARY:")
    print(f"  Total tweets analyzed: {results['n_tweets']:,}")
    if 'mention_metrics' in results:
        print(f"  Mention network: {results['mention_metrics']['n_nodes']:,} nodes, {results['mention_metrics']['n_edges']:,} edges")
    if 'communities' in results:
        print(f"  Communities detected: {len(results['communities'])}")
        print(f"  Modularity: {results['modularity']:.4f}")

    return results


if __name__ == "__main__":
    results = run_full_analysis()
