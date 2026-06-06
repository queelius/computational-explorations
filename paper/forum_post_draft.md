# Forum post draft for erdosproblems.com — AI Contributions thread

**Disclosure: This work was done with extensive AI assistance (Claude, Anthropic Opus 4.6). The computational pipeline, analysis code, and all outputs were primarily produced by Claude. I directed the research and built the verification infrastructure. I am not a number theorist and cannot personally vouch for the mathematical claims — if any of this is wrong or trivial, I apologize for the noise.**

---

I'm a CS PhD student who used AI to do a tag-based exploratory analysis of the Erdős problem corpus (all 1,135 problems in the database). I wanted to share the methodology and some things it surfaced, in case any of it is useful.

## What I did

I built a pipeline that:
- Parsed the full problem corpus and extracted tags, status, OEIS references, and metadata
- Constructed a tag-based proximity graph (problems sharing tags or OEIS sequences are connected — this is NOT a causal dependency graph, just structural similarity)
- Clustered problems into 52 families via spectral methods on the tag similarity matrix
- Scored problems on solve-rate patterns across tags
- Looked for tag pairs whose joint solve rate differs from individual rates

This is fundamentally a bibliometric / tag co-occurrence analysis — it rediscovers the tag structure rather than finding hidden mathematical dependencies. The pipeline has ~1,830 automated tests.

## Things the analysis surfaced

The methodology also flagged three gaps in the literature that led to what might be novel problems. One (the density-relaxed Schur number DS(2, 1/2) = 5) has a complete Lean 4 formalization with 0 sorry statements. The other Lean files are partial (14 sorry total across 3 files). I'm not qualified to judge whether the mathematics is correct or trivial — number theory is not my field (my background is M.S. Mathematics, M.S. Computer Science, Ph.D. student in CS).

Briefly:
1. A density-relaxed variant of Schur numbers with a sharp phase transition at α = 1/k (Lean: complete, 0 sorry)
2. Ramsey numbers on the coprime graph (R_cop(3) = 11 by exhaustive search, if the code is right)
3. An optimization of coprime pair counts over primitive sets where primes are not optimal

If any of these are known, trivial, or wrong, I'd genuinely appreciate being told — I don't want to waste anyone's time. Code is on GitHub; details on Zenodo under my name.

— Alexander Towell, SIUE (M.S. Mathematics, M.S. Computer Science, Ph.D. student in CS — number theory is not my forte, so corrections are especially welcome)

Thanks for building this database — it's a remarkable resource.
