# Dependency Graph Analysis

Directed dependency graph: 1135 nodes, 132705 edges

## 1. Graph Structure

| Edge Type | Count | Weight |
|-----------|-------|--------|
| oeis_bridge | 96668 | 3 |
| tag_containment | 34097 | 2 |
| oeis_cooccurrence | 1940 | 1 |

## 2. Strongly Connected Components

Total SCCs: 620 (1 with >1 member)

| SCC | Size | Sample Members |
|-----|------|----------------|
| 1 | 516 | #1, #3, #5, #14, #15 (+511 more) |

## 3. Topological Layers

Maximum depth: 471

| Layer | Problems | Description |
|-------|----------|-------------|
| 0 | 568 | Source (no dependencies) |
| 1 | 9 | Depth 1 |
| 2 | 0 | Depth 2 |
| 3 | 1 | Depth 3 |
| 4 | 0 | Depth 4 |
| 5 | 0 | Depth 5 |
| 6 | 0 | Depth 6 |
| 7 | 1 | Depth 7 |
| 8 | 0 | Depth 8 |
| 9 | 0 | Depth 9 |

## 4. Keystone Problems

| Problem | Downstream | Tags | Prize |
|---------|-----------|------|-------|
| #51 | 559 open | number theory | - |
| #145 | 559 open | number theory | - |
| #416 | 559 open | number theory | - |
| #457 | 559 open | number theory | - |
| #687 | 559 open | number theory | $1000 |
| #1103 | 559 open | number theory | - |
| #12 | 558 open | number theory | - |
| #20 | 558 open | combinatorics | $1000 |
| #82 | 558 open | graph theory | - |
| #86 | 558 open | graph theory | $100 |
| #104 | 558 open | geometry | $100 |
| #131 | 558 open | number theory | - |
| #138 | 558 open | additive combinatorics | $500 |
| #156 | 558 open | sidon sets | - |
| #168 | 558 open | additive combinatorics | - |

## 5. Critical Paths (Longest Dependency Chains)

### Chain 1 (length 474)
- Path: #51 → #821 → #1 → #3 → #142 → #201 → #217 → #252 → ...
- Tags: additive basis, additive combinatorics, analysis, arithmetic progressions, base representations
- Total prize: $29525

### Chain 2 (length 474)
- Path: #145 → #208 → #1 → #3 → #142 → #201 → #217 → #252 → ...
- Tags: additive basis, additive combinatorics, analysis, arithmetic progressions, base representations
- Total prize: $29525

### Chain 3 (length 474)
- Path: #416 → #417 → #1 → #3 → #142 → #201 → #217 → #252 → ...
- Tags: additive basis, additive combinatorics, analysis, arithmetic progressions, base representations
- Total prize: $29525

### Chain 4 (length 474)
- Path: #457 → #663 → #1 → #3 → #142 → #201 → #217 → #252 → ...
- Tags: additive basis, additive combinatorics, analysis, arithmetic progressions, base representations
- Total prize: $29525

### Chain 5 (length 474)
- Path: #687 → #854 → #1 → #3 → #142 → #201 → #217 → #252 → ...
- Tags: additive basis, additive combinatorics, analysis, arithmetic progressions, base representations
- Total prize: $30525

## 6. Orphan Problems (No Dependencies)

Total orphans: 69 (must be attacked directly)

| Problem | Tags | Prize | Out-Degree |
|---------|------|-------|-----------|
| #51 | number theory | - | 171 |
| #145 | number theory | - | 171 |
| #367 | number theory | - | 171 |
| #368 | number theory | - | 171 |
| #416 | number theory | - | 171 |
| #457 | number theory | - | 171 |
| #687 | number theory | $1000 | 171 |
| #1103 | number theory | - | 171 |
| #131 | number theory | - | 170 |
| #342 | number theory | - | 170 |
| #359 | number theory | - | 170 |
| #365 | number theory | - | 170 |
| #371 | number theory | - | 170 |
| #374 | number theory | - | 170 |
| #380 | number theory | - | 170 |

## 7. Influence Flow Simulation

Seed problems: #51
Total influenced: 559 problems

| Wave | New Problems | Sample |
|------|-------------|--------|
| 1 | 171 | #1, #3, #5, #9, #10 |
| 2 | 121 | #25, #38, #50, #60, #61 |
| 3 | 176 | #77, #78, #89, #90, #91 |
| 4 | 76 | #101, #117, #120, #122, #123 |
| 5 | 15 | #200, #616, #619, #623, #783 |

### Influenced Tags
- **number theory**: 275 problems
- **graph theory**: 124 problems
- **geometry**: 61 problems
- **ramsey theory**: 57 problems
- **additive combinatorics**: 46 problems
- **primes**: 36 problems
- **distances**: 36 problems
- **analysis**: 31 problems
- **chromatic number**: 29 problems
- **unit fractions**: 21 problems
