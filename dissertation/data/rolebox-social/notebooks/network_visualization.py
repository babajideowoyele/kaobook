"""
Network Visualization for EIT Twitter Data
===========================================

This script provides multiple visualization options for the mention network:
1. Static plots with matplotlib/networkx
2. Interactive HTML with pyvis
3. Export for Gephi desktop application

Usage:
    python network_visualization.py

Requirements:
    pip install networkx matplotlib pyvis
"""

import json
from pathlib import Path
import sys

# Paths
DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# LOAD DATA
# =============================================================================

def load_network_data():
    """Load the pre-computed network visualization data."""
    viz_file = DATA_DIR / "mention_network_viz.json"

    if not viz_file.exists():
        print(f"Error: {viz_file} not found")
        print("Run twitter_analysis_pipeline.py first to generate the network data")
        return None

    with open(viz_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Loaded network: {len(data['nodes'])} nodes, {len(data['edges'])} edges")
    return data


def load_community_data():
    """Load community structure data."""
    comm_file = DATA_DIR / "community_structure.json"

    if comm_file.exists():
        with open(comm_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


# =============================================================================
# OPTION 1: MATPLOTLIB/NETWORKX STATIC PLOTS
# =============================================================================

def plot_with_networkx(data, output_file="network_plot.png", max_nodes=200):
    """
    Create static network plot with matplotlib.
    Good for publication-quality figures.
    """
    try:
        import networkx as nx
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("Install requirements: pip install networkx matplotlib numpy")
        return

    print(f"\nCreating NetworkX visualization ({max_nodes} nodes)...")

    # Build graph from data
    G = nx.DiGraph()

    # Sort nodes by degree and take top N
    nodes_sorted = sorted(data['nodes'], key=lambda x: x['degree'], reverse=True)[:max_nodes]
    node_ids = {n['id'] for n in nodes_sorted}

    # Add nodes
    for node in nodes_sorted:
        G.add_node(node['id'],
                   degree=node['degree'],
                   community=node.get('community', 0),
                   kic=node.get('kic', ''))

    # Add edges (only between included nodes)
    for edge in data['edges']:
        if edge['source'] in node_ids and edge['target'] in node_ids:
            G.add_edge(edge['source'], edge['target'], weight=edge.get('weight', 1))

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))

    # Layout
    print("  Computing layout (this may take a moment)...")
    pos = nx.spring_layout(G, k=2/np.sqrt(G.number_of_nodes()), iterations=50, seed=42)

    # Node colors by community
    communities = [G.nodes[n].get('community', 0) for n in G.nodes()]
    unique_comms = list(set(communities))
    cmap = plt.cm.Set3
    colors = [cmap(unique_comms.index(c) % 12 / 12) for c in communities]

    # Node sizes by degree
    degrees = [G.nodes[n].get('degree', 10) for n in G.nodes()]
    max_deg = max(degrees) if degrees else 1
    sizes = [100 + 500 * (d / max_deg) for d in degrees]

    # Draw edges
    nx.draw_networkx_edges(G, pos, alpha=0.2, arrows=True,
                           arrowsize=5, edge_color='gray', ax=ax)

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=sizes, alpha=0.8, ax=ax)

    # Labels for high-degree nodes only
    high_degree_nodes = {n: n.replace('@', '') for n in G.nodes()
                         if G.nodes[n].get('degree', 0) > np.percentile(degrees, 90)}
    nx.draw_networkx_labels(G, pos, high_degree_nodes, font_size=6, ax=ax)

    # Highlight KIC nodes
    kic_nodes = [n for n in G.nodes() if G.nodes[n].get('kic', '')]
    if kic_nodes:
        kic_pos = {n: pos[n] for n in kic_nodes}
        nx.draw_networkx_nodes(G, kic_pos, nodelist=kic_nodes,
                               node_color='red', node_size=400,
                               node_shape='s', alpha=0.9, ax=ax)
        kic_labels = {n: G.nodes[n]['kic'] for n in kic_nodes}
        nx.draw_networkx_labels(G, kic_pos, kic_labels, font_size=8,
                                font_color='darkred', font_weight='bold', ax=ax)

    ax.set_title(f"EIT Twitter Mention Network\n({G.number_of_nodes()} actors, {G.number_of_edges()} mentions)",
                 fontsize=14)
    ax.axis('off')

    plt.tight_layout()

    output_path = OUTPUT_DIR / output_file
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"  Saved: {output_path}")

    # Also save PDF for LaTeX
    pdf_path = OUTPUT_DIR / output_file.replace('.png', '.pdf')
    plt.savefig(pdf_path, bbox_inches='tight', facecolor='white')
    print(f"  Saved: {pdf_path}")

    plt.close()

    return G


# =============================================================================
# OPTION 2: PYVIS INTERACTIVE HTML
# =============================================================================

def plot_with_pyvis(data, output_file="network_interactive.html", max_nodes=300):
    """
    Create interactive HTML visualization with pyvis.
    Good for exploration and presentations.
    """
    try:
        from pyvis.network import Network
    except ImportError:
        print("Install pyvis: pip install pyvis")
        return

    print(f"\nCreating PyVis interactive visualization ({max_nodes} nodes)...")

    # Create network
    net = Network(height="800px", width="100%", bgcolor="#ffffff",
                  font_color="black", directed=True)

    # Physics settings for better layout
    net.barnes_hut(gravity=-5000, central_gravity=0.3, spring_length=200)

    # Sort nodes by degree
    nodes_sorted = sorted(data['nodes'], key=lambda x: x['degree'], reverse=True)[:max_nodes]
    node_ids = {n['id'] for n in nodes_sorted}

    # Color palette for communities
    colors = [
        '#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00',
        '#ffff33', '#a65628', '#f781bf', '#999999', '#66c2a5',
        '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f'
    ]

    # KIC-specific colors
    kic_colors = {
        'Climate-KIC': '#2ecc71',
        'EIT Digital': '#3498db',
        'EIT Health': '#e74c3c',
        'EIT RawMaterials': '#f39c12',
        'InnoEnergy': '#9b59b6',
        'EIT Food': '#1abc9c',
        'EIT Urban Mobility': '#34495e',
        'EIT Central': '#95a5a6',
    }

    # Add nodes
    for node in nodes_sorted:
        node_id = node['id']
        degree = node['degree']
        community = node.get('community', 0)
        kic = node.get('kic', '')

        # Determine color
        if kic:
            color = kic_colors.get(kic, '#e74c3c')
            title = f"{node_id}\nKIC: {kic}\nDegree: {degree}"
        else:
            color = colors[community % len(colors)]
            title = f"{node_id}\nCommunity: {community}\nDegree: {degree}"

        # Size based on degree
        size = 10 + min(degree / 10, 50)

        net.add_node(node_id,
                     label=node_id.replace('@', ''),
                     title=title,
                     color=color,
                     size=size)

    # Add edges
    for edge in data['edges']:
        if edge['source'] in node_ids and edge['target'] in node_ids:
            weight = edge.get('weight', 1)
            net.add_edge(edge['source'], edge['target'],
                         value=weight,
                         title=f"Weight: {weight}")

    # Configure options
    net.set_options("""
    var options = {
      "nodes": {
        "borderWidth": 1,
        "borderWidthSelected": 3,
        "font": {"size": 10}
      },
      "edges": {
        "color": {"inherit": true},
        "smooth": {"type": "continuous"}
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -5000,
          "springLength": 200
        }
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100
      }
    }
    """)

    output_path = OUTPUT_DIR / output_file
    net.save_graph(str(output_path))
    print(f"  Saved: {output_path}")
    print(f"  Open in browser to explore interactively!")

    return net


# =============================================================================
# OPTION 3: GEPHI INSTRUCTIONS
# =============================================================================

def gephi_instructions():
    """Print instructions for using Gephi."""
    graphml_path = DATA_DIR / "mention_network.graphml"

    print("""
================================================================================
                        GEPHI VISUALIZATION GUIDE
================================================================================

  1. DOWNLOAD GEPHI
     https://gephi.org/

  2. IMPORT THE NETWORK
     File > Open > Select: mention_network.graphml
     Location: {path}

  3. LAYOUT (try in order)
     - ForceAtlas2: Best for large networks, reveals structure
       * Scaling: 10-50
       * Prevent Overlap: ON
       * LinLog mode: ON for tighter clusters

     - Fruchterman Reingold: Good alternative, faster
     - Yifan Hu: Very fast for initial positioning

  4. NODE APPEARANCE
     - Size by: Ranking > Degree (in or out)
       Min: 5, Max: 50
     - Color by: Partition > Run Modularity first (Statistics panel)

  5. COMMUNITY DETECTION
     Statistics > Modularity > Run
     Then: Appearance > Nodes > Color > Partition > Modularity Class

  6. LABELS
     - Show labels for high-degree nodes only:
       Filters > Topology > Degree Range > Adjust slider
     - Or: Data Laboratory > sort by degree, copy top nodes

  7. EXPORT
     File > Export > SVG/PDF/PNG
     Preview panel for high-quality rendering

================================================================================
""".format(path=graphml_path))


# =============================================================================
# OPTION 4: COMMUNITY SIZE VISUALIZATION
# =============================================================================

def plot_community_sizes(output_file="community_sizes.png"):
    """Plot community size distribution."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("Install matplotlib: pip install matplotlib")
        return

    comm_data = load_community_data()
    if not comm_data:
        print("No community data found")
        return

    print("\nCreating community size visualization...")

    sizes = sorted(comm_data['community_sizes'], reverse=True)
    labels = comm_data.get('community_labels', {})

    # Find labeled (KIC) communities
    kic_comms = {}
    for comm_id, label in labels.items():
        if label != f"Community_{comm_id}":
            idx = int(comm_id)
            if idx < len(comm_data['community_sizes']):
                kic_comms[label] = comm_data['community_sizes'][idx]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Plot 1: All communities (log scale)
    ax1 = axes[0]
    ax1.bar(range(len(sizes)), sizes, color='steelblue', alpha=0.7)
    ax1.set_xlabel('Community Rank')
    ax1.set_ylabel('Community Size (actors)')
    ax1.set_title(f'Community Size Distribution\n({len(sizes)} communities, modularity={comm_data["modularity"]:.3f})')
    ax1.set_yscale('log')

    # Plot 2: KIC communities only
    ax2 = axes[1]
    if kic_comms:
        kic_names = list(kic_comms.keys())
        kic_sizes = list(kic_comms.values())

        # Sort by size
        sorted_pairs = sorted(zip(kic_names, kic_sizes), key=lambda x: -x[1])
        kic_names = [p[0] for p in sorted_pairs]
        kic_sizes = [p[1] for p in sorted_pairs]

        colors = ['#2ecc71', '#3498db', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c']
        bars = ax2.barh(kic_names, kic_sizes, color=colors[:len(kic_names)])
        ax2.set_xlabel('Community Size (actors)')
        ax2.set_title('KIC Community Sizes')

        # Add value labels
        for bar, size in zip(bars, kic_sizes):
            ax2.text(bar.get_width() + 100, bar.get_y() + bar.get_height()/2,
                     f'{size:,}', va='center', fontsize=9)

    plt.tight_layout()

    output_path = OUTPUT_DIR / output_file
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"  Saved: {output_path}")

    plt.close()


# =============================================================================
# OPTION 5: KIC SUBNETWORK COMPARISON
# =============================================================================

def plot_kic_comparison(output_file="kic_comparison.png"):
    """Plot KIC subnetwork comparison (size vs density)."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("Install matplotlib: pip install matplotlib")
        return

    kic_file = DATA_DIR / "kic_subnetworks.json"
    if not kic_file.exists():
        print("No KIC subnetwork data found")
        return

    with open(kic_file, 'r', encoding='utf-8') as f:
        kic_data = json.load(f)

    print("\nCreating KIC comparison visualization...")

    fig, ax = plt.subplots(figsize=(10, 7))

    kic_colors = {
        'Climate-KIC': '#2ecc71',
        'EIT Digital': '#3498db',
        'EIT Health': '#e74c3c',
        'EIT RawMaterials': '#f39c12',
        'InnoEnergy': '#9b59b6',
        'EIT Food': '#1abc9c',
        'EIT Urban Mobility': '#34495e',
    }

    for kic, stats in kic_data.items():
        size = stats['n_nodes']
        density = stats['density'] * 10000  # Scale for readability
        color = kic_colors.get(kic, 'gray')

        ax.scatter(size, density, s=200, c=color, alpha=0.8, edgecolors='black', linewidth=1)
        ax.annotate(kic.replace('EIT ', ''), (size, density),
                    xytext=(5, 5), textcoords='offset points', fontsize=9)

    ax.set_xlabel('Subnetwork Size (actors)', fontsize=11)
    ax.set_ylabel('Network Density (×10⁻⁴)', fontsize=11)
    ax.set_title('KIC Subnetwork Characteristics:\nSize vs. Density Trade-off', fontsize=12)
    ax.grid(True, alpha=0.3)

    # Add trend line
    sizes = [stats['n_nodes'] for stats in kic_data.values()]
    densities = [stats['density'] * 10000 for stats in kic_data.values()]
    if len(sizes) > 2:
        z = np.polyfit(np.log(sizes), densities, 1)
        x_trend = np.linspace(min(sizes), max(sizes), 100)
        y_trend = z[0] * np.log(x_trend) + z[1]
        ax.plot(x_trend, y_trend, 'k--', alpha=0.3, label='Log trend')

    plt.tight_layout()

    output_path = OUTPUT_DIR / output_file
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"  Saved: {output_path}")

    plt.close()


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("EIT Twitter Network Visualization")
    print("=" * 60)

    # Load data
    data = load_network_data()
    if not data:
        return

    # Run all visualizations
    print("\n" + "=" * 60)
    print("VISUALIZATION OPTIONS")
    print("=" * 60)

    # 1. Static matplotlib plot
    plot_with_networkx(data, max_nodes=200)

    # 2. Interactive pyvis
    plot_with_pyvis(data, max_nodes=300)

    # 3. Community sizes
    plot_community_sizes()

    # 4. KIC comparison
    plot_kic_comparison()

    # 5. Gephi instructions
    gephi_instructions()

    print("\n" + "=" * 60)
    print("VISUALIZATION COMPLETE")
    print("=" * 60)
    print(f"\nOutput files in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
