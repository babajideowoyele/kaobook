"""
Interactive HTML visualization generator.

Creates self-contained HTML files with Plotly ternary visualizations.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import json

from rolebox_triads.core.triad_config import TriadConfig
from rolebox_triads.core.normalizer import OrganizationTriadPosition, NetworkEdge
from rolebox_triads.visualization.ternary_scatter import TernaryScatterPlot
from rolebox_triads.visualization.ternary_network import TernaryNetworkPlot


class TriadHTMLGenerator:
    """
    Generates interactive HTML visualizations for triad data.

    Features:
    - Sidebar with statistics and filters
    - Multiple view tabs (Overview, Positions, Network, Animation)
    - Organization search
    - Hover tooltips and click info panel
    - Export capabilities
    """

    def __init__(self, config: TriadConfig):
        self.config = config
        self.scatter_plot = TernaryScatterPlot(config)
        self.network_plot = TernaryNetworkPlot(config)

    def generate(
        self,
        positions: List[OrganizationTriadPosition],
        edges: Optional[List[NetworkEdge]] = None,
        output_path: Optional[Path] = None,
        title: Optional[str] = None,
    ) -> str:
        """
        Generate complete HTML visualization.

        Args:
            positions: List of organization positions
            edges: Optional network edges
            output_path: Path to write HTML file
            title: Optional custom title

        Returns:
            HTML string
        """
        title = title or f"Triad Explorer - {self.config.name}"

        # Prepare data
        positions_json = json.dumps([p.to_dict() for p in positions])
        edges_json = json.dumps([e.to_dict() for e in edges]) if edges else "[]"
        config_json = json.dumps(self.config.to_dict())

        # Compute statistics
        stats = self._compute_statistics(positions)
        stats_json = json.dumps(stats)

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
{self._get_css()}
    </style>
</head>
<body>
<div class="app">
    <header class="header">
        <div class="logo">
            <i class="fas fa-triangle"></i>
            <h1>{title}</h1>
        </div>
        <nav class="nav">
            <a class="nav-item active" data-screen="overview">Overview</a>
            <a class="nav-item" data-screen="positions">Positions</a>
            <a class="nav-item" data-screen="network">Network</a>
            <a class="nav-item" data-screen="annotate">Annotate</a>
        </nav>
        <div class="header-actions">
            <button class="btn btn-sm" onclick="exportPNG()">
                <i class="fas fa-download"></i> Export
            </button>
        </div>
    </header>

    <div class="main">
        <aside class="sidebar">
            <div class="card">
                <div class="card-header">
                    <i class="fas fa-chart-pie"></i> Statistics
                </div>
                <div class="card-body" id="stats-panel">
                    <!-- Populated by JS -->
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <i class="fas fa-filter"></i> Filters
                </div>
                <div class="card-body">
                    <div class="form-group">
                        <label>Classification</label>
                        <select id="filter-classification" class="select" onchange="applyFilters()">
                            <option value="all">All</option>
                            <option value="dominant_{self.config.axis_a.key}">{self.config.axis_a.name}</option>
                            <option value="dominant_{self.config.axis_b.key}">{self.config.axis_b.name}</option>
                            <option value="dominant_{self.config.axis_c.key}">{self.config.axis_c.name}</option>
                            <option value="interstitial">Interstitial</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Color By</label>
                        <select id="color-by" class="select" onchange="updateVisualization()">
                            <option value="classification">Classification</option>
                            <option value="confidence">Confidence</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Size By</label>
                        <select id="size-by" class="select" onchange="updateVisualization()">
                            <option value="fixed">Fixed</option>
                            <option value="confidence">Confidence</option>
                            <option value="raw_total">Raw Total</option>
                        </select>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <i class="fas fa-search"></i> Search
                </div>
                <div class="card-body">
                    <input type="text" id="search-input" class="input"
                           placeholder="Search organizations..."
                           oninput="searchOrganizations(this.value)">
                    <div id="search-results" class="search-results"></div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <i class="fas fa-palette"></i> Legend
                </div>
                <div class="card-body" id="legend-panel">
                    <!-- Populated by JS -->
                </div>
            </div>
        </aside>

        <main class="content">
            <div id="screen-overview" class="screen active">
                <div class="grid-2">
                    <div class="card">
                        <div class="card-header">Distribution Overview</div>
                        <div class="card-body">
                            <div id="overview-chart" style="height: 300px;"></div>
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-header">Key Metrics</div>
                        <div class="card-body" id="key-metrics">
                            <!-- Populated by JS -->
                        </div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">Triad Visualization</div>
                    <div class="card-body">
                        <div id="overview-ternary" style="height: 500px;"></div>
                    </div>
                </div>
            </div>

            <div id="screen-positions" class="screen">
                <div class="card">
                    <div class="card-header">
                        Position Analysis
                        <span class="tag" id="position-count">0 organizations</span>
                    </div>
                    <div class="card-body">
                        <div id="positions-ternary" style="height: 600px;"></div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">Top Organizations by Pole</div>
                    <div class="card-body">
                        <div class="grid-3" id="top-by-pole">
                            <!-- Populated by JS -->
                        </div>
                    </div>
                </div>
            </div>

            <div id="screen-network" class="screen">
                <div class="card">
                    <div class="card-header">
                        Network View
                        <div class="header-controls">
                            <label class="checkbox-label">
                                <input type="checkbox" id="show-edges" checked onchange="toggleEdges()">
                                Show Edges
                            </label>
                            <label>
                                Edge Opacity:
                                <input type="range" id="edge-opacity" min="0" max="100" value="30"
                                       oninput="updateEdgeOpacity(this.value)">
                            </label>
                        </div>
                    </div>
                    <div class="card-body">
                        <div id="network-ternary" style="height: 600px;"></div>
                    </div>
                </div>
            </div>

            <div id="screen-annotate" class="screen">
                <div class="grid-annotate">
                    <div class="card annotate-list-card">
                        <div class="card-header">
                            <i class="fas fa-list"></i> Queue
                            <span class="tag" id="annotate-progress">0/0</span>
                        </div>
                        <div class="card-body">
                            <div class="annotate-controls">
                                <select id="annotate-filter" class="select" onchange="filterAnnotateQueue()">
                                    <option value="all">All</option>
                                    <option value="pending">Pending</option>
                                    <option value="annotated">Annotated</option>
                                </select>
                                <button class="btn btn-sm" onclick="randomNext()">
                                    <i class="fas fa-random"></i> Random
                                </button>
                            </div>
                            <div id="annotate-queue" class="annotate-queue"></div>
                        </div>
                    </div>
                    <div class="annotate-main">
                        <div class="card">
                            <div class="card-header">
                                <i class="fas fa-edit"></i> Annotation
                                <div class="header-controls">
                                    <button class="btn btn-sm" onclick="prevAnnotation()">
                                        <i class="fas fa-chevron-left"></i>
                                    </button>
                                    <span id="annotate-index">1 of 100</span>
                                    <button class="btn btn-sm" onclick="nextAnnotation()">
                                        <i class="fas fa-chevron-right"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="card-body">
                                <div id="annotate-current" class="annotate-current">
                                    <p class="text-gray text-center">Select an organization to annotate</p>
                                </div>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-header">Triad Position</div>
                            <div class="card-body">
                                <div id="annotate-ternary" style="height: 400px;"></div>
                            </div>
                        </div>
                    </div>
                    <div class="card annotate-form-card">
                        <div class="card-header">
                            <i class="fas fa-check-circle"></i> Validate & Correct
                        </div>
                        <div class="card-body" id="annotate-form">
                            <div class="form-group">
                                <label>Computed Classification</label>
                                <div id="computed-classification" class="computed-value">-</div>
                            </div>
                            <div class="form-group">
                                <label>Validation</label>
                                <div class="btn-group">
                                    <button class="btn btn-validate" data-valid="true" onclick="setValidation(true)">
                                        <i class="fas fa-check"></i> Correct
                                    </button>
                                    <button class="btn btn-validate" data-valid="false" onclick="setValidation(false)">
                                        <i class="fas fa-times"></i> Incorrect
                                    </button>
                                </div>
                            </div>
                            <div id="correction-panel" class="correction-panel hidden">
                                <div class="form-group">
                                    <label>Corrected Classification</label>
                                    <select id="corrected-classification" class="select">
                                        <option value="">-- Select --</option>
                                        <option value="dominant_{self.config.axis_a.key}">{self.config.axis_a.name}</option>
                                        <option value="dominant_{self.config.axis_b.key}">{self.config.axis_b.name}</option>
                                        <option value="dominant_{self.config.axis_c.key}">{self.config.axis_c.name}</option>
                                        <option value="interstitial">Interstitial</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>{self.config.axis_a.name} (0-1)</label>
                                    <input type="range" id="corrected-a" min="0" max="100" value="33"
                                           oninput="updateCorrectedCoords()">
                                    <span id="corrected-a-val">0.33</span>
                                </div>
                                <div class="form-group">
                                    <label>{self.config.axis_b.name} (0-1)</label>
                                    <input type="range" id="corrected-b" min="0" max="100" value="33"
                                           oninput="updateCorrectedCoords()">
                                    <span id="corrected-b-val">0.33</span>
                                </div>
                                <div class="form-group">
                                    <label>{self.config.axis_c.name} (0-1)</label>
                                    <input type="range" id="corrected-c" min="0" max="100" value="33"
                                           oninput="updateCorrectedCoords()">
                                    <span id="corrected-c-val">0.33</span>
                                </div>
                                <div class="form-group">
                                    <label>Reason for Adjustment</label>
                                    <select id="adjustment-reason" class="select">
                                        <option value="">-- Select --</option>
                                        <option value="misclassified">Misclassified by algorithm</option>
                                        <option value="ambiguous">Ambiguous text content</option>
                                        <option value="hybrid">Genuinely hybrid organization</option>
                                        <option value="context">Domain knowledge correction</option>
                                        <option value="other">Other</option>
                                    </select>
                                </div>
                            </div>
                            <div class="form-group">
                                <label>Confidence</label>
                                <div class="btn-group btn-group-3">
                                    <button class="btn btn-conf" data-conf="high" onclick="setConfidence('high')">High</button>
                                    <button class="btn btn-conf active" data-conf="medium" onclick="setConfidence('medium')">Medium</button>
                                    <button class="btn btn-conf" data-conf="low" onclick="setConfidence('low')">Low</button>
                                </div>
                            </div>
                            <div class="form-group">
                                <label>Notes</label>
                                <textarea id="annotation-notes" class="textarea" placeholder="Optional notes..."></textarea>
                            </div>
                            <div class="form-actions">
                                <button class="btn" onclick="skipAnnotation()">
                                    <i class="fas fa-forward"></i> Skip
                                </button>
                                <button class="btn btn-primary" onclick="saveAnnotation()">
                                    <i class="fas fa-save"></i> Save & Next
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="annotate-footer">
                    <div class="progress-bar">
                        <div class="progress-fill" id="annotate-progress-bar" style="width: 0%"></div>
                    </div>
                    <div class="annotate-stats">
                        <span><strong id="stat-annotated">0</strong> annotated</span>
                        <span><strong id="stat-validated">0</strong> validated correct</span>
                        <span><strong id="stat-corrected">0</strong> corrected</span>
                        <button class="btn btn-sm" onclick="exportAnnotations()">
                            <i class="fas fa-download"></i> Export Annotations
                        </button>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <!-- Info Panel (overlay) -->
    <div id="info-panel" class="info-panel hidden">
        <div class="info-panel-header">
            <span id="info-panel-title">Organization</span>
            <button class="btn btn-sm" onclick="closeInfoPanel()">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="info-panel-body" id="info-panel-body">
            <!-- Populated by JS -->
        </div>
    </div>

    <!-- Toast notification -->
    <div id="toast" class="toast"></div>
</div>

<script>
// Data
const TRIAD_CONFIG = {config_json};
const POSITIONS = {positions_json};
const EDGES = {edges_json};
const STATS = {stats_json};

// State
const state = {{
    screen: 'overview',
    filteredPositions: POSITIONS,
    selectedOrg: null,
    showEdges: true,
    edgeOpacity: 0.3
}};

// Initialize
document.addEventListener('DOMContentLoaded', () => {{
    renderStats();
    renderLegend();
    renderOverview();
    setupNavigation();
}});

function setupNavigation() {{
    document.querySelectorAll('.nav-item').forEach(item => {{
        item.addEventListener('click', () => {{
            const screen = item.dataset.screen;
            showScreen(screen);
        }});
    }});
}}

function showScreen(screenId) {{
    state.screen = screenId;

    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {{
        item.classList.toggle('active', item.dataset.screen === screenId);
    }});

    // Update screens
    document.querySelectorAll('.screen').forEach(screen => {{
        screen.classList.toggle('active', screen.id === 'screen-' + screenId);
    }});

    // Render screen content
    if (screenId === 'overview') renderOverview();
    else if (screenId === 'positions') renderPositions();
    else if (screenId === 'network') renderNetwork();
    else if (screenId === 'annotate') renderAnnotate();
}}

function renderStats() {{
    const panel = document.getElementById('stats-panel');
    panel.innerHTML = `
        <div class="stat-row">
            <span class="stat-label">Total Organizations</span>
            <span class="stat-value">${{STATS.total}}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">${{TRIAD_CONFIG.axis_a.name}}</span>
            <span class="stat-value">${{STATS.by_classification['dominant_' + TRIAD_CONFIG.axis_a.key] || 0}}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">${{TRIAD_CONFIG.axis_b.name}}</span>
            <span class="stat-value">${{STATS.by_classification['dominant_' + TRIAD_CONFIG.axis_b.key] || 0}}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">${{TRIAD_CONFIG.axis_c.name}}</span>
            <span class="stat-value">${{STATS.by_classification['dominant_' + TRIAD_CONFIG.axis_c.key] || 0}}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Interstitial</span>
            <span class="stat-value">${{STATS.by_classification.interstitial || 0}}</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">Avg Confidence</span>
            <span class="stat-value">${{(STATS.avg_confidence * 100).toFixed(1)}}%</span>
        </div>
    `;
}}

function renderLegend() {{
    const panel = document.getElementById('legend-panel');
    const items = [
        {{ name: TRIAD_CONFIG.axis_a.name, color: TRIAD_CONFIG.axis_a.color, key: 'dominant_' + TRIAD_CONFIG.axis_a.key }},
        {{ name: TRIAD_CONFIG.axis_b.name, color: TRIAD_CONFIG.axis_b.color, key: 'dominant_' + TRIAD_CONFIG.axis_b.key }},
        {{ name: TRIAD_CONFIG.axis_c.name, color: TRIAD_CONFIG.axis_c.color, key: 'dominant_' + TRIAD_CONFIG.axis_c.key }},
        {{ name: 'Interstitial', color: TRIAD_CONFIG.color_palette.interstitial || '#f1c40f', key: 'interstitial' }}
    ];

    panel.innerHTML = items.map(item => `
        <div class="legend-item">
            <span class="legend-color" style="background: ${{item.color}}"></span>
            <span class="legend-label">${{item.name}}</span>
        </div>
    `).join('');
}}

function renderOverview() {{
    // Render pie chart
    const pieData = [{{
        type: 'pie',
        values: [
            STATS.by_classification['dominant_' + TRIAD_CONFIG.axis_a.key] || 0,
            STATS.by_classification['dominant_' + TRIAD_CONFIG.axis_b.key] || 0,
            STATS.by_classification['dominant_' + TRIAD_CONFIG.axis_c.key] || 0,
            STATS.by_classification.interstitial || 0
        ],
        labels: [TRIAD_CONFIG.axis_a.name, TRIAD_CONFIG.axis_b.name, TRIAD_CONFIG.axis_c.name, 'Interstitial'],
        marker: {{
            colors: [TRIAD_CONFIG.axis_a.color, TRIAD_CONFIG.axis_b.color, TRIAD_CONFIG.axis_c.color, '#f1c40f']
        }},
        hole: 0.4,
        textinfo: 'label+percent'
    }}];

    Plotly.newPlot('overview-chart', pieData, {{
        margin: {{ t: 20, b: 20, l: 20, r: 20 }},
        showlegend: false,
        font: {{ family: 'Inter, sans-serif' }}
    }}, {{ responsive: true }});

    // Render key metrics
    document.getElementById('key-metrics').innerHTML = `
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-value">${{STATS.centroid.a.toFixed(2)}}</div>
                <div class="metric-label">Centroid ${{TRIAD_CONFIG.axis_a.name}}</div>
            </div>
            <div class="metric">
                <div class="metric-value">${{STATS.centroid.b.toFixed(2)}}</div>
                <div class="metric-label">Centroid ${{TRIAD_CONFIG.axis_b.name}}</div>
            </div>
            <div class="metric">
                <div class="metric-value">${{STATS.centroid.c.toFixed(2)}}</div>
                <div class="metric-label">Centroid ${{TRIAD_CONFIG.axis_c.name}}</div>
            </div>
            <div class="metric">
                <div class="metric-value">${{STATS.dispersion.toFixed(3)}}</div>
                <div class="metric-label">Dispersion</div>
            </div>
        </div>
    `;

    // Render ternary
    renderTernary('overview-ternary', state.filteredPositions);
}}

function renderPositions() {{
    document.getElementById('position-count').textContent = `${{state.filteredPositions.length}} organizations`;
    renderTernary('positions-ternary', state.filteredPositions);
    renderTopByPole();
}}

function renderNetwork() {{
    if (EDGES.length === 0) {{
        document.getElementById('network-ternary').innerHTML = '<p class="text-gray text-center">No network edges available.</p>';
        return;
    }}
    renderTernaryWithEdges('network-ternary', state.filteredPositions, EDGES);
}}

function renderAnimation() {{
    // Check if time series data exists
    const hasTimeSeries = POSITIONS.some(p => p.time_series && p.time_series.length > 0);
    if (!hasTimeSeries) {{
        document.getElementById('animation-ternary').innerHTML = '<p class="text-gray text-center">No time-series data available.</p>';
    }}
}}

function renderTernary(containerId, positions) {{
    const colorBy = document.getElementById('color-by').value;
    const sizeBy = document.getElementById('size-by').value;

    // Group by classification
    const groups = {{}};
    positions.forEach(p => {{
        const cls = p.classification;
        if (!groups[cls]) groups[cls] = [];
        groups[cls].push(p);
    }});

    const traces = Object.entries(groups).map(([cls, grpPositions]) => ({{
        type: 'scatterternary',
        mode: 'markers',
        name: cls.replace('dominant_', '').replace('_', ' '),
        a: grpPositions.map(p => p.coordinates.a),
        b: grpPositions.map(p => p.coordinates.b),
        c: grpPositions.map(p => p.coordinates.c),
        text: grpPositions.map(p => p.org_name),
        customdata: grpPositions,
        hovertemplate: '<b>%{{text}}</b><br>' +
            `${{TRIAD_CONFIG.axis_a.name}}: %{{a:.2f}}<br>` +
            `${{TRIAD_CONFIG.axis_b.name}}: %{{b:.2f}}<br>` +
            `${{TRIAD_CONFIG.axis_c.name}}: %{{c:.2f}}<extra></extra>`,
        marker: {{
            size: sizeBy === 'fixed' ? 10 : grpPositions.map(p => 6 + p.confidence * 14),
            color: TRIAD_CONFIG.color_palette[cls] || '#999',
            opacity: 0.8,
            line: {{ color: 'white', width: 1 }}
        }}
    }}));

    const layout = {{
        ternary: {{
            sum: 1,
            aaxis: {{ title: {{ text: TRIAD_CONFIG.axis_a.name }}, min: 0, linecolor: TRIAD_CONFIG.axis_a.color }},
            baxis: {{ title: {{ text: TRIAD_CONFIG.axis_b.name }}, min: 0, linecolor: TRIAD_CONFIG.axis_b.color }},
            caxis: {{ title: {{ text: TRIAD_CONFIG.axis_c.name }}, min: 0, linecolor: TRIAD_CONFIG.axis_c.color }},
            bgcolor: '#fafafa'
        }},
        showlegend: true,
        legend: {{ x: 1.02, y: 0.5 }},
        margin: {{ l: 50, r: 120, t: 50, b: 50 }},
        font: {{ family: 'Inter, sans-serif' }},
        paper_bgcolor: 'white'
    }};

    Plotly.newPlot(containerId, traces, layout, {{ responsive: true }});

    // Add click handler
    document.getElementById(containerId).on('plotly_click', data => {{
        if (data.points.length > 0) {{
            const point = data.points[0];
            showInfoPanel(point.customdata);
        }}
    }});
}}

function renderTernaryWithEdges(containerId, positions, edges) {{
    // Create position lookup
    const posLookup = {{}};
    positions.forEach(p => posLookup[p.org_id] = p);

    // Create edge traces
    const edgeA = [], edgeB = [], edgeC = [];
    edges.forEach(e => {{
        const src = posLookup[e.source_id];
        const tgt = posLookup[e.target_id];
        if (src && tgt) {{
            edgeA.push(src.coordinates.a, tgt.coordinates.a, null);
            edgeB.push(src.coordinates.b, tgt.coordinates.b, null);
            edgeC.push(src.coordinates.c, tgt.coordinates.c, null);
        }}
    }});

    const edgeTrace = {{
        type: 'scatterternary',
        mode: 'lines',
        a: edgeA,
        b: edgeB,
        c: edgeC,
        line: {{ color: '#999', width: 0.5 }},
        opacity: state.showEdges ? state.edgeOpacity : 0,
        hoverinfo: 'skip',
        showlegend: false
    }};

    // Node traces
    const groups = {{}};
    positions.forEach(p => {{
        const cls = p.classification;
        if (!groups[cls]) groups[cls] = [];
        groups[cls].push(p);
    }});

    const nodeTraces = Object.entries(groups).map(([cls, grpPositions]) => ({{
        type: 'scatterternary',
        mode: 'markers',
        name: cls.replace('dominant_', '').replace('_', ' '),
        a: grpPositions.map(p => p.coordinates.a),
        b: grpPositions.map(p => p.coordinates.b),
        c: grpPositions.map(p => p.coordinates.c),
        text: grpPositions.map(p => p.org_name),
        customdata: grpPositions,
        hovertemplate: '<b>%{{text}}</b><extra></extra>',
        marker: {{
            size: 10,
            color: TRIAD_CONFIG.color_palette[cls] || '#999',
            opacity: 0.9,
            line: {{ color: 'white', width: 1 }}
        }}
    }}));

    const layout = {{
        ternary: {{
            sum: 1,
            aaxis: {{ title: {{ text: TRIAD_CONFIG.axis_a.name }}, min: 0 }},
            baxis: {{ title: {{ text: TRIAD_CONFIG.axis_b.name }}, min: 0 }},
            caxis: {{ title: {{ text: TRIAD_CONFIG.axis_c.name }}, min: 0 }},
            bgcolor: '#fafafa'
        }},
        showlegend: true,
        margin: {{ l: 50, r: 120, t: 50, b: 50 }},
        font: {{ family: 'Inter, sans-serif' }}
    }};

    Plotly.newPlot(containerId, [edgeTrace, ...nodeTraces], layout, {{ responsive: true }});
}}

function renderTopByPole() {{
    const container = document.getElementById('top-by-pole');
    const poles = [
        {{ key: 'dominant_' + TRIAD_CONFIG.axis_a.key, name: TRIAD_CONFIG.axis_a.name, color: TRIAD_CONFIG.axis_a.color }},
        {{ key: 'dominant_' + TRIAD_CONFIG.axis_b.key, name: TRIAD_CONFIG.axis_b.name, color: TRIAD_CONFIG.axis_b.color }},
        {{ key: 'dominant_' + TRIAD_CONFIG.axis_c.key, name: TRIAD_CONFIG.axis_c.name, color: TRIAD_CONFIG.axis_c.color }}
    ];

    container.innerHTML = poles.map(pole => {{
        const polePositions = state.filteredPositions
            .filter(p => p.classification === pole.key)
            .sort((a, b) => b.confidence - a.confidence)
            .slice(0, 5);

        return `
            <div class="pole-list">
                <h4 style="color: ${{pole.color}}">${{pole.name}}</h4>
                <ul>
                    ${{polePositions.map(p => `<li>${{p.org_name}} <span class="text-gray">${{(p.confidence * 100).toFixed(0)}}%</span></li>`).join('')}}
                </ul>
            </div>
        `;
    }}).join('');
}}

function applyFilters() {{
    const classification = document.getElementById('filter-classification').value;

    if (classification === 'all') {{
        state.filteredPositions = POSITIONS;
    }} else {{
        state.filteredPositions = POSITIONS.filter(p => p.classification === classification);
    }}

    updateVisualization();
}}

function updateVisualization() {{
    if (state.screen === 'overview') renderOverview();
    else if (state.screen === 'positions') renderPositions();
    else if (state.screen === 'network') renderNetwork();
}}

function searchOrganizations(query) {{
    const results = document.getElementById('search-results');
    if (!query || query.length < 2) {{
        results.innerHTML = '';
        return;
    }}

    const matches = POSITIONS
        .filter(p => p.org_name.toLowerCase().includes(query.toLowerCase()))
        .slice(0, 10);

    results.innerHTML = matches.map(p => `
        <div class="search-result" onclick="highlightOrg('${{p.org_id}}')">
            ${{p.org_name}}
            <span class="tag" style="background: ${{TRIAD_CONFIG.color_palette[p.classification] || '#999'}}; color: white;">
                ${{p.classification.replace('dominant_', '')}}
            </span>
        </div>
    `).join('');
}}

function highlightOrg(orgId) {{
    const pos = POSITIONS.find(p => p.org_id === orgId);
    if (pos) {{
        showInfoPanel(pos);
        toast(`Selected: ${{pos.org_name}}`);
    }}
}}

function showInfoPanel(position) {{
    state.selectedOrg = position;
    const panel = document.getElementById('info-panel');
    document.getElementById('info-panel-title').textContent = position.org_name;

    document.getElementById('info-panel-body').innerHTML = `
        <div class="info-section">
            <h4>Classification</h4>
            <span class="tag" style="background: ${{TRIAD_CONFIG.color_palette[position.classification] || '#999'}}; color: white;">
                ${{position.classification.replace('dominant_', '').replace('_', ' ')}}
            </span>
        </div>
        <div class="info-section">
            <h4>Coordinates</h4>
            <div class="coord-bar">
                <span>${{TRIAD_CONFIG.axis_a.name}}</span>
                <div class="bar"><div class="bar-fill" style="width: ${{position.coordinates.a * 100}}%; background: ${{TRIAD_CONFIG.axis_a.color}}"></div></div>
                <span>${{position.coordinates.a.toFixed(2)}}</span>
            </div>
            <div class="coord-bar">
                <span>${{TRIAD_CONFIG.axis_b.name}}</span>
                <div class="bar"><div class="bar-fill" style="width: ${{position.coordinates.b * 100}}%; background: ${{TRIAD_CONFIG.axis_b.color}}"></div></div>
                <span>${{position.coordinates.b.toFixed(2)}}</span>
            </div>
            <div class="coord-bar">
                <span>${{TRIAD_CONFIG.axis_c.name}}</span>
                <div class="bar"><div class="bar-fill" style="width: ${{position.coordinates.c * 100}}%; background: ${{TRIAD_CONFIG.axis_c.color}}"></div></div>
                <span>${{position.coordinates.c.toFixed(2)}}</span>
            </div>
        </div>
        <div class="info-section">
            <h4>Confidence</h4>
            <div class="confidence-meter">
                <div class="meter-fill" style="width: ${{position.confidence * 100}}%"></div>
            </div>
            <span class="text-sm text-gray">${{(position.confidence * 100).toFixed(1)}}%</span>
        </div>
        ${{position.kic_sectors.length > 0 ? `
        <div class="info-section">
            <h4>KIC Sectors</h4>
            <div class="tags">
                ${{position.kic_sectors.map(s => `<span class="tag tag-outline">${{s}}</span>`).join('')}}
            </div>
        </div>` : ''}}
    `;

    panel.classList.remove('hidden');
}}

function closeInfoPanel() {{
    document.getElementById('info-panel').classList.add('hidden');
    state.selectedOrg = null;
}}

function toggleEdges() {{
    state.showEdges = document.getElementById('show-edges').checked;
    renderNetwork();
}}

function updateEdgeOpacity(value) {{
    state.edgeOpacity = value / 100;
    renderNetwork();
}}

function exportPNG() {{
    const containerId = state.screen === 'network' ? 'network-ternary' :
                       state.screen === 'positions' ? 'positions-ternary' : 'overview-ternary';
    Plotly.downloadImage(containerId, {{
        format: 'png',
        width: 1200,
        height: 800,
        filename: 'triad-visualization'
    }});
    toast('Image exported!');
}}

function toast(message) {{
    const t = document.getElementById('toast');
    t.textContent = message;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2500);
}}

// ============================================================================
// ANNOTATION FUNCTIONS
// ============================================================================

// Annotation state
const annotationState = {{
    currentIndex: 0,
    annotations: {{}},  // org_id -> annotation
    validated: null,
    confidence: 'medium',
    filteredQueue: []
}};

// Load annotations from localStorage
function loadAnnotations() {{
    const saved = localStorage.getItem('triad_annotations_' + TRIAD_CONFIG.triad_type);
    if (saved) {{
        annotationState.annotations = JSON.parse(saved);
    }}
}}

// Save annotations to localStorage
function saveAnnotationsToStorage() {{
    localStorage.setItem('triad_annotations_' + TRIAD_CONFIG.triad_type,
                        JSON.stringify(annotationState.annotations));
}}

function renderAnnotate() {{
    loadAnnotations();
    filterAnnotateQueue();
    updateAnnotateStats();
    if (annotationState.filteredQueue.length > 0) {{
        selectForAnnotation(annotationState.filteredQueue[0].org_id);
    }}
}}

function filterAnnotateQueue() {{
    const filter = document.getElementById('annotate-filter').value;

    if (filter === 'all') {{
        annotationState.filteredQueue = [...POSITIONS];
    }} else if (filter === 'pending') {{
        annotationState.filteredQueue = POSITIONS.filter(p => !annotationState.annotations[p.org_id]);
    }} else {{
        annotationState.filteredQueue = POSITIONS.filter(p => annotationState.annotations[p.org_id]);
    }}

    renderAnnotateQueue();
    updateAnnotateProgress();
}}

function renderAnnotateQueue() {{
    const container = document.getElementById('annotate-queue');
    const queue = annotationState.filteredQueue;

    container.innerHTML = queue.slice(0, 50).map((p, idx) => {{
        const isAnnotated = !!annotationState.annotations[p.org_id];
        const isCurrent = annotationState.currentIndex === POSITIONS.indexOf(p);
        return `
            <div class="queue-item ${{isCurrent ? 'active' : ''}} ${{isAnnotated ? 'annotated' : ''}}"
                 onclick="selectForAnnotation('${{p.org_id}}')">
                <span class="queue-name">${{p.org_name}}</span>
                <span class="queue-status">
                    ${{isAnnotated ? '<i class="fas fa-check text-success"></i>' : '<i class="fas fa-circle text-gray"></i>'}}
                </span>
            </div>
        `;
    }}).join('');

    if (queue.length > 50) {{
        container.innerHTML += `<div class="queue-more">+ ${{queue.length - 50}} more...</div>`;
    }}
}}

function selectForAnnotation(orgId) {{
    const pos = POSITIONS.find(p => p.org_id === orgId);
    if (!pos) return;

    annotationState.currentIndex = POSITIONS.indexOf(pos);
    annotationState.validated = null;
    annotationState.confidence = 'medium';

    // Update current display
    const container = document.getElementById('annotate-current');
    container.innerHTML = `
        <h3>${{pos.org_name}}</h3>
        <div class="annotate-coords">
            <div class="coord-display">
                <span class="coord-label">${{TRIAD_CONFIG.axis_a.name}}</span>
                <span class="coord-value" style="color: ${{TRIAD_CONFIG.axis_a.color}}">${{pos.coordinates.a.toFixed(3)}}</span>
            </div>
            <div class="coord-display">
                <span class="coord-label">${{TRIAD_CONFIG.axis_b.name}}</span>
                <span class="coord-value" style="color: ${{TRIAD_CONFIG.axis_b.color}}">${{pos.coordinates.b.toFixed(3)}}</span>
            </div>
            <div class="coord-display">
                <span class="coord-label">${{TRIAD_CONFIG.axis_c.name}}</span>
                <span class="coord-value" style="color: ${{TRIAD_CONFIG.axis_c.color}}">${{pos.coordinates.c.toFixed(3)}}</span>
            </div>
        </div>
        <div class="annotate-meta">
            <span class="tag" style="background: ${{TRIAD_CONFIG.color_palette[pos.classification] || '#999'}}; color: white;">
                ${{pos.classification.replace('dominant_', '').replace('_', ' ')}}
            </span>
            <span class="text-gray">Confidence: ${{(pos.confidence * 100).toFixed(0)}}%</span>
        </div>
    `;

    // Update computed classification display
    document.getElementById('computed-classification').innerHTML = `
        <span class="tag" style="background: ${{TRIAD_CONFIG.color_palette[pos.classification] || '#999'}}; color: white;">
            ${{pos.classification.replace('dominant_', '').replace('_', ' ')}}
        </span>
    `;

    // Update index display
    document.getElementById('annotate-index').textContent = `${{annotationState.currentIndex + 1}} of ${{POSITIONS.length}}`;

    // Reset form
    document.querySelectorAll('.btn-validate').forEach(b => b.classList.remove('active'));
    document.getElementById('correction-panel').classList.add('hidden');
    document.querySelectorAll('.btn-conf').forEach(b => {{
        b.classList.toggle('active', b.dataset.conf === 'medium');
    }});
    document.getElementById('annotation-notes').value = '';

    // Load existing annotation if any
    const existing = annotationState.annotations[pos.org_id];
    if (existing) {{
        annotationState.validated = existing.validated;
        annotationState.confidence = existing.confidence;
        document.querySelectorAll('.btn-validate').forEach(b => {{
            b.classList.toggle('active', b.dataset.valid === String(existing.validated));
        }});
        document.querySelectorAll('.btn-conf').forEach(b => {{
            b.classList.toggle('active', b.dataset.conf === existing.confidence);
        }});
        document.getElementById('annotation-notes').value = existing.notes || '';
        if (!existing.validated) {{
            document.getElementById('correction-panel').classList.remove('hidden');
            if (existing.corrected_classification) {{
                document.getElementById('corrected-classification').value = existing.corrected_classification;
            }}
        }}
    }}

    // Render ternary with highlight
    renderAnnotateTernary(pos);
    renderAnnotateQueue();
}}

function renderAnnotateTernary(highlightPos) {{
    // All positions in gray
    const otherPositions = POSITIONS.filter(p => p.org_id !== highlightPos.org_id);

    const traces = [
        {{
            type: 'scatterternary',
            mode: 'markers',
            name: 'Others',
            a: otherPositions.map(p => p.coordinates.a),
            b: otherPositions.map(p => p.coordinates.b),
            c: otherPositions.map(p => p.coordinates.c),
            text: otherPositions.map(p => p.org_name),
            hovertemplate: '<b>%{{text}}</b><extra></extra>',
            marker: {{ size: 8, color: '#ddd', opacity: 0.5 }}
        }},
        {{
            type: 'scatterternary',
            mode: 'markers',
            name: highlightPos.org_name,
            a: [highlightPos.coordinates.a],
            b: [highlightPos.coordinates.b],
            c: [highlightPos.coordinates.c],
            text: [highlightPos.org_name],
            hovertemplate: '<b>%{{text}}</b><extra></extra>',
            marker: {{
                size: 16,
                color: TRIAD_CONFIG.color_palette[highlightPos.classification] || '#e74c3c',
                line: {{ color: '#000', width: 2 }},
                symbol: 'star'
            }}
        }}
    ];

    const layout = {{
        ternary: {{
            sum: 1,
            aaxis: {{ title: {{ text: TRIAD_CONFIG.axis_a.name }}, min: 0, linecolor: TRIAD_CONFIG.axis_a.color }},
            baxis: {{ title: {{ text: TRIAD_CONFIG.axis_b.name }}, min: 0, linecolor: TRIAD_CONFIG.axis_b.color }},
            caxis: {{ title: {{ text: TRIAD_CONFIG.axis_c.name }}, min: 0, linecolor: TRIAD_CONFIG.axis_c.color }},
            bgcolor: '#fafafa'
        }},
        showlegend: false,
        margin: {{ l: 50, r: 50, t: 30, b: 30 }},
        font: {{ family: 'Inter, sans-serif' }}
    }};

    Plotly.newPlot('annotate-ternary', traces, layout, {{ responsive: true }});
}}

function setValidation(isValid) {{
    annotationState.validated = isValid;
    document.querySelectorAll('.btn-validate').forEach(b => {{
        b.classList.toggle('active', b.dataset.valid === String(isValid));
    }});

    // Show/hide correction panel
    if (isValid) {{
        document.getElementById('correction-panel').classList.add('hidden');
    }} else {{
        document.getElementById('correction-panel').classList.remove('hidden');
    }}
}}

function setConfidence(level) {{
    annotationState.confidence = level;
    document.querySelectorAll('.btn-conf').forEach(b => {{
        b.classList.toggle('active', b.dataset.conf === level);
    }});
}}

function updateCorrectedCoords() {{
    const a = document.getElementById('corrected-a').value / 100;
    const b = document.getElementById('corrected-b').value / 100;
    const c = document.getElementById('corrected-c').value / 100;
    const total = a + b + c;

    // Normalize
    const normA = a / total;
    const normB = b / total;
    const normC = c / total;

    document.getElementById('corrected-a-val').textContent = normA.toFixed(2);
    document.getElementById('corrected-b-val').textContent = normB.toFixed(2);
    document.getElementById('corrected-c-val').textContent = normC.toFixed(2);
}}

function saveAnnotation() {{
    if (annotationState.validated === null) {{
        toast('Please validate the classification first');
        return;
    }}

    const pos = POSITIONS[annotationState.currentIndex];

    const annotation = {{
        org_id: pos.org_id,
        org_name: pos.org_name,
        original_classification: pos.classification,
        original_coords: pos.coordinates,
        validated: annotationState.validated,
        confidence: annotationState.confidence,
        notes: document.getElementById('annotation-notes').value,
        annotated_at: new Date().toISOString()
    }};

    if (!annotationState.validated) {{
        annotation.corrected_classification = document.getElementById('corrected-classification').value;
        const a = document.getElementById('corrected-a').value / 100;
        const b = document.getElementById('corrected-b').value / 100;
        const c = document.getElementById('corrected-c').value / 100;
        const total = a + b + c;
        annotation.corrected_coords = {{
            a: a / total,
            b: b / total,
            c: c / total
        }};
        annotation.adjustment_reason = document.getElementById('adjustment-reason').value;
    }}

    annotationState.annotations[pos.org_id] = annotation;
    saveAnnotationsToStorage();

    toast(`Saved annotation for ${{pos.org_name}}`);
    updateAnnotateStats();
    nextAnnotation();
}}

function skipAnnotation() {{
    nextAnnotation();
}}

function nextAnnotation() {{
    // Find next unannotated
    const pending = POSITIONS.filter(p => !annotationState.annotations[p.org_id]);
    if (pending.length > 0) {{
        selectForAnnotation(pending[0].org_id);
    }} else if (annotationState.currentIndex < POSITIONS.length - 1) {{
        selectForAnnotation(POSITIONS[annotationState.currentIndex + 1].org_id);
    }} else {{
        toast('All items annotated!');
    }}
    filterAnnotateQueue();
}}

function prevAnnotation() {{
    if (annotationState.currentIndex > 0) {{
        selectForAnnotation(POSITIONS[annotationState.currentIndex - 1].org_id);
    }}
}}

function randomNext() {{
    const pending = POSITIONS.filter(p => !annotationState.annotations[p.org_id]);
    if (pending.length > 0) {{
        const randomIdx = Math.floor(Math.random() * pending.length);
        selectForAnnotation(pending[randomIdx].org_id);
    }} else {{
        toast('All items annotated!');
    }}
}}

function updateAnnotateProgress() {{
    const total = POSITIONS.length;
    const annotated = Object.keys(annotationState.annotations).length;
    const pct = (annotated / total * 100).toFixed(0);

    document.getElementById('annotate-progress').textContent = `${{annotated}}/${{total}}`;
    document.getElementById('annotate-progress-bar').style.width = pct + '%';
}}

function updateAnnotateStats() {{
    const annotations = Object.values(annotationState.annotations);
    const annotated = annotations.length;
    const validated = annotations.filter(a => a.validated).length;
    const corrected = annotations.filter(a => !a.validated).length;

    document.getElementById('stat-annotated').textContent = annotated;
    document.getElementById('stat-validated').textContent = validated;
    document.getElementById('stat-corrected').textContent = corrected;

    updateAnnotateProgress();
}}

function exportAnnotations() {{
    const annotations = Object.values(annotationState.annotations);
    if (annotations.length === 0) {{
        toast('No annotations to export');
        return;
    }}

    const data = {{
        triad_type: TRIAD_CONFIG.triad_type,
        triad_name: TRIAD_CONFIG.name,
        exported_at: new Date().toISOString(),
        total_positions: POSITIONS.length,
        annotations: annotations
    }};

    const blob = new Blob([JSON.stringify(data, null, 2)], {{ type: 'application/json' }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `triad_annotations_${{TRIAD_CONFIG.triad_type}}_${{new Date().toISOString().split('T')[0]}}.json`;
    a.click();
    URL.revokeObjectURL(url);

    toast(`Exported ${{annotations.length}} annotations`);
}}
</script>
</body>
</html>'''

        if output_path:
            Path(output_path).write_text(html, encoding="utf-8")

        return html

    def _compute_statistics(
        self, positions: List[OrganizationTriadPosition]
    ) -> Dict[str, Any]:
        """Compute statistics for positions."""
        if not positions:
            return {
                "total": 0,
                "by_classification": {},
                "avg_confidence": 0,
                "centroid": {"a": 0.33, "b": 0.33, "c": 0.33},
                "dispersion": 0,
            }

        # Count by classification
        by_class = {}
        for pos in positions:
            cls = pos.classification
            by_class[cls] = by_class.get(cls, 0) + 1

        # Compute centroid
        avg_a = sum(p.coordinates[0] for p in positions) / len(positions)
        avg_b = sum(p.coordinates[1] for p in positions) / len(positions)
        avg_c = sum(p.coordinates[2] for p in positions) / len(positions)

        # Compute dispersion
        import math

        dispersion = 0
        for pos in positions:
            dist = math.sqrt(
                (pos.coordinates[0] - avg_a) ** 2
                + (pos.coordinates[1] - avg_b) ** 2
                + (pos.coordinates[2] - avg_c) ** 2
            )
            dispersion += dist
        dispersion /= len(positions)

        return {
            "total": len(positions),
            "by_classification": by_class,
            "avg_confidence": sum(p.confidence for p in positions) / len(positions),
            "centroid": {"a": avg_a, "b": avg_b, "c": avg_c},
            "dispersion": dispersion,
        }

    def _get_css(self) -> str:
        """Get CSS styles for the HTML visualization."""
        return '''
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 13px;
    line-height: 1.5;
    color: #000;
    background: #f5f5f5;
}

.app {
    display: flex;
    flex-direction: column;
    height: 100vh;
}

.header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 20px;
    background: #fff;
    border-bottom: 1px solid #e5e5e5;
}

.logo {
    display: flex;
    align-items: center;
    gap: 10px;
}

.logo i { font-size: 18px; color: #3498db; }
.logo h1 { font-size: 16px; font-weight: 600; }

.nav {
    display: flex;
    gap: 4px;
}

.nav-item {
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 500;
    color: #666;
    cursor: pointer;
    border-radius: 4px;
    transition: all .15s;
}

.nav-item:hover { color: #000; background: #f5f5f5; }
.nav-item.active { color: #fff; background: #000; }

.main {
    display: flex;
    flex: 1;
    overflow: hidden;
}

.sidebar {
    width: 280px;
    background: #fff;
    border-right: 1px solid #e5e5e5;
    padding: 16px;
    overflow-y: auto;
    flex-shrink: 0;
}

.content {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
}

.card {
    background: #fff;
    border: 1px solid #e5e5e5;
    margin-bottom: 12px;
}

.card-header {
    padding: 10px 14px;
    border-bottom: 1px solid #e5e5e5;
    font-weight: 600;
    font-size: 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

.card-header i { color: #666; }

.card-body { padding: 14px; }

.btn {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    border: 1px solid #e5e5e5;
    background: #fff;
    color: #000;
    transition: all .15s;
}

.btn:hover { background: #f5f5f5; }
.btn-sm { padding: 4px 8px; font-size: 10px; }

.tag {
    display: inline-flex;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 600;
    background: #000;
    color: #fff;
    border-radius: 2px;
}

.tag-outline { background: #fff; color: #000; border: 1px solid #e5e5e5; }
.tag-warning { background: #fef3c7; color: #92400e; }

.select, .input {
    width: 100%;
    padding: 8px 10px;
    font-size: 12px;
    border: 1px solid #e5e5e5;
    font-family: inherit;
    background: #fff;
}

.select:focus, .input:focus {
    outline: none;
    border-color: #000;
}

.form-group {
    margin-bottom: 12px;
}

.form-group label {
    display: block;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .5px;
    color: #666;
    margin-bottom: 4px;
}

.stat-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid #f5f5f5;
}

.stat-label { color: #666; }
.stat-value { font-weight: 600; }

.legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
}

.legend-color {
    width: 12px;
    height: 12px;
    border-radius: 2px;
}

.legend-label { font-size: 12px; }

.search-results {
    max-height: 200px;
    overflow-y: auto;
    margin-top: 8px;
}

.search-result {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px;
    cursor: pointer;
    border-bottom: 1px solid #f5f5f5;
}

.search-result:hover { background: #f5f5f5; }

.screen { display: none; }
.screen.active { display: block; }

.grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 16px;
}

.grid-3 {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 16px;
}

.metric-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}

.metric { text-align: center; }
.metric-value { font-size: 24px; font-weight: 600; }
.metric-label { font-size: 11px; color: #666; }

.pole-list h4 { margin-bottom: 8px; font-size: 12px; }
.pole-list ul { list-style: none; }
.pole-list li { padding: 4px 0; font-size: 12px; display: flex; justify-content: space-between; }

.header-controls {
    display: flex;
    align-items: center;
    gap: 16px;
    font-size: 11px;
}

.checkbox-label {
    display: flex;
    align-items: center;
    gap: 4px;
    cursor: pointer;
}

input[type="range"] {
    width: 80px;
    height: 4px;
    -webkit-appearance: none;
    background: #e5e5e5;
    border-radius: 2px;
}

input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 12px;
    height: 12px;
    background: #000;
    border-radius: 50%;
    cursor: pointer;
}

.info-panel {
    position: fixed;
    right: 20px;
    top: 80px;
    width: 320px;
    background: #fff;
    border: 1px solid #e5e5e5;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    z-index: 100;
}

.info-panel.hidden { display: none; }

.info-panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid #e5e5e5;
    font-weight: 600;
}

.info-panel-body { padding: 16px; }

.info-section {
    margin-bottom: 16px;
}

.info-section h4 {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .5px;
    color: #666;
    margin-bottom: 8px;
}

.coord-bar {
    display: grid;
    grid-template-columns: 80px 1fr 40px;
    gap: 8px;
    align-items: center;
    margin-bottom: 6px;
    font-size: 11px;
}

.bar {
    height: 8px;
    background: #f5f5f5;
    border-radius: 4px;
    overflow: hidden;
}

.bar-fill {
    height: 100%;
    border-radius: 4px;
}

.confidence-meter {
    height: 6px;
    background: #f5f5f5;
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 4px;
}

.meter-fill {
    height: 100%;
    background: linear-gradient(90deg, #3498db, #2ecc71);
    border-radius: 3px;
}

.tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}

.text-gray { color: #666; }
.text-sm { font-size: 11px; }
.text-center { text-align: center; }

.toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 12px 20px;
    background: #000;
    color: #fff;
    font-size: 12px;
    font-weight: 500;
    z-index: 200;
    transform: translateY(100px);
    opacity: 0;
    transition: all .3s;
}

.toast.show {
    transform: translateY(0);
    opacity: 1;
}

@media (max-width: 1024px) {
    .sidebar { width: 240px; }
    .grid-2, .grid-3 { grid-template-columns: 1fr; }
}

/* Annotation screen styles */
.grid-annotate {
    display: grid;
    grid-template-columns: 280px 1fr 320px;
    gap: 16px;
    height: calc(100% - 60px);
}

.annotate-list-card {
    display: flex;
    flex-direction: column;
    max-height: 100%;
}

.annotate-list-card .card-body {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
}

.annotate-controls {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
}

.annotate-controls .select { flex: 1; }

.annotate-queue {
    flex: 1;
    overflow-y: auto;
}

.queue-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 10px;
    border-bottom: 1px solid #f5f5f5;
    cursor: pointer;
    transition: all .1s;
}

.queue-item:hover { background: #f5f5f5; }
.queue-item.active { background: #e3f2fd; border-left: 3px solid #2196f3; }
.queue-item.annotated .queue-name { color: #666; }
.queue-name { font-size: 12px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.queue-status { font-size: 10px; }
.queue-more { padding: 8px; text-align: center; color: #666; font-size: 11px; }

.text-success { color: #2ecc71; }

.annotate-main {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.annotate-current h3 {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 12px;
}

.annotate-coords {
    display: flex;
    gap: 16px;
    margin-bottom: 12px;
}

.coord-display {
    text-align: center;
}

.coord-label {
    display: block;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: .5px;
    color: #666;
    margin-bottom: 4px;
}

.coord-value {
    font-size: 20px;
    font-weight: 700;
}

.annotate-meta {
    display: flex;
    align-items: center;
    gap: 12px;
}

.annotate-form-card {
    display: flex;
    flex-direction: column;
    max-height: 100%;
}

.annotate-form-card .card-body {
    flex: 1;
    overflow-y: auto;
}

.btn-group {
    display: flex;
    gap: 8px;
}

.btn-group-3 { }

.btn-group .btn {
    flex: 1;
    justify-content: center;
}

.btn-validate.active[data-valid="true"] {
    background: #d4edda;
    border-color: #28a745;
    color: #155724;
}

.btn-validate.active[data-valid="false"] {
    background: #f8d7da;
    border-color: #dc3545;
    color: #721c24;
}

.btn-conf.active {
    background: #000;
    color: #fff;
}

.btn-primary {
    background: #000;
    color: #fff;
    border-color: #000;
}

.btn-primary:hover {
    background: #333;
}

.correction-panel {
    background: #fffbeb;
    border: 1px solid #fcd34d;
    padding: 12px;
    margin: 12px 0;
}

.correction-panel.hidden { display: none; }

.textarea {
    width: 100%;
    padding: 8px 10px;
    font-size: 12px;
    border: 1px solid #e5e5e5;
    font-family: inherit;
    min-height: 60px;
    resize: vertical;
}

.textarea:focus {
    outline: none;
    border-color: #000;
}

.form-actions {
    display: flex;
    gap: 8px;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #e5e5e5;
}

.form-actions .btn { flex: 1; justify-content: center; }

.computed-value {
    padding: 4px 0;
}

.annotate-footer {
    position: fixed;
    bottom: 0;
    left: 280px;
    right: 0;
    background: #fff;
    border-top: 1px solid #e5e5e5;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 16px;
}

.progress-bar {
    flex: 1;
    height: 8px;
    background: #e5e5e5;
    border-radius: 4px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #3498db, #2ecc71);
    border-radius: 4px;
    transition: width .3s;
}

.annotate-stats {
    display: flex;
    align-items: center;
    gap: 16px;
    font-size: 12px;
}

.annotate-stats span { white-space: nowrap; }

#screen-annotate {
    padding-bottom: 60px;
}

#screen-annotate.active {
    display: grid;
}
'''
