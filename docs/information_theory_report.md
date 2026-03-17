# Information-Theoretic Analysis

Applying information theory to discover which features carry
the most information about problem solvability.

## 1. Feature Mutual Information with Solvability

Base entropy of solvability: **0.9667 bits**

| Feature | MI (bits) | NMI | Entropy Reduction |
|---------|-----------|-----|-------------------|
| formalized | 0.053847 | 0.0592 | 5.6% |
| oeis_count | 0.016190 | 0.0216 | 1.7% |
| tag:primes | 0.005310 | 0.0107 | 0.5% |
| tag:number theory | 0.004981 | 0.0051 | 0.5% |
| tag:combinatorics | 0.003638 | 0.0076 | 0.4% |
| tag:analysis | 0.003631 | 0.0063 | 0.4% |
| tag:distances | 0.003434 | 0.0067 | 0.4% |
| tag:base representations | 0.003181 | 0.0160 | 0.3% |
| tag:powers | 0.002544 | 0.0141 | 0.3% |
| tag:topology | 0.002378 | 0.0177 | 0.2% |
| tag:iterated functions | 0.002288 | 0.0090 | 0.2% |
| tag:intersecting family | 0.002213 | 0.0111 | 0.2% |
| tag:graph theory | 0.002138 | 0.0024 | 0.2% |
| prize_bucket | 0.001903 | 0.0026 | 0.2% |
| tag:diophantine approximation | 0.001894 | 0.0083 | 0.2% |
| tag_count | 0.001875 | 0.0017 | 0.2% |
| tag:sidon sets | 0.001659 | 0.0041 | 0.2% |
| tag:unit fractions | 0.001496 | 0.0030 | 0.1% |
| tag:set theory | 0.001418 | 0.0037 | 0.1% |
| number_quartile | 0.001154 | 0.0008 | 0.1% |

## 2. Tag-Tag Mutual Information (Strongest Associations)

| Tag A | Tag B | MI (bits) | NMI |
|-------|-------|-----------|-----|
| graph theory | number theory | 0.263014 | 0.2958 |
| distances | geometry | 0.167048 | 0.4755 |
| chromatic number | graph theory | 0.090190 | 0.1891 |
| geometry | number theory | 0.088354 | 0.1313 |
| analysis | polynomials | 0.066047 | 0.3300 |
| graph theory | ramsey theory | 0.060118 | 0.1023 |
| analysis | number theory | 0.055497 | 0.0951 |
| chromatic number | number theory | 0.048785 | 0.0911 |
| number theory | unit fractions | 0.046572 | 0.0927 |
| distances | number theory | 0.045241 | 0.0868 |
| cycles | graph theory | 0.041054 | 0.1242 |
| graph theory | turan number | 0.039148 | 0.1207 |
| combinatorics | number theory | 0.037338 | 0.0768 |
| number theory | ramsey theory | 0.036882 | 0.0559 |
| convex | geometry | 0.036679 | 0.1873 |

## 3. Most Surprising Problem Outcomes

### Surprisingly Solved (solved despite prediction of open)

- **#4** (surprise=2.05 bits, P(solved)=0.24): number theory, primes
- **#6** (surprise=2.05 bits, P(solved)=0.24): number theory, primes
- **#427** (surprise=2.05 bits, P(solved)=0.24): number theory, primes
- **#379** (surprise=1.94 bits, P(solved)=0.26): binomial coefficients, number theory
- **#397** (surprise=1.94 bits, P(solved)=0.26): binomial coefficients, number theory
- **#259** (surprise=1.91 bits, P(solved)=0.27): irrationality
- **#266** (surprise=1.91 bits, P(solved)=0.27): irrationality
- **#229** (surprise=1.91 bits, P(solved)=0.27): analysis, iterated functions
- **#590** (surprise=1.91 bits, P(solved)=0.27): ramsey theory, set theory
- **#69** (surprise=1.86 bits, P(solved)=0.28): irrationality, number theory

### Surprisingly Open (open despite prediction of solved)


## 4. Redundancy Analysis

### Most Redundant Feature Pairs
- graph theory ↔ ramsey theory: MI=0.0601, redundancy=318749.2×
- number theory ↔ ramsey theory: MI=0.0369, redundancy=195550.4×
- ramsey theory ↔ set theory: MI=0.0120, redundancy=63745.3×
- chromatic number ↔ graph theory: MI=0.0902, redundancy=5075.6×
- chromatic number ↔ number theory: MI=0.0488, redundancy=2745.4×
- cycles ↔ graph theory: MI=0.0411, redundancy=2648.8×
- convex ↔ geometry: MI=0.0367, redundancy=2031.6×
- additive combinatorics ↔ arithmetic progressions: MI=0.0346, redundancy=1635.0×
- convex ↔ distances: MI=0.0224, redundancy=1242.4×
- cycles ↔ number theory: MI=0.0184, redundancy=1187.6×

### Most Complementary Feature Pairs
- distances + formalized: joint info=0.0568 bits
- analysis + formalized: joint info=0.0562 bits
- intersecting family + formalized: joint info=0.0560 bits
- powers + formalized: joint info=0.0558 bits
- topology + formalized: joint info=0.0554 bits
- base representations + primes: joint info=0.0082 bits
- powers + primes: joint info=0.0076 bits
- analysis + primes: joint info=0.0076 bits
- primes + topology: joint info=0.0076 bits
- intersecting family + primes: joint info=0.0072 bits

## 5. Tag Channel Capacity

| Tag | MI (bits) | Solve Entropy | Capacity Ratio | Problems |
|-----|-----------|--------------|----------------|----------|
| complete sequences | 0.466917 | 0.8113 | 57.55% | 8 |
| additive basis | 0.440792 | 0.9510 | 46.35% | 27 |
| diophantine approximation | 0.305958 | 0.8631 | 35.45% | 7 |
| convex | 0.236562 | 0.9799 | 24.14% | 12 |
| covering systems | 0.231461 | 0.9980 | 23.19% | 19 |
| probability | 0.224788 | 0.9911 | 22.68% | 9 |
| primitive sets | 0.169584 | 0.8631 | 19.65% | 7 |
| chromatic number | 0.115643 | 0.9730 | 11.89% | 57 |
| cycles | 0.114111 | 0.9760 | 11.69% | 22 |
| distances | 0.106584 | 0.8037 | 13.26% | 53 |
| divisors | 0.084645 | 0.9871 | 8.57% | 30 |
| geometry | 0.078966 | 0.9273 | 8.52% | 108 |
| binomial coefficients | 0.073912 | 0.8454 | 8.74% | 22 |
| intersecting family | 0.072906 | 0.7219 | 10.10% | 5 |
| hypergraphs | 0.066219 | 0.9911 | 6.68% | 27 |

## 6. Optimal Classification Tree

Greedy tree built by maximizing information gain at each split:

**Split on formalized** (IG=0.0538, n=1135)
  YES:
    **Split on tag:additive basis** (IG=0.0115, n=317)
      YES:
        → **open** (n=12, solve rate=0.0%)
      NO:
        **Split on tag:distances** (IG=0.0125, n=305)
          YES:
            → **open** (n=12, solve rate=0.0%)
          NO:
            **Split on tag:chromatic number** (IG=0.0090, n=293)
              YES:
                → **open** (n=8, solve rate=0.0%)
              NO:
                → **open** (n=285, solve rate=20.7%)
  NO:
    **Split on tag:distances** (IG=0.0038, n=818)
      YES:
        **Split on tag:convex** (IG=0.0180, n=41)
          YES:
            → **open** (n=6, solve rate=50.0%)
          NO:
            **Split on tag:geometry** (IG=0.0141, n=35)
              YES:
                → **open** (n=34, solve rate=29.4%)
              NO:
                → **open** (n=1, solve rate=0.0%)
      NO:
        **Split on tag:primes** (IG=0.0032, n=777)
          YES:
            **Split on tag:additive basis** (IG=0.0905, n=21)
              YES:
                → **solved** (n=1, solve rate=100.0%)
              NO:
                → **open** (n=20, solve rate=25.0%)
          NO:
            **Split on tag:diophantine approximation** (IG=0.0030, n=756)
              YES:
                → **solved** (n=6, solve rate=83.3%)
              NO:
                → **open** (n=750, solve rate=48.4%)

## 7. Tag Predictiveness (Status Entropy)

### Most Predictive Tags (lowest entropy)
- **base representations** (H=-0.000): open (5/5)
- **powers** (H=-0.000): open (4/4)
- **iterated functions** (H=0.503): open (8/9)
- **complete sequences** (H=0.811): open (6/8)
- **group theory** (H=0.811): open (3/4)
- **squares** (H=0.811): open (3/4)
- **primitive sets** (H=1.149): open (5/7)
- **sidon sets** (H=1.200): open (21/28)
- **primes** (H=1.230): open (36/49)
- **polynomials** (H=1.233): open (10/18)

### Least Predictive Tags (highest entropy)
- **factorials** (H=2.031): 6 distinct statuses
- **hypergraphs** (H=2.071): 6 distinct statuses
- **analysis** (H=2.086): 8 distinct statuses
- **graph theory** (H=2.108): 9 distinct statuses
- **unit fractions** (H=2.220): 8 distinct statuses
