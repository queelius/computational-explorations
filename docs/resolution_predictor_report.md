# Resolution Predictor: Which Problems Get Solved Next?

KNN-based resolution prediction for 636 open problems.

## 1. Model Performance (Leave-One-Out CV)

- **Accuracy**: 62.8%
- **Precision**: 55.9%
- **Recall**: 45.5%
- TP=203, FP=160, FN=243, TN=476

### Calibration
| Predicted Range | Actual Rate | Count |
|-----------------|-------------|-------|
| 0.0-0.1 | 21.3% | 47 |
| 0.1-0.2 | 29.6% | 71 |
| 0.2-0.3 | 27.9% | 208 |
| 0.3-0.4 | 43.9% | 132 |
| 0.4-0.5 | 36.8% | 261 |
| 0.5-0.6 | 57.4% | 216 |
| 0.6-0.7 | 52.9% | 87 |
| 0.7-0.8 | 55.6% | 45 |
| 0.8-0.9 | 53.3% | 15 |

## 2. Feature Importance

Baseline accuracy: 64.0%

| Feature | Importance | Permuted Accuracy |
|---------|------------|-------------------|
| tag_solve_rate | 0.100 █████████ | 54.0% |
| problem_age | 0.080 ███████ | 56.0% |
| oeis_richness | 0.045 ████ | 59.5% |
| tag_popularity | 0.045 ████ | 59.5% |
| prize_signal | 0.025 ██ | 61.5% |
| oeis_exclusivity | 0.025 ██ | 61.5% |
| tag_diversity | 0.020 ██ | 62.0% |

## 3. Most Likely to Be Solved (Open Problems)

| Rank | Problem | Probability | Tags | Prize | Nearest Solved |
|------|---------|-------------|------|-------|----------------|
| 1 | #837 | 87% | graph theory, hypergraphs | - | #834, #775, #808 |
| 2 | #450 | 80% | divisors, number theory | - | #449, #448, #444 |
| 3 | #778 | 80% | graph theory | - | #803, #804, #807 |
| 4 | #802 | 80% | graph theory | - | #803, #804, #807 |
| 5 | #805 | 80% | graph theory | - | #804, #803, #807 |
| 6 | #813 | 80% | graph theory | - | #814, #815, #816 |
| 7 | #934 | 80% | graph theory | - | #927, #926, #915 |
| 8 | #61 | 73% | graph theory | - | #73, #24, #22 |
| 9 | #62 | 73% | graph theory | - | #73, #24, #22 |
| 10 | #78 | 73% | graph theory, ramsey theory | $100 | #166, #140, #88 |
| 11 | #81 | 73% | graph theory | - | #73, #127, #133 |
| 12 | #120 | 73% | combinatorics | $100 | #21, #426, #56 |
| 13 | #149 | 73% | graph theory | - | #150, #136, #134 |
| 14 | #151 | 73% | graph theory | - | #150, #136, #134 |
| 15 | #256 | 73% | analysis | - | #227, #226, #225 |
| 16 | #400 | 73% | factorials, number theory | - | #401, #399, #403 |
| 17 | #477 | 73% | number theory | - | #480, #481, #471 |
| 18 | #488 | 73% | number theory | - | #487, #490, #491 |
| 19 | #489 | 73% | number theory | - | #490, #487, #491 |
| 20 | #507 | 73% | geometry | - | #505, #504, #606 |

## 4. Surprise Resolutions

**89 solved problems** with predicted probability ≤ 30%
(they were solved despite looking like they shouldn't have been).

| Problem | Predicted | Tags | Prize |
|---------|-----------|------|-------|
| #941 | 0% | number theory | - |
| #34 | 7% | number theory | - |
| #459 | 7% | number theory, primes | - |
| #526 | 7% | geometry, probability | - |
| #765 | 7% | graph theory, turan number | - |
| #861 | 7% | number theory, sidon sets | - |
| #897 | 7% | number theory | - |
| #937 | 7% | number theory | - |
| #946 | 7% | divisors, number theory | - |
| #981 | 7% | number theory | - |

### Stuck Problems
**27 open problems** with predicted probability ≥ 70%
(they should have been solved by now — something is blocking them).

| Problem | Predicted | Tags | Prize |
|---------|-----------|------|-------|
| #837 | 87% | graph theory, hypergraphs | - |
| #450 | 80% | divisors, number theory | - |
| #778 | 80% | graph theory | - |
| #802 | 80% | graph theory | - |
| #805 | 80% | graph theory | - |
| #813 | 80% | graph theory | - |
| #934 | 80% | graph theory | - |
| #61 | 73% | graph theory | - |
| #62 | 73% | graph theory | - |
| #78 | 73% | graph theory, ramsey theory | $100 |

## 5. Tag Resolution Forecast

| Tag | Expected Resolutions | Avg Prob | Open | Current Rate |
|-----|---------------------|----------|------|--------------|
| number theory | 107.4 | 32% | 335 | 38% |
| graph theory | 58.3 | 46% | 128 | 53% |
| geometry | 25.4 | 40% | 64 | 41% |
| ramsey theory | 22.9 | 40% | 57 | 44% |
| additive combinatorics | 18.3 | 37% | 50 | 44% |
| analysis | 15.5 | 50% | 31 | 57% |
| chromatic number | 14.7 | 51% | 29 | 49% |
| distances | 12.9 | 36% | 36 | 32% |
| unit fractions | 11.0 | 52% | 21 | 56% |
| primes | 8.9 | 25% | 36 | 27% |
| combinatorics | 8.9 | 49% | 18 | 59% |
| additive basis | 7.7 | 48% | 16 | 41% |
| sidon sets | 7.2 | 34% | 21 | 25% |
| divisors | 6.6 | 39% | 17 | 43% |
| irrationality | 6.3 | 42% | 15 | 32% |
