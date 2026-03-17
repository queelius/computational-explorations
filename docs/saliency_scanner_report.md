# Saliency Scanner: Critical Threshold Problems

Finding open problems where a small advance would settle them.
Scanning 650 open Erdos problems across 5 dimensions.

## 1. Near-Resolved Problems (Active OEIS Computation)

Open problems with recently created OEIS sequences (A350000+),
indicating someone is actively extending computations.

| Rank | Problem | Score | Recent OEIS | Connections | Tags | Prize |
|------|---------|-------|-------------|-------------|------|-------|
| 1 | #82 | 0.950 | A390256, A390257 | 0 | graph theory | - |
| 2 | #374 | 0.948 | A388851, A387184, A389117 (+1) | 0 | number theory | - |
| 3 | #321 | 0.906 | A384927, A391592 | 1 | number theory, unit fractions | - |
| 4 | #1107 | 0.906 | A392342, A392343 | 1 | number theory, powerful | - |
| 5 | #202 | 0.891 | A389975 | 0 | covering systems | - |
| 6 | #380 | 0.867 | A388654, A387054, A389100 | 0 | number theory | - |
| 7 | #468 | 0.836 | A387502, A387503 | 1 | divisors, number theory | - |
| 8 | #421 | 0.762 | A389544, A390848 | 0 | number theory | - |
| 9 | #1109 | 0.762 | A392164, A392165 | 1 | number theory | - |
| 10 | #1148 | 0.762 | A390380, A393168 | 0 | number theory | - |
| 11 | #301 | 0.731 | A390394 | 0 | number theory, unit fractions | - |
| 12 | #302 | 0.731 | A390395 | 0 | number theory, unit fractions | - |
| 13 | #393 | 0.711 | A388302 | 0 | factorials, number theory | - |
| 14 | #727 | 0.711 | A389396 | 0 | factorials, number theory | - |
| 15 | #36 | 0.685 | A393584 | 0 | additive combinatorics, number theory | - |
| 16 | #693 | 0.674 | A391118 | 0 | divisors, number theory | - |
| 17 | #528 | 0.658 | A387897 | 0 | geometry | - |
| 18 | #168 | 0.641 | A386439 | 0 | additive combinatorics | - |
| 19 | #283 | 0.621 | A380791 | 0 | number theory, unit fractions | - |
| 20 | #327 | 0.621 | A384927 | 1 | number theory, unit fractions | - |

## 2. Frontier Problems (At the Solved Boundary)

Open problems whose tag-neighbours are solved. These sit at the
resolution frontier and may yield to the same techniques.

| Rank | Problem | Frontier Score | Solved Density | Tags | Prize |
|------|---------|----------------|----------------|------|-------|
| 1 | #20 | 0.777 | 1.000 | combinatorics | $1000 |
| 2 | #120 | 0.777 | 1.000 | combinatorics | $100 |
| 3 | #624 | 0.777 | 1.000 | combinatorics | - |
| 4 | #644 | 0.777 | 1.000 | combinatorics | - |
| 5 | #665 | 0.777 | 1.000 | combinatorics | - |
| 6 | #724 | 0.777 | 1.000 | combinatorics | - |
| 7 | #725 | 0.777 | 1.000 | combinatorics | - |
| 8 | #734 | 0.777 | 1.000 | combinatorics | - |
| 9 | #776 | 0.777 | 1.000 | combinatorics | - |
| 10 | #857 | 0.777 | 1.000 | combinatorics | - |
| 11 | #1159 | 0.777 | 1.000 | combinatorics | - |
| 12 | #256 | 0.773 | 1.000 | analysis | - |
| 13 | #509 | 0.773 | 1.000 | analysis | - |
| 14 | #510 | 0.773 | 1.000 | analysis | - |
| 15 | #513 | 0.773 | 1.000 | analysis | - |
| 16 | #514 | 0.773 | 1.000 | analysis | - |
| 17 | #517 | 0.773 | 1.000 | analysis | - |
| 18 | #671 | 0.773 | 1.000 | analysis | $250 |
| 19 | #973 | 0.773 | 1.000 | analysis | - |
| 20 | #990 | 0.773 | 1.000 | analysis | - |

### Frontier Problem per Tag Family

| Tag | Frontier Problem | Score | Solved Neighbours |
|-----|-----------------|-------|-------------------|
| combinatorics | #20 | 0.777 | 26 |
| analysis | #256 | 0.773 | 42 |
| polynomials | #114 | 0.736 | 42 |
| graph theory | #61 | 0.726 | 124 |
| additive combinatorics | #138 | 0.723 | 41 |
| number theory | #148 | 0.716 | 202 |
| unit fractions | #148 | 0.716 | 202 |
| chromatic number | #75 | 0.711 | 125 |
| ramsey theory | #77 | 0.711 | 143 |
| factorials | #373 | 0.710 | 202 |
| divisors | #450 | 0.699 | 202 |
| geometry | #101 | 0.694 | 42 |
| covering systems | #273 | 0.686 | 203 |
| distances | #89 | 0.673 | 42 |
| additive basis | #11 | 0.671 | 203 |
| irrationality | #257 | 0.597 | 8 |
| cycles | #60 | 0.584 | 124 |
| primes | #5 | 0.583 | 202 |
| group theory | #117 | 0.573 | 3 |
| turan number | #146 | 0.563 | 124 |

## 3. Technique Bottlenecks

Clusters of open problems blocked by the same technique gap.
Breaking one bottleneck may resolve many problems at once.

| Bottleneck | Description | Open Problems | Top Problem |
|------------|-------------|---------------|-------------|
| sieve_methods | Sieve theory / prime distribution | 299 | #9 |
| ramsey_partition | Ramsey / partition regularity | 59 | #70 |
| topological_geometric | Geometric / topological method | 52 | #89 |
| probabilistic_method | Probabilistic / random construction | 51 | #901 |
| fourier_analytic | Fourier analysis of subset structure | 42 | #1 |
| spectral_methods | Spectral / eigenvalue methods | 32 | #74 |
| extremal_counting | Extremal graph / Turan-type argument | 21 | #500 |
| algebraic_structure | Algebraic / polynomial method | 20 | #11 |
| density_increment | Density increment / regularity method | 15 | #3 |
| computational_search | Computational / exhaustive search | 14 | #60 |

### Tightly Coupled Problem Pairs (shared primary + secondary bottleneck)

| Problem A | Problem B | Shared Bottleneck | Secondary |
|-----------|-----------|-------------------|-----------|
| #1 | #14 | fourier_analytic | density_increment |
| #1 | #30 | fourier_analytic | density_increment |
| #1 | #36 | fourier_analytic | density_increment |
| #1 | #39 | fourier_analytic | density_increment |
| #1 | #41 | fourier_analytic | density_increment |
| #1 | #42 | fourier_analytic | density_increment |
| #1 | #43 | fourier_analytic | density_increment |
| #1 | #44 | fourier_analytic | density_increment |
| #1 | #52 | fourier_analytic | density_increment |
| #1 | #138 | fourier_analytic | density_increment |

## 4. Cross-Field Bridge Problems

Problems at the intersection of rarely-combined tags.
Technique import from the less-expected field often cracks these.

| Rank | Problem | Bridge Score | Bridge Pair | Pair Rate | Tags |
|------|---------|-------------|-------------|-----------|------|
| 1 | #141 | 0.650 | additive combinatorics + primes | 50% | additive combinatorics, arithmetic progressions, primes |
| 2 | #997 | 0.643 | analysis + primes | 0% | analysis, discrepancy, primes |
| 3 | #704 | 0.635 | geometry + graph theory | 0% | chromatic number, geometry, graph theory |
| 4 | #883 | 0.634 | graph theory + number theory | 0% | graph theory, number theory |
| 5 | #769 | 0.619 | geometry + number theory | 0% | geometry, number theory |
| 6 | #1145 | 0.551 | additive basis + additive combinatorics | 50% | additive basis, additive combinatorics |
| 7 | #3 | 0.503 | arithmetic progressions + number theory | 50% | additive combinatorics, arithmetic progressions, number theory |
| 8 | #529 | 0.463 | geometry + probability | 50% | geometry, probability |
| 9 | #757 | 0.461 | distances + sidon sets | 0% | distances, geometry, sidon sets |
| 10 | #18 | 0.455 | divisors + factorials | 0% | divisors, factorials, number theory |
| 11 | #1002 | 0.453 | analysis + diophantine approximation | 50% | analysis, diophantine approximation |
| 12 | #701 | 0.450 | combinatorics + intersecting family | 50% | combinatorics, intersecting family |
| 13 | #176 | 0.434 | additive combinatorics + discrepancy | 0% | additive combinatorics, arithmetic progressions, discrepancy |
| 14 | #1167 | 0.400 | probability + set theory | 0% | probability, set theory |
| 15 | #906 | 0.382 | analysis + iterated functions | 50% | analysis, iterated functions |
| 16 | #274 | 0.379 | covering systems + group theory | 0% | covering systems, group theory |
| 17 | #1107 | 0.363 | number theory + powerful | 50% | number theory, powerful |
| 18 | #1066 | 0.317 | graph theory + planar graphs | 67% | graph theory, planar graphs |
| 19 | #773 | 0.313 | sidon sets + squares | 0% | number theory, sidon sets, squares |
| 20 | #901 | 0.311 | combinatorics + hypergraphs | 80% | combinatorics, hypergraphs |

## 5. PREDICTION: Next 10 Problems to Fall

Ensemble combining KNN, OEIS activity, frontier proximity,
survival hazard, cross-field bridge potential, and community signals.

### #1: Problem #321
- **Tags**: number theory, unit fractions
- **Ensemble score**: 0.615
- **Dominant signal**: formalization (1.00)
- **Prize**: none
- **Formalized**: yes
- **WHY**: formalized (community attention); active OEIS computation (recency 0.95); neighbours are solved (frontier 0.92). Likely technique: Sieve theory / prime distribution

  Signal breakdown:
  - formalization: 1.000 ####################
  - near_resolved: 0.954 ###################
  - frontier_proximity: 0.922 ##################
  - survival_hazard: 0.791 ###############
  - knn_probability: 0.400 ########
  - bottleneck_relevance: 0.250 #####
  - cross_field_bridge: 0.044 
  - prize_signal: 0.000 

### #2: Problem #202
- **Tags**: covering systems
- **Ensemble score**: 0.566
- **Dominant signal**: near_resolved (0.94)
- **Prize**: none
- **Formalized**: no
- **WHY**: active OEIS computation (recency 0.94); structurally similar to solved problems (80%); timing suggests imminent resolution. Likely technique: Computational / exhaustive search

  Signal breakdown:
  - near_resolved: 0.938 ##################
  - knn_probability: 0.800 ################
  - survival_hazard: 0.566 ###########
  - frontier_proximity: 0.540 ##########
  - bottleneck_relevance: 0.250 #####
  - cross_field_bridge: 0.000 
  - prize_signal: 0.000 
  - formalization: 0.000 

### #3: Problem #727
- **Tags**: factorials, number theory
- **Ensemble score**: 0.565
- **Dominant signal**: formalization (1.00)
- **Prize**: none
- **Formalized**: yes
- **WHY**: formalized (community attention); timing suggests imminent resolution; neighbours are solved (frontier 0.91). Likely technique: Sieve theory / prime distribution

  Signal breakdown:
  - formalization: 1.000 ####################
  - survival_hazard: 0.948 ##################
  - frontier_proximity: 0.914 ##################
  - near_resolved: 0.748 ##############
  - knn_probability: 0.267 #####
  - bottleneck_relevance: 0.250 #####
  - cross_field_bridge: 0.070 #
  - prize_signal: 0.000 

### #4: Problem #495
- **Tags**: diophantine approximation, number theory
- **Ensemble score**: 0.564
- **Dominant signal**: formalization (1.00)
- **Prize**: none
- **Formalized**: yes
- **WHY**: formalized (community attention); timing suggests imminent resolution; structurally similar to solved problems (87%). Likely technique: Sieve theory / prime distribution

  Signal breakdown:
  - formalization: 1.000 ####################
  - survival_hazard: 0.973 ###################
  - knn_probability: 0.867 #################
  - frontier_proximity: 0.694 #############
  - cross_field_bridge: 0.348 ######
  - bottleneck_relevance: 0.250 #####
  - near_resolved: 0.000 
  - prize_signal: 0.000 

### #5: Problem #663
- **Tags**: number theory
- **Ensemble score**: 0.555
- **Dominant signal**: survival_hazard (0.99)
- **Prize**: none
- **Formalized**: no
- **WHY**: timing suggests imminent resolution; neighbours are solved (frontier 0.88); active OEIS computation (recency 0.65). Likely technique: Sieve theory / prime distribution

  Signal breakdown:
  - survival_hazard: 0.985 ###################
  - frontier_proximity: 0.878 #################
  - near_resolved: 0.648 ############
  - knn_probability: 0.533 ##########
  - bottleneck_relevance: 0.250 #####
  - cross_field_bridge: 0.000 
  - prize_signal: 0.000 
  - formalization: 0.000 

### #6: Problem #488
- **Tags**: number theory
- **Ensemble score**: 0.553
- **Dominant signal**: survival_hazard (1.17)
- **Prize**: none
- **Formalized**: yes
- **WHY**: timing suggests imminent resolution; formalized (community attention); neighbours are solved (frontier 0.88). Likely technique: Sieve theory / prime distribution

  Signal breakdown:
  - survival_hazard: 1.169 #######################
  - formalization: 1.000 ####################
  - frontier_proximity: 0.878 #################
  - knn_probability: 0.733 ##############
  - bottleneck_relevance: 0.250 #####
  - near_resolved: 0.000 
  - cross_field_bridge: 0.000 
  - prize_signal: 0.000 

### #7: Problem #472
- **Tags**: number theory
- **Ensemble score**: 0.551
- **Dominant signal**: survival_hazard (0.96)
- **Prize**: none
- **Formalized**: no
- **WHY**: timing suggests imminent resolution; neighbours are solved (frontier 0.88); active OEIS computation (recency 0.65). Likely technique: Sieve theory / prime distribution

  Signal breakdown:
  - survival_hazard: 0.959 ###################
  - frontier_proximity: 0.878 #################
  - near_resolved: 0.648 ############
  - knn_probability: 0.533 ##########
  - bottleneck_relevance: 0.250 #####
  - cross_field_bridge: 0.000 
  - prize_signal: 0.000 
  - formalization: 0.000 

### #8: Problem #421
- **Tags**: number theory
- **Ensemble score**: 0.542
- **Dominant signal**: formalization (1.00)
- **Prize**: none
- **Formalized**: yes
- **WHY**: formalized (community attention); timing suggests imminent resolution; neighbours are solved (frontier 0.88). Likely technique: Sieve theory / prime distribution

  Signal breakdown:
  - formalization: 1.000 ####################
  - survival_hazard: 0.917 ##################
  - frontier_proximity: 0.878 #################
  - near_resolved: 0.803 ################
  - bottleneck_relevance: 0.250 #####
  - knn_probability: 0.200 ####
  - cross_field_bridge: 0.000 
  - prize_signal: 0.000 

### #9: Problem #393
- **Tags**: factorials, number theory
- **Ensemble score**: 0.539
- **Dominant signal**: frontier_proximity (0.91)
- **Prize**: none
- **Formalized**: no
- **WHY**: neighbours are solved (frontier 0.91); timing suggests imminent resolution; active OEIS computation (recency 0.75). Likely technique: Sieve theory / prime distribution

  Signal breakdown:
  - frontier_proximity: 0.914 ##################
  - survival_hazard: 0.887 #################
  - near_resolved: 0.748 ##############
  - knn_probability: 0.400 ########
  - bottleneck_relevance: 0.250 #####
  - cross_field_bridge: 0.070 #
  - prize_signal: 0.000 
  - formalization: 0.000 

### #10: Problem #812
- **Tags**: graph theory, ramsey theory
- **Ensemble score**: 0.530
- **Dominant signal**: formalization (1.00)
- **Prize**: none
- **Formalized**: yes
- **WHY**: formalized (community attention); neighbours are solved (frontier 0.92); timing suggests imminent resolution. Likely technique: Ramsey / partition regularity

  Signal breakdown:
  - formalization: 1.000 ####################
  - frontier_proximity: 0.915 ##################
  - survival_hazard: 0.861 #################
  - knn_probability: 0.733 ##############
  - bottleneck_relevance: 0.550 ###########
  - cross_field_bridge: 0.026 
  - near_resolved: 0.000 
  - prize_signal: 0.000 
