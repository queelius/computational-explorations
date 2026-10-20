> Historical research note from October 18, 2026; promoted October 20.
> Read README.md in this directory for current status and reproduction.
> Statements about unresolved work describe that historical stage.

# Every longest nine-vertex path has at most five possible endpoints

Definitions: G17 has vertex set {1,...,17}, with edges exactly between coprime integers. Paths are simple and length counts edges. Consider a red/blue coloring with no monochromatic nine-edge path.

## Finite host-cut lemma

For any disjoint sets A,B of sizes six and eight, the host edges between A and B cannot all have the same color in an avoiding coloring.

The proof is a finite, independently replayable case proof. The host automorphism classes are derived and checked by transposing pairs and testing every unordered vertex pair. They are

{1,11,13,17}, {2,4,8,16}, {3,9}, {5}, {6,12}, {7}, {10}, {14}, {15}.

The 30,793 orbits of disjoint six/eight sets are all covered. In 30,749 orbits the crossing graph already contains a nine-edge path, supplied as a positive witness. The remaining 44 orbits admit a contradiction after assuming all crossing edges blue. Each implication consists of an unassigned host edge e, a proposed forced color c, and a ten-distinct-vertex path whose other edges were already assigned color 1-c. Hence e must have color c. There are 1,079 such implications in total, followed by 44 explicit monochromatic nine-edge paths. Every terminal contradiction is a path: the proof uses no edge-count, connectivity, or other structural hypothesis, and it imposes no symmetry on the coloring.

Artifacts:
- attempts/009-near-extremal-structure/endpoint-cuts.json.gz
- attempts/009-near-extremal-structure/validate_endpoint_cuts.py
- attempts/012-endpoint-forced-edges/propagation.json.gz
- attempts/012-endpoint-forced-edges/validate.py

The first validator independently derives the host symmetry, reconstructs every orbit signature, validates the direct paths, and also checks the 44 negative crossing graphs by subset dynamic programming. Negative checks are not logically necessary for the combined lemma: each of those cases is separately contradicted by the positive implication proof. The second validator replays every implication without searching for paths; it rejects count-based contradictions.

## Endpoint consequence

Let X be a nine-vertex set on which the red graph has a Hamilton path. Let E(X) be the set of all vertices that occur as an endpoint of some red Hamilton path on X. Every host edge from E(X) to Y=V(G17)\X is blue. Otherwise its red edge extends a corresponding red Hamilton path to ten vertices. If |E(X)|>=6, choose six of its vertices. Their crossing edges to the eight vertices Y are blue, contradicting the cut lemma. Thus |E(X)|<=5. The argument applies to either color.

Every possible endpoint v has red degree at most four in the full graph. All its red neighbors lie in X. Choose a Hamilton ordering x1,...,x9=v. For each neighbor xi of v, reversing the terminal segment gives an endpoint x_(i+1) on the same X (with i=8 giving v itself). These d(v) endpoints are distinct and exclude x1, which is also a possible endpoint. Therefore d(v)+1<=|E(X)|<=5.

Both hypothetical color graphs contain such an X: earlier work proves each connected and with 47/48 edges; Balister--Gyori--Lehel--Schelp Theorem 1.3 bounds a connected P9-free 17-vertex graph by max(31,46)=46 edges. Source: https://www.memphis.edu/msci/people/pbalistr/nopk.pdf .

## Limit

This is a necessary condition, not a contradiction. The remaining dense color graphs may have all longest-path endpoint sets of size at most five and all longest-path endpoints of degree at most four. Exact P_cop(9)=17 is still unresolved.
