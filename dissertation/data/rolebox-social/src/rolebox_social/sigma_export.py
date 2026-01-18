"""
Sigma.js Network Export
=======================

Generate interactive HTML visualizations using Sigma.js.

Sigma.js is a JavaScript library for displaying graphs in the browser,
optimized for large networks with smooth WebGL rendering.

This module exports networks to:
1. JSON format compatible with Sigma.js
2. Self-contained HTML files with embedded visualization
3. GEXF format for Gephi interoperability

References:
- Sigma.js: https://www.sigmajs.org/
- GEXF format: https://gexf.net/
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict

# Try imports
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


# =============================================================================
# COLOR PALETTES
# =============================================================================

# EIT KIC color palette
KIC_COLORS = {
    'EIT Central': '#6c757d',
    'Climate-KIC': '#28a745',
    'EIT Digital': '#007bff',
    'EIT Health': '#dc3545',
    'EIT InnoEnergy': '#6f42c1',
    'InnoEnergy': '#6f42c1',
    'EIT Food': '#20c997',
    'EIT RawMaterials': '#fd7e14',
    'EIT Urban Mobility': '#343a40',
    'EIT Manufacturing': '#e83e8c',
    'EIT Culture & Creativity': '#17a2b8',
}

# Community color palette (for non-KIC communities)
COMMUNITY_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
]


# =============================================================================
# SIGMA.JS JSON EXPORT
# =============================================================================

def network_to_sigma_json(
    G: 'nx.Graph',
    communities: Dict[str, int] = None,
    community_labels: Dict[int, str] = None,
    node_sizes: Dict[str, float] = None,
    output_path: Path = None,
) -> Dict:
    """
    Convert NetworkX graph to Sigma.js-compatible JSON format.

    Args:
        G: NetworkX graph
        communities: Mapping of node IDs to community indices
        community_labels: Mapping of community indices to labels
        node_sizes: Mapping of node IDs to sizes (default: degree)
        output_path: Optional path to save JSON file

    Returns:
        Dict with 'nodes' and 'edges' lists
    """
    communities = communities or {}
    community_labels = community_labels or {}
    node_sizes = node_sizes or {}

    # Compute layout if not present
    if not all('x' in G.nodes[n] and 'y' in G.nodes[n] for n in G.nodes()):
        print("  Computing layout...")
        pos = nx.spring_layout(G, k=1.5/math.sqrt(G.number_of_nodes()),
                               iterations=50, seed=42)
        for node, (x, y) in pos.items():
            G.nodes[node]['x'] = x * 1000  # Scale for better visualization
            G.nodes[node]['y'] = y * 1000

    # Build nodes array
    nodes = []
    for node in G.nodes():
        attrs = G.nodes[node]

        # Determine community and color
        comm_idx = communities.get(node, attrs.get('community', 0))
        comm_label = community_labels.get(comm_idx, f"Community {comm_idx}")

        # Get color from KIC or community palette
        if comm_label in KIC_COLORS:
            color = KIC_COLORS[comm_label]
        else:
            color = COMMUNITY_COLORS[comm_idx % len(COMMUNITY_COLORS)]

        # Get size (default to degree)
        size = node_sizes.get(node, G.degree(node))
        size = max(3, min(50, size))  # Clamp size

        node_data = {
            'id': str(node),
            'label': str(node).replace('@', ''),
            'x': attrs.get('x', 0),
            'y': attrs.get('y', 0),
            'size': size,
            'color': color,
            'community': comm_idx,
            'communityLabel': comm_label,
        }

        # Add any extra attributes
        for key in ['kic', 'type', 'degree', 'betweenness']:
            if key in attrs:
                node_data[key] = attrs[key]

        nodes.append(node_data)

    # Build edges array
    edges = []
    for i, (u, v, data) in enumerate(G.edges(data=True)):
        edge_data = {
            'id': f"e{i}",
            'source': str(u),
            'target': str(v),
            'weight': data.get('weight', 1),
        }
        edges.append(edge_data)

    result = {
        'nodes': nodes,
        'edges': edges,
    }

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"  Saved: {output_path.name}")

    return result


# =============================================================================
# SELF-CONTAINED HTML EXPORT
# =============================================================================

def generate_sigma_html(
    graph_data: Dict,
    title: str = "Network Visualization",
    output_path: Path = None,
    width: str = "100%",
    height: str = "800px",
) -> str:
    """
    Generate self-contained HTML file with Sigma.js visualization.

    Uses CDN-hosted Sigma.js and Graphology libraries.

    Args:
        graph_data: Dict with 'nodes' and 'edges' from network_to_sigma_json
        title: Page title
        output_path: Path to save HTML file
        width: Container width
        height: Container height

    Returns:
        HTML string
    """

    # Build legend from unique community labels
    communities_in_data = {}
    for node in graph_data['nodes']:
        comm_label = node.get('communityLabel', 'Unknown')
        color = node.get('color', '#666')
        if comm_label not in communities_in_data:
            communities_in_data[comm_label] = color

    legend_items = '\n'.join([
        f'<div class="legend-item"><span class="legend-color" style="background-color: {color}"></span>{label}</div>'
        for label, color in sorted(communities_in_data.items())[:15]
    ])

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>

    <!-- Sigma.js and Graphology from CDN -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/graphology/0.25.4/graphology.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/sigma.js/2.4.0/sigma.min.js"></script>

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
        }}
        .header {{
            padding: 15px 20px;
            background: #16213e;
            border-bottom: 1px solid #0f3460;
        }}
        .header h1 {{
            font-size: 1.4em;
            font-weight: 500;
        }}
        .header p {{
            font-size: 0.85em;
            color: #aaa;
            margin-top: 4px;
        }}
        #container {{
            width: {width};
            height: {height};
            background: #0f0f23;
        }}
        .controls {{
            position: absolute;
            top: 80px;
            right: 20px;
            background: rgba(22, 33, 62, 0.95);
            padding: 15px;
            border-radius: 8px;
            max-width: 250px;
            z-index: 100;
        }}
        .controls h3 {{
            font-size: 0.9em;
            margin-bottom: 10px;
            color: #fff;
        }}
        .search-box {{
            width: 100%;
            padding: 8px;
            border: 1px solid #0f3460;
            border-radius: 4px;
            background: #1a1a2e;
            color: #fff;
            margin-bottom: 12px;
        }}
        .legend {{
            max-height: 300px;
            overflow-y: auto;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            padding: 4px 0;
            font-size: 0.8em;
        }}
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            flex-shrink: 0;
        }}
        .info-panel {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(22, 33, 62, 0.95);
            padding: 15px;
            border-radius: 8px;
            max-width: 300px;
            z-index: 100;
            display: none;
        }}
        .info-panel h3 {{
            font-size: 1em;
            margin-bottom: 8px;
        }}
        .info-panel p {{
            font-size: 0.85em;
            color: #aaa;
            margin: 4px 0;
        }}
        .stats {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: rgba(22, 33, 62, 0.95);
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 0.8em;
            color: #aaa;
            z-index: 100;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>Interactive network visualization - scroll to zoom, drag to pan, click nodes for details</p>
    </div>

    <div id="container"></div>

    <div class="controls">
        <h3>Search</h3>
        <input type="text" class="search-box" id="search" placeholder="Search nodes...">
        <h3>Communities</h3>
        <div class="legend">
            {legend_items}
        </div>
    </div>

    <div class="info-panel" id="info-panel">
        <h3 id="node-label">Node</h3>
        <p id="node-community">Community: -</p>
        <p id="node-degree">Degree: -</p>
        <p id="node-details"></p>
    </div>

    <div class="stats">
        <span id="stats-nodes">0</span> nodes, <span id="stats-edges">0</span> edges
    </div>

    <script>
        // Graph data embedded
        const graphData = {json.dumps(graph_data)};

        // Create graph
        const graph = new graphology.Graph();

        // Add nodes
        graphData.nodes.forEach(node => {{
            graph.addNode(node.id, {{
                label: node.label,
                x: node.x,
                y: node.y,
                size: node.size,
                color: node.color,
                community: node.community,
                communityLabel: node.communityLabel,
            }});
        }});

        // Add edges
        graphData.edges.forEach(edge => {{
            if (!graph.hasEdge(edge.source, edge.target)) {{
                graph.addEdge(edge.source, edge.target, {{
                    weight: edge.weight,
                    color: '#ffffff22',
                }});
            }}
        }});

        // Update stats
        document.getElementById('stats-nodes').textContent = graph.order();
        document.getElementById('stats-edges').textContent = graph.size();

        // Create Sigma instance
        const container = document.getElementById('container');
        const renderer = new Sigma(graph, container, {{
            renderEdgeLabels: false,
            defaultEdgeColor: '#ffffff22',
            labelColor: {{ color: '#ffffff' }},
            labelSize: 12,
            labelWeight: 'normal',
            labelFont: 'sans-serif',
            labelDensity: 0.07,
            labelGridCellSize: 60,
            zIndex: true,
        }});

        // Search functionality
        const searchInput = document.getElementById('search');
        searchInput.addEventListener('input', (e) => {{
            const query = e.target.value.toLowerCase();

            graph.forEachNode((node, attrs) => {{
                const match = attrs.label.toLowerCase().includes(query);
                graph.setNodeAttribute(node, 'hidden', query && !match);
            }});

            renderer.refresh();
        }});

        // Click handler for node info
        const infoPanel = document.getElementById('info-panel');

        renderer.on('clickNode', ({{ node }}) => {{
            const attrs = graph.getNodeAttributes(node);
            document.getElementById('node-label').textContent = '@' + attrs.label;
            document.getElementById('node-community').textContent = 'Community: ' + attrs.communityLabel;
            document.getElementById('node-degree').textContent = 'Connections: ' + graph.degree(node);
            infoPanel.style.display = 'block';
        }});

        renderer.on('clickStage', () => {{
            infoPanel.style.display = 'none';
        }});

        // Hover effects
        renderer.on('enterNode', ({{ node }}) => {{
            graph.setNodeAttribute(node, 'highlighted', true);

            // Highlight neighbors
            graph.forEachNeighbor(node, (neighbor) => {{
                graph.setNodeAttribute(neighbor, 'highlighted', true);
            }});

            renderer.refresh();
        }});

        renderer.on('leaveNode', ({{ node }}) => {{
            graph.forEachNode((n) => {{
                graph.setNodeAttribute(n, 'highlighted', false);
            }});
            renderer.refresh();
        }});
    </script>
</body>
</html>
'''

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  Saved: {output_path.name}")

    return html


# =============================================================================
# GEXF EXPORT (Gephi compatible)
# =============================================================================

def export_gexf(
    G: 'nx.Graph',
    communities: Dict[str, int] = None,
    community_labels: Dict[int, str] = None,
    output_path: Path = None,
) -> None:
    """
    Export network to GEXF format for Gephi.

    Args:
        G: NetworkX graph
        communities: Mapping of node IDs to community indices
        community_labels: Mapping of community indices to labels
        output_path: Path to save GEXF file
    """
    if not HAS_NETWORKX:
        print("  NetworkX required for GEXF export")
        return

    communities = communities or {}
    community_labels = community_labels or {}

    # Add community attributes to nodes
    for node in G.nodes():
        comm_idx = communities.get(node, 0)
        comm_label = community_labels.get(comm_idx, f"Community_{comm_idx}")
        G.nodes[node]['community'] = comm_idx
        G.nodes[node]['community_label'] = comm_label

        # Add color as viz attribute
        if comm_label in KIC_COLORS:
            color = KIC_COLORS[comm_label]
        else:
            color = COMMUNITY_COLORS[comm_idx % len(COMMUNITY_COLORS)]
        G.nodes[node]['viz_color'] = color

    nx.write_gexf(G, output_path)
    print(f"  Saved: {output_path.name}")


# =============================================================================
# MAIN EXPORT FUNCTION
# =============================================================================

def export_network_visualization(
    G: 'nx.Graph',
    output_dir: Path,
    title: str = "Field Network",
    communities: Dict[str, int] = None,
    community_labels: Dict[int, str] = None,
) -> Dict[str, Path]:
    """
    Export network in all visualization formats.

    Args:
        G: NetworkX graph
        output_dir: Directory for output files
        title: Title for visualizations
        communities: Node to community mapping
        community_labels: Community index to label mapping

    Returns:
        Dict mapping format names to output paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {}

    print(f"\nExporting network visualizations to {output_dir}...")

    # 1. Sigma.js JSON
    json_path = output_dir / "network_sigma.json"
    graph_data = network_to_sigma_json(
        G, communities, community_labels, output_path=json_path
    )
    outputs['json'] = json_path

    # 2. Self-contained HTML
    html_path = output_dir / "network_interactive.html"
    generate_sigma_html(graph_data, title, output_path=html_path)
    outputs['html'] = html_path

    # 3. GEXF for Gephi
    gexf_path = output_dir / "network.gexf"
    export_gexf(G, communities, community_labels, output_path=gexf_path)
    outputs['gexf'] = gexf_path

    return outputs


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    print("Sigma.js Network Export")
    print("Usage: from sigma_export import export_network_visualization")
    print()
    print("Or run on existing network data:")
    print("  python sigma_export.py --input network.graphml --output ./viz/")
