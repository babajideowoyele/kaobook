"""
Ternary scatter plot visualization.

Creates basic ternary scatter plots using Plotly.
"""

from typing import Any, Dict, List, Optional
import json

from rolebox_triads.core.triad_config import TriadConfig
from rolebox_triads.core.normalizer import OrganizationTriadPosition


class TernaryScatterPlot:
    """
    Creates ternary scatter plots using Plotly.
    """

    def __init__(self, config: TriadConfig):
        self.config = config

    def create_plotly_figure(
        self,
        positions: List[OrganizationTriadPosition],
        color_by: str = "classification",  # "classification", "kic", "confidence"
        size_by: str = "fixed",  # "fixed", "confidence", "raw_total"
        show_legend: bool = True,
    ) -> Dict[str, Any]:
        """
        Create Plotly figure specification for ternary scatter plot.

        Args:
            positions: List of organization positions
            color_by: How to color points
            size_by: How to size points
            show_legend: Whether to show legend

        Returns:
            Plotly figure specification as dictionary
        """
        # Group positions by classification for legend
        groups = self._group_by_classification(positions) if color_by == "classification" else {"all": positions}

        traces = []

        for group_name, group_positions in groups.items():
            color = self._get_group_color(group_name, color_by)
            sizes = self._compute_sizes(group_positions, size_by)

            trace = {
                "type": "scatterternary",
                "mode": "markers",
                "name": self._format_group_name(group_name),
                "a": [p.coordinates[0] for p in group_positions],
                "b": [p.coordinates[1] for p in group_positions],
                "c": [p.coordinates[2] for p in group_positions],
                "text": [p.org_name for p in group_positions],
                "customdata": [
                    {
                        "org_id": p.org_id,
                        "classification": p.classification,
                        "confidence": p.confidence,
                        "kic_sectors": p.kic_sectors,
                        "coordinates": p.coordinates,
                        "raw_scores": p.raw_scores,
                    }
                    for p in group_positions
                ],
                "hovertemplate": self._get_hover_template(),
                "marker": {
                    "size": sizes,
                    "color": color,
                    "opacity": 0.8,
                    "line": {"color": "white", "width": 1},
                },
            }
            traces.append(trace)

        layout = {
            "ternary": {
                "sum": 1,
                "aaxis": {
                    "title": {"text": self.config.axis_a.name},
                    "min": 0,
                    "linecolor": self.config.axis_a.color,
                    "tickfont": {"size": 11},
                },
                "baxis": {
                    "title": {"text": self.config.axis_b.name},
                    "min": 0,
                    "linecolor": self.config.axis_b.color,
                    "tickfont": {"size": 11},
                },
                "caxis": {
                    "title": {"text": self.config.axis_c.name},
                    "min": 0,
                    "linecolor": self.config.axis_c.color,
                    "tickfont": {"size": 11},
                },
                "bgcolor": "#fafafa",
            },
            "showlegend": show_legend,
            "legend": {
                "x": 1.02,
                "y": 0.5,
                "font": {"size": 11},
            },
            "margin": {"l": 50, "r": 50, "t": 50, "b": 50},
            "font": {"family": "Inter, sans-serif"},
            "paper_bgcolor": "white",
            "plot_bgcolor": "white",
        }

        return {"data": traces, "layout": layout}

    def _group_by_classification(
        self, positions: List[OrganizationTriadPosition]
    ) -> Dict[str, List[OrganizationTriadPosition]]:
        """Group positions by classification."""
        groups = {}
        for pos in positions:
            cls = pos.classification
            if cls not in groups:
                groups[cls] = []
            groups[cls].append(pos)
        return groups

    def _get_group_color(self, group_name: str, color_by: str) -> str:
        """Get color for a group."""
        if color_by == "classification":
            return self.config.color_palette.get(group_name, "#999999")
        return "#3498db"

    def _compute_sizes(
        self, positions: List[OrganizationTriadPosition], size_by: str
    ) -> List[float]:
        """Compute marker sizes."""
        if size_by == "fixed":
            return [10] * len(positions)
        elif size_by == "confidence":
            return [8 + p.confidence * 12 for p in positions]
        elif size_by == "raw_total":
            totals = [sum(p.raw_scores) for p in positions]
            max_total = max(totals) if totals else 1
            return [6 + (t / max_total) * 18 for t in totals]
        return [10] * len(positions)

    def _format_group_name(self, name: str) -> str:
        """Format group name for legend."""
        return name.replace("dominant_", "").replace("_", " ").title()

    def _get_hover_template(self) -> str:
        """Get hover template for points."""
        return (
            "<b>%{text}</b><br>"
            f"{self.config.axis_a.name}: %{{a:.2f}}<br>"
            f"{self.config.axis_b.name}: %{{b:.2f}}<br>"
            f"{self.config.axis_c.name}: %{{c:.2f}}<br>"
            "<extra></extra>"
        )

    def to_json(
        self,
        positions: List[OrganizationTriadPosition],
        **kwargs,
    ) -> str:
        """Export figure as JSON string."""
        fig = self.create_plotly_figure(positions, **kwargs)
        return json.dumps(fig, indent=2)
