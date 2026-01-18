"""
Run Field Identification Pipeline
=================================

Executes the complete Benabdelkrim et al. (2020) methodology on EIT Twitter data.

Reference:
    Benabdelkrim, M., Levallois, C., Savinien, J., & Robardet, C. (2020).
    Opening Fields: A Methodological Contribution to the Identification of
    Heterogeneous Actors in Unbounded Relational Orders.
    M@n@gement, 23(1), 4-18.
    https://doi.org/10.37725/mgmt.v23.4245

This script:
1. Loads TweetBinder tweet data
2. Builds mention co-classification proxy
3. Runs seed expansion from EIT accounts
4. Detects communities via Louvain
5. Extracts characteristic terms per community
6. Generates visualizations and term clouds

Usage:
    python run_field_identification.py
"""

import json
import re
import csv
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Set, Tuple

# Try imports
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from wordcloud import WordCloud
    HAS_WORDCLOUD = True
except ImportError:
    HAS_WORDCLOUD = False

# Local imports - handle both module and direct execution
try:
    from .seed_expansion import (
        FieldIdentifier,
        MentionBasedCoClassification,
        SeedAccount,
        SubRegion,
    )
    from .sigma_export import export_network_visualization
except ImportError:
    from seed_expansion import (
        FieldIdentifier,
        MentionBasedCoClassification,
        SeedAccount,
        SubRegion,
    )
    from sigma_export import export_network_visualization


# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).parent.parent.parent  # rolebox-social
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "field_identification"
FIGURES_DIR = DATA_DIR / "figures"

# Create directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# EIT SEED ACCOUNTS
# =============================================================================

EIT_SEEDS = [
    {
        'username': '@EITeu',
        'type': 'central',
        'description': 'EIT Central',
        'kic': 'EIT Central',
    },
    {
        'username': '@EITClimatekic',
        'type': 'institutional',
        'description': 'Climate-KIC',
        'kic': 'Climate-KIC',
    },
    {
        'username': '@EITDigital',
        'type': 'institutional',
        'description': 'EIT Digital',
        'kic': 'EIT Digital',
    },
    {
        'username': '@EITHealth',
        'type': 'institutional',
        'description': 'EIT Health',
        'kic': 'EIT Health',
    },
    {
        'username': '@InnoEnergy',
        'type': 'institutional',
        'description': 'EIT InnoEnergy',
        'kic': 'EIT InnoEnergy',
    },
    {
        'username': '@EITFood',
        'type': 'institutional',
        'description': 'EIT Food',
        'kic': 'EIT Food',
    },
    {
        'username': '@EITRawMaterials',
        'type': 'institutional',
        'description': 'EIT RawMaterials',
        'kic': 'EIT RawMaterials',
    },
    {
        'username': '@EIT_Urban',
        'type': 'institutional',
        'description': 'EIT Urban Mobility',
        'kic': 'EIT Urban Mobility',
    },
    {
        'username': '@EITManufacturing',
        'type': 'institutional',
        'description': 'EIT Manufacturing',
        'kic': 'EIT Manufacturing',
    },
]


# =============================================================================
# DATA LOADING
# =============================================================================

def load_tweets_csv(filepath: Path) -> List[Dict]:
    """Load tweets from CSV file."""
    tweets = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tweets.append(row)

    print(f"Loaded {len(tweets)} tweets from {filepath.name}")
    return tweets


def load_existing_network() -> Tuple[Dict, Dict]:
    """Load pre-computed network and community data."""
    network_data = None
    community_data = None

    viz_file = PROCESSED_DIR / "mention_network_viz.json"
    if viz_file.exists():
        with open(viz_file, 'r', encoding='utf-8') as f:
            network_data = json.load(f)
        print(f"Loaded network: {len(network_data['nodes'])} nodes, {len(network_data['edges'])} edges")

    comm_file = PROCESSED_DIR / "community_structure.json"
    if comm_file.exists():
        with open(comm_file, 'r', encoding='utf-8') as f:
            community_data = json.load(f)
        print(f"Loaded communities: {community_data['n_communities']} communities")

    return network_data, community_data


def build_mention_data_source(tweets: List[Dict]) -> MentionBasedCoClassification:
    """Build mention co-classification source from tweets."""
    data_source = MentionBasedCoClassification(min_co_mentions=2)

    for i, tweet in enumerate(tweets):
        # Get mentions from field or extract from text
        mentions_str = tweet.get('mentions', '')
        if mentions_str:
            mentions = [m.strip() for m in mentions_str.split(';') if m.strip()]
        else:
            text = tweet.get('text', '')
            mentions = re.findall(r'@(\w+)', text)

        # Add author to mentions for self-reference tracking
        author = tweet.get('author_handle', '').replace('@', '')
        if author:
            mentions.append(author)

        data_source.add_tweet(str(i), mentions, author)

        # Add author bio from description if available
        author_handle = tweet.get('author_handle', '')
        author_name = tweet.get('author_name', '')
        if author_handle:
            bio = f"{author_name} - KIC account" if tweet.get('kic') else author_name
            data_source.add_user_bio(author_handle, bio)

    stats = data_source.get_statistics()
    print(f"\nData source built:")
    print(f"  Users: {stats['n_users']}")
    print(f"  Tweets: {stats['n_tweets']}")
    print(f"  Bios: {stats['n_bios']}")

    return data_source


# =============================================================================
# VISUALIZATION: TERM CLOUDS
# =============================================================================

def generate_term_cloud(terms: List[Tuple[str, float]], title: str, output_path: Path):
    """Generate word cloud from term frequencies."""
    if not HAS_WORDCLOUD or not HAS_MATPLOTLIB:
        print(f"  Skipping word cloud (wordcloud or matplotlib not available)")
        return

    if not terms:
        print(f"  No terms for {title}")
        return

    # Build frequency dict
    freq_dict = {term: score for term, score in terms if score > 0}

    if not freq_dict:
        return

    # Generate word cloud
    wc = WordCloud(
        width=800,
        height=400,
        background_color='white',
        max_words=50,
        relative_scaling=0.7,
        colormap='viridis',
    )

    wc.generate_from_frequencies(freq_dict)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    ax.set_title(title, fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  Saved: {output_path.name}")


def generate_all_term_clouds(sub_regions: List, output_dir: Path):
    """Generate term clouds for all significant sub-regions."""
    print("\nGenerating term clouds...")

    cloud_dir = output_dir / "term_clouds"
    cloud_dir.mkdir(parents=True, exist_ok=True)

    for sr in sub_regions[:15]:  # Top 15 communities
        if sr.size < 10:
            continue

        # Absolute terms cloud
        if sr.top_terms:
            safe_label = re.sub(r'[^\w\s-]', '', sr.label)[:30].strip()
            output_path = cloud_dir / f"community_{sr.id}_{safe_label}_absolute.png"
            generate_term_cloud(sr.top_terms, f"{sr.label} (n={sr.size})", output_path)

        # Relative/distinctive terms cloud
        if sr.top_terms_relative:
            safe_label = re.sub(r'[^\w\s-]', '', sr.label)[:30].strip()
            output_path = cloud_dir / f"community_{sr.id}_{safe_label}_distinctive.png"
            generate_term_cloud(
                sr.top_terms_relative,
                f"{sr.label} - Distinctive Terms (n={sr.size})",
                output_path
            )


# =============================================================================
# VISUALIZATION: COMMUNITY COMPARISON
# =============================================================================

def plot_community_characteristics(sub_regions: List, output_path: Path):
    """Plot community size vs density comparison."""
    if not HAS_MATPLOTLIB:
        return

    print("\nPlotting community characteristics...")

    # Filter to significant communities
    significant = [sr for sr in sub_regions if sr.size >= 20]

    if len(significant) < 3:
        print("  Not enough significant communities")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # KIC colors
    kic_colors = {
        'EIT Central': '#95a5a6',
        'Climate-KIC': '#2ecc71',
        'EIT Digital': '#3498db',
        'EIT Health': '#e74c3c',
        'EIT InnoEnergy': '#9b59b6',
        'EIT Food': '#1abc9c',
        'EIT RawMaterials': '#f39c12',
        'EIT Urban Mobility': '#34495e',
        'EIT Manufacturing': '#e67e22',
    }
    default_color = '#7f8c8d'

    # Plot 1: Size vs Density
    ax1 = axes[0]
    sizes = [sr.size for sr in significant]
    densities = [sr.internal_density * 100 for sr in significant]  # As percentage

    colors = [kic_colors.get(sr.seed_affiliation, default_color) for sr in significant]

    scatter = ax1.scatter(sizes, densities, c=colors, s=100, alpha=0.7, edgecolors='black')

    # Label notable communities
    for sr in significant[:10]:
        ax1.annotate(
            sr.label[:20],
            (sr.size, sr.internal_density * 100),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=8,
            alpha=0.8
        )

    ax1.set_xlabel('Community Size', fontsize=11)
    ax1.set_ylabel('Internal Density (%)', fontsize=11)
    ax1.set_title('Community Size vs. Internal Density', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')

    # Plot 2: Top communities by size
    ax2 = axes[1]
    top_n = 12
    top_communities = sorted(significant, key=lambda x: x.size, reverse=True)[:top_n]

    labels = [sr.label[:25] for sr in top_communities]
    sizes = [sr.size for sr in top_communities]
    colors = [kic_colors.get(sr.seed_affiliation, default_color) for sr in top_communities]

    bars = ax2.barh(labels[::-1], sizes[::-1], color=colors[::-1], edgecolor='black', alpha=0.8)

    ax2.set_xlabel('Community Size', fontsize=11)
    ax2.set_title(f'Top {top_n} Communities by Size', fontsize=12)

    # Add legend for KIC colors
    kic_patches = [
        mpatches.Patch(color=color, label=kic)
        for kic, color in kic_colors.items()
    ]
    ax1.legend(handles=kic_patches, loc='upper right', fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  Saved: {output_path.name}")


def plot_term_comparison(sub_regions: List, output_path: Path):
    """Plot distinctive terms comparison across top communities."""
    if not HAS_MATPLOTLIB:
        return

    print("\nPlotting term comparison...")

    # Get top 6 communities with terms
    top = [sr for sr in sub_regions if sr.size >= 50 and sr.top_terms_relative][:6]

    if len(top) < 3:
        print("  Not enough communities with terms")
        return

    n_terms = 8

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    for i, sr in enumerate(top):
        ax = axes[i]

        terms = sr.top_terms_relative[:n_terms]
        term_labels = [t for t, _ in terms]
        scores = [s for _, s in terms]

        colors = plt.cm.viridis([s / max(scores) if scores else 0 for s in scores])

        ax.barh(term_labels[::-1], scores[::-1], color=colors[::-1], edgecolor='black', alpha=0.8)
        ax.set_xlabel('Relative Frequency', fontsize=10)
        ax.set_title(f"{sr.label[:25]}\n(n={sr.size})", fontsize=11, fontweight='bold')
        ax.tick_params(axis='y', labelsize=9)

    # Hide empty subplots
    for i in range(len(top), len(axes)):
        axes[i].set_visible(False)

    plt.suptitle('Distinctive Terms by Community', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  Saved: {output_path.name}")


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_pipeline():
    """Run complete field identification pipeline."""
    print("=" * 70)
    print("FIELD IDENTIFICATION PIPELINE")
    print("Implementing Benabdelkrim et al. (2020) Social Curation Methodology")
    print("=" * 70)

    # Step 1: Load data
    print("\n[STEP 1] Loading data...")

    # Try to load existing network data first
    network_data, community_data = load_existing_network()

    # Load tweet data
    csv_file = RAW_DIR / "eit_twitter_sample.csv"
    if csv_file.exists():
        tweets = load_tweets_csv(csv_file)
    else:
        print(f"Warning: {csv_file} not found, using existing network data only")
        tweets = []

    # Step 2: Build or use existing data source
    print("\n[STEP 2] Building co-classification data source...")

    if tweets:
        data_source = build_mention_data_source(tweets)
    else:
        # Create empty data source, will use existing network
        data_source = MentionBasedCoClassification(min_co_mentions=2)

    # Step 3: Run field identification
    print("\n[STEP 3] Running field identification...")

    config = {
        'min_k': 2,
        'max_ring1': 5000,
        'max_ring2': 50000,
        'random_walk_iterations': 500,
        'louvain_resolution': 1.0,
        'top_terms_per_community': 25,
    }

    identifier = FieldIdentifier(config)
    identifier.set_seeds(EIT_SEEDS)
    identifier.set_data_source(data_source)

    # Run expansion if we have data
    if data_source.get_statistics()['n_users'] > 0:
        try:
            identifier.run_expansion(denoise=True)
            identifier.detect_communities()
            identifier.characterize_regions()
        except Exception as e:
            print(f"  Warning: Pipeline error: {e}")
            print("  Falling back to existing community data...")

    # If no results, use existing community data for visualization
    if not identifier.sub_regions and community_data:
        print("\n[STEP 3b] Using pre-computed community data...")

        sizes = community_data['community_sizes']
        labels = community_data['community_labels']

        for i, size in enumerate(sizes):
            label = labels.get(str(i), f"Community_{i}")

            # Determine seed affiliation from label
            seed_affiliation = ""
            for kic_name in ['Climate-KIC', 'EIT Digital', 'EIT Health', 'EIT InnoEnergy',
                            'EIT Food', 'EIT RawMaterials', 'EIT Urban Mobility', 'EIT Manufacturing']:
                if kic_name in label:
                    seed_affiliation = kic_name
                    break

            sr = SubRegion(
                id=i,
                label=label,
                members=set(),
                size=size,
                internal_density=0,
                external_ties=0,
                top_terms=[],
                top_terms_relative=[],
                languages={},
                seed_affiliation=seed_affiliation,
            )
            identifier.sub_regions.append(sr)

        # Sort by size
        identifier.sub_regions.sort(key=lambda x: x.size, reverse=True)

    # Step 4: Export results
    print("\n[STEP 4] Exporting results...")

    if identifier.sub_regions:
        # Only export if we have meaningful results
        try:
            results = identifier.export_results(OUTPUT_DIR)
        except Exception as e:
            print(f"  Warning: Export error: {e}")
            results = None

        # Save summary
        summary = {
            'methodology': 'Benabdelkrim et al. (2020) Social Curation',
            'data_source': 'TweetBinder mention co-occurrence',
            'n_seeds': len(EIT_SEEDS),
            'seeds': [s['username'] for s in EIT_SEEDS],
            'n_communities': len(identifier.sub_regions),
            'top_communities': [
                {
                    'rank': i + 1,
                    'label': sr.label,
                    'size': sr.size,
                    'seed': sr.seed_affiliation,
                }
                for i, sr in enumerate(identifier.sub_regions[:20])
            ],
        }

        with open(OUTPUT_DIR / 'summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

    # Step 5: Generate visualizations
    print("\n[STEP 5] Generating visualizations...")

    if identifier.sub_regions:
        # Community characteristics plot
        plot_community_characteristics(
            identifier.sub_regions,
            FIGURES_DIR / 'field_community_characteristics.png'
        )

        # Term comparison plot
        plot_term_comparison(
            identifier.sub_regions,
            FIGURES_DIR / 'field_term_comparison.png'
        )

        # Term clouds
        generate_all_term_clouds(identifier.sub_regions, FIGURES_DIR)

    # Step 6: Generate Sigma.js interactive visualization
    print("\n[STEP 6] Generating Sigma.js interactive visualization...")

    if network_data and HAS_NETWORKX:
        # Build graph from existing network data
        G = nx.DiGraph()

        # Add nodes with attributes
        for node in network_data['nodes']:
            G.add_node(
                node['id'],
                degree=node.get('degree', 1),
                community=node.get('community', 0),
                kic=node.get('kic', ''),
            )

        # Add edges
        for edge in network_data['edges']:
            G.add_edge(
                edge['source'],
                edge['target'],
                weight=edge.get('weight', 1)
            )

        # Build community mappings
        node_communities = {node['id']: node.get('community', 0) for node in network_data['nodes']}
        comm_labels = community_data.get('community_labels', {}) if community_data else {}
        comm_labels_int = {int(k): v for k, v in comm_labels.items()}

        # Export to Sigma.js formats
        try:
            export_network_visualization(
                G,
                FIGURES_DIR / 'sigma',
                title="EIT Innovation Network - Field Identification",
                communities=node_communities,
                community_labels=comm_labels_int,
            )
        except Exception as e:
            print(f"  Warning: Sigma.js export error: {e}")

    # Final summary
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)

    print(f"\nResults saved to:")
    print(f"  Data: {OUTPUT_DIR}")
    print(f"  Figures: {FIGURES_DIR}")

    if identifier.sub_regions:
        print(f"\nField structure:")
        print(f"  Total communities: {len(identifier.sub_regions)}")
        print(f"  KIC-affiliated: {sum(1 for sr in identifier.sub_regions if sr.seed_affiliation)}")

        print(f"\nLargest communities:")
        for i, sr in enumerate(identifier.sub_regions[:10]):
            seed_info = f" [{sr.seed_affiliation}]" if sr.seed_affiliation else ""
            print(f"  {i+1}. {sr.label}{seed_info} (n={sr.size})")


if __name__ == "__main__":
    run_pipeline()
