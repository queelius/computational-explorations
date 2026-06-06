# Interdisciplinary Open Problems Survey: Domains 9--13

*Compiled 2026-03-18. Each problem includes precise statement, current best results, computational attack vectors, verification approaches, feasibility ratings, and bridge value.*

---

## Domain 9: Coding Theory <-> Combinatorics

### 9.1 The MDS Conjecture (Main Conjecture)

**Name and reference:** MDS Conjecture (Segre 1955; extended by various authors).

**Statement:** Over a finite field F_q, the maximum length n of a non-trivial [n,k,n-k+1]_q MDS code satisfies n <= q+1, except when q is even and k=3 or k=q-1, in which case n <= q+2.

**Current best results:** The conjecture is proved for k <= 2p-2 where p = char(F_q) (Ball, 2012). The GM-MDS conjecture (that the MDS condition on generator matrices is achievable over small fields) was proved by Lovett (2018) and Yildiz-Hassibi (2019). For prime fields, the conjecture holds for k <= p. For general fields, it remains open when k is large relative to q. Non-Reed-Solomon MDS codes from elliptic curves have been constructed (Wang-Liu, 2025), providing evidence that the MDS landscape is richer than previously thought.

**Computational attack vector:**
- Exhaustive search for MDS codes over small fields F_q for moderate q (say q <= 32) and all dimensions k, verifying or refuting the bound.
- SAT/SMT encoding: encode the MDS property as a constraint satisfaction problem---every k x k minor of the generator matrix must be nonsingular. For fixed q and moderate n, this is feasible.
- Computer algebra (Magma/SageMath): systematic enumeration of arcs in PG(k-1,q), since MDS codes correspond to arcs.

**Verification approach:** Exact computation over finite fields is fully rigorous. For small parameters, exhaustive enumeration yields proofs. Lean formalization of the algebraic framework (matroid theory over finite fields) is feasible but nontrivial.

**Feasibility rating:** HIGH for small field sizes (q <= 32, moderate k). MEDIUM for extending Ball's bound computationally. LOW for the full conjecture.

**Bridge value:** Connects coding theory's fundamental length-vs-distance tradeoff with finite geometry (arcs in projective spaces) and combinatorial design theory. Progress on either side---better arc constructions or better coding bounds---immediately transfers.

---

### 9.2 List Decoding Capacity over Constant-Sized Fields

**Name and reference:** List decoding capacity conjecture (Guruswami-Sudan framework, c. 2000; AG code achievement: Brakensiek-Gopi-Makam, 2023; Alrabiah-Guruswami-Li, 2024).

**Statement:** For any rate R and epsilon > 0, does there exist an explicit code over a field of size O_epsilon(1) that is (1-R-epsilon)-list-decodable with list size O(1/epsilon)?

**Current best results:** AG codes achieve list-decoding capacity over constant-sized fields (STOC 2024). Folded RS codes achieve capacity with optimal O(1/epsilon) list size but require field size poly(n). A major remaining gap: achieving these parameters with *linear* codes over constant-sized fields. The optimal field size for (n,k)-MDS(L) codes has bounds of the form exp(Omega(n)) to exp(O(nL)), and closing this gap is open.

**Computational attack vector:**
- Implement AG code list decoders and benchmark against random linear codes to identify the practical performance gap.
- Exhaustive search for short list-decodable codes over small fields, tabulating the list-decoding radius as a function of rate and field size.
- Search for algebraic curves with extremal properties (many rational points, low genus) that yield good AG codes via computer algebra.

**Verification approach:** Decoding experiments yield statistical evidence. Exact computation of minimum distances and list sizes for short codes is rigorous. Lean formalization of the list-decoding capacity theorem is a significant but tractable project.

**Feasibility rating:** HIGH for experimental benchmarking. MEDIUM for finding improved explicit constructions. LOW for proving new capacity results.

**Bridge value:** Bridges algebraic geometry (curves over finite fields) with combinatorial coding theory (Johnson bound, list-size combinatorics). Improvements in either Ihara's constant or combinatorial list-size bounds translate directly.

---

### 9.3 Locally Decodable Codes: Optimal Rate-Query Tradeoff

**Name and reference:** LDC rate-query tradeoff conjecture (Katz-Trevisan 2000; Yekhanin 2007; Efremenko 2009; Dvir-Gopi 2016).

**Statement:** What is the optimal length N(k,q) of a q-query binary locally decodable code encoding k-bit messages? Is it true that for constant q >= 3, we must have N = exp(k^{Omega(1)})?

**Current best results:** For q=2, N >= k^2 (Kerenidis-de Wolf, 2003) and this is tight. For q=3, the best constructions give N = exp(k^{o(1)}) (matching sets approach). For q >= 3, best lower bound is N = Omega-tilde(k^{(q+1)/(q-1)}) from the 2-query reduction framework. In 2025, nearly tight lower bounds for relaxed LDCs were proved: any q-query linear RLDC must have n = k^{1+Omega(1/q)}, closely matching the upper bound n = k^{1+O(1/q)}.

**Computational attack vector:**
- Exhaustive search for short LDCs with 3 queries over small message lengths.
- Reduction to matching vector families: computationally search for large matching vector families over Z_m^n for small m, n.
- Linear programming/SDP relaxations of the LDC length problem.

**Verification approach:** Any code found is verifiable by checking the local decoding property. Lower bounds require proof, but computer-assisted proofs (LP/SDP certificates) can provide rigorous bounds for specific parameters. Lean formalization of the information-theoretic lower bounds is feasible.

**Feasibility rating:** HIGH for tabulating small cases. MEDIUM for improving matching vector constructions computationally. LOW for resolving the exponential vs. sub-exponential question.

**Bridge value:** Connects coding theory's local correction paradigm with combinatorics (matching vector families, additive combinatorics in Z_m^n) and complexity theory (private information retrieval). LDCs are the coding-theoretic face of deep combinatorial structure.

---

### 9.4 Reed-Muller Codes: Block Error Rate Capacity

**Name and reference:** Reed-Muller capacity conjecture (folklore, formalized by Abbe-Shpilka-Ye, 2020; partially resolved by Abbe-Sandon 2023; Reeves-Pfister 2023).

**Statement:** Do Reed-Muller codes achieve capacity on every binary memoryless symmetric (BMS) channel under MAP decoding, in the strong sense that block error probability vanishes?

**Current best results:** RM codes achieve capacity in the *bit error* sense: for any BMS channel of capacity C and any RM code sequence with rate R < C, the bit-MAP error probability vanishes (Reeves-Pfister, 2023; Abbe-Sandon, 2023). The *block error* question remains open. RM codes achieve capacity on the BEC (Kudekar-Kumar-Mondelli-Pfister-Sasoglu-Urbanke, 2017). Efficient ML decoding remains open.

**Computational attack vector:**
- Monte Carlo simulation of RM codes under BMS channels at moderate block lengths (n = 64, 128, 256, 512) to estimate block error rates at rates near capacity.
- Weight distribution computation for RM codes using the recursive structure, comparing with random codes.
- Implement successive-cancellation-like decoders specific to RM codes and benchmark gap to ML decoding.

**Verification approach:** Simulation provides statistical evidence. Exact weight enumerator computation for small RM codes is rigorous. A Lean formalization of the bit-MAP result would be ambitious but structured.

**Feasibility rating:** HIGH for simulation and weight enumeration at moderate lengths. MEDIUM for algorithmic improvements to decoding. LOW for proving block error vanishing.

**Bridge value:** RM codes sit at the intersection of Boolean function analysis (algebraic combinatorics), probability theory (sharp threshold phenomena), and information theory (channel coding). Progress on the combinatorial side (weight distribution, symmetry) feeds coding-theoretic conclusions and vice versa.

---

### 9.5 LDPC Threshold Conjectures

**Name and reference:** LDPC threshold conjecture / MAP threshold conjecture (Richardson-Urbanke 2001; Measson-Montanari-Richardson-Urbanke 2009).

**Statement:** For a given LDPC ensemble over a BMS channel, does the MAP decoding threshold equal the conjectured value derived from the area theorem and the EXIT chart analysis? More precisely, is the MAP threshold of a standard (lambda, rho) LDPC ensemble equal to the value at which the GEXIT curve area equals the design rate?

**Current best results:** The MAP threshold is known to satisfy the area theorem bound. For specific regular LDPC ensembles, the BP threshold and MAP threshold are known to be close. Spatial coupling achieves the MAP threshold (Kudekar-Richardson-Urbanke, 2011), establishing "threshold saturation." The conjectured exact MAP thresholds remain unproven for most ensembles. In 2025, quantum LDPC codes approaching the hashing bound with efficient decoding were demonstrated.

**Computational attack vector:**
- Density evolution computation for specific LDPC ensembles to high precision (using the discretized density evolution algorithm).
- Monte Carlo simulation at large block lengths to estimate thresholds.
- Implement the GEXIT kernel computation and verify the area theorem predictions.
- SAT-based verification of small LDPC code properties (stopping sets, trapping sets).

**Verification approach:** Density evolution is exact in the infinite-block-length limit and can be made rigorous via interval arithmetic. Simulation provides statistical confidence. Lean formalization of the area theorem is feasible.

**Feasibility rating:** HIGH for numerical density evolution and threshold estimation. MEDIUM for rigorous interval arithmetic proofs. LOW for proving threshold exactness.

**Bridge value:** LDPC codes connect graph theory (Tanner graphs, expansion) with information theory (channel capacity). The threshold problem is fundamentally about phase transitions in random constraint satisfaction---a combinatorial/statistical physics question with information-theoretic implications.

---

### 9.6 Capacity of the Binary Deletion Channel

**Name and reference:** Binary deletion channel capacity (Dobrushin 1967; Mitzenmacher 2006; Kanoria-Montanari 2013; Cheraghchi 2020).

**Statement:** Determine the capacity C(d) of the binary deletion channel with deletion probability d, where each bit is independently deleted with probability d.

**Current best results:** Best upper bounds: C(d) <= (1-d) log(phi) for d >= 0.65 (Dalai, 2011); general upper bound framework via channel fragmentation (Rahmati-Duman, 2015). Best lower bounds: C(d)/(1-d) >= 0.1185 (Drinea-Mitzenmacher, 2006). For d -> 0, C(d) = 1-d*log(1/d) - Theta(d). For d -> 1, Kanoria-Montanari showed C(d) ~ (1-d) * 0.4943. Polar codes achieve the capacity of the deletion channel (Tal-Pfister-Fazeli-Vardy, 2021), though the capacity value itself is unknown.

**Computational attack vector:**
- Information-theoretic bounding via Blahut-Arimoto-type algorithms adapted to channels with memory.
- Monte Carlo estimation of mutual information I(X;Y) for specific input distributions over the deletion channel using importance sampling.
- Linear programming bounds on capacity using the framework of Fertonani-Duman (2010).
- Exhaustive search for good codebooks at short lengths over the deletion channel.

**Verification approach:** Numerical bounds are rigorous when computed with interval arithmetic. The LP approach can produce certificates. Statistical estimation provides confidence intervals.

**Feasibility rating:** HIGH for tightening numerical bounds at specific d values. MEDIUM for improving the general bound framework. LOW for finding a closed-form expression.

**Bridge value:** The deletion channel is the information-theoretic face of trace reconstruction (combinatorics), sequence alignment (bioinformatics), and synchronization (communications). Coding-theoretic bounds inform combinatorial trace reconstruction complexity and vice versa.

---

### 9.7 Binary Codes and Ramsey Theory: The Shannon Capacity of C_7

**Name and reference:** Shannon capacity of odd cycles (Shannon 1956; Lovász 1979 for C_5; C_7 open since 1956).

**Statement:** Determine Theta(C_7), the Shannon zero-error capacity of the 7-cycle graph. Equivalently, determine lim_{n->inf} alpha(C_7^{box n})^{1/n}, where alpha is the independence number and box denotes the strong graph product.

**Current best results:** Lovász theta function gives Theta(C_5) = sqrt(5). For C_7: Lovász theta = 7*cos(pi/7)/(1+cos(pi/7)) ~ 3.3177. Best known lower bound: Theta(C_7) >= 3.2578 (Polak-Schrijver, 2019, via circular graphs). Best upper bound: Theta(C_7) <= vartheta(C_7) ~ 3.3177. The gap remains substantial.

**Computational attack vector:**
- Large-scale independent set computation in C_7^{box n} for n = 2, 3, 4, 5 using combinatorial optimization (branch and bound, ILP).
- Semidefinite programming hierarchies (Lasserre/theta-body) applied to C_7^{box n}.
- Search for structured independent sets in C_7^{box n} with symmetry exploitation (automorphism group of C_7^{box n}).
- Computational search over circular graph parameters to improve the lower bound.

**Verification approach:** Independent sets found are trivially verifiable. SDP bounds produce certificates (dual feasible solutions). Lean formalization of the Lovász theta framework is feasible and has been partially done.

**Feasibility rating:** HIGH for improving computational lower bounds at moderate n. MEDIUM for finding clever structured constructions. LOW for determining the exact value.

**Bridge value:** Shannon capacity connects zero-error information theory with graph theory (Ramsey-type independence number problems), algebra (polynomial method), and optimization (SDP hierarchies). It is a perfect example where information-theoretic motivation drives combinatorial research.

---

### 9.8 Covering Codes: Minimum Covering Density

**Name and reference:** Covering code problem / football pool problem (Hamming 1950; Cohen-Lobstein-Sloane, 1986 onwards).

**Statement:** Determine K_q(n,R), the minimum size of a q-ary code of length n with covering radius R (every word in F_q^n is within Hamming distance R of some codeword). What is the asymptotic covering density theta_q(R) = lim inf K_q(n,R)/q^n * V_q(n,R)?

**Current best results:** For binary codes, K_2(n,1) is known exactly for n <= 23 (via football pool results and computer search). Asymptotically, the sphere-covering bound gives K_q(n,R) >= q^n / V_q(n,R). The excess coverage (density) remains poorly understood for R >= 2. Cohen-Lobstein-Sloane tables are the definitive reference, updated periodically.

**Computational attack vector:**
- ILP/constraint programming for K_2(n,R) with small n and R.
- Simulated annealing and genetic algorithms for finding good covering codes.
- SAT encoding of the covering property for exhaustive search at small parameters.
- Algebraic constructions via polynomial methods, automated by computer algebra.

**Verification approach:** Covering codes can be verified by checking coverage. Lower bounds from LP or ILP are certifiable. Computer-assisted proofs for specific values are standard.

**Feasibility rating:** HIGH for extending tables of K_q(n,R) by one or two parameters. MEDIUM for new asymptotic constructions. LOW for tight asymptotics for R >= 2.

**Bridge value:** Covering codes are the coding-theoretic dual of packing (error-correcting) codes and connect to combinatorial design theory (coverings, Turán-type problems), optimization, and even football prediction pools. Both coding bounds and combinatorial constructions co-evolve.

---

### 9.9 Constant-Weight Codes: Optimal Parameters

**Name and reference:** Constant-weight code problem (Johnson 1962; Graham-Sloane 1980; Brouwer-Shearer-Sloane-Smith 1990; Agrell-Vardy-Zeger 2000).

**Statement:** Determine A(n,d,w), the maximum size of a binary code of length n, minimum Hamming distance d, and constant weight w.

**Current best results:** Exact values known for many small parameters via extensive computation (tables maintained by Brouwer and others). Best general upper bound: Johnson bound. Best constructions use Steiner systems (when they exist), lexicodes, and designs. For A(n,4,w) and A(n,6,w), extensive tables are available. The 2025 work classifies maximal binary constant-weight codes with 2, 3, and 4 distances for many parameter ranges.

**Computational attack vector:**
- Isomorph-free exhaustive generation using McKay-type algorithms.
- Clique finding in Johnson graphs J(n,w) with appropriate edge thresholds.
- ILP formulation and LP relaxation for upper bounds.
- Connection to Steiner systems: use design-theoretic construction algorithms.

**Verification approach:** Codes found are trivially verifiable. Upper bounds from LP/ILP produce certificates. Connections to design existence can be formalized.

**Feasibility rating:** HIGH for extending known tables. MEDIUM for new asymptotic results. LOW for closed-form solutions.

**Bridge value:** Constant-weight codes correspond to cliques in Johnson graphs, connecting coding theory to extremal set theory, design theory (Steiner systems, t-designs), and discrete geometry. Progress in design existence feeds code construction and vice versa.

---

### 9.10 DNA Storage Codes: Optimal Redundancy for Combined Error Models

**Name and reference:** DNA storage channel coding (Lenz-Siegel-Bossert-Schwartz 2019; Cai-Chee-Gabrys-Kiah-Nguyen 2021; Sima-Bruck 2020).

**Statement:** Determine the optimal redundancy for correcting t substitutions, s deletions, and i insertions in a binary (or quaternary) string of length n. For single edit (t+s+i = 1), the VT code achieves log n + O(1) bits of redundancy. For t edits, what is the optimal redundancy?

**Current best results:** Single edit: VT codes give log n + 1 bits of redundancy (asymptotically optimal). Two deletions: O(log n) redundancy achieved (Brakensiek-Guruswami-Zbarsky, 2016; Sima-Bruck, 2020). General k deletions: 8k log n + o(log n) redundancy (Sima-Bruck, 2020), optimal to within a constant factor for constant k. The DNA storage context adds constraints: GC-content balance, homopolymer run-length limits, absence of specific motifs.

**Computational attack vector:**
- Exhaustive enumeration of codes correcting t edits for small n, establishing exact values.
- Constraint programming for DNA storage codes incorporating biological constraints.
- Simulation of DNA synthesis/sequencing error channels to estimate practical performance.
- Search for syndromes that efficiently characterize edit patterns.

**Verification approach:** Edit-correcting capability is verifiable by checking all edit patterns (exponential but feasible for small n). For DNA codes, sequencing experiments provide empirical validation.

**Feasibility rating:** HIGH for small-parameter exact results and practical DNA code design. MEDIUM for improving the constant in the k-deletion redundancy. LOW for proving tight bounds in general.

**Bridge value:** DNA storage codes bridge information theory, combinatorics on words (edit distance, sequence reconstruction), and molecular biology (synthesis/sequencing error models). The biological constraints create a novel combinatorial optimization landscape.

---

### 9.11 Polar Code Scaling Exponent and Universality

**Name and reference:** Polar code scaling exponent (Arikan 2009; Hassani-Alishahi-Urbanke 2014; Mondelli-Hassani-Urbanke 2015; Blasiak-Kleinberg-Lubetzky 2023).

**Statement:** For a BMS channel of capacity C, a polar code of block length N = 2^n achieves rate R with block error probability P_e. The scaling exponent mu is defined by the relation N ~ (P_e)^{-mu} * (C - R)^{-mu}. Determine mu exactly. Is mu universal across all BMS channels?

**Current best results:** The scaling exponent satisfies 3.553 <= mu <= 4.714 for the BEC. Simulation suggests mu ~ 3.627 for BEC. For general BMS channels, mu >= 3.553 (Mondelli-Hassani-Urbanke). Large-kernel polar codes can improve mu toward 2 (the information-theoretic optimum). Recent work suggests mu may not be universal.

**Computational attack vector:**
- High-precision density evolution for polar codes to estimate mu at very large block lengths.
- Numerical study of the polarization process for specific channels (BSC, AWGN) using interval arithmetic.
- Search for large polarization kernels that minimize mu.
- GPU-accelerated simulation of polar codes at block lengths N = 2^20 and beyond.

**Verification approach:** Density evolution with interval arithmetic can produce rigorous bounds. Simulation provides statistical estimates. The exact value of mu for the BEC is a well-posed numerical problem.

**Feasibility rating:** HIGH for numerical estimation and kernel search. MEDIUM for rigorous bounds on mu. LOW for proving universality or determining exact mu.

**Bridge value:** The scaling exponent connects information theory (finite-length coding) with probability theory (martingale convergence rates) and combinatorics (kernel design as a combinatorial optimization). Improvements in kernel search directly improve practical polar code performance.

---

### 9.12 Codes from Algebraic Geometry: Beating Gilbert-Varshamov over Small Fields

**Name and reference:** AG codes exceeding GV bound (Tsfasman-Vladut-Zink 1982; Garcia-Stichtenoth 1995; Bassa-Beelen-Garcia-Stichtenoth 2015).

**Statement:** For which finite field sizes q can AG codes beat the Gilbert-Varshamov bound? The TVZ bound exceeds GV when A(q) > 1, which is known for q >= 49 (squares) and q >= p^3 for certain primes p. Does there exist an explicit family of codes over F_7 or F_8 that exceeds the GV bound?

**Current best results:** For q = p^2 with q >= 49, the Garcia-Stichtenoth tower achieves the Drinfeld-Vladut bound A(q) = sqrt(q)-1. For non-square q, the situation is much less clear. For q = p^2 with p small (q = 4, 9, 16, 25), explicit constructions exist but the gap over GV is small. For q = 8, new towers (Bassa-Beelen-Garcia-Stichtenoth, 2015) improve the bounds. A January 2026 paper further improved the quantum and classical GV bounds using symplectic self-orthogonal structures.

**Computational attack vector:**
- Enumerate rational points on towers of curves over small finite fields using Magma/SageMath.
- Compute Weierstrass semigroups and design improved one-point AG codes.
- Search for new towers via automated exploration of recursive equations over function fields.
- Compute exact parameters of AG codes for specific curves of moderate genus.

**Verification approach:** Point counts over finite fields are exact. Code parameters computed from algebraic structures are rigorous. Lean formalization of AG code constructions is feasible (requires algebraic geometry formalization).

**Feasibility rating:** HIGH for computing parameters of AG codes from known towers. MEDIUM for discovering new towers. LOW for proving new asymptotic results for non-square fields.

**Bridge value:** This is the quintessential bridge between algebraic geometry and coding theory. Better curves (more rational points for given genus) yield better codes, and the quest for good codes motivates the search for curves with extremal properties.

---

## Domain 10: Algebraic Geometry Codes <-> Number Theory

### 10.1 Ihara's Constant A(q) for Non-Square q

**Name and reference:** Ihara's constant (Ihara 1981; Serre 1983; Drinfeld-Vladut 1983; Tsfasman-Vladut 1997).

**Statement:** Determine A(q) = lim sup_{g -> inf} N_q(g)/g, where N_q(g) is the maximum number of F_q-rational points on a curve of genus g over F_q. The Drinfeld-Vladut bound gives A(q) <= sqrt(q)-1. For q a square, A(q) = sqrt(q)-1. For non-square q (especially q prime), determine A(q).

**Current best results:** For q prime: the best general lower bound is A(q) >= c*log(q) (Serre, 1983), where the constant c can be taken as 1/(96 log 2). For specific primes: A(2) >= 97/352 ~ 0.2756 (Elkies 2001); A(3) >= (2*(sqrt(10)-1))/9 ~ 0.7326 (Bassa-Beelen-Garcia-Stichtenoth 2012); A(5) and A(7) have improved bounds from explicit towers. For q = p^3 (non-square but cubic): A(q) >= 2(p-1)/(p+2) from Zink's construction. In 2025, new optimal towers over F_{q^4} (quartic power fields) were announced.

**Computational attack vector:**
- Systematically compute N_q(g) for small g over specific prime fields using Magma's function field machinery.
- Search for algebraic curves with many rational points over F_2, F_3, F_5, F_7 using computational algebraic geometry.
- Explore recursive tower constructions by automated search over polynomial equations defining towers.
- Compute class numbers and zeta functions of function fields to extract point counts.

**Verification approach:** Point counts on curves over finite fields are exact computations. Zeta function computations are rigorous. Tables of N_q(g) for small q and g have been maintained (manypoints.org) and are verified.

**Feasibility rating:** HIGH for extending tables of N_q(g). MEDIUM for discovering new towers over prime fields. LOW for determining the exact value of A(q) for any prime q.

**Bridge value:** Ihara's constant is where number theory (arithmetic of function fields, class field theory), algebraic geometry (curves and their rational points), and coding theory (AG code parameters) meet. Every improvement in A(q) has immediate consequences for all three fields.

---

### 10.2 Garcia-Stichtenoth Towers: Extensions and Optimal Splitting

**Name and reference:** Garcia-Stichtenoth towers (Garcia-Stichtenoth 1995, 1996; Bassa-Beelen-Garcia-Stichtenoth 2015).

**Statement:** For the canonical Garcia-Stichtenoth tower over F_{q^2} defined recursively by y^q + y = x^q/(x^{q-1}+1), determine the exact splitting behavior of places at each level and find variants achieving the Drinfeld-Vladut bound with better explicit parameters (smaller genus at each level, faster convergence of the N/g ratio).

**Current best results:** The original Garcia-Stichtenoth tower achieves A(q^2) = q-1. Subsequent variants (second and third Garcia-Stichtenoth towers) give the same limit with different convergence behavior. New towers over F_{q^4} were constructed by Bassa-Beelen-Garcia-Stichtenoth (2015) achieving A(q^4) = q^2-1. In 2025, new optimal towers over quartic power fields were announced.

**Computational attack vector:**
- Compute the genus and rational point count at each level of known towers for specific small q (q = 2, 3, 4, 5) using function field arithmetic in Magma.
- Implement the splitting analysis algorithm for arbitrary recursive towers.
- Search for new recursive equations defining towers with improved convergence properties.
- Compute AG code parameters from these towers at each level.

**Verification approach:** All computations are exact over finite fields. Genus and point count formulas can be verified symbolically. Lean formalization of tower theory would require function field arithmetic.

**Feasibility rating:** HIGH for computational analysis of known towers. MEDIUM for discovering new towers. LOW for proving optimality of convergence rates.

**Bridge value:** These towers are the primary source of explicit asymptotically good AG codes and provide the concrete connection between number-theoretic objects (class field towers, Artin-Schreier extensions) and practically useful codes.

---

### 10.3 Drinfeld-Vladut Bound Tightness for Non-Square Fields

**Name and reference:** Drinfeld-Vladut bound (Drinfeld-Vladut 1983; Ihara's question).

**Statement:** Is the Drinfeld-Vladut bound A(q) <= sqrt(q)-1 tight for non-square q? More precisely: is A(q) = sqrt(q)-1 when q is not a perfect square, or is there a strictly smaller upper bound?

**Current best results:** For q = p (prime), there is a vast gap: the best lower bound is roughly logarithmic in q (Serre's bound) while the upper bound is sqrt(q)-1. It is widely believed that A(p) < sqrt(p)-1 for primes p, but no improved upper bound has been proved. For q = p^3, the Zink bound A(p^3) >= 2(p-1)/(p+2) is substantially below sqrt(p^3)-1. No non-square q is known where A(q) = sqrt(q)-1.

**Computational attack vector:**
- For specific small primes p, compute N_p(g) for all g up to a feasible limit to get the best possible lower bound on A(p).
- Compare the resulting bounds with sqrt(p)-1 to quantify the gap.
- Use modular curves and Shimura curves over non-square fields to search for curves with many points.
- Apply Weil-Serre explicit formulae computationally to obtain improved upper bounds on N_p(g) for specific g.

**Verification approach:** Point counts are exact. The Weil-Serre method produces rigorous upper bounds. Tables of N_q(g) are verified by multiple independent computations.

**Feasibility rating:** HIGH for extending tables of N_p(g) for small primes. MEDIUM for computational evidence about the true value of A(p). LOW for proving improved upper bounds.

**Bridge value:** This is a fundamental number-theoretic question with direct coding-theoretic consequences. If A(p) is strictly less than sqrt(p)-1, then AG codes over prime fields are fundamentally limited, redirecting code design efforts.

---

### 10.4 Explicit Constructions of Good Curves over Small Fields

**Name and reference:** Curves with many points (Serre, 1983 onwards; manypoints.org database).

**Statement:** For given genus g and field size q, determine N_q(g), the maximum number of F_q-rational points on a smooth projective curve of genus g over F_q.

**Current best results:** Tables of N_q(g) are maintained at manypoints.org for small q (2 <= q <= 128) and moderate g (g <= 50 for most q). Exact values known for many (q,g) pairs. For larger g, upper bounds come from the Weil bound N_q(g) <= q+1+g*floor(2*sqrt(q)) (Hasse-Weil) and refinements (Serre, Oesterlé, Lauter). Notable constructions: maximal curves over F_{q^2} (Hermitian curve), optimal curves from class field theory.

**Computational attack vector:**
- Systematic search for curves of given genus and field size using moduli space enumeration.
- Isogeny class enumeration via Honda-Tate theory to determine possible Weil polynomials and then construct curves.
- Point counting algorithms (Schoof-Elkies-Atkin for elliptic curves, generalizations for higher genus) applied to candidate curves.
- Database expansion: fill in unknown entries in the N_q(g) tables using targeted construction algorithms.

**Verification approach:** Point counts are exact. Weil polynomials determine the point count structure rigorously. Lean formalization of the Weil bound is feasible.

**Feasibility rating:** HIGH for extending manypoints.org tables. MEDIUM for finding curves achieving new records. LOW for proving asymptotic results.

**Bridge value:** Every new record curve potentially yields a new record AG code. The interplay between number-theoretic construction methods (class field theory, explicit equations) and coding-theoretic needs (specific rate-distance tradeoffs) is direct and productive.

---

### 10.5 Zeta Functions of Curves: Computational Aspects

**Name and reference:** Zeta function computation for curves (Kedlaya 2001; Harvey 2007; Harvey-Sutherland 2014, 2016).

**Statement:** Given a curve C of genus g over F_q, compute its zeta function Z(C/F_q, T) = exp(sum_{n>=1} #C(F_{q^n})/n * T^n). Equivalently, compute the L-polynomial L(T) of degree 2g such that Z(C/F_q, T) = L(T)/((1-T)(1-qT)). What is the optimal complexity as a function of g and q?

**Current best results:** Kedlaya's p-adic algorithm: O(p^{1/2+epsilon} * g^3 * n^3) for C/F_{p^n}. Harvey's improvement: O(p^{1/2+epsilon} * g^{5/2} * n^{5/2}). For fixed p and large g: O(g^4) using p-adic cohomology. Harvey-Sutherland's average polynomial time method: amortizes over families of curves, achieving O(g * log(q)^{3+epsilon}) per curve on average. In 2025, zeta functions of isogeny graphs connecting to modular curve Hasse-Weil zeta functions were studied.

**Computational attack vector:**
- Implement and optimize Kedlaya-Harvey algorithms for specific small primes p and moderate genus.
- Use average polynomial time methods for systematic point counting over families.
- Parallelize zeta function computation on GPUs for hyperelliptic curves.
- Compute zeta functions of curves arising from towers to study the convergence of A(q).

**Verification approach:** Zeta function computations can be verified by checking functional equation, checking point counts modulo multiple primes, or comparing with independent methods. Results are mathematically exact.

**Feasibility rating:** HIGH for genus <= 10 curves over small fields. MEDIUM for genus 10-30 with optimized algorithms. LOW for very large genus without amortization.

**Bridge value:** Zeta function computation is where number theory (Weil conjectures, now theorems), algebraic geometry (cohomology), and coding theory (AG code parameters) converge algorithmically. Faster algorithms enable larger surveys of curves, which drive both number-theoretic conjectures and coding breakthroughs.

---

### 10.6 Supersingular Curves and Isogeny Graphs

**Name and reference:** Supersingular isogeny graph (Pizer 1990; Charles-Goren-Lauter 2006; De Feo-Jao-Plut 2014 (SIDH); Castryck-Decru 2022 (SIDH attack)).

**Statement:** Characterize the structure of the supersingular l-isogeny graph over F_{p^2}. Specifically: what is the spectral gap of this Ramanujan graph? What are the shortest paths (isogeny walks) between given vertices? The computational problem: given two supersingular elliptic curves E_1, E_2 over F_{p^2}, find an isogeny between them of degree l^e for specified e.

**Current best results:** Supersingular l-isogeny graphs are Ramanujan graphs (Pizer, 1990), meaning their spectral gap is optimal. The SIDH key exchange was broken by Castryck-Decru (2022) and others using auxiliary torsion point information. The underlying path-finding problem in the full supersingular graph without auxiliary information remains hard (best known: O(p^{1/2}) classical, O(p^{1/4}) quantum). The structure of endomorphism rings (Deuring correspondence) is central. In 2025, Ihara zeta functions of supersingular isogeny graphs were related to Hasse-Weil zeta functions of modular curves.

**Computational attack vector:**
- Enumerate supersingular j-invariants over F_{p^2} for moderate primes p (p <= 10000).
- Compute isogeny graph structure: adjacency matrices, spectra, diameter, girth.
- Implement isogeny computation algorithms (Velu's formulas, BSGS on isogeny graphs).
- Compute endomorphism rings and explore Deuring correspondence computationally.

**Verification approach:** Isogeny computations are exact. Graph properties are verifiable. Connection to modular forms provides cross-verification. Lean formalization of isogeny theory is actively underway.

**Feasibility rating:** HIGH for graph computations at moderate primes. MEDIUM for algorithmic improvements to path-finding. LOW for proving hardness of the general isogeny problem.

**Bridge value:** Supersingular isogeny graphs are simultaneously Ramanujan graphs (combinatorics/spectral graph theory), objects in arithmetic geometry (moduli of abelian varieties), and the basis of post-quantum cryptographic protocols. Progress on any front impacts all others.

---

### 10.7 Rational Points and the Hasse-Weil Bound: Serre's Improvement

**Name and reference:** Serre's improvement of the Hasse-Weil bound (Serre 1983; Oesterlé; Lauter 2002).

**Statement:** For a curve C of genus g over F_q, the Hasse-Weil bound gives |#C(F_q) - (q+1)| <= 2g*sqrt(q). Serre improved this to #C(F_q) <= q + 1 + g*floor(2*sqrt(q)). Determine the exact maximum N_q(g) and characterize when Serre's bound (or Oesterlé's refinement) is tight.

**Current best results:** Serre's bound is tight for g = 0, 1, 2 for many q. For g = 1, N_q(1) is known exactly for all q (Honda-Tate theory). For g = 2, N_q(2) is known for many q via Jacobian analysis. For g >= 3, the bound is not always tight and the defect can be substantial. Lauter's bound (2002) gives further improvements using real Weil polynomials. Oesterlé's bound (unpublished, reconstructed by Serre) gives the tightest known upper bounds.

**Computational attack vector:**
- Implement Oesterlé's bound computation as an optimization problem over real Weil polynomials.
- Systematic search for curves achieving or approaching Serre's bound for specific (q,g).
- Compute defects (N_q(g) vs. Serre bound) and look for patterns.
- Use Honda-Tate theory computationally to enumerate possible isogeny classes and then construct curves.

**Verification approach:** All computations are exact. Bounds are rigorous. The Honda-Tate classification provides a framework for complete enumeration of possibilities.

**Feasibility rating:** HIGH for systematic computation of defects. MEDIUM for new constructions approaching bounds. LOW for proving new upper bounds beyond Serre-Oesterlé.

**Bridge value:** This is a fundamental question in arithmetic geometry that directly governs AG code performance. Number-theoretic techniques (explicit formulas, Honda-Tate theory) and combinatorial search (enumerating curves) jointly push the frontier.

---

### 10.8 Function Field Analogues of the Riemann Hypothesis: Higher Genus

**Name and reference:** Riemann Hypothesis for function fields (Weil 1948, proved; higher-dimensional analogue open).

**Statement:** The Riemann Hypothesis for curves over finite fields (Weil conjectures, proved by Deligne in 1974 for higher-dimensional varieties) is a theorem. The analogue for function fields of higher-dimensional varieties over finite fields: understanding the distribution of eigenvalues of Frobenius (Sato-Tate type distributions) and their implications for point counts.

**Current best results:** The Riemann Hypothesis for curves is proved. Sato-Tate for elliptic curves over Q is proved (Taylor et al., 2008-2011). For generic curves of genus g >= 2 over F_q, the distribution of normalized Frobenius eigenvalues follows the USp(2g) distribution as q -> infinity (Katz-Sarnak). The finite-field version: understanding fluctuations of #C(F_q) around q+1 for random curves of genus g. Computational evidence is extensive for g <= 3.

**Computational attack vector:**
- Compute point count statistics for random hyperelliptic curves of genus g over F_p for many primes p.
- Compare distributions with Katz-Sarnak predictions using statistical tests.
- Extend computations to non-hyperelliptic curves using Harvey-Sutherland methods.
- Study low-lying zeros of L-functions attached to function fields computationally.

**Verification approach:** Statistical comparisons with predicted distributions. Exact zeta function computations for individual curves. The Katz-Sarnak framework provides theoretical predictions to test.

**Feasibility rating:** HIGH for statistical verification of Katz-Sarnak predictions. MEDIUM for extending to non-hyperelliptic families. LOW for proving new distributional results.

**Bridge value:** Connects analytic number theory (random matrix theory, L-function distributions) with algebraic geometry (moduli of curves) and coding theory (statistical behavior of AG code parameters). The computational pipeline flows from number theory through geometry to codes.

---

### 10.9 Isogeny-Based Problems: Computational Endomorphism Ring

**Name and reference:** Endomorphism ring computation / Deuring correspondence (Deuring 1941; Kohel 1996; Eisenträger-Hallgren-Lauter-Morrison-Petit 2018).

**Statement:** Given a supersingular elliptic curve E over F_{p^2}, compute its endomorphism ring End(E) as a maximal order in a quaternion algebra B_{p,inf}. The computational complexity of this problem is central to isogeny-based cryptography.

**Current best results:** Classical complexity: O(p^{1/2+epsilon}) for computing End(E) via random walks on the isogeny graph (equivalent to factoring the discriminant of the maximal order). Quantum complexity: O(p^{1/4+epsilon}) using Grover-type search. Polynomial-time algorithms exist given certain auxiliary information (e.g., an isogeny to a curve with known endomorphism ring). The problem is equivalent to the isogeny path-finding problem under standard assumptions. In 2025, new isogeny invariants (weighted permutation representations) encompassing Galois group, Newton polygon, and angle rank were studied.

**Computational attack vector:**
- Implement and optimize the quaternion algebra algorithms for small primes p.
- Benchmarking: time the endomorphism ring computation for p up to 2^64 using state-of-the-art algorithms.
- Explore lattice-based methods for the quaternion ideal problem (analogous to ideal class group computation).
- Study the statistical distribution of endomorphism rings as p varies.

**Verification approach:** Endomorphism ring computations can be verified by checking that the computed isogenies compose correctly. Quaternion order computations are exact. Multiple independent algorithms provide cross-verification.

**Feasibility rating:** HIGH for computational benchmarking at moderate primes. MEDIUM for algorithmic improvements. LOW for proving hardness unconditionally.

**Bridge value:** This problem sits at the confluence of number theory (quaternion algebras, class field theory), algebraic geometry (moduli of abelian varieties), and cryptography (post-quantum key exchange). Algorithmic progress has immediate cryptographic and number-theoretic implications.

---

### 10.10 Function Field BSD and Class Number Computations

**Name and reference:** Birch-Swinnerton-Dyer conjecture for function fields (Artin-Tate conjecture; proved in many cases; Ulmer 2002, 2019).

**Statement:** For an elliptic curve E over a function field F_q(t), the BSD conjecture predicts that the rank of E(F_q(t)) equals the order of vanishing of the L-function L(E/F_q(t), s) at s=1, and gives an exact formula for the leading coefficient involving the Tate-Shafarevich group, regulator, and other invariants.

**Current best results:** The BSD conjecture is proved for elliptic curves over function fields when the L-function is known to be entire (i.e., when the Tate conjecture holds for the corresponding elliptic surface). This includes all elliptic curves over F_q(t) with split semistable reduction. The Tate-Shafarevich group is known to be finite in many cases. Ulmer (2002) constructed elliptic curves over F_q(t) with arbitrarily large rank.

**Computational attack vector:**
- Compute L-functions of elliptic curves over F_q(t) for specific families.
- Verify the BSD formula numerically for curves of moderate conductor.
- Enumerate elliptic curves over F_q(t) and compute ranks, searching for patterns.
- Compute class numbers of function fields using zeta function methods.

**Verification approach:** L-function computations are exact over finite fields. Rank computations via descent are rigorous. The BSD formula can be verified term by term for specific curves.

**Feasibility rating:** HIGH for verifying BSD in specific cases. MEDIUM for extending to new families. LOW for proving new cases of BSD in general.

**Bridge value:** Function field BSD is the testing ground for the number field BSD conjecture (a Millennium Problem). Computational verification in the function field setting guides conjectures and proof strategies for the number field case. The connection to algebraic geometry (elliptic surfaces, Néron models) and coding theory (via the curves involved) is direct.

---

## Domain 11: Quantum Computing <-> Combinatorics

### 11.1 Quantum Chromatic Number vs. Classical Chromatic Number

**Name and reference:** Quantum chromatic number (Cameron-Montanaro-Newman-Severini-Winter 2006; Mancinska-Roberson 2012).

**Statement:** For a graph G, the quantum chromatic number chi_q(G) is the minimum number of colors needed to win the graph coloring game with quantum strategies. Determine the maximum gap between chi(G) and chi_q(G). Is it true that for every k >= 3, there exists a graph with chi_q(G) = 3 and chi(G) = k?

**Current best results:** chi_q(G) <= chi(G) always. Exponential gaps exist: chi(G) can be exponentially larger than chi_q(G) via quantum pseudo-telepathy constructions. In 2025, it was confirmed that the smallest graph with chi_q = 4 and chi = 5 has 14 vertices (Mancinska-Roberson conjecture resolved). The question of whether unbounded gaps exist with chi_q = 3 is conditional on a quantum pseudo-telepathy variant of Khot's d-to-1 conjecture.

**Computational attack vector:**
- Exhaustive enumeration of small graphs, computing both chi and chi_q.
- SDP computation of chi_q (it equals the quantum fractional chromatic number in some formulations).
- Search for graph families with large chi/chi_q ratio using algebraic constructions.
- SAT-based computation of chi for candidate graphs with low chi_q.

**Verification approach:** chi_q can be bounded from above by exhibiting quantum strategies. chi can be verified by SAT encoding. SDP bounds are certifiable.

**Feasibility rating:** HIGH for small graph enumeration. MEDIUM for constructing graphs with specified gaps. LOW for proving unbounded gaps unconditionally.

**Bridge value:** Quantum chromatic number connects quantum information (entangled strategies, operator systems) with graph theory (coloring, homomorphisms). Every advance in graph coloring algorithms or quantum strategy design impacts the other side.

---

### 11.2 Quantum Shannon Capacity

**Name and reference:** Quantum Shannon capacity / entanglement-assisted capacity (Leung-Mancinska-Matthews-Ozols-Roy 2012; Duan-Severini-Winter 2013).

**Statement:** For a graph G, define the entanglement-assisted Shannon capacity Theta_q(G) analogously to the classical Shannon capacity Theta(G), but where Alice and Bob share entanglement. Determine Theta_q(G) for specific graphs. Is Theta_q(G) always equal to the Lovász theta function vartheta(G)?

**Current best results:** For self-complementary vertex-transitive graphs (including C_5), Theta_q(G) = vartheta(G). For the pentagon, Theta_q(C_5) = sqrt(5) (agreeing with the classical Shannon capacity). The conjecture that Theta_q(G) = vartheta(G) in general remains open. The quantum independence number alpha_q(G) is connected to quantum homomorphism games.

**Computational attack vector:**
- Compute vartheta(G) via SDP for families of graphs and compare with Theta_q bounds.
- Search for graphs where Theta_q and vartheta diverge using quantum strategy enumeration.
- Implement quantum protocols for specific graphs and compute achievable rates.
- Use noncommutative polynomial optimization (NPA hierarchy) to bound Theta_q from above.

**Verification approach:** SDP bounds are certifiable. Quantum strategies provide constructive lower bounds. NPA hierarchy convergence can be checked computationally.

**Feasibility rating:** HIGH for SDP computations and small graph searches. MEDIUM for NPA hierarchy computations. LOW for proving Theta_q = vartheta in general.

**Bridge value:** Quantum Shannon capacity connects quantum information (entanglement as a resource) with combinatorial optimization (independent sets, SDP relaxations) and algebra (operator systems, C*-algebras). This problem is where the quantum and classical worlds of zero-error information theory meet.

---

### 11.3 Quantum Error Correction: Exceeding the Quantum Gilbert-Varshamov Bound

**Name and reference:** Quantum GV bound (Calderbank-Shor 1996; Steane 1996; Feng-Ma 2004; Ashikhmin-Litsyn 1999).

**Statement:** The quantum GV bound states that there exist [[n,k,d]]_q quantum codes with parameters satisfying k/n >= 1 - H_q(2d/n) - d/n*log_q(q^2-1) (for CSS codes over F_q). Can explicit constructions beat this bound?

**Current best results:** The quantum GV bound is not known to be tight. Random stabilizer codes achieve the quantum GV bound. AG-based quantum codes can beat the quantum GV bound for q >= 49 (using the TVZ bound). In January 2026, a new probabilistic method improved both classical and quantum GV bounds by analyzing symplectic self-orthogonal structures. Quantum LDPC codes achieving constant rate and linear distance were constructed (Panteleev-Kalachev 2021; Leverrier-Zémor 2022). In 2025, quantum LDPC codes of almost linear distance via iterated homological products were announced.

**Computational attack vector:**
- Compute parameters of quantum AG codes from specific towers for small field sizes.
- Search for quantum codes beating the quantum GV bound at specific lengths using algebraic constructions.
- Implement the symplectic self-orthogonal probabilistic method and compute explicit improved bounds.
- Monte Carlo simulation of random stabilizer codes to estimate typical parameters.

**Verification approach:** Quantum code parameters can be verified by checking the stabilizer conditions and computing minimum distance. Bounds are rigorous.

**Feasibility rating:** HIGH for computing quantum code parameters from known constructions. MEDIUM for finding new explicit codes beating QGV. LOW for proving new asymptotic results.

**Bridge value:** Quantum error correction sits at the intersection of combinatorics (self-orthogonal codes, graph states), algebraic geometry (AG code constructions with symplectic structure), and quantum information (fault tolerance). Combinatorial code search and algebraic construction techniques from classical coding theory are essential tools.

---

### 11.4 NLTS and Beyond: Quantum Circuit Lower Bounds

**Name and reference:** NLTS theorem / qPCP conjecture (Freedman-Hastings 2013; Anshu-Breuckmann-Nirkhe 2023; Eldar-Harrow 2017).

**Statement:** The NLTS (No Low-Energy Trivial States) theorem (now proved) states: there exists a family of local Hamiltonians H_n on n qubits such that every state with energy below epsilon*n requires circuit depth Omega(log n) to prepare. The stronger qPCP conjecture: is it QMA-hard to approximate the ground energy of a local Hamiltonian to within a constant fraction of the total norm?

**Current best results:** NLTS was proved by Anshu-Breuckmann-Nirkhe (2023) using quantum LDPC codes (specifically, quantum Tanner codes). The qPCP conjecture remains wide open. The NLTS result shows that the ground states of certain local Hamiltonians require super-constant depth circuits, but the conjectured Omega(n) lower bound for approximation remains unproven. The proof technique relies on properties of quantum LDPC codes (constant rate, linear distance, local testability).

**Computational attack vector:**
- Compute energy spectra of small instances of the NLTS Hamiltonians constructed from quantum Tanner codes.
- Search for explicit circuit lower bounds for specific quantum code Hamiltonians.
- Numerical study of the approximation gap for small instances of qPCP candidate Hamiltonians.
- Variational quantum algorithms applied to NLTS Hamiltonians to study the energy landscape.

**Verification approach:** Energy computations for small systems are exact (matrix diagonalization). Circuit lower bounds for specific instances can be verified. Statistical evidence from sampling the energy landscape.

**Feasibility rating:** HIGH for small-system exact diagonalization. MEDIUM for moderate-size numerical studies. LOW for proving qPCP.

**Bridge value:** NLTS/qPCP connects quantum Hamiltonian complexity with classical combinatorics (LDPC codes, expander graphs, locally testable codes). The proof of NLTS was fundamentally a combinatorial/coding-theoretic achievement with quantum complexity implications.

---

### 11.5 Quantum Advantage for Combinatorial Optimization: Exact Characterization

**Name and reference:** Quantum computational advantage for combinatorial optimization (Farhi-Goldstone-Gutmann 2014 (QAOA); Hastings 2019; Bravyi-Kliesch-Koenig-Tang 2020; Abbas et al. 2023).

**Statement:** For which combinatorial optimization problems does a quantum algorithm (QAOA, quantum annealing, Grover-based) provide a provable polynomial or super-polynomial speedup over the best classical algorithm?

**Current best results:** No provable super-polynomial quantum advantage for NP-hard optimization in the worst case (modulo complexity-theoretic assumptions). Bravyi-Kliesch-Koenig-Tang (2020) showed a quantum advantage for a specific shallow-circuit optimization problem. Abbas et al. (2023) proved a super-polynomial quantum advantage for approximating certain combinatorial optimization problems using computational learning theory. In 2025, end-to-end benchmarking showed quantum solvers matching ground states in 14/20 instances at sub-second runtimes, while classical solvers required longer for some structured instances. Barren plateaus remain a fundamental obstacle for variational approaches.

**Computational attack vector:**
- Benchmark QAOA at depth p on specific graph optimization problems (MaxCut, Max-k-SAT) against classical heuristics.
- Implement Grover-based branch-and-bound for specific combinatorial problems and measure practical speedup.
- Study the performance ratio of quantum annealing vs. simulated annealing on structured problem instances.
- Identify problem families where quantum speedup is provable by construction.

**Verification approach:** Benchmarking results are empirical. Approximation ratios for specific instances are verifiable. Theoretical speedup claims require proof.

**Feasibility rating:** HIGH for benchmarking studies. MEDIUM for identifying new problem families with quantum advantage. LOW for proving unconditional separations.

**Bridge value:** This is the central question of whether quantum mechanics helps with discrete optimization. It connects quantum complexity theory with combinatorial optimization, approximation algorithms, and statistical physics (spin glasses). Resolution would fundamentally reshape both quantum computing and combinatorial optimization.

---

### 11.6 Nonlocal Games and Graph Homomorphisms

**Name and reference:** Nonlocal games / graph homomorphism games (Mancinska-Roberson 2014; Ji-Natarajan-Vidick-Wright-Yuen 2020 (MIP*=RE)).

**Statement:** For a graph G, the graph homomorphism game is a nonlocal game where players must demonstrate a homomorphism from G to K_c (a c-coloring). The quantum value omega_q of this game determines the quantum chromatic number. The key result MIP*=RE (2020) showed that the set of quantum correlations is not closed and refuted the Connes embedding conjecture. Remaining open: characterize which games have a quantum advantage, and develop efficient algorithms for computing or approximating quantum values.

**Current best results:** MIP*=RE is proved. The quantum value of specific games (CHSH, Magic Square, graph coloring games for specific graphs) is known. Computing the quantum value is undecidable in general (consequence of MIP*=RE). The NPA hierarchy provides converging upper bounds. For specific graph families, quantum vs. classical value gaps are being catalogued. In 2025, bounds on compiled nonlocal games (from interactive proofs) were established.

**Computational attack vector:**
- Compute NPA hierarchy bounds for quantum values of graph games at moderate hierarchy levels.
- Enumerate graphs with quantum advantages in coloring games using SDP-based screening.
- Implement compiled nonlocal game protocols and benchmark their soundness.
- Search for new game constructions with large quantum/classical value gaps.

**Verification approach:** NPA hierarchy gives rigorous upper bounds. Quantum strategies provide constructive lower bounds. SDP solutions are certifiable.

**Feasibility rating:** HIGH for NPA hierarchy computations on small games. MEDIUM for discovering new game families. LOW for general decidability questions.

**Bridge value:** Nonlocal games are the operational bridge between quantum information and graph theory. MIP*=RE showed that this bridge connects to the deepest questions in operator algebras (Connes' embedding) and computability theory. Combinatorial game design and quantum strategy analysis co-evolve.

---

### 11.7 Quantum Error Correction: The Quantum Singleton Bound

**Name and reference:** Quantum Singleton bound (Knill-Laflamme 1997; Rains 1999; Grassl-Rötteler-Beth 2004).

**Statement:** Any [[n,k,d]] quantum error-correcting code satisfies k <= n - 2(d-1) (the quantum Singleton bound). Codes meeting this bound are called quantum MDS codes. For which parameters do quantum MDS codes exist?

**Current best results:** Quantum MDS codes exist for all n <= q+1 when q is a prime power (via Hermitian self-orthogonal RS codes), paralleling the classical MDS conjecture. For n > q+1, quantum MDS codes are rare. Explicit constructions use algebraic geometry codes, constacyclic codes, and generalized RS codes. The quantum MDS conjecture (analogous to the classical one) states that quantum MDS codes of length n over F_q satisfy n <= q^2 + d - 1 or fall into specific exceptional families.

**Computational attack vector:**
- Exhaustive search for self-orthogonal MDS codes over small fields.
- Computer algebra construction of quantum MDS codes from algebraic geometry.
- Verify the quantum MDS conjecture computationally for small field sizes.
- Search for new constructions using constacyclic and twisted codes.

**Verification approach:** Quantum code parameters are exactly verifiable. Self-orthogonality checks are linear algebra. The MDS property is checked via minors.

**Feasibility rating:** HIGH for exhaustive verification at small parameters. MEDIUM for new constructions. LOW for proving the quantum MDS conjecture.

**Bridge value:** Quantum MDS codes require self-orthogonal classical MDS codes, directly linking the quantum Singleton bound to the classical MDS conjecture and algebraic geometry (Hermitian curves, AG code duality). Combinatorial constraints on self-orthogonality create a rich interplay.

---

### 11.8 Quantum Money from Knot Invariants and Graphs

**Name and reference:** Quantum money (Wiesner 1983; Aaronson-Christiano 2012; Farhi-Gosset-Hassidim-Lutomirski-Shor 2012).

**Statement:** Construct a public-key quantum money scheme based on mathematical structure: given a graph G, produce a quantum state |G> that encodes G in an unclonable way, where verification is efficient but counterfeiting is computationally hard. Can knot invariants, graph invariants, or other combinatorial structures provide the basis for provably secure quantum money?

**Current best results:** Aaronson-Christiano proposed a scheme based on hidden subspaces. Farhi et al. proposed schemes based on knot invariants (Alexander polynomial), but security remains unproven. Graph-based approaches face the challenge that graph isomorphism (the natural verification problem) is in quasi-polynomial time (Babai, 2015). No provably secure public-key quantum money scheme exists unconditionally. Lattice-based approaches show promise.

**Computational attack vector:**
- Implement candidate quantum money verification circuits and test against classical counterfeiting attacks.
- Search for graph families where the quantum money verification problem is hard (e.g., non-isomorphic graphs with identical invariants).
- Compute knot invariants (Jones polynomial, HOMFLY) for candidate knot families.
- Develop and benchmark classical attacks on proposed schemes.

**Verification approach:** Security reductions are theoretical. Concrete security analysis can be done computationally for specific parameter ranges. Quantum circuit simulation provides verification for small instances.

**Feasibility rating:** HIGH for implementing and testing specific schemes. MEDIUM for finding better combinatorial bases. LOW for proving security.

**Bridge value:** Quantum money connects quantum information (unclonability, quantum computational assumptions) with combinatorics (graph invariants, knot invariants) and complexity theory (GI complexity). The search for "hard" combinatorial structures suitable for money schemes drives new combinatorial questions.

---

### 11.9 Entanglement in Graph States: Characterization and Optimization

**Name and reference:** Graph state entanglement (Hein-Eisert-Briegel 2004; Van den Nest-Dehaene-De Moor 2004).

**Statement:** A graph state |G> on n qubits is defined by a graph G: apply CZ gates according to edges starting from |+>^n. Characterize the entanglement structure of |G>: which graphs G produce states with maximal multipartite entanglement? Which graph transformations (local complementation, vertex deletion) preserve entanglement properties?

**Current best results:** Graph states are fully characterized up to local Clifford equivalence by orbits under local complementation. The entanglement width (Schmidt rank across bipartitions) is related to the rank-width of the graph. Constructability of complex entangled states from graph states is an active research area. In 2025, Ramsey-theoretic thresholds for multipartite entanglement in graph states were identified: states on ~100-160 qubits either contain 6 uncorrelated qubits or 6 entangled qubits.

**Computational attack vector:**
- Enumerate graph states up to LC equivalence for small qubit counts (n <= 12) using McKay-type isomorphism rejection.
- Compute entanglement measures (concurrence, negativity, entanglement entropy) for specific graph families.
- Optimization: find graphs maximizing specific entanglement measures subject to experimental constraints.
- SAT/CSP-based search for graphs with specified entanglement properties.

**Verification approach:** Entanglement measures are computable for moderate-size states. LC equivalence is decidable via rank-width. Experimental verification is possible on quantum hardware.

**Feasibility rating:** HIGH for small-scale enumeration. MEDIUM for optimization over larger graph families. LOW for proving general characterization results.

**Bridge value:** Graph states are where quantum information meets graph theory most directly. Graph-theoretic properties (rank-width, vertex-minor theory, local complementation) determine quantum entanglement structure. This is a two-way bridge: graph theory informs quantum state design, and quantum applications motivate new graph-theoretic questions.

---

### 11.10 Quantum Walk Mixing Times on Graphs

**Name and reference:** Quantum walk mixing (Aharonov-Ambainis-Kempe-Vazirani 2001; Richter 2007; Chakraborty-Gilyén-Jeffery 2019).

**Statement:** For a graph G, a continuous-time quantum walk is defined by the unitary U(t) = exp(iAt) where A is the adjacency matrix. The mixing time t_mix is the time at which the walk distribution is epsilon-close to the average distribution. How does t_mix^{quantum} relate to t_mix^{classical} for various graph families? Are there graphs where quantum walks mix quadratically faster?

**Current best results:** Quantum walks on hypercubes mix in O(n) vs. classical O(n log n). On certain Cayley graphs, quadratic speedups exist. The average mixing time (time-averaged distribution) may converge faster. For expander graphs, quantum walks do not always provide speedup. In 2025, hybrid quantum walk models integrating discrete and continuous walks were developed, and quantum walks on bounded infinite graphs were studied.

**Computational attack vector:**
- Compute quantum walk distributions on specific graph families (Johnson graphs, Kneser graphs, Cayley graphs) by matrix exponentiation.
- Compare quantum and classical mixing times numerically for graph families up to moderate size.
- Search for graph families with maximal quantum/classical mixing time ratio.
- Simulate quantum walks on quantum hardware and compare with theoretical predictions.

**Verification approach:** Matrix exponentiation is exact for small graphs. Mixing time can be estimated rigorously from spectral gaps. Quantum hardware experiments provide empirical data.

**Feasibility rating:** HIGH for numerical computation on moderate-size graphs. MEDIUM for identifying optimal graph families. LOW for proving general speedup theorems.

**Bridge value:** Quantum walks connect quantum algorithm design with spectral graph theory (eigenvalues of adjacency/Laplacian matrices) and combinatorics (graph structure). The mixing time question is simultaneously about quantum dynamics and classical graph properties.

---

## Domain 12: Information Theory <-> Combinatorics

### 12.1 Capacity of the Binary Deletion Channel (Revisited from IT Perspective)

**Name and reference:** Binary deletion channel capacity (Dobrushin 1967; Mitzenmacher 2006).

**Statement:** (See Domain 9.6 for precise statement.) From the information-theoretic side: determine C(d) for the binary deletion channel with deletion probability d. This is perhaps the oldest major open problem in information theory.

**Current best results:** (See Domain 9.6.) The problem is unique in that even the capacity of the simplest synchronization error channel is unknown. The best numerical bounds leave a gap of roughly 2x at d = 0.5. Polar codes have been shown to achieve capacity (though the capacity is unknown).

**Computational attack vector:**
- Novel approach: formulate as an optimization over input distributions with memory (hidden Markov models) and use EM-type algorithms.
- Dynamic programming over jittered trellis representations of the deletion channel.
- Information-geometric methods: study the capacity-achieving input distribution's structure.
- Connect to combinatorics of subsequences: the number of distinct subsequences of a binary string is related to channel behavior.

**Verification approach:** Numerical bounds via convex optimization are rigorous with interval arithmetic. Monte Carlo estimation provides complementary evidence.

**Feasibility rating:** HIGH for improved numerical bounds. MEDIUM for structural characterization of the capacity-achieving input distribution. LOW for closed-form capacity.

**Bridge value:** The deletion channel capacity is where information theory meets combinatorics on words (subsequence counting, Levenshtein distance), probability (random subsequences), and molecular biology (DNA sequence errors). The combinatorics of subsequences is the essential mathematical structure.

---

### 12.2 Network Coding: Capacity of the Butterfly Network Variants

**Name and reference:** Network coding capacity (Ahlswede-Cai-Li-Yeung 2000; Li-Yeung-Cai 2003; Dougherty-Freiling-Zeger 2005).

**Statement:** For a directed acyclic network with specified source-sink pairs, determine the multi-commodity network coding capacity. Even for small networks, the capacity region is often unknown. The specific question: for which networks does linear network coding achieve capacity?

**Current best results:** Linear network coding is sufficient for multicast (Li-Yeung-Cai, 2003). For multi-source multi-sink networks, linear coding is insufficient in general (Dougherty-Freiling-Zeger, 2005). The Väämönen network is the smallest known example where nonlinear coding is needed. The capacity region of the 2-source 2-sink interference network is not fully characterized. Information inequalities beyond Shannon (non-Shannon-type inequalities) play a crucial role.

**Computational attack vector:**
- Enumerate small networks and compute their linear and nonlinear coding capacities using LP formulations.
- Implement the entropy function approach: compute inner and outer bounds on the capacity region using Shannon and non-Shannon-type inequalities.
- Use the ITIP (Information Theoretic Inequality Prover) software to derive new network coding bounds.
- Search for new non-Shannon-type information inequalities using computer-aided methods.

**Verification approach:** LP bounds are certifiable. Coding schemes provide achievable rate vectors (constructive). Entropy inequality proofs can be verified symbolically.

**Feasibility rating:** HIGH for small network capacity computation. MEDIUM for discovering new non-Shannon inequalities. LOW for general capacity region characterization.

**Bridge value:** Network coding capacity connects information theory with matroid theory (representability, linear vs. nonlinear), combinatorial optimization (LP/flow problems), and algebra (entropic vectors, group-based constructions). The linear/nonlinear gap is fundamentally about matroid representability.

---

### 12.3 Entropy Methods for Additive Combinatorics: The Polynomial Freiman-Ruzsa Conjecture

**Name and reference:** Polynomial Freiman-Ruzsa conjecture (Freiman 1973; Ruzsa 1994; Green-Tao; proved by Gowers-Green-Manners-Tao 2023).

**Statement:** (Now a theorem.) If A is a subset of F_2^n with |A+A| <= K|A|, then A is contained in a coset of a subgroup of size at most K^C * |A| for some absolute constant C. The entropy-theoretic formulation: if H(X+Y) - H(X) <= log K for i.i.d. copies X, Y of a random variable on an abelian group, what structural conclusions can be drawn about X?

**Current best results:** The PFR conjecture was proved by Gowers-Green-Manners-Tao (2023) with C = 12. The entropic approach was instrumental: Ruzsa's entropy distance, the Plünnecke-Ruzsa inequality, and related tools. In 2025, the entropic additive energy framework was developed, providing new entropy inequalities for sums and products including a general ring Plünnecke-Ruzsa entropy inequality.

**Computational attack vector:**
- Compute explicit constants in the PFR theorem for specific groups using exhaustive search.
- Implement the entropy-theoretic characterization of sets with small doubling.
- Search for tight examples: sets with small doubling that are maximally far from cosets.
- Extend the entropic framework to the sum-product problem over integers.

**Verification approach:** Entropy computations are exact for discrete distributions. Set computations are exact. The entropic inequalities have been formalized in Lean (the PFR proof was formalized shortly after its announcement).

**Feasibility rating:** HIGH for constant optimization and specific group computations. MEDIUM for extending to sum-product settings. LOW for proving new structural results.

**Bridge value:** PFR is the clearest example of information theory enabling combinatorial breakthroughs. Shannon entropy provides a "soft" version of cardinality that admits analytic techniques. The 2023 proof and its subsequent entropy extensions demonstrate the power of the information-theoretic lens on additive combinatorics.

---

### 12.4 Broadcast Channel Capacity

**Name and reference:** Broadcast channel capacity (Cover 1972; Marton 1979; El Gamal-Kim 2011).

**Statement:** Determine the capacity region of the general broadcast channel: a channel with one sender and two (or more) receivers. For the 2-receiver broadcast channel, the capacity region is known for degraded channels (Cover 1972) and specific special cases, but the general case is open.

**Current best results:** The best inner bound is Marton's bound (1979), which uses auxiliary random variables. The best outer bound is the UV outer bound (Nair-El Gamal, 2007). For the 2-receiver Gaussian broadcast channel, the capacity region is known (superposition coding is optimal). For discrete broadcast channels, the gap between Marton's inner bound and the best outer bound is non-zero in general. It is unknown whether Marton's bound is tight.

**Computational attack vector:**
- Compute Marton's inner bound and UV outer bound for specific small-alphabet channels using Blahut-Arimoto-type algorithms.
- Cardinality bounding: optimize the auxiliary random variable alphabet size for specific channels.
- Exhaustive computation for binary-input broadcast channels.
- Use the ITIP prover to derive new outer bounds from entropy inequalities.

**Verification approach:** Inner bounds are achieved by specific coding schemes (constructive). Outer bounds follow from entropy inequalities (verifiable). Numerical optimization with certified solvers.

**Feasibility rating:** HIGH for specific channel computations. MEDIUM for new inner/outer bound techniques. LOW for the general capacity region.

**Bridge value:** The broadcast channel connects information theory with combinatorial optimization (auxiliary variable selection is a combinatorial problem), convex geometry (capacity regions as convex sets), and algebra (entropic vectors). The open problem drives development of new information-theoretic techniques with combinatorial structure.

---

### 12.5 Interference Channel Capacity

**Name and reference:** Interference channel capacity (Ahlswede 1974; Han-Kobayashi 1981; Etkin-Tse-Wang 2008).

**Statement:** Determine the capacity region of the 2-user interference channel, where two sender-receiver pairs communicate simultaneously with mutual interference.

**Current best results:** The Han-Kobayashi (HK) scheme (1981) is the best known inner bound. Etkin-Tse-Wang (2008) showed the HK scheme achieves within 1 bit of capacity for the Gaussian interference channel. For very strong and very weak interference, the capacity is known. For moderate interference, the exact capacity is open. In 2025, new results on multi-user interference channels using entropy power inequality chain-rule decomposition showed that single-user Gaussian codebooks suffice for optimal performance.

**Computational attack vector:**
- Compute HK inner bound for specific discrete interference channels using multi-dimensional Blahut-Arimoto.
- Derive outer bounds for specific channels using genie-aided arguments and ITIP.
- Cardinality bounding for the HK auxiliary random variables.
- Numerical optimization of the rate-splitting parameter in the HK scheme.

**Verification approach:** Inner bounds are constructive. Outer bounds from entropy inequalities are certifiable. Numerical bounds with interval arithmetic.

**Feasibility rating:** HIGH for specific channel computations. MEDIUM for tightening the gap. LOW for exact capacity.

**Bridge value:** The interference channel bridges information theory with game theory (strategic interaction), optimization (rate region computation), and combinatorics (auxiliary variable structure). The 1-bit gap result is a striking example of approximate capacity determination.

---

### 12.6 Rényi Entropy in Combinatorics: Extensions of Shearer's Lemma

**Name and reference:** Shearer's lemma / entropy method (Chung-Graham-Frankl-Shearer 1986; Madiman-Tetali 2010; Gavinsky-Lovett-Saks-Srinivasan 2014).

**Statement:** Shearer's lemma bounds the entropy of a random variable in terms of its marginals over a covering family. Does an analogous inequality hold for Rényi entropy of all orders? What are the optimal constants?

**Current best results:** Shearer's lemma for Shannon entropy is exact. For Rényi entropy of order alpha > 1, analogues have been proved in some settings but with weaker constants. The Rényi entropy power inequality has been established for alpha in [0,1] with various approaches (Bobkov-Marsiglietti, 2016; Marsiglietti-Melbourne, 2019). Extensions to dependent random variables were developed in 2025.

**Computational attack vector:**
- Compute optimal constants in Rényi Shearer-type inequalities for small covering families by optimization.
- Search for extremal distributions achieving equality in Rényi entropy inequalities.
- Implement and compare different EPI formulations (multiplicative, exponential, logarithmic) numerically.
- Apply Rényi entropy methods to specific combinatorial counting problems.

**Verification approach:** Entropy computations are exact for discrete distributions. Optimization bounds are certifiable. The inequalities can be formalized in proof assistants.

**Feasibility rating:** HIGH for numerical optimization of constants. MEDIUM for discovering new inequalities. LOW for proving optimal constants.

**Bridge value:** Shearer's lemma is the primary tool for applying information theory to combinatorics (Loomis-Whitney inequality, graph entropy, property testing). Rényi extensions would provide a richer toolkit with parameters tunable to specific combinatorial applications.

---

### 12.7 Common Information: Gaps and Exact Computation

**Name and reference:** Common information (Wyner 1975; Gács-Körner 1973; Exact common information: Kumar-Li-El Gamal 2014).

**Statement:** For a pair of random variables (X,Y), Wyner's common information C_W(X;Y) >= I(X;Y) >= C_GK(X;Y) (Gács-Körner common information). Determine the exact common information (Kumar-Li-El Gamal) for specific joint distributions. Characterize when C_W = I (or C_GK = I).

**Current best results:** Wyner's common information equals mutual information iff the joint distribution can be written as a mixture of product distributions (Li-El Gamal, 2018). Gács-Körner common information is zero for "generic" distributions. Exact common information has been computed for some binary distributions. In 2025, efficient solvers for Wyner common information extensions and mutual information bounds for lossy common information were developed.

**Computational attack vector:**
- Implement convex optimization algorithms for computing C_W for arbitrary discrete distributions.
- Compute C_GK using the maximal correlation approach.
- Search for distributions with interesting common information profiles (large gap between C_W and I).
- Apply common information to clustering problems (Wyner common information as a clustering objective).

**Verification approach:** Convex optimization solutions are verifiable. The computed auxiliary random variables provide constructive certificates. Distribution-specific results are exact.

**Feasibility rating:** HIGH for computing common information for specific distributions. MEDIUM for characterizing extremal distributions. LOW for proving general structural results.

**Bridge value:** Common information connects information theory with combinatorics (partition problems, common randomness extraction), machine learning (representation learning, clustering), and probability theory (coupling, mixing). The gap between different common information measures reflects fundamentally different combinatorial structures.

---

### 12.8 Polar Coding for Channels with Memory and Non-Standard Channels

**Name and reference:** Polar codes beyond memoryless channels (Sasoglu-Tal-Telatar 2012; Honda-Yamamoto 2013; Tal-Pfister-Fazeli-Vardy 2021).

**Statement:** Do polar codes achieve the capacity of channels with memory (e.g., intersymbol interference channels, fading channels)? Do they achieve the capacity of channels with synchronization errors (deletion/insertion channels)?

**Current best results:** Polar codes achieve capacity for stationary ergodic channels (Sasoglu-Tal-Telatar, 2012) under some regularity conditions. For the deletion channel, polar codes achieve capacity (Tal-Pfister-Fazeli-Vardy, 2021), though the capacity value is unknown. For channels with both deletions and insertions, polar coding with guard bands achieves capacity (Thomas-Pfister, 2021). For DNA storage channels, GC-balanced polar codes were proposed in 2025.

**Computational attack vector:**
- Implement polar code construction for specific channels with memory using Monte Carlo density evolution.
- Benchmark polar codes against LDPC codes on non-standard channels.
- Design and evaluate guard-band schemes for deletion/insertion channels.
- Optimize polar code construction for DNA storage channel models.

**Verification approach:** Capacity-achieving is proved theoretically. Performance at finite lengths can be evaluated by simulation. Code parameters are exactly computable.

**Feasibility rating:** HIGH for implementation and benchmarking. MEDIUM for new channel models. LOW for proving capacity achievement for new channel classes.

**Bridge value:** Extending polar codes to non-standard channels requires understanding the combinatorial structure of the channel (synchronization patterns, memory structure) and designing the polarization transform accordingly. This is where information-theoretic coding meets combinatorics of sequences.

---

### 12.9 Information-Theoretic Bounds on Ramsey Numbers

**Name and reference:** Entropy bounds on Ramsey numbers (Naor 2005; Fox 2011; Conlon-Fox-Sudakov 2015).

**Statement:** Can information-theoretic (entropy) methods provide new bounds on Ramsey numbers R(k,l) or other extremal combinatorial quantities? Specifically, can the entropy method improve the upper bound R(k,k) <= 4^k / sqrt(k) (Thomason 1988, Conlon 2009)?

**Current best results:** The best upper bound on R(k,k) is (4-epsilon)^k for some small epsilon > 0 (Campos-Griffiths-Morris-Sahasrabudhe, 2023). Entropy methods have been applied to hypergraph Ramsey numbers and off-diagonal Ramsey numbers with some success. The graph entropy method of Körner gives bounds on the Shannon capacity and related Ramsey-type problems. Information-theoretic proofs of the Kruskal-Katona theorem exist via entropy.

**Computational attack vector:**
- Apply the entropy compression method systematically to Ramsey-type problems using automated inequality provers.
- Implement the Loomis-Whitney/Shearer framework for hypergraph counting.
- Use information-theoretic tools to derive new bounds on specific Ramsey numbers R(k,l) for small k.
- Develop automated tools for deriving combinatorial consequences of entropy inequalities.

**Verification approach:** Entropy-based proofs are fully rigorous. Automated inequality verification using ITIP or similar software. Lean formalization of entropy-based combinatorial proofs.

**Feasibility rating:** HIGH for applying known entropy methods to new combinatorial problems. MEDIUM for developing new entropy-based techniques. LOW for breaking the 4^k barrier further.

**Bridge value:** This is a direct application of information theory to extremal combinatorics. The recent breakthrough on diagonal Ramsey numbers used probabilistic and combinatorial methods; integrating information-theoretic techniques could yield further improvements. The bridge is methodological: entropy provides a toolkit for counting and probabilistic arguments.

---

### 12.10 Entropy and the Sum-Product Conjecture

**Name and reference:** Entropic sum-product phenomenon (Tao 2010; Roche-Newton-Rudnev-Shkredov 2016; 2025 extensions).

**Statement:** For a finite set A of integers, the sum-product conjecture (Erdős-Szemerédi 1983) states max(|A+A|, |A*A|) >= |A|^{2-epsilon} for every epsilon > 0. The entropic version: for a random variable X taking values in Z, if H(X+X') is small, must H(X*X') be large (where X' is an independent copy)?

**Current best results:** Best bound on the sum-product conjecture: max(|A+A|, |A*A|) >= |A|^{4/3+c} for some small c > 0 (Rudnev-Stevens, 2022). The entropic formulation has been developed but not pushed as far. In 2025, entropic additive energy and entropy inequalities for sums and products were established, including a characterization of discrete random variables with "large doubling" analogous to Tao's Freiman-type inverse theory.

**Computational attack vector:**
- Compute sum-product ratios for specific set families and compare with entropy predictions.
- Search for extremal sets (achieving near-equality in sum-product bounds) by exhaustive enumeration.
- Implement the entropic sum-product framework and compute bounds for specific distributions.
- Use automated entropy inequality provers to derive new sum-product bounds.

**Verification approach:** Set computations are exact. Entropy computations are exact for discrete distributions. Automated inequality proofs are verifiable.

**Feasibility rating:** HIGH for computational exploration of sum-product behavior. MEDIUM for deriving new entropy-based bounds. LOW for proving the full conjecture.

**Bridge value:** The sum-product conjecture is a central problem in additive combinatorics, and the entropic approach provides a fundamentally different toolkit. The bridge between information theory and additive combinatorics is mediated by the analogy between set cardinality and entropy, with entropy providing analytic power that pure combinatorics lacks.

---

## Domain 13: Topology <-> Combinatorics

### 13.1 Topological Tverberg Conjecture: Remaining Cases

**Name and reference:** Topological Tverberg conjecture (Tverberg 1966; topological version: Bárány-Shlosman-Szücs 1981; counterexamples: Frick 2015; Mabillard-Wagner 2014).

**Statement:** For any continuous map f: Delta_{(d+1)(r-1)} -> R^d (from a (d+1)(r-1)-dimensional simplex to R^d), there exist r pairwise disjoint faces whose images have a common point. The conjecture is true for r prime (Bárány-Shlosman-Szücs) and r a prime power (Özaydin; Volovikov). It is false for r not a prime power (Frick, 2015). Open: determine the exact threshold dimension for each non-prime-power r.

**Current best results:** For r not a prime power, counterexamples exist in dimension N = (d+1)(r-1) - r*ceil((d+2)/(r+1)) - 2 (Avvakumov-Karasev-Skopenkov, 2019, published in Combinatorica 2023). The smallest counterexample dimension is unknown for many r. For r = 6 (the smallest non-prime-power), the exact threshold dimension is not determined.

**Computational attack vector:**
- For small r and d, implement the Mabillard-Wagner deleted product obstruction and check it computationally.
- Search for explicit counterexamples in low dimensions using optimization over triangulations.
- Compute equivariant cohomology obstructions for specific (r,d) pairs using computational algebraic topology.
- Implement the constraint method of Blagojević-Ziegler-Frick computationally for specific parameters.

**Verification approach:** Explicit counterexample maps can be verified by checking the disjointness condition. Obstruction theory computations are rigorous. Equivariant cohomology can be computed exactly for small complexes.

**Feasibility rating:** HIGH for computational obstruction theory at specific (r,d). MEDIUM for finding explicit counterexamples. LOW for determining exact thresholds for all r.

**Bridge value:** The topological Tverberg conjecture is the flagship problem of topological combinatorics. It connects equivariant topology (group actions, obstruction theory) with discrete geometry (convex partitions) and combinatorics (simplex structure). The prime/non-prime-power dichotomy is a surprising intersection of number theory with topology.

---

### 13.2 Borsuk's Conjecture in Small Dimensions

**Name and reference:** Borsuk's conjecture (Borsuk 1933; counterexample: Kahn-Kalai 1993; Bondarenko 2013).

**Statement:** Can every bounded set in R^n be partitioned into n+1 parts, each of smaller diameter? True for n <= 3. False for n >= 64 (Jenrich, 2013, improving Bondarenko's n >= 65). The critical question: for which 4 <= n <= 63 is the conjecture true?

**Current best results:** True for n = 1, 2, 3. Open for 4 <= n <= 63. Counterexamples for n >= 64 use sets from the Leech lattice and Bondarenko's construction. Jenrich (2025 update) explored sub-25-dimensional counterexamples from the Leech lattice. For n = 4, the best known bound is b(4) <= 9 (can be partitioned into 9 parts). For smooth convex bodies, the conjecture holds for all n (Hadwiger).

**Computational attack vector:**
- For n = 4, 5, 6: exhaustive or heuristic search for counterexample sets using combinatorial optimization.
- SDP/LP bounds on the Borsuk partition number b(n) for small n.
- Search for two-distance sets or other structured point sets in low dimensions that might yield counterexamples.
- Leech lattice computations: explore cross-sections and low-dimensional substructures for counterexamples.
- SAT encoding: for a given point set, determine the minimum number of parts of smaller diameter.

**Verification approach:** A counterexample set is verifiable by computing all pairwise distances and checking that no partition into n+1 parts has smaller diameter. LP/SDP bounds produce certificates.

**Feasibility rating:** HIGH for computational attacks on n = 4, 5, 6. MEDIUM for n = 7-25 via Leech lattice exploration. LOW for determining the exact threshold.

**Bridge value:** Borsuk's conjecture connects topology (Borsuk-Ulam theorem), combinatorial geometry (point configurations, distance sets), and coding theory (binary codes with specified distance distributions). The Kahn-Kalai counterexample used probabilistic combinatorics, and improvements use algebraic structures (Leech lattice).

---

### 13.3 Chromatic Number of Kneser Graphs: Higher Extensions

**Name and reference:** Kneser graph coloring (Lovász 1978; Schrijver 1978; stable Kneser graphs: Björner-de Longueville 2003; Meunier 2014).

**Statement:** chi(KG(n,k)) = n-2k+2 (Lovász, 1978, proved using topological methods). Extensions: determine the chromatic number of r-uniform Kneser hypergraphs KG^r(n,k). The Kneser hypergraph conjecture states chi(KG^r(n,k)) = ceil((n-r(k-1))/(r-1)).

**Current best results:** The Kneser hypergraph conjecture is proved for specific cases using topological methods (Tverberg-type theorems). In 2025, it was shown that the Consensus Division theorem implies lower bounds on chromatic numbers of Kneser hypergraphs, providing new proofs of results by Alon-Frankl-Lovász and Kříž. The stable Kneser graph (Schrijver graph) has been analyzed for its homotopy type (Björner-de Longueville: homotopy spheres). The chromatic number of random Kneser graphs has sharp bounds.

**Computational attack vector:**
- Compute chromatic numbers of small Kneser hypergraphs exactly using SAT solvers or ILP.
- Compute the topological connectivity of neighborhood complexes of Kneser graphs/hypergraphs.
- Implement the Consensus Division approach computationally for specific parameters.
- Compute homotopy types of Hom complexes between specific graphs using discrete Morse theory.

**Verification approach:** Chromatic numbers computed by SAT are certifiable. Topological computations (homology, homotopy type) can be done rigorously for finite complexes. The proofs are formalizeable in Lean.

**Feasibility rating:** HIGH for small parameter computations. MEDIUM for extending topological results to new hypergraph families. LOW for proving the general Kneser hypergraph conjecture.

**Bridge value:** Kneser's conjecture and its proof are the founding monument of topological combinatorics. The chromatic number problem is purely combinatorial, but the proof requires the Borsuk-Ulam theorem (topology). Extensions to hypergraphs require increasingly sophisticated topological tools (Tverberg, equivariant topology), creating a rich two-way flow.

---

### 13.4 Homotopy Type of Graph Complexes

**Name and reference:** Graph complexes (Kontsevich 1993; Vassiliev 1994; Jonsson 2008).

**Statement:** For a monotone graph property P, the graph complex Delta_P is the simplicial complex on edge set E(K_n) where faces are edge sets satisfying P. Determine the homotopy type of Delta_P for fundamental properties: matchings (M_n), forests (F_n), bipartite graphs (B_n), non-Hamiltonian graphs, triangle-free graphs.

**Current best results:** For matching complexes M_n: the homotopy type is known for small n; for large n, the complex is highly connected (Bouc, 1992; Björner-Lovász-Vrecica-Zivaljevic, 1994). For the complex of not-2-connected graphs: homotopy type of a wedge of spheres (Babson-Björner-Linusson-Shareshian-Welker). Forest complexes: homotopy type related to partition lattice. Computational homology of independence complexes of chordal graphs is known to be polynomial, while general simplicial homology is NP-hard.

**Computational attack vector:**
- Compute homology of graph complexes for small n using Smith normal form or persistent homology algorithms.
- Apply discrete Morse theory computationally to reduce complex size before homology computation.
- Use the CHomP or PHAT/Ripser libraries for efficient homology computation.
- Search for discrete Morse functions that reveal the homotopy type.

**Verification approach:** Homology computations are exact (integer arithmetic). Discrete Morse theory reductions are verifiable. The results are formalizable in principle.

**Feasibility rating:** HIGH for homology computation at small n. MEDIUM for discovering homotopy types of new graph complexes. LOW for proving general homotopy type results.

**Bridge value:** Graph complexes are where topology meets combinatorics most intimately. The homotopy type encodes combinatorial information (Betti numbers count "holes" in the combinatorial structure), and topological tools (Morse theory, spectral sequences) provide otherwise inaccessible combinatorial results.

---

### 13.5 Persistent Homology for Combinatorial Structures

**Name and reference:** Persistent homology / TDA for combinatorics (Edelsbrunner-Letscher-Zomorodian 2002; Carlsson 2009; combinatorial PHT: Curry-Mukherjee-Turner 2018).

**Statement:** How can persistent homology be applied to study combinatorial structures (graphs, hypergraphs, simplicial complexes) beyond point cloud data? The Persistent Homology Transform (PHT) assigns to a shape a family of persistence diagrams parameterized by directions. Can the PHT be computed efficiently for combinatorial objects, and does it distinguish combinatorial types?

**Current best results:** The PHT is a complete invariant of embedded simplicial complexes (Turner-Mukherjee-Boyer, 2014). The combinatorial PHT (Curry-Mukherjee-Turner, 2018) recasts this in the category of combinatorial persistence diagrams. Recent 2025 work extends persistent homology via persistent combinatorial Laplacians and persistent Dirac operators, addressing limitations of standard PH (insensitivity to non-topological changes, restriction to point clouds).

**Computational attack vector:**
- Implement the combinatorial PHT and apply to graph/hypergraph classification problems.
- Compute persistent homology of flag complexes arising from combinatorial data.
- Develop efficient algorithms for persistent Laplacian computation on combinatorial complexes.
- Compare PHT-based invariants with classical graph invariants for discrimination power.

**Verification approach:** Persistent homology computations are exact. The PHT completeness theorem is proved. Discrimination results for specific combinatorial families can be verified computationally.

**Feasibility rating:** HIGH for implementation and application. MEDIUM for algorithmic improvements. LOW for proving new theoretical results about PHT discrimination.

**Bridge value:** Persistent homology brings topological thinking to combinatorial data analysis. The PHT provides a complete invariant that captures both topological and geometric information, bridging algebraic topology, computational geometry, and combinatorics. The combinatorial Laplacian perspective connects to spectral graph theory.

---

### 13.6 Lovász Theta Function: Generalizations to Hypergraphs

**Name and reference:** Lovász theta function (Lovász 1979; Jost-Mulas 2021; recursive hypergraph extensions, 2025 conference).

**Statement:** The Lovász theta function vartheta(G) provides a polynomial-time computable bound: alpha(G) <= vartheta(G) <= chi-bar(G). Generalize vartheta to uniform hypergraphs in a way that preserves its key properties (sandwiching, SDP computability, connection to capacity).

**Current best results:** Several proposals for hypergraph theta functions exist, with different properties. The walk-generating function characterization (2025) provides a new approach. Recursive definitions for r-uniform hypergraphs were presented in 2025. For graphs, the Lovász theta equals the quantum Shannon capacity for self-complementary vertex-transitive graphs, but the hypergraph analogue of this connection is unexplored.

**Computational attack vector:**
- Implement the various proposed hypergraph theta functions and compare them on specific hypergraph families.
- Compute the SDP relaxation for hypergraph independence number and compare with proposed theta functions.
- Search for hypergraphs where different theta generalizations diverge most.
- Test the walk-generating function approach on specific graph/hypergraph families.

**Verification approach:** SDP computations are certifiable. Comparison with exact independence numbers provides validation. The algebraic characterizations are verifiable.

**Feasibility rating:** HIGH for computational comparison of proposals. MEDIUM for discovering which generalization is "right." LOW for proving optimal properties.

**Bridge value:** The Lovász theta function is the most celebrated meeting point of topology (neighborhood complex), combinatorics (chromatic number, independence number), information theory (Shannon capacity), and optimization (SDP). Its generalization to hypergraphs would extend this bridge to a much richer combinatorial landscape.

---

### 13.7 Equivariant Topology Methods for Chromatic Number Lower Bounds

**Name and reference:** Topological lower bounds on chromatic number (Lovász 1978; Babson-Kozlov 2006; Schultz 2021).

**Statement:** The Lovász bound chi(G) >= conn(N(G)) + 3 (where N(G) is the neighborhood complex and conn denotes connectivity) provides a topological lower bound on chromatic number. How tight is this bound? For which graph families is it tight? Can it be improved using higher homotopy information?

**Current best results:** The bound is tight for Kneser graphs and Schrijver graphs. It is not tight in general (the bound can be arbitrarily loose). Babson-Kozlov proved that the Hom complex Hom(K_2, G) has the same connectivity as N(G), providing an alternative topological approach. The Stiefel-Whitney characteristic class of the Hom complex provides additional information in some cases. Reconfiguration and discrete homotopy theory provide new perspectives.

**Computational attack vector:**
- Compute conn(N(G)) for small graphs by computing the homotopy type of the neighborhood complex.
- Compare the topological bound with the actual chromatic number for systematic graph families.
- Compute Hom complexes and their homotopy type using discrete Morse theory.
- Implement the Stiefel-Whitney class computation for Hom complexes.

**Verification approach:** Homotopy computations are exact for finite complexes. Chromatic number computation by SAT provides the comparison value. All computations are rigorous.

**Feasibility rating:** HIGH for small graph computations. MEDIUM for identifying graph families where the bound is tight. LOW for proving tightness results.

**Bridge value:** This is the core mechanism of topological combinatorics: using the topology of associated complexes to derive combinatorial bounds. The gap between the topological bound and the true chromatic number measures how much combinatorial information is invisible to topology. Understanding this gap is central to both fields.

---

### 13.8 Ham Sandwich Theorem: Computational and Generalized Versions

**Name and reference:** Ham sandwich theorem (Banach-Steinhaus 1938; generalizations: Barany 1981; Zivaljevic-Vrecica 1990; Soberon 2012).

**Statement:** Any d finite Borel measures in R^d can be simultaneously bisected by a single hyperplane. Generalizations: the Grünbaum-Hadwiger-Ramos problem asks for the minimum number of hyperplanes needed to simultaneously bisect j measures into 2^j equal parts in R^d. The "colorful" ham sandwich theorem (Barany-Hubard-Jeronimo 2008) provides additional structure.

**Current best results:** The Grünbaum-Hadwiger-Ramos problem is solved for d = 2 and partially for d = 3. The colorful generalization (proved using the colorful Borsuk-Ulam theorem) provides new existence results. The algorithmic problem of finding ham sandwich cuts is well-studied: exact algorithms in O(n^{d-1}) time and approximate algorithms exist.

**Computational attack vector:**
- Implement exact ham sandwich cut algorithms for point measures in R^d for small d.
- Compute Grünbaum-Hadwiger-Ramos solutions for small (d,j) by exhaustive search over hyperplane arrangements.
- Test colorful ham sandwich theorem computationally for random point configurations.
- Develop certified algorithms that produce provably correct ham sandwich cuts with numerical certificates.

**Verification approach:** A ham sandwich cut can be verified by counting points on each side. Algorithmic certificates are constructive. The topological proofs can be made computational via equivariant Borsuk-Ulam algorithms.

**Feasibility rating:** HIGH for algorithmic implementation. MEDIUM for resolving Grünbaum-Hadwiger-Ramos in low dimensions. LOW for general solutions.

**Bridge value:** The ham sandwich theorem is where the Borsuk-Ulam theorem (topology) meets computational geometry (hyperplane arrangements, fair division). The algorithmic challenge of finding the cut that topology guarantees exists creates a productive tension between existence proofs and constructive methods.

---

### 13.9 Simplicial Depth and Topological Data Analysis for Combinatorial Optimization

**Name and reference:** Topological methods for combinatorial optimization (Ehrenborg 2007; Adiprasito-Benedetti 2017; Kahle 2011).

**Statement:** Random simplicial complexes (analogues of Erdős-Rényi random graphs) undergo topological phase transitions. Characterize these transitions: at what density does the random d-complex on n vertices become d-connected? What is the threshold for the vanishing of the (d-1)-th homology?

**Current best results:** The Linial-Meshulam model for random 2-complexes: the homology threshold is at p ~ (2 log n)/n (analogous to the connectivity threshold for random graphs). For higher-dimensional complexes, the threshold for vanishing of H_{d-1} with Z/2 coefficients is known. The threshold for integer homology involves more subtle number-theoretic considerations (torsion). Random flag complexes have been studied extensively (Kahle, 2009-2014).

**Computational attack vector:**
- Monte Carlo simulation of random simplicial complexes at various densities, computing homology at each sample.
- Detect phase transitions numerically by tracking Betti numbers as density varies.
- Compare theoretical thresholds with empirical observations for d = 2, 3, 4.
- Study the torsion in random simplicial complexes computationally.

**Verification approach:** Homology computations are exact. Phase transition detection is statistical. The theoretical thresholds provide predictions to verify.

**Feasibility rating:** HIGH for simulation and homology computation. MEDIUM for torsion analysis. LOW for proving new threshold results.

**Bridge value:** Random simplicial complexes are the higher-dimensional generalization of random graphs, connecting algebraic topology (homology, torsion) with probabilistic combinatorics (phase transitions, thresholds). The topological phase transition is a new type of combinatorial phenomenon revealed by topology.

---

### 13.10 Topological Bounds on the Turán Problem for Hypergraphs

**Name and reference:** Turán-type problems and topological methods (Frankl-Füredi 1984; Mubayi-Verstraëte; de Caen-Füredi 2000).

**Statement:** For a k-uniform hypergraph F, determine the Turán number ex(n,F) = maximum number of hyperedges in a k-uniform hypergraph on n vertices not containing F as a subhypergraph. For which F can topological methods (e.g., the topological Tverberg theorem, Borsuk-Ulam) provide bounds?

**Current best results:** For the Fano plane (the unique (7,3,1)-design), ex(n, Fano) was determined exactly (de Caen-Füredi, 2000; Keevash-Sudakov, 2005). For the octahedron hypergraph and other structured hypergraphs, bounds have been improved using a combination of algebraic and topological methods. The general Turán problem for 3-uniform hypergraphs remains wide open (even for the tetrahedron K_4^3).

**Computational attack vector:**
- Compute ex(n,F) exactly for small n and specific forbidden hypergraphs F using ILP.
- Use flag algebra computations (Razborov's method) to derive asymptotic upper bounds.
- Search for connections between the topological properties of F (e.g., homology of its independence complex) and the Turán density.
- Implement Razborov's flag algebra framework for specific hypergraph Turán problems.

**Verification approach:** Exact Turán numbers are verifiable. Flag algebra certificates are formal proofs. ILP solutions produce certificates.

**Feasibility rating:** HIGH for small exact computations and flag algebra bounds. MEDIUM for discovering new connections. LOW for determining Turán densities of basic hypergraphs.

**Bridge value:** The hypergraph Turán problem is central to extremal combinatorics, and topological methods provide a new approach to these notoriously difficult problems. The flag algebra method has a combinatorial/algebraic character that bridges with topology through the structure of forbidden configurations.

---

## Cross-Domain Computational Cross-Pollination Highlights

### Problems Where Both Sides of the Bridge Enable Computational Progress

1. **AG codes and Ihara's constant (Domains 9.12 + 10.1):** Number-theoretic curve searches yield better codes; coding-theoretic needs motivate targeted curve searches. Both sides use the same computational algebra infrastructure (Magma, SageMath).

2. **Quantum chromatic number and nonlocal games (Domains 11.1 + 11.6):** Graph-theoretic enumeration (SAT solvers) identifies candidate graphs; quantum information tools (SDP/NPA hierarchy) compute quantum parameters. The combination is strictly more powerful than either alone.

3. **Shannon capacity of C_7 (Domain 9.7) and quantum Shannon capacity (Domain 11.2):** The same SDP infrastructure applies to both classical and quantum versions. Quantum entanglement potentially provides new constructions for independent sets in strong products.

4. **Entropy methods and additive combinatorics (Domains 12.3 + 12.10):** Information-theoretic inequality provers (ITIP) automate entropy-based combinatorial proofs. Combinatorial structure (small doubling, sum-product) guides which entropy inequalities to seek.

5. **Topological Tverberg and Kneser chromatic numbers (Domains 13.1 + 13.3):** The same equivariant obstruction theory applies to both. Computational topology tools (discrete Morse theory, homology computation) serve both problems simultaneously.

6. **Deletion channel capacity (Domains 9.6/12.1) and DNA storage codes (Domain 9.10):** Channel capacity bounds inform DNA code design; DNA sequencing experiments provide empirical channel models. The combinatorics of subsequences underpins both.

7. **Borsuk's conjecture (Domain 13.2) and binary codes (Domain 9):** Point sets giving Borsuk counterexamples often have code-like structure (two-distance sets from Leech lattice). Coding theory bounds on distance distributions constrain Borsuk counterexamples.

8. **Quantum LDPC codes (Domain 11.4) and graph complexes (Domain 13.4):** Quantum LDPC codes are constructed from homological products of chain complexes---the same objects whose homotopy type is studied in topological combinatorics. Breakthroughs in one directly enable the other.
