# Cross-Analysis: Third-Order Synthesis

Combining all analysis modules to discover patterns visible only
from multiple perspectives simultaneously.

## 1. Unified Opportunity Score (Top 20)

| Rank | Problem | Unified | Vuln | Predicted | PageRank | Cascade | Prize |
|------|---------|---------|------|-----------|----------|---------|-------|
| 1 | #39 | 0.666 | 0.612 | 0.261 | 0.919 | 1.000 | $500 |
| 2 | #41 | 0.666 | 0.612 | 0.261 | 0.919 | 1.000 | $500 |
| 3 | #43 | 0.616 | 0.645 | 0.212 | 0.961 | 0.880 | $100 |
| 4 | #563 | 0.606 | 0.641 | 0.443 | 0.908 | 0.996 | - |
| 5 | #74 | 0.592 | 0.639 | 0.493 | 0.000 | 0.996 | $500 |
| 6 | #80 | 0.570 | 0.672 | 0.460 | 0.879 | 0.777 | - |
| 7 | #550 | 0.570 | 0.672 | 0.460 | 0.879 | 0.777 | - |
| 8 | #42 | 0.569 | 0.662 | 0.263 | 0.919 | 1.000 | - |
| 9 | #44 | 0.569 | 0.662 | 0.263 | 0.919 | 1.000 | - |
| 10 | #625 | 0.551 | 0.603 | 0.492 | 0.000 | 0.777 | $1000 |
| 11 | #70 | 0.550 | 0.631 | 0.406 | 0.903 | 0.777 | - |
| 12 | #596 | 0.550 | 0.631 | 0.406 | 0.903 | 0.777 | - |
| 13 | #597 | 0.550 | 0.631 | 0.406 | 0.903 | 0.777 | - |
| 14 | #282 | 0.547 | 0.583 | 0.457 | 0.880 | 0.777 | - |
| 15 | #288 | 0.547 | 0.583 | 0.457 | 0.880 | 0.777 | - |
| 16 | #289 | 0.547 | 0.583 | 0.457 | 0.880 | 0.777 | - |
| 17 | #306 | 0.547 | 0.583 | 0.457 | 0.880 | 0.777 | - |
| 18 | #311 | 0.547 | 0.583 | 0.457 | 0.880 | 0.777 | - |
| 19 | #312 | 0.547 | 0.583 | 0.457 | 0.880 | 0.777 | - |
| 20 | #317 | 0.547 | 0.583 | 0.457 | 0.880 | 0.777 | - |

## 2. Most Interesting Problems (High Model Disagreement)

Problems where different scoring systems strongly disagree —
these are the most structurally unusual and worth investigating.

| Problem | Disagreement | Vuln | Pred | PR | Cascade | Tags |
|---------|-------------|------|------|-----|---------|------|
| #74 | 0.1278 | 0.639 | 0.493 | 0.000 | 0.996 | chromatic number, cycles |
| #108 | 0.1051 | 0.689 | 0.495 | 0.000 | 0.868 | chromatic number, cycles |
| #626 | 0.1051 | 0.689 | 0.495 | 0.000 | 0.868 | chromatic number, cycles |
| #564 | 0.0986 | 0.591 | 0.441 | 0.000 | 0.868 | graph theory, hypergraphs |
| #683 | 0.0916 | 0.560 | 0.215 | 1.000 | 0.868 | binomial coefficients, number theory |
| #685 | 0.0890 | 0.560 | 0.265 | 0.945 | 0.996 | binomial coefficients, number theory |
| #61 | 0.0871 | 0.646 | 0.531 | 0.000 | 0.777 | graph theory |
| #28 | 0.0857 | 0.592 | 0.323 | 0.000 | 0.777 | additive basis, number theory |
| #40 | 0.0857 | 0.592 | 0.323 | 0.000 | 0.777 | additive basis, number theory |
| #66 | 0.0857 | 0.592 | 0.323 | 0.000 | 0.777 | additive basis, number theory |
| #43 | 0.0848 | 0.645 | 0.212 | 0.961 | 0.880 | additive combinatorics, number theory |
| #39 | 0.0846 | 0.612 | 0.261 | 0.919 | 1.000 | additive combinatorics, number theory |
| #41 | 0.0846 | 0.612 | 0.261 | 0.919 | 1.000 | additive combinatorics, number theory |
| #625 | 0.0833 | 0.603 | 0.492 | 0.000 | 0.777 | chromatic number, graph theory |
| #50 | 0.0830 | 0.574 | 0.352 | 0.000 | 0.777 | number theory |

## 3. Strategic Research Roadmap

### Quick Wins (high solvability, low barrier)

- **#256** (pred=0.588): analysis
- **#509** (pred=0.588): analysis
- **#510** (pred=0.588): analysis
- **#513** (pred=0.588): analysis
- **#514** (pred=0.588): analysis
- **#517** (pred=0.588): analysis
- **#973** (pred=0.588): analysis
- **#990** (pred=0.588): analysis

### Strategic Targets (influential + solvable)

- **#39** (unified=0.666, cascade=1.000): additive combinatorics, number theory, sidon sets
- **#41** (unified=0.666, cascade=1.000): additive combinatorics, number theory, sidon sets
- **#43** (unified=0.616, cascade=0.880): additive combinatorics, number theory, sidon sets
- **#563** (unified=0.606, cascade=0.996): graph theory, hypergraphs, ramsey theory
- **#74** (unified=0.592, cascade=0.996): chromatic number, cycles, graph theory
- **#42** (unified=0.569, cascade=1.000): additive combinatorics, number theory, sidon sets
- **#44** (unified=0.569, cascade=1.000): additive combinatorics, number theory, sidon sets
- **#625** (unified=0.551, cascade=0.777): chromatic number, graph theory

### Prize Hunts

- **#142** ($10000, pred=0.334): additive combinatorics, arithmetic progressions
- **#20** ($1000, pred=0.485): combinatorics
- **#711** ($1000, pred=0.352): number theory
- **#138** ($500, pred=0.432): additive combinatorics
- **#713** ($500, pred=0.431): graph theory, turan number
- **#712** ($500, pred=0.421): graph theory, hypergraphs, turan number
- **#500** ($500, pred=0.348): graph theory, hypergraphs, turan number
- **#1** ($500, pred=0.344): additive combinatorics, number theory

### Moonshots (high impact, difficult)

- **#3** ($5000, cascade=0.235): additive combinatorics, arithmetic progressions, number theory
- **#710** ($2000, cascade=0.000): number theory
- **#687** ($1000, cascade=0.000): number theory

## 4. Problem Genomes (Top 10)

### #39
- Tags: additive combinatorics, number theory, sidon sets
- Prize: $500
- Vulnerability: 0.612
- OEIS bridges: 215
- Technique matches: 5
- Tag synergy: additive combinatorics × number theory = +0.091

### #41
- Tags: additive combinatorics, number theory, sidon sets
- Prize: $500
- Vulnerability: 0.612
- OEIS bridges: 215
- Technique matches: 5
- Tag synergy: additive combinatorics × number theory = +0.091

### #43
- Tags: additive combinatorics, number theory, sidon sets
- Prize: $100
- Vulnerability: 0.645
- OEIS bridges: 81
- Technique matches: 5
- Tag synergy: additive combinatorics × number theory = +0.091

### #563
- Tags: graph theory, hypergraphs, ramsey theory
- Vulnerability: 0.641
- OEIS bridges: 215
- Technique matches: 4

### #74
- Tags: chromatic number, cycles, graph theory
- Prize: $500
- Vulnerability: 0.639
- OEIS bridges: 215
- Technique matches: 5
- Tag synergy: chromatic number × cycles = +0.182

### #80
- Tags: graph theory, ramsey theory
- Vulnerability: 0.672
- OEIS bridges: 215
- Technique matches: 4

### #550
- Tags: graph theory, ramsey theory
- Vulnerability: 0.672
- OEIS bridges: 215
- Technique matches: 4

### #42
- Tags: additive combinatorics, number theory, sidon sets
- Vulnerability: 0.662
- OEIS bridges: 215
- Technique matches: 5
- Tag synergy: additive combinatorics × number theory = +0.091

### #44
- Tags: additive combinatorics, number theory, sidon sets
- Vulnerability: 0.662
- OEIS bridges: 215
- Technique matches: 5
- Tag synergy: additive combinatorics × number theory = +0.091

### #625
- Tags: chromatic number, graph theory
- Prize: $1000
- Vulnerability: 0.603
- OEIS bridges: 215
- Technique matches: 4

## 5. Hidden Structures

### Dark Horses (ML predicts solvable, structure says hard)

- **#202**: pred=0.563 vs vuln=0.256

### False Positives (structure says easy, ML says hard)

- **#43**: vuln=0.645 vs pred=0.212
- **#530**: vuln=0.623 vs pred=0.196
- **#14**: vuln=0.662 vs pred=0.245
- **#425**: vuln=0.623 vs pred=0.211
- **#42**: vuln=0.662 vs pred=0.263

### Influence Orphans (important but unsolvable)

- **#683**: PageRank=1.000, pred=0.215
- **#201**: PageRank=0.963, pred=0.368
- **#43**: PageRank=0.961, pred=0.212
- **#685**: PageRank=0.945, pred=0.265
- **#404**: PageRank=0.923, pred=0.363
