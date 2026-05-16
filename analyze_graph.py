import json
import networkx as nx
from networkx.readwrite import json_graph
from collections import Counter


GRAPH_PATH = "skill_graph.json"


def main():
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    G = json_graph.node_link_graph(data)

    print("Graph summary")
    print("Nodes:", G.number_of_nodes())
    print("Edges:", G.number_of_edges())
    print("Density:", nx.density(G))

    components = list(nx.connected_components(G))
    print("Connected components:", len(components))
    print("Largest component size:", len(max(components, key=len)))

    degree_sorted = sorted(G.degree, key=lambda x: x[1], reverse=True)

    degrees = [degree for _, degree in G.degree()]
    print("Average degree:", sum(degrees) / len(degrees))

    print("\nTop 30 high-degree nodes:")
    for node, degree in degree_sorted[:30]:
        print(node, degree)

    print("\nDomain node counts:")
    domains = []
    for node, attrs in G.nodes(data=True):
        if attrs.get("node_type") == "skill":
            domains.append(attrs.get("domain", "unknown"))

    for domain, count in Counter(domains).most_common():
        print(domain, count)

    print("\nSample strongest edges:")
    weighted_edges = sorted(
        G.edges(data=True),
        key=lambda x: x[2].get("weight", 0),
        reverse=True
    )

    for u, v, attrs in weighted_edges[:30]:
        print(u, "--", v, "| weight:", attrs.get("weight"), "| relation:", attrs.get("relation"))


if __name__ == "__main__":
    main()