# Erdős Problem Resolution Predictions

Logistic regression model trained on solved/disproved problems
to predict which open problems are most likely to be resolved next.

## 1. Model Performance

- **5-fold CV accuracy**: 65.3%
- **Precision** (solved class): 51.0%
- **Recall** (solved class): 32.8%

### Per-Fold Results

| Fold | Accuracy | Precision | Recall |
|------|----------|-----------|--------|
| 1 | 64.1% | 50.0% | 28.6% |
| 2 | 63.6% | 41.8% | 37.1% |
| 3 | 63.6% | 53.5% | 31.1% |
| 4 | 68.2% | 54.5% | 36.4% |
| 5 | 67.2% | 55.3% | 30.9% |

## 2. Model Statistics

- Features: 24
- Training set (solved): 343
- Prediction set (open): 636
- Mean score (solved): 0.437
- Mean score (open): 0.376
- Score separation: 0.061

## 3. Feature Importance

| Rank | Feature | Importance |
|------|---------|-----------|
| 1 | avg_tag_solve_rate | 0.1301 |
| 2 | min_tag_solve_rate | 0.1249 |
| 3 | oeis_solved_bridges | 0.1242 |
| 4 | max_tag_solve_rate | 0.1138 |
| 5 | n_oeis | 0.0544 |
| 6 | tag_unit_fractions | 0.0529 |
| 7 | tag_sidon_sets | 0.0448 |
| 8 | tag_distances | 0.0404 |
| 9 | tag_graph_theory | 0.0327 |
| 10 | tag_additive_combinatorics | 0.0317 |
| 11 | n_tags | 0.0310 |
| 12 | technique_match_count | 0.0296 |
| 13 | tag_number_theory | 0.0254 |
| 14 | tag_primes | 0.0254 |
| 15 | tag_divisors | 0.0229 |

## 4. Top Predictions — Most Likely to Fall

| Rank | Problem | Predicted Solvability | Tags | Prize |
|------|---------|---------------------|------|-------|
| 1 | #256 | 0.588 | analysis | - |
| 2 | #509 | 0.588 | analysis | - |
| 3 | #510 | 0.588 | analysis | - |
| 4 | #513 | 0.588 | analysis | - |
| 5 | #514 | 0.588 | analysis | - |
| 6 | #517 | 0.588 | analysis | - |
| 7 | #973 | 0.588 | analysis | - |
| 8 | #990 | 0.588 | analysis | - |
| 9 | #996 | 0.588 | analysis | - |
| 10 | #1038 | 0.588 | analysis | - |
| 11 | #1039 | 0.588 | analysis | - |
| 12 | #1040 | 0.588 | analysis | - |
| 13 | #1044 | 0.588 | analysis | - |
| 14 | #1117 | 0.588 | analysis | - |
| 15 | #1120 | 0.588 | analysis | - |
| 16 | #671 | 0.586 | analysis | $250 |
| 17 | #114 | 0.584 | analysis, polynomials | - |
| 18 | #1129 | 0.584 | analysis, polynomials | - |
| 19 | #1130 | 0.584 | analysis, polynomials | - |
| 20 | #1131 | 0.584 | analysis, polynomials | - |
| 21 | #1132 | 0.584 | analysis, polynomials | - |
| 22 | #1133 | 0.584 | analysis, polynomials | - |
| 23 | #119 | 0.582 | analysis, polynomials | $100 |
| 24 | #1002 | 0.574 | analysis, diophantine approximation | - |
| 25 | #624 | 0.565 | combinatorics | - |

## 5. High-Value Targets (Prize × Solvability)

| Problem | Predicted Solvability | Prize | Expected Value |
|---------|---------------------|-------|---------------|
| #671 | 0.586 | $250 | $146 |
| #119 | 0.582 | $100 | $58 |
