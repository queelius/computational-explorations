# Meta-Conjectures: Structural Laws About Problem Ensembles

These are conjectures *about* the Erdős problem corpus itself —
patterns about patterns, laws about mathematical difficulty.

## 1. The Formalization Paradox — Causal Analysis
**Overall**: formalized solve rate = 0.186, unformalized = 0.473
**Gap**: 0.287 (non-formalized solve MORE)
**Mantel-Haenszel OR**: 0.232 (genuine_effect)
**Strata where paradox holds**: 24/24
**Strata where paradox reverses**: 0/24

### Per-Tag Stratification (top by gap magnitude)
- **additive basis**: form=0.0, no-form=0.667, gap=0.667 (n_form=12, n_noform=15)
- **complete sequences**: form=0.0, no-form=0.667, gap=0.667 (n_form=5, n_noform=3)
- **covering systems**: form=0.0, no-form=0.643, gap=0.643 (n_form=4, n_noform=14)
- **convex**: form=0.0, no-form=0.556, gap=0.556 (n_form=3, n_noform=9)
- **chromatic number**: form=0.0, no-form=0.523, gap=0.523 (n_form=8, n_noform=44)
- **cycles**: form=0.0, no-form=0.5, gap=0.5 (n_form=3, n_noform=18)
- **graph theory**: form=0.118, no-form=0.502, gap=0.384 (n_form=17, n_noform=233)
- **geometry**: form=0.05, no-form=0.429, gap=0.379 (n_form=20, n_noform=84)
- **combinatorics**: form=0.25, no-form=0.6, gap=0.35 (n_form=4, n_noform=40)
- **divisors**: form=0.2, no-form=0.55, gap=0.35 (n_form=10, n_noform=20)

## 2. Universal Solvability Scaling Law
**Logistic regression accuracy**: 0.608 (base rate: 0.412)
**Scaling interpretation**: older → harder; formalized → harder
**Coefficients**:
  - intercept: 0.1544
  - age_proxy: -0.3591
  - tag_count: -0.0902
  - oeis_count: -0.0905
  - prize: -0.0312
  - formalized: -1.3509
**Calibration**:
  - 0.0-0.2: predicted=0.185, actual=0.135 (n=111)
  - 0.2-0.4: predicted=0.214, actual=0.235 (n=187)
  - 0.4-0.6: predicted=0.489, actual=0.494 (n=784)

## 3. The Hard-Center Conjecture
**Spearman(tractability, impact)**: 0.158
**Pearson**: 0.087
**Hard center**: 5 problems
**Easy wins**: 4 problems
**Effect size**: weak
**Top hard-center problems**:
  - #30: tract=0.347, impact=11
  - #43: tract=0.348, impact=11
  - #155: tract=0.355, impact=11
  - #14: tract=0.346, impact=5
  - #530: tract=0.344, impact=5

## 4. Prize Monotonicity Theorem
**Is monotone**: False
**Kendall's tau**: 0.333
  - No prize: 58% open (n=987, avg_tags=1.6)
  - $1-$100: 51% open (n=35, avg_tags=1.6)
  - $101-$500: 68% open (n=47, avg_tags=2.0)
  - $501-$1000: 67% open (n=9, avg_tags=1.8)
  - $1000+: 75% open (n=4, avg_tags=2.0)

## 5. Solvability Phase Transition
**Has sharp transition**: False
**Transition point**: 0.351
**Transition width**: None
**Max gradient**: 0.148
**Solvability curve**:
  signal=0.276: #### (0.20, n=54)
  signal=0.277: #### (0.22, n=54)
  signal=0.294: #### (0.20, n=54)
  signal=0.300: ##### (0.30, n=54)
  signal=0.312: ###### (0.32, n=54)
  signal=0.318: ###### (0.33, n=54)
  signal=0.342: ######## (0.44, n=54)
  signal=0.343: ######## (0.41, n=54)
  signal=0.345: ####### (0.35, n=54)
  signal=0.351: ###### (0.33, n=54)
  signal=0.351: ####### (0.37, n=54)
  signal=0.351: ########## (0.50, n=54)
  signal=0.351: ######## (0.43, n=54)
  signal=0.351: ##### (0.28, n=54)
  signal=0.351: #### (0.20, n=54)
  signal=0.351: ### (0.17, n=54)
  signal=0.351: ### (0.18, n=54)
  signal=0.360: ##### (0.26, n=54)
  signal=0.367: ######## (0.41, n=54)
  signal=0.387: ######### (0.46, n=54)
  signal=0.392: ######## (0.44, n=54)
  signal=0.392: ######### (0.46, n=54)
  signal=0.404: ######## (0.41, n=54)
  signal=0.413: ######### (0.46, n=54)
  signal=0.416: ######## (0.43, n=54)
  signal=0.416: ######## (0.41, n=54)
  signal=0.418: ######### (0.46, n=54)
  signal=0.422: ######## (0.43, n=54)
  signal=0.425: ########## (0.50, n=54)
  signal=0.425: ######### (0.46, n=54)
  signal=0.433: ######## (0.41, n=54)
  signal=0.437: ########## (0.52, n=54)
  signal=0.441: ############ (0.61, n=54)
  signal=0.441: ############ (0.65, n=54)
  signal=0.441: ############ (0.65, n=54)
  signal=0.486: ############ (0.61, n=54)
  signal=0.510: ########### (0.56, n=54)
  signal=0.528: ########### (0.59, n=54)
  signal=0.568: ############# (0.67, n=54)

## 6. Tag Ecosystem Dynamics
**Active tags**: 26
**Average fitness**: 0.413 (std=0.1)
**Ecosystem diversity (bits)**: 3.739
**Dominant tags**:
  - **graph theory**: fitness=0.482, niche=270, dominance=3.894
  - **analysis**: fitness=0.551, niche=72, dominance=3.409
  - **number theory**: fitness=0.362, niche=542, dominance=3.288
  - **combinatorics**: fitness=0.581, niche=44, dominance=3.193
  - **unit fractions**: fitness=0.533, niche=48, dominance=2.995
  - **additive combinatorics**: fitness=0.438, niche=90, dominance=2.852
  - **ramsey theory**: fitness=0.412, niche=102, dominance=2.757
  - **chromatic number**: fitness=0.442, niche=57, dominance=2.591
  - **geometry**: fitness=0.366, niche=108, dominance=2.479
  - **hypergraphs**: fitness=0.48, niche=27, dominance=2.308
**Mutualistic pairs** (synergy in joint solve rate):
  - ('chromatic number', 'cycles'): joint=0.5, expected=0.199, synergy=0.301
  - ('distances', 'convex'): joint=0.375, expected=0.147, synergy=0.228
  - ('geometry', 'convex'): joint=0.417, expected=0.204, synergy=0.213
  - ('additive combinatorics', 'arithmetic progressions'): joint=0.375, expected=0.164, synergy=0.211
  - ('analysis', 'polynomials'): joint=0.444, expected=0.245, synergy=0.2

## 7. Problem Complexity Classes
**Separation quality**: good
**Monotone (E > M > H > U)**: False
  - **Class E**: 3 problems, solve rate=0.333, avg_prize=$0.0
  - **Class M**: 949 problems, solve rate=0.444, avg_prize=$15.0
  - **Class H**: 111 problems, solve rate=0.216, avg_prize=$181.1
  - **Class U**: 19 problems, solve rate=0.0, avg_prize=$1242.1
