"""
Ternary network plot visualization.

Creates ternary plots with network edges between organizations.
"""

from typing import Any, Dict, List, Optional
import json

from rolebox_triads.core.triad_config import TriadConfig
from rolebox_triads.core.normalizer import OrganizationTriadPosition, NetworkEdge
from rolebox_triads.visualization.ternary_scatter import TernaryScatterPlot


class TernaryNetworkPlot(TernaryScatterPlot):
    """
    Creates ternary scatter plots with network edges using Plotly.
    """

    def create_plotly_figure_with_edges(
        self,
        positions: List[OrganizationTriadPosition],
        edges: List[NetworkEdge],
        color_by: str = "classification",
        size_by: str = "fixed",
        show_legend: bool = True,
        edge_opacity: float = 0.3,
        edge_width_scale: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Create Plotly figure with nodes and edges.

        Args:
            positions: List of organization positions
            edges: List of network edges
            color_by: How to color points
            size_by: How to size points
            show_legend: Whether to show legend
            edge_opacity: Opacity of edges (0-1)
            edge_width_scale: Scale factor for edge widths

        Returns:
            Plotly figure specification as dictionary
        """
        # Create position lookup
        pos_lookup = {p.org_id: p for p in positions}

        # Create edge traces
        edge_traces = self._create_edge_traces(
            edges, pos_lookup, edge_opacity, edge_width_scale
        )

        # Create node traces (from parent class)
        base_fig = self.create_plotly_figure(
            positions, color_by=color_by, size_by=size_by, show_legend=show_legend
        )

        # Combine: edges first, then nodes (so nodes are on top)
        all_traces = edge_traces + base_fig["data"]

        return {"data": all_traces, "layout": base_fig["layout"]}

    def _create_edge_traces(
        self,
        edges: List[NetworkEdge],
        pos_lookup: Dict[str, OrganizationTriadPosition],
        opacity: float,
        width_scale: float,
    ) -> List[Dict[str, Any]]:
        """Create edge traces for the network."""
        traces = []

        # Group edges by type for different styling
        edge_groups = {}
        for edge in edges:
            edge_type = edge.edge_type
            if edge_type not in edge_groups:
                edge_groups[edge_type] = []
            edge_groups[edge_type].append(edge)

        for edge_type, type_edges in edge_groups.items():
            # Collect all edge coordinates for this type
            a_coords = []
            b_coords = []
            c_coords = []

            for edge in type_edges:
                source = pos_lookup.get(edge.source_id)
                target = pos_lookup.get(edge.target_id)

                if source is None or target is None:
                    continue

                # Add source point
                a_coords.append(source.coordinates[0])
                b_coords.append(source.coordinates[1])
                c_coords.append(source.coordinates[2])

                # Add target point
                a_coords.append(target.coordinates[0])
                b_coords.append(target.coordinates[1])
                c_coords.append(target.coordinates[2])

                # Add None to break the line
                a_coords.append(None)
                b_coords.append(None)
                c_coords.append(None)

            if not a_coords:
                continue

            trace = {
                "type": "scatterternary",
                "mode": "lines",
                "name": f"Edges ({edge_type})",
                "a": a_coords,
                "b": b_coords,
                "c": c_coords,
                "line": {
                    "color": self._get_edge_color(edge_type),
                    "width": 0.5 * width_scale,
                },
                "opacity": opacity,
                "hoverinfo": "skip",
                "showlegend": False,
            }
            traces.append(trace)

        return traces

    def _get_edge_color(self, edge_type: str) -> str:
        """Get color for edge type."""
        colors = {
            "hyperlink": "#999999",
            "mention": "#3498db",
            "investment": "#2ecc71",
            "co_membership": "#9b59b6",
            "generic": "#cccccc",
        }
        return colors.get(edge_type, "#cccccc")

    def create_animated_figure(
        self,
        position_frames: List[List[OrganizationTriadPosition]],
        frame_labels: List[str],
        edges: Optional[List[NetworkEdge]] = None,
        color_by: str = "classification",
        animation_duration: int = 1000,
    ) -> Dict[str, Any]:
        """
        Create animated Plotly figure showing position transitions.

        Args:
            position_frames: List of position lists (one per frame)
            frame_labels: Labels for each frame (e.g., years)
            edges: Optional network edges (static across frames)
            color_by: How to color points
            animation_duration: Duration of transition in ms

        Returns:
            Plotly figure specification with animation
        """
        if not position_frames:
            return {"data": [], "layout": {}}

        # Use first frame as initial data
        initial_fig = self.create_plotly_figure(
            position_frames[0], color_by=color_by, show_legend=True
        )

        # Create frames
        frames = []
        for i, (positions, label) in enumerate(zip(position_frames, frame_labels)):
            frame_fig = self.create_plotly_figure(
                positions, color_by=color_by, show_legend=False
            )
            frames.append({
                "name": label,
                "data": frame_fig["data"],
            })

        # Add slider and buttons
        sliders = [
            {
                "active": 0,
                "steps": [
                    {"args": [[label], {"frame": {"duration": animation_duration}}], "label": label, "method": "animate"}
                    for label in frame_labels
                ],
                "x": 0.1,
                "len": 0.8,
                "y": -0.05,
                "currentvalue": {
                    "prefix": "Period: ",
                    "visible": True,
                    "xanchor": "center",
                },
                "transition": {"duration": animation_duration},
            }
        ]

        updatemenus = [
            {
                "type": "buttons",
                "showactive": False,
                "y": -0.1,
                "x": 0.05,
                "buttons": [
                    {
                        "label": "Play",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": animation_duration},
                                "transition": {"duration": animation_duration // 2},
                                "fromcurrent": True,
                            },
                        ],
                    },
                    {
                        "label": "Pause",
                        "method": "animate",
                        "args": [
                            [None],
                            {
                                "frame": {"duration": 0},
                                "mode": "immediate",
                            },
                        ],
                    },
                ],
            }
        ]

        layout = initial_fig["layout"]
        layout["sliders"] = sliders
        layout["updatemenus"] = updatemenus

        return {
            "data": initial_fig["data"],
            "layout": layout,
            "frames": frames,
        }
