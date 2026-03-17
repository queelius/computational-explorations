# Problem Network Analysis

Network science applied to the Erdos problems corpus.

## 1. Graph Construction

- **Nodes**: 1183 problems
- **Edges**: 58261
- **Density**: 0.0833
- **Average degree**: 98.5
- **Max degree**: 267
- **Median degree**: 62
- **Connected components**: 1
- **Largest component**: 1183 nodes (100.0%)

### Edge type breakdown

| Edge type | Count | Total weight |
|-----------|-------|-------------|
| tag_cooccurrence | 50,508 | 48,490.0 |
| same_status | 24,887 | 4,977.4 |
| numerical_proximity | 10,602 | 2,834.1 |
| oeis_cooccurrence | 90 | 244.0 |

## 2. Community Detection (Louvain)

- **Communities found**: 12
- **Modularity Q**: 0.5626
- **NMI with tags**: 0.8434 (1.0 = perfect alignment; low = communities reveal deeper structure)

### Community profiles (top 15 by size)

| # | Size | Dominant tag | Solve % | Top tags |
|---|------|-------------|---------|----------|
| 9 | 250 | number theory (100%) | 32% | number theory |
| 0 | 149 | chromatic number (28%) | 47% | graph theory, chromatic number, combinatorics |
| 5 | 105 | ramsey theory (69%) | 35% | ramsey theory, graph theory, set theory |
| 10 | 104 | primes (40%) | 26% | number theory, primes, additive basis |
| 7 | 93 | graph theory (100%) | 56% | graph theory, number theory |
| 4 | 89 | divisors (33%) | 35% | number theory, divisors, binomial coefficients |
| 11 | 88 | analysis (49%) | 55% | analysis, polynomials, probability |
| 2 | 83 | arithmetic progressions (27%) | 49% | number theory, arithmetic progressions, irrationality |
| 6 | 60 | distances (72%) | 32% | geometry, distances, convex |
| 8 | 56 | additive combinatorics (100%) | 52% | additive combinatorics, number theory, ramsey theory |
| 1 | 54 | geometry (85%) | 46% | geometry, number theory, complete sequences |
| 3 | 52 | unit fractions (92%) | 46% | number theory, unit fractions, powers |

## 3. Centrality Analysis

### Central problems are more likely to be solved?

| Measure | Solved mean | Open mean | Direction | Rank-biserial r |
|---------|------------|-----------|-----------|----------------|
| pagerank | 0.000806 | 0.000878 | open_higher | 0.184 |
| betweenness | 0.005285 | 0.002260 | solved_higher | 0.457 |
| eigenvector | 0.010009 | 0.016694 | open_higher | 0.190 |

### Top 15 by PageRank

| Rank | Problem | PageRank |
|------|---------|----------|
| 1 | #986 (open) | 0.001285 |
| 2 | #342 (open) | 0.001265 |
| 3 | #1030 (open) | 0.001262 |
| 4 | #261 (open) | 0.001257 |
| 5 | #341 (open) | 0.001250 |
| 6 | #145 (open) | 0.001245 |
| 7 | #1148 (open) | 0.001243 |
| 8 | #329 (open) | 0.001243 |
| 9 | #1096 (open) | 0.001241 |
| 10 | #1146 (open) | 0.001241 |
| 11 | #726 (open) | 0.001239 |
| 12 | #854 (open) | 0.001239 |
| 13 | #1003 (open) | 0.001239 |
| 14 | #687 (open) | 0.001238 |
| 15 | #254 (open) | 0.001238 |

### Top 15 by betweenness

| Rank | Problem | Betweenness |
|------|---------|-------------|
| 1 | #439 (proved) | 0.049388 |
| 2 | #54 (solved) | 0.030983 |
| 3 | #45 (proved) | 0.028543 |
| 4 | #55 (solved) | 0.027120 |
| 5 | #189 (disproved (Lean)) | 0.025002 |
| 6 | #894 (proved) | 0.024214 |
| 7 | #1145 (open) | 0.023867 |
| 8 | #358 (open) | 0.023456 |
| 9 | #1090 (proved (Lean)) | 0.022790 |
| 10 | #46 (proved (Lean)) | 0.022596 |
| 11 | #982 (falsifiable) | 0.022495 |
| 12 | #446 (solved) | 0.021974 |
| 13 | #110 (not provable) | 0.021570 |
| 14 | #1127 (independent) | 0.021525 |
| 15 | #615 (disproved) | 0.021480 |

## 4. Temporal Network Evolution

**Connectivity trend**: decreasing

| Window | Problems | Edges | Density | Avg degree | Clustering | Solve % |
|--------|----------|-------|---------|------------|------------|---------|
| 1-118 | 118 | 1258 | 0.1822 | 21.3 | 0.047 | 40% |
| 119-236 | 118 | 1267 | 0.1835 | 21.5 | 0.031 | 45% |
| 237-354 | 118 | 1697 | 0.2458 | 28.8 | 0.202 | 40% |
| 355-472 | 118 | 2754 | 0.3990 | 46.7 | 0.174 | 41% |
| 473-590 | 118 | 1469 | 0.2128 | 24.9 | 0.167 | 43% |
| 591-708 | 118 | 1378 | 0.1996 | 23.4 | 0.224 | 36% |
| 709-826 | 118 | 1571 | 0.2276 | 26.6 | 0.124 | 50% |
| 827-944 | 118 | 1601 | 0.2319 | 27.1 | 0.113 | 38% |
| 945-1062 | 118 | 1555 | 0.2253 | 26.4 | 0.091 | 44% |
| 1063-1183 | 121 | 1354 | 0.1865 | 22.4 | 0.104 | 32% |

## 5. Solved vs. Open Subgraphs

**Cross-edges** (solved-open): 24761
**More clustered**: solved subgraph

| Metric | Solved | Open |
|--------|--------|------|
| n_nodes | 483 | 650 |
| n_edges | 8601 | 20600 |
| density | 0.0739 | 0.0977 |
| avg_degree | 35.6149 | 63.3846 |
| max_degree | 92 | 175 |
| clustering_coefficient | 0.1645 | 0.0819 |
| n_components | 1 | 1 |
| largest_component_frac | 1.0000 | 1.0000 |
| avg_shortest_path | 2.6458 | 2.5481 |

## 6. Solvability Prediction from Network Position

- **Accuracy**: 69.0%
- **AUC (approx)**: 0.765
- **Samples**: 1133 (483 solved, 650 open)

### Feature coefficients (standardized)

| Feature | Coefficient | Direction |
|---------|------------|-----------|
| intercept | -0.2991 | - |
| pagerank | -0.4693 | - |
| betweenness | +0.8153 | + |
| eigenvector | -0.3867 | - |
| degree | +0.6277 | + |
| n_tags | -0.3117 | - |
| community_solve_rate | +0.3816 | + |

### Top 20 open problems predicted most likely to be solved

| Rank | Problem | P(solved) |
|------|---------|-----------|
| 1 | #1145 | 0.953 |
| 2 | #483 | 0.925 |
| 3 | #508 | 0.922 |
| 4 | #197 | 0.897 |
| 5 | #358 | 0.890 |
| 6 | #973 | 0.878 |
| 7 | #373 | 0.865 |
| 8 | #524 | 0.833 |
| 9 | #1032 | 0.825 |
| 10 | #274 | 0.823 |
| 11 | #1156 | 0.817 |
| 12 | #934 | 0.802 |
| 13 | #531 | 0.786 |
| 14 | #62 | 0.780 |
| 15 | #200 | 0.775 |
| 16 | #902 | 0.770 |
| 17 | #271 | 0.768 |
| 18 | #906 | 0.766 |
| 19 | #990 | 0.743 |
| 20 | #346 | 0.734 |
