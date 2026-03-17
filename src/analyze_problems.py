#!/usr/bin/env python3
"""
Erdős Problems Relationship Analysis

This script analyzes the erdosproblems.com dataset to identify:
1. Cross-category problems (span multiple areas)
2. Tag co-occurrence networks
3. Gateway problems (highly connected)
4. Formalization opportunities
"""

import yaml
import json
from collections import defaultdict, Counter
from itertools import combinations
from pathlib import Path
import networkx as nx

DATA_PATH = Path(__file__).parent.parent / "data" / "erdosproblems" / "data" / "problems.yaml"
OUTPUT_DIR = Path(__file__).parent.parent / "analysis"

def load_problems():
    """Load problems from YAML file."""
    with open(DATA_PATH, 'r') as f:
        return yaml.safe_load(f)

def analyze_status_distribution(problems):
    """Analyze problem status distribution."""
    status_counts = Counter()
    formalized_counts = Counter()

    for p in problems:
        status = p.get('status', {}).get('state', 'unknown')
        status_counts[status] += 1

        formalized = p.get('formalized', {}).get('state', 'unknown')
        formalized_counts[formalized] += 1

    return {
        'status': dict(status_counts.most_common()),
        'formalized': dict(formalized_counts.most_common())
    }

def analyze_tags(problems):
    """Analyze tag distribution and co-occurrence."""
    tag_counts = Counter()
    tag_pairs = Counter()
    problems_by_tag = defaultdict(list)

    for p in problems:
        tags = p.get('tags', [])
        num = p['number']

        for tag in tags:
            tag_counts[tag] += 1
            problems_by_tag[tag].append(num)

        # Count tag pairs (co-occurrence)
        for t1, t2 in combinations(sorted(tags), 2):
            tag_pairs[(t1, t2)] += 1

    return {
        'tag_counts': dict(tag_counts.most_common()),
        'tag_pairs': dict(tag_pairs.most_common(50)),
        'problems_by_tag': {k: v for k, v in problems_by_tag.items()}
    }

def find_cross_category_problems(problems):
    """Find problems that span multiple major categories."""
    major_categories = {
        'number theory', 'graph theory', 'geometry',
        'ramsey theory', 'additive combinatorics', 'analysis',
        'combinatorics', 'set theory'
    }

    cross_category = []
    for p in problems:
        tags = set(p.get('tags', []))
        major_tags = tags & major_categories

        if len(major_tags) >= 2:
            cross_category.append({
                'number': p['number'],
                'major_categories': list(major_tags),
                'all_tags': list(tags),
                'status': p.get('status', {}).get('state', 'unknown'),
                'formalized': p.get('formalized', {}).get('state', 'unknown')
            })

    return cross_category

def build_problem_graph(problems):
    """Build a graph where problems are connected if they share tags."""
    G = nx.Graph()

    # Add all problems as nodes
    for p in problems:
        G.add_node(p['number'],
                   tags=p.get('tags', []),
                   status=p.get('status', {}).get('state', 'unknown'),
                   formalized=p.get('formalized', {}).get('state', 'unknown'),
                   prize=p.get('prize', 'no'))

    # Group problems by tag
    tag_to_problems = defaultdict(list)
    for p in problems:
        for tag in p.get('tags', []):
            tag_to_problems[tag].append(p['number'])

    # Connect problems that share tags
    for tag, prob_list in tag_to_problems.items():
        for p1, p2 in combinations(prob_list, 2):
            if G.has_edge(p1, p2):
                G[p1][p2]['weight'] += 1
                G[p1][p2]['shared_tags'].append(tag)
            else:
                G.add_edge(p1, p2, weight=1, shared_tags=[tag])

    return G

def find_gateway_problems(G, top_n=50):
    """Find problems with highest connectivity (gateway problems)."""
    # Calculate various centrality measures
    degree_cent = nx.degree_centrality(G)

    # Get top problems by degree
    gateway = sorted(degree_cent.items(), key=lambda x: -x[1])[:top_n]

    result = []
    for prob_num, centrality in gateway:
        node_data = G.nodes[prob_num]
        neighbors = list(G.neighbors(prob_num))
        result.append({
            'number': prob_num,
            'degree': G.degree(prob_num),
            'centrality': round(centrality, 4),
            'tags': node_data.get('tags', []),
            'status': node_data.get('status', 'unknown'),
            'formalized': node_data.get('formalized', 'unknown'),
            'neighbor_count': len(neighbors)
        })

    return result

def find_open_formalization_opportunities(problems):
    """Find open problems that are not yet formalized but are highly connected."""
    open_not_formalized = []

    for p in problems:
        status = p.get('status', {}).get('state', 'unknown')
        formalized = p.get('formalized', {}).get('state', 'unknown')

        if status == 'open' and formalized == 'no':
            tags = p.get('tags', [])
            open_not_formalized.append({
                'number': p['number'],
                'tags': tags,
                'tag_count': len(tags),
                'prize': p.get('prize', 'no'),
                'oeis': p.get('oeis', [])
            })

    # Sort by tag count (more tags = more connections)
    return sorted(open_not_formalized, key=lambda x: -x['tag_count'])

def analyze_prize_problems(problems):
    """Analyze problems with prizes."""
    prize_problems = []

    for p in problems:
        prize = p.get('prize', 'no')
        if prize != 'no':
            prize_problems.append({
                'number': p['number'],
                'prize': prize,
                'status': p.get('status', {}).get('state', 'unknown'),
                'tags': p.get('tags', []),
                'formalized': p.get('formalized', {}).get('state', 'unknown')
            })

    return sorted(prize_problems, key=lambda x: -int(x['prize'].replace('$', '').replace(',', '')) if x['prize'].startswith('$') else 0)

def main():
    print("Loading problems...")
    problems = load_problems()
    print(f"Loaded {len(problems)} problems")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 1. Status distribution
    print("\n=== STATUS DISTRIBUTION ===")
    status_dist = analyze_status_distribution(problems)
    print(json.dumps(status_dist, indent=2))

    # 2. Tag analysis
    print("\n=== TAG ANALYSIS ===")
    tag_analysis = analyze_tags(problems)
    print(f"Top tags: {list(tag_analysis['tag_counts'].items())[:10]}")
    print(f"Top tag pairs: {list(tag_analysis['tag_pairs'].items())[:10]}")

    # 3. Cross-category problems
    print("\n=== CROSS-CATEGORY PROBLEMS ===")
    cross_cat = find_cross_category_problems(problems)
    print(f"Found {len(cross_cat)} problems spanning multiple major categories")
    for p in cross_cat[:10]:
        print(f"  Problem {p['number']}: {p['major_categories']} ({p['status']})")

    # 4. Build graph and find gateway problems
    print("\n=== GATEWAY PROBLEMS ===")
    G = build_problem_graph(problems)
    print(f"Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

    gateway = find_gateway_problems(G, top_n=30)
    print("Top 10 gateway problems (highest connectivity):")
    for p in gateway[:10]:
        print(f"  Problem {p['number']}: degree={p['degree']}, tags={p['tags']}, status={p['status']}")

    # 5. Open problems needing formalization
    print("\n=== FORMALIZATION OPPORTUNITIES ===")
    form_opps = find_open_formalization_opportunities(problems)
    print(f"Found {len(form_opps)} open problems not yet formalized")
    print("Top 10 by connectivity (tag count):")
    for p in form_opps[:10]:
        print(f"  Problem {p['number']}: tags={p['tags']}")

    # 6. Prize problems
    print("\n=== PRIZE PROBLEMS ===")
    prize_probs = analyze_prize_problems(problems)
    print(f"Found {len(prize_probs)} problems with prizes")
    print("Open prize problems:")
    for p in prize_probs:
        if p['status'] == 'open':
            print(f"  Problem {p['number']}: {p['prize']} - tags={p['tags']}")

    # Save detailed results
    results = {
        'summary': {
            'total_problems': len(problems),
            'status_distribution': status_dist['status'],
            'formalization_distribution': status_dist['formalized']
        },
        'tag_analysis': {
            'tag_counts': tag_analysis['tag_counts'],
            'top_tag_pairs': {str(k): v for k, v in list(tag_analysis['tag_pairs'].items())[:30]}
        },
        'cross_category_problems': cross_cat,
        'gateway_problems': gateway,
        'formalization_opportunities': form_opps[:50],
        'prize_problems': [p for p in prize_probs if p['status'] == 'open']
    }

    output_file = OUTPUT_DIR / "problem_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to {output_file}")

    return results

if __name__ == "__main__":
    main()
