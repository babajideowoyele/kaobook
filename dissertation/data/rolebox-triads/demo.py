#!/usr/bin/env python3
"""
Demo script for rolebox-triads visualization framework.

Generates sample visualizations with mock data to demonstrate all three triad types.
"""

import random
from pathlib import Path

# Add src to path for development
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rolebox_triads.core.triad_config import (
    get_powell_framework_config,
    get_role_modalities_config,
    get_actor_types_config,
    get_multi_actor_perspective_config,
)
from rolebox_triads.core.normalizer import TriadNormalizer, OrganizationTriadPosition, NetworkEdge
from rolebox_triads.visualization.html_generator import TriadHTMLGenerator
from rolebox_triads.triads.powell_framework import PowellFrameworkCalculator


def generate_mock_positions(config, n=50, triad_type="powell"):
    """Generate mock organization positions for demonstration."""
    normalizer = TriadNormalizer(config)
    positions = []

    # Organization name prefixes by type
    org_types = {
        "University": ["MIT", "Stanford", "Oxford", "Cambridge", "ETH Zurich", "TU Delft", "KU Leuven"],
        "Company": ["CleanTech", "GreenEnergy", "EcoSolutions", "SustainCorp", "NetZero", "CarbonFree"],
        "NGO": ["GreenPeace", "WWF", "Climate Action", "Earth First", "Sustainable Future"],
        "Government": ["EU Commission", "Ministry of", "Agency for", "Department of"],
        "Research": ["Fraunhofer", "TNO", "VITO", "CEA", "CSIC"],
    }

    kics = ["Climate-KIC", "EIT Digital", "EIT InnoEnergy", "EIT Health", "EIT Food"]

    for i in range(n):
        # Pick random org type
        org_type = random.choice(list(org_types.keys()))
        base_name = random.choice(org_types[org_type])
        org_name = f"{base_name} {random.randint(1, 99)}" if random.random() > 0.5 else base_name

        # Generate biased random scores based on org type and triad type
        if triad_type == "map":
            # Multi-actor Perspective: State vs Market vs Community
            if org_type == "Government":
                # Government leans State
                a = random.uniform(0.5, 0.9)
                b = random.uniform(0.1, 0.3)
                c = random.uniform(0.1, 0.2)
            elif org_type == "Company":
                # Companies lean Market
                a = random.uniform(0.1, 0.2)
                b = random.uniform(0.6, 0.9)
                c = random.uniform(0.1, 0.2)
            elif org_type == "NGO":
                # NGOs lean Community
                a = random.uniform(0.1, 0.3)
                b = random.uniform(0.1, 0.2)
                c = random.uniform(0.5, 0.8)
            elif org_type == "University":
                # Universities are third sector: between state and community
                a = random.uniform(0.3, 0.5)
                b = random.uniform(0.1, 0.25)
                c = random.uniform(0.3, 0.5)
            else:
                # Research is similar to university
                a = random.uniform(0.35, 0.5)
                b = random.uniform(0.15, 0.3)
                c = random.uniform(0.25, 0.4)
        else:
            # Original Powell framework scoring
            if org_type == "University":
                # Universities lean scientific
                a = random.uniform(0.1, 0.4)
                b = random.uniform(0.4, 0.8)
                c = random.uniform(0.1, 0.3)
            elif org_type == "Company":
                # Companies lean managerial
                a = random.uniform(0.1, 0.3)
                b = random.uniform(0.1, 0.4)
                c = random.uniform(0.4, 0.8)
            elif org_type == "NGO":
                # NGOs lean associational
                a = random.uniform(0.4, 0.8)
                b = random.uniform(0.1, 0.3)
                c = random.uniform(0.1, 0.3)
            else:
                # Others are more balanced
                a = random.uniform(0.2, 0.5)
                b = random.uniform(0.2, 0.5)
                c = random.uniform(0.2, 0.5)

        # Add some interstitial cases
        if random.random() < 0.15:
            a, b, c = 0.33 + random.uniform(-0.05, 0.05), 0.33 + random.uniform(-0.05, 0.05), 0.33 + random.uniform(-0.05, 0.05)

        position = normalizer.compute_position(
            org_id=f"org_{i:03d}",
            org_name=org_name,
            raw_a=a,
            raw_b=b,
            raw_c=c,
            kic_sectors=[random.choice(kics)] if random.random() > 0.3 else [],
            metadata={"org_type": org_type},
        )
        positions.append(position)

    return positions


def generate_mock_edges(positions, density=0.1):
    """Generate mock network edges between positions."""
    edges = []
    n = len(positions)

    for i in range(n):
        for j in range(i + 1, n):
            if random.random() < density:
                edges.append(NetworkEdge(
                    source_id=positions[i].org_id,
                    target_id=positions[j].org_id,
                    weight=random.uniform(0.3, 1.0),
                    edge_type=random.choice(["hyperlink", "mention", "co_membership"]),
                ))

    return edges


def main():
    """Generate demo visualizations."""
    output_dir = Path(__file__).parent / "ui"
    output_dir.mkdir(exist_ok=True)

    print("RoleBox Triads - Demo Visualization Generator")
    print("=" * 50)

    # 1. Powell Framework Demo
    print("\n1. Generating Powell Framework visualization...")
    powell_config = get_powell_framework_config()
    powell_positions = generate_mock_positions(powell_config, n=60)
    powell_edges = generate_mock_edges(powell_positions, density=0.08)

    generator = TriadHTMLGenerator(powell_config)
    output_path = output_dir / "demo-powell-framework.html"
    generator.generate(powell_positions, edges=powell_edges, output_path=output_path)
    print(f"   Saved to: {output_path}")

    # 2. Role Modalities Demo
    print("\n2. Generating Role Modalities visualization...")
    role_config = get_role_modalities_config()
    role_positions = generate_mock_positions(role_config, n=50)
    role_edges = generate_mock_edges(role_positions, density=0.05)

    generator = TriadHTMLGenerator(role_config)
    output_path = output_dir / "demo-role-modalities.html"
    generator.generate(role_positions, edges=role_edges, output_path=output_path)
    print(f"   Saved to: {output_path}")

    # 3. Actor Types Demo
    print("\n3. Generating Actor Types visualization...")
    actor_config = get_actor_types_config()
    actor_positions = generate_mock_positions(actor_config, n=45)
    actor_edges = generate_mock_edges(actor_positions, density=0.12)

    generator = TriadHTMLGenerator(actor_config)
    output_path = output_dir / "demo-actor-types.html"
    generator.generate(actor_positions, edges=actor_edges, output_path=output_path)
    print(f"   Saved to: {output_path}")

    # 4. Multi-actor Perspective Demo (Avelino & Wittmayer 2015)
    print("\n4. Generating Multi-actor Perspective visualization...")
    map_config = get_multi_actor_perspective_config()
    map_positions = generate_mock_positions(map_config, n=55, triad_type="map")
    map_edges = generate_mock_edges(map_positions, density=0.06)

    generator = TriadHTMLGenerator(map_config)
    output_path = output_dir / "demo-multi-actor-perspective.html"
    generator.generate(map_positions, edges=map_edges, output_path=output_path)
    print(f"   Saved to: {output_path}")

    # Summary
    print("\n" + "=" * 50)
    print("Demo visualizations generated successfully!")
    print(f"\nOpen any of these files in a browser:")
    print(f"  - {output_dir / 'demo-powell-framework.html'}")
    print(f"  - {output_dir / 'demo-role-modalities.html'}")
    print(f"  - {output_dir / 'demo-actor-types.html'}")
    print(f"  - {output_dir / 'demo-multi-actor-perspective.html'} (State vs Market vs Community)")


if __name__ == "__main__":
    main()
