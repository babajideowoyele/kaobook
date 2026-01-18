"""
Static export for PDF/PNG output.

Generates publication-quality figures for LaTeX dissertation.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from rolebox_triads.core.triad_config import TriadConfig
from rolebox_triads.core.normalizer import OrganizationTriadPosition, NetworkEdge
from rolebox_triads.visualization.ternary_scatter import TernaryScatterPlot
from rolebox_triads.visualization.ternary_network import TernaryNetworkPlot


class StaticExporter:
    """
    Export ternary plots for LaTeX publication.

    Outputs:
    - High-resolution PNG (300 DPI)
    - Vector PDF
    - Optionally TikZ/pgfplots code
    """

    def __init__(self, config: TriadConfig):
        self.config = config
        self.scatter_plot = TernaryScatterPlot(config)
        self.network_plot = TernaryNetworkPlot(config)

        # Default figure dimensions
        self.fig_width = 800  # pixels
        self.fig_height = 600
        self.scale = 3  # For high DPI

    def export_png(
        self,
        positions: List[OrganizationTriadPosition],
        output_path: Path,
        edges: Optional[List[NetworkEdge]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        **kwargs,
    ) -> None:
        """
        Export ternary plot as PNG.

        Args:
            positions: List of organization positions
            output_path: Path for output file
            edges: Optional network edges
            width: Figure width in pixels
            height: Figure height in pixels
            **kwargs: Additional arguments for plot creation
        """
        try:
            import plotly.graph_objects as go
            import plotly.io as pio
        except ImportError:
            raise ImportError("plotly and kaleido required for static export")

        width = width or self.fig_width
        height = height or self.fig_height

        if edges:
            fig_data = self.network_plot.create_plotly_figure_with_edges(
                positions, edges, **kwargs
            )
        else:
            fig_data = self.scatter_plot.create_plotly_figure(positions, **kwargs)

        fig = go.Figure(data=fig_data["data"], layout=fig_data["layout"])

        # Update layout for publication
        fig.update_layout(
            font=dict(family="Inter, Arial, sans-serif", size=12),
            paper_bgcolor="white",
            plot_bgcolor="white",
        )

        fig.write_image(
            str(output_path),
            format="png",
            width=width,
            height=height,
            scale=self.scale,
        )

    def export_pdf(
        self,
        positions: List[OrganizationTriadPosition],
        output_path: Path,
        edges: Optional[List[NetworkEdge]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        **kwargs,
    ) -> None:
        """
        Export ternary plot as PDF.

        Args:
            positions: List of organization positions
            output_path: Path for output file
            edges: Optional network edges
            width: Figure width in pixels
            height: Figure height in pixels
            **kwargs: Additional arguments for plot creation
        """
        try:
            import plotly.graph_objects as go
        except ImportError:
            raise ImportError("plotly and kaleido required for static export")

        width = width or self.fig_width
        height = height or self.fig_height

        if edges:
            fig_data = self.network_plot.create_plotly_figure_with_edges(
                positions, edges, **kwargs
            )
        else:
            fig_data = self.scatter_plot.create_plotly_figure(positions, **kwargs)

        fig = go.Figure(data=fig_data["data"], layout=fig_data["layout"])

        fig.update_layout(
            font=dict(family="Inter, Arial, sans-serif", size=12),
            paper_bgcolor="white",
        )

        fig.write_image(
            str(output_path),
            format="pdf",
            width=width,
            height=height,
        )

    def export_svg(
        self,
        positions: List[OrganizationTriadPosition],
        output_path: Path,
        edges: Optional[List[NetworkEdge]] = None,
        **kwargs,
    ) -> None:
        """
        Export ternary plot as SVG.

        Args:
            positions: List of organization positions
            output_path: Path for output file
            edges: Optional network edges
            **kwargs: Additional arguments for plot creation
        """
        try:
            import plotly.graph_objects as go
        except ImportError:
            raise ImportError("plotly and kaleido required for static export")

        if edges:
            fig_data = self.network_plot.create_plotly_figure_with_edges(
                positions, edges, **kwargs
            )
        else:
            fig_data = self.scatter_plot.create_plotly_figure(positions, **kwargs)

        fig = go.Figure(data=fig_data["data"], layout=fig_data["layout"])

        fig.write_image(
            str(output_path),
            format="svg",
            width=self.fig_width,
            height=self.fig_height,
        )

    def export_tikz(
        self,
        positions: List[OrganizationTriadPosition],
        output_path: Path,
    ) -> None:
        """
        Export as TikZ/pgfplots code for direct LaTeX inclusion.

        Note: This generates basic ternary coordinates; full TikZ ternary
        plots require the ternaryaxis package.

        Args:
            positions: List of organization positions
            output_path: Path for output file
        """
        # Group by classification
        groups: Dict[str, List[OrganizationTriadPosition]] = {}
        for pos in positions:
            cls = pos.classification
            if cls not in groups:
                groups[cls] = []
            groups[cls].append(pos)

        tikz_code = r"""\begin{figure}[htbp]
\centering
\begin{tikzpicture}
\begin{ternaryaxis}[
    xlabel={""" + self.config.axis_a.name + r"""},
    ylabel={""" + self.config.axis_b.name + r"""},
    zlabel={""" + self.config.axis_c.name + r"""},
    xmin=0, xmax=1,
    ymin=0, ymax=1,
    zmin=0, zmax=1,
    grid=both,
    minor tick num=1,
    legend pos=outer north east,
]
"""

        # Add scatter points for each group
        for cls, cls_positions in groups.items():
            color = self._tikz_color(self.config.color_palette.get(cls, "#999999"))
            label = cls.replace("dominant_", "").replace("_", " ").title()

            coords = " ".join(
                f"({p.coordinates[0]:.3f},{p.coordinates[1]:.3f},{p.coordinates[2]:.3f})"
                for p in cls_positions
            )

            tikz_code += f"""
\\addplot3[
    only marks,
    mark=*,
    mark size=2pt,
    color={color},
] coordinates {{ {coords} }};
\\addlegendentry{{{label}}}
"""

        tikz_code += r"""
\end{ternaryaxis}
\end{tikzpicture}
\caption{""" + f"Triad visualization: {self.config.name}" + r"""}
\label{fig:triad-visualization}
\end{figure}
"""

        Path(output_path).write_text(tikz_code, encoding="utf-8")

    def _tikz_color(self, hex_color: str) -> str:
        """Convert hex color to TikZ color definition."""
        # Remove # and parse RGB
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        return f"{{rgb,255:red,{r};green,{g};blue,{b}}}"

    def export_all(
        self,
        positions: List[OrganizationTriadPosition],
        output_dir: Path,
        base_name: str = "triad",
        edges: Optional[List[NetworkEdge]] = None,
        formats: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Path]:
        """
        Export to multiple formats at once.

        Args:
            positions: List of organization positions
            output_dir: Directory for output files
            base_name: Base filename (without extension)
            edges: Optional network edges
            formats: List of formats to export (default: ["png", "pdf"])
            **kwargs: Additional arguments for plot creation

        Returns:
            Dictionary mapping format to output path
        """
        formats = formats or ["png", "pdf"]
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exported = {}

        if "png" in formats:
            path = output_dir / f"{base_name}.png"
            self.export_png(positions, path, edges=edges, **kwargs)
            exported["png"] = path

        if "pdf" in formats:
            path = output_dir / f"{base_name}.pdf"
            self.export_pdf(positions, path, edges=edges, **kwargs)
            exported["pdf"] = path

        if "svg" in formats:
            path = output_dir / f"{base_name}.svg"
            self.export_svg(positions, path, edges=edges, **kwargs)
            exported["svg"] = path

        if "tikz" in formats:
            path = output_dir / f"{base_name}.tex"
            self.export_tikz(positions, path)
            exported["tikz"] = path

        return exported
