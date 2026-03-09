"""Build investor→company and co-investment networks from Crunchbase data."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx
import pandas as pd


def anon(name: str) -> str:
    """Anonymize entity name to 8-char hash."""
    return hashlib.sha256(name.encode()).hexdigest()[:8]


def main() -> None:
    base = Path(__file__).resolve().parent.parent
    raw_csv = base / "data/rolebox-crunchbase/data/raw/eit_companies-11-29-2025.csv"
    out_path = base / "data/rolesim/data/outputs/investor_network_typology.json"

    df = pd.read_csv(raw_csv, low_memory=False)

    # ── Bipartite network: investor → company ──
    G_bip = nx.DiGraph()
    company_investors: dict[str, set[str]] = defaultdict(set)

    for _, row in df.iterrows():
        company = str(row["Organization Name"]).strip()
        G_bip.add_node(company, node_type="company")

        top5 = row.get("Top 5 Investors")
        if pd.notna(top5):
            for inv in str(top5).split(","):
                inv = inv.strip()
                if inv and inv != "nan":
                    if not G_bip.has_node(inv):
                        G_bip.add_node(inv, node_type="investor")
                    if not G_bip.has_edge(inv, company):
                        G_bip.add_edge(inv, company, weight=1)
                    company_investors[company].add(inv)

    in_deg = dict(G_bip.in_degree())
    out_deg = dict(G_bip.out_degree())

    n_inv = sum(1 for _, d in G_bip.nodes(data=True) if d.get("node_type") == "investor")
    n_comp = sum(1 for _, d in G_bip.nodes(data=True) if d.get("node_type") == "company")
    print(f"Bipartite: {n_inv} investors, {n_comp} companies, {G_bip.number_of_edges()} edges")

    # Classify bipartite roles
    bip_roles: dict[str, str] = {}
    for node, data in G_bip.nodes(data=True):
        ntype = data.get("node_type", "unknown")
        ind = in_deg[node]
        outd = out_deg[node]

        if ntype == "company":
            bip_roles[node] = "Well-Funded Receiver" if ind >= 10 else "Receiver"
        elif ntype == "investor":
            if outd >= 50:
                bip_roles[node] = "Hub"
            elif outd >= 20:
                bip_roles[node] = "Amplifier"
            elif outd >= 5:
                bip_roles[node] = "Emitter"
            else:
                bip_roles[node] = "Low Emitter"

    bip_dist = Counter(bip_roles.values())
    print("\nBipartite roles:")
    for role, count in bip_dist.most_common():
        print(f"  {role}: {count} ({100*count/len(bip_roles):.1f}%)")

    # ── Co-investment projection ──
    G_coinv = nx.Graph()
    for company, investors in company_investors.items():
        inv_list = list(investors)
        for i in range(len(inv_list)):
            for j in range(i + 1, len(inv_list)):
                a, b = inv_list[i], inv_list[j]
                if G_coinv.has_edge(a, b):
                    G_coinv[a][b]["weight"] += 1
                else:
                    G_coinv.add_edge(a, b, weight=1)

    # Add isolated investors
    for node, data in G_bip.nodes(data=True):
        if data.get("node_type") == "investor" and not G_coinv.has_node(node):
            G_coinv.add_node(node)

    components = list(nx.connected_components(G_coinv))
    largest_cc = max(components, key=len)
    G_cc = G_coinv.subgraph(largest_cc).copy()

    print(f"\nCo-investment: {G_coinv.number_of_nodes()} investors, {G_coinv.number_of_edges()} edges")
    print(f"Components: {len(components)}, largest CC: {len(largest_cc)}")

    deg = dict(G_cc.degree())
    bc = nx.betweenness_centrality(G_cc, k=min(500, G_cc.number_of_nodes()))

    # Percentile thresholds
    deg_vals = sorted(deg.values())
    bc_vals = sorted(v for v in bc.values() if v > 0)
    deg_p90 = deg_vals[int(0.9 * len(deg_vals))] if deg_vals else 1
    deg_p75 = deg_vals[int(0.75 * len(deg_vals))] if deg_vals else 1
    bc_p95 = bc_vals[int(0.95 * len(bc_vals))] if bc_vals else 0.001
    bc_p75 = bc_vals[int(0.75 * len(bc_vals))] if bc_vals else 0.001

    print(f"Degree p75={deg_p75}, p90={deg_p90}")
    print(f"Betweenness p75={bc_p75:.4f}, p95={bc_p95:.4f}")

    coinv_roles: dict[str, str] = {}
    for node in G_coinv.nodes():
        d = deg.get(node, 0)
        b = bc.get(node, 0)
        if d >= deg_p90 and b >= bc_p75:
            coinv_roles[node] = "Hub"
        elif b >= bc_p95:
            coinv_roles[node] = "Bridge"
        elif d >= deg_p75:
            coinv_roles[node] = "Connector"
        elif d >= 3:
            coinv_roles[node] = "Transceiver"
        elif d >= 1:
            coinv_roles[node] = "Low Emitter"
        else:
            coinv_roles[node] = "Isolate"

    coinv_dist = Counter(coinv_roles.values())
    print("\nCo-investment roles:")
    for role, count in coinv_dist.most_common():
        print(f"  {role}: {count} ({100*count/G_coinv.number_of_nodes():.1f}%)")

    # Top actors by role
    hub_inv = [(n, deg.get(n, 0), bc.get(n, 0)) for n, r in coinv_roles.items() if r == "Hub"]
    bridge_inv = [(n, deg.get(n, 0), bc.get(n, 0)) for n, r in coinv_roles.items() if r == "Bridge"]

    print("\nHubs (co-investment):")
    for name, d, b in sorted(hub_inv, key=lambda x: -x[1])[:10]:
        print(f"  {name}: degree={d}, bc={b:.4f}")

    print("\nBridges (co-investment):")
    for name, d, b in sorted(bridge_inv, key=lambda x: -x[2])[:10]:
        print(f"  {name}: degree={d}, bc={b:.4f}")

    # ── Save anonymized results ──
    results = {
        "metadata": {
            "pipeline_date": "2026-02-16",
            "source": "Crunchbase EIT ventures (654 companies, Top 5 Investors)",
            "anonymized": True,
        },
        "bipartite_network": {
            "n_investors": n_inv,
            "n_companies": n_comp,
            "n_edges": G_bip.number_of_edges(),
            "role_distribution": dict(bip_dist.most_common()),
            "hub_actors": [
                {"id": anon(n), "out_degree": out_deg[n]}
                for n, _, _ in sorted(
                    [(n, out_deg[n], 0) for n, r in bip_roles.items() if r == "Hub"],
                    key=lambda x: -x[1],
                )
            ],
        },
        "coinvestment_network": {
            "n_investors": G_coinv.number_of_nodes(),
            "n_edges": G_coinv.number_of_edges(),
            "n_components": len(components),
            "largest_cc": len(largest_cc),
            "density": round(nx.density(G_coinv), 4),
            "role_distribution": dict(coinv_dist.most_common()),
            "hub_actors": [
                {"id": anon(n), "degree": deg.get(n, 0), "betweenness": round(bc.get(n, 0), 4)}
                for n, _, _ in sorted(hub_inv, key=lambda x: -x[1])[:10]
            ],
            "bridge_actors": [
                {"id": anon(n), "degree": deg.get(n, 0), "betweenness": round(bc.get(n, 0), 4)}
                for n, _, _ in sorted(bridge_inv, key=lambda x: -x[2])[:10]
            ],
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
