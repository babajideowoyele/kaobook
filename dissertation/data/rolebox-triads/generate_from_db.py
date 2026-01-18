#!/usr/bin/env python3
"""
Generate triad visualizations from database data.
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "rolebox-db"))

from db import RoleBoxDB
from rolebox_triads.core.triad_config import get_powell_framework_config
from rolebox_triads.core.normalizer import TriadNormalizer, OrganizationTriadPosition
from rolebox_triads.visualization.html_generator import TriadHTMLGenerator


def load_positions_from_db(db: RoleBoxDB, project_id: str, config) -> list:
    """Load triad positions from database and convert to OrganizationTriadPosition."""
    normalizer = TriadNormalizer(config)
    positions = []

    db_positions = db.get_triad_positions(project_id, "powell_framework")

    for p in db_positions:
        position = OrganizationTriadPosition(
            org_id=p["org_id"],
            org_name=p["name"],
            coordinates=(p["coord_a"], p["coord_b"], p["coord_c"]),
            raw_scores=(p["raw_a"], p["raw_b"], p["raw_c"]),
            classification=p["classification"],
            confidence=p.get("confidence") or 0.8,
            kic_sectors=[],
            metadata={"source": p.get("source_modality", "rolebox-wikipedia")}
        )
        positions.append(position)

    return positions


def main():
    output_dir = Path(__file__).parent / "ui"
    output_dir.mkdir(exist_ok=True)

    db = RoleBoxDB()
    config = get_powell_framework_config()

    # Get projects
    projects = db.get_projects(module="rolebox-triads")
    print(f"Found {len(projects)} triad projects")

    for project in projects:
        project_id = project["project_id"]
        project_name = project["name"]

        print(f"\nGenerating visualization for: {project_name}")

        positions = load_positions_from_db(db, project_id, config)
        print(f"  Loaded {len(positions)} positions")

        if positions:
            # Generate HTML
            generator = TriadHTMLGenerator(config)
            safe_name = project_name.lower().replace(" ", "-")
            output_path = output_dir / f"live-{safe_name}.html"
            generator.generate(positions, edges=[], output_path=output_path)
            print(f"  Saved to: {output_path}")

    print("\n" + "=" * 50)
    print("Visualizations generated!")
    print(f"Open files in: {output_dir}")


if __name__ == "__main__":
    main()
