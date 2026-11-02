# The nine-edge coprime path threshold is 17

**October 18, 2026 — Alexander Richard Towell; investigation assisted by Codex.**

Let G_n have vertex set {1,…,n}, with an edge between coprime distinct
integers. Let P_cop(k) be the least n such that every two-coloring of its
edges contains a monochromatic simple path with **k edges**.

**Theorem. P_cop(9) = 17.** The upper bound follows by combining the
[previously certified structural constraints](coprime-path-nine-2026-10-18.md)
with the extremal classification proved below. Those constraints say that
any avoiding coloring of G_17 has connected color graphs with 47 and 48
edges, each retaining at least five edges after every four-vertex deletion.
The 48-edge color cannot satisfy these conditions.

For the lower bound, split the eight odd vertices of G_16 into
A={1,3,5,7} and B={9,11,13,15}. Give an edge color 0 if it meets A,
and color 1 otherwise. All edges meet an odd vertex, so each color has a
four-vertex cover. A simple path in a graph with a cover of size four has
at most eight edges. The [complete 79-edge witness](audits/coprime-path-nine-resolution-2026-10-18/lower-n16-k9.json)
is also checked independently by subset dynamic programming; both longest
path lengths are eight.

The [audit record](audits/coprime-path-nine-resolution-2026-10-18/README.md)
identifies the finite certificates, primary sources, auxiliary checks, and
limits of verification. This is a mathematical proof using independently
checked finite lemmas; it is not a Lean formalization or a new SAT UNSAT
certificate. No priority claim or proof of the infinite odd-path family is
made. The earlier structural note is retained as the record of that stage.

## Extremal classification

Every connected graph G on 17 vertices, with exactly 48 edges and no path
on ten vertices, either has a vertex cover of size at most four or is
isomorphic to

    K3 join (K3 disjoint union I11).

In either case, some four-vertex deletion leaves at most one edge.
This contradicts the deletion condition for the 48-edge color in an
avoiding coloring of G_17.

All path sizes P_j count vertices; ordinary path lengths count edges.

## Published ingredients and definitions

Define H(n,k,a) by parts A,B,C of sizes a,n-k+a,k-2a, with every A-B edge
and every edge inside A union C. Its edge count is

    h(n,k,a) = binom(k-a,2) + a(n-k+a).

For k=11, write F0 for the family of K(5,6) graphs with at most two edges
deleted, with parts A of size five and B of size six.

1. **FKV stability.** Füredi, Kostochka, Verstraëte,
   https://arxiv.org/pdf/1507.05338v2 , Theorem 1.4: a 2-connected graph
   on n>=15 vertices with no cycle of length at least 11 and more than
   h(n,11,4) edges is a subgraph of H(n,11,5).
2. **FKVL stability for smaller orders.** Füredi, Kostochka, Luo,
   Verstraëte, https://arxiv.org/pdf/1704.02866 , Theorem 2.3: for n>=11,
   more than max(h(n,11,4),h(n,11,3)) edges gives containment in
   H(n,11,5) or H(n,11,2), under the same connectivity and circumference
   assumptions. Here

       h(n,11,4)=4n-7, h(n,11,3)=3n+4, h(n,11,2)=2n+18.

3. **Dense bipartite subgraph and contraction.** FKVL Lemma 4.6 says a
   subgraph of H(n,11,5) with more than h(n,11,4) edges contains a member
   of F0. FKV Lemma 4.9 says that if Q and Q/xy are 2-connected, Q has
   circumference less than 11, and Q/xy contains F0, then Q contains F0.
   This last statement has no density requirement.
4. **Paths within F0.** FKV Lemma 4.8(a),(b): between any two vertices of
   F0 there is a path of length at least eight; unless both lie in A,
   there is one of length at least nine. In particular, between two B
   vertices the latter length is even, hence ten.
5. **Ali–Staton classification.** Ali and Staton, *On Extremal Graphs
   With No Long Paths*, Electronic Journal of Combinatorics 3 (1996),
   R20, https://doi.org/10.37236/1244 , Theorem 3: if a connected graph
   has minimum degree delta>=2, longest path order exactly 2*delta+1,
   and n>=2*delta+2, then it is a subgraph of K_delta join I_(n-delta),
   or is exactly K1 join t disjoint K_delta's, n=t*delta+1.
6. **Hamiltonian closure and Chvátal.** Adding an edge between nonadjacent
   vertices whose degree sum is at least the order preserves existence
   of a Hamiltonian cycle (Bondy–Chvátal, *A method in graph theory*,
   Discrete Mathematics 15 (1976), 111–135,
   https://doi.org/10.1016/0012-365X(76)90078-9 ; the publisher's abstract
   explicitly states the Hamiltonian n-closure implication). Chvátal's degree-sequence
   theorem says a non-Hamiltonian n-vertex graph, with ascending degrees
   d_1,...,d_n, has some i<n/2 with d_i<=i and d_(n-i)<=n-i-1. The latter
   is also stated as FKVL Theorem 4.2.

## 1. F0 in an augmentation forces a four-vertex cover

Let Q be 2-connected, contain F0 with parts A,B, and have no cycle of
length at least 11. Each component S outside A union B has at least two
attachment vertices in A union B. If |S|>=2, 2-connectivity implies that
there is a path between two distinct attachment vertices with at least
two internal vertices in S. Indeed, the attachment edges meet at least
two vertices on each side, since a unique incident vertex on either side
would separate S. Choose attachment edges ax and by with a!=b in F0 and
x!=y in S, and join x to y within S. Such a path has length at least three, and
the eight-edge path between its endpoints in F0 gives a forbidden cycle.
Thus every S is a singleton.

If this singleton has an attachment in B, take another attachment; the
nine-edge F0 path between them completes a forbidden cycle. Hence all
outside vertices attach only to A. No edge can lie inside B, because it
would close a ten-edge B-to-B path in F0. Thus Q-A is independent, so A
is a vertex cover of size five.

In the universal-vertex augmentation Q=G+u of a connected graph G on at
least ten vertices, u must belong to A: every vertex outside A has degree
at most five. Hence G has a four-vertex cover.

We may therefore assume that G has no four-vertex cover; its augmentation
Q contains no F0. Every induced augmentation occurring below also contains
no F0.

## 2. Low-triangle contractions and seven simplicial deletions

Initially, Q has 18 vertices and 65 edges. If an edge xy of G lies in at
most one triangle, it lies in at most two triangles of Q. Contracting xy
therefore leaves a 17-vertex graph Q' with at least 62 edges. Q' is the
universal augmentation of connected G/xy, so is 2-connected, and its
circumference is still less than 11. Since 62>h(17,11,4)=61, ingredients
1 and 3 give F0 in Q', then in Q, a contradiction. Thus every edge of G
lies in at least two triangles, in particular delta(G)>=3.

We will maintain, for the current induced graph J on n vertices:

    J is connected and P10-free; e(J)=3n-3;
    its universal augmentation contains no F0;
    delta(J)>=2.

For n>=13, a contraction of an edge in at most one triangle would leave
an n-vertex augmentation with at least 4n-6 edges. This exceeds both
h(n,11,4)=4n-7 and h(n,11,3)=3n+4, and also h(n,11,2)=2n+18. Ingredients
2 and 3 again force F0. Thus every edge lies in at least two triangles.

For n=11 or 12 the same contraction still exceeds the two stability
thresholds, but H(n,11,2) could meet the edge count. It cannot occur for
the following reason. In a connected graph of minimum degree at least
two and order greater than three, contracting an edge in at most one
triangle creates at most one leaf. Indeed, an old vertex can become a
leaf only if it is the unique common neighbor of the endpoints. The
merged vertex can become a leaf only if both endpoints have degree two
and share that neighbor. Both possibilities together would make the
three vertices an isolated triangle, contradicting connectivity.

On the other hand, the universal vertex in a subgraph of H(n,11,2) must
be one of its two A vertices. Removing it leaves a graph contained in
K1 join (K7 disjoint union I_(n-9)). Connectivity forces all n-9>=2
degree-one vertices to retain their edge. This contradicts the at-most-
one-leaf conclusion. Therefore every edge lies in at least two triangles
also at n=11 and n=12.

At each n>=11, minimum degree at least four is impossible. First, a longest
nonspanning path has at least 2*delta+1 vertices. Otherwise its endpoint
neighbor sets, indexed along the path, overlap to close the entire path
into a cycle; connectivity supplies an edge from outside that cycle and
extends the path. Here the longest path has at most nine vertices and is
nonspanning, so delta>=4 forces delta=4 and longest path order exactly nine.
Apply Ali–Staton, with n>=11>2*4+1. The windmill exception has 5(n-1)/2 edges, less than
3n-3. In the K4 join independent-set exception, minimum degree four makes
every edge between the four-vertex side and the independent side present.
Its augmentation then contains K(5,6), since n-4>=7, contrary to the
absence of F0. Thus the current graph has a degree-three vertex.

As every incident edge is in two triangles, the three neighbors of every
degree-three vertex form a triangle. Deleting such a simplicial vertex
preserves connectivity and the equality e(J)=3n-3; the new minimum degree
is at least two. We can therefore delete seven vertices, obtaining a
connected P10-free graph J10 on ten vertices with 27 edges and minimum
degree at least two. Its predecessor J11 had minimum degree at least
three. Reverse reconstruction adds one vertex at a time whose neighborhood
among already present vertices is a clique of size exactly three.

## 3. Classification of the ten-vertex core

Augment J10 by a universal vertex to obtain Q11, with eleven vertices,
37 edges, and minimum degree at least three. It is non-Hamiltonian because
J10 has no Hamilton path. Take its 11-closure Q*.

If closure adds any edge, Q* has at least 38 edges. FKVL Theorem 2.3 gives
containment in H(11,11,5) or H(11,11,2), because both stability thresholds
equal 37. Minimum degree at least three rules out H(11,11,2), whose two
B vertices have degree two. Thus Q11 is a subgraph of K5 join I6, and
J10 is a subgraph of K4 join I6.

Suppose closure adds no edge. Q11 is already closed. Chvátal gives
i in {3,4,5}, because its minimum degree is at least three. Removing the
universal vertex gives the corresponding bounds on J10's ascending
degree sequence.

For i=3 they are

    (2,2,2,6,6,6,6,6,9,9).

Their sum is exactly 54=2e(J10), so equality holds in every bound. The
two universal vertices meet all vertices; the three degree-two vertices
have no other neighbors; and the remaining five form a clique. Hence

    J10 = K2 join (K5 disjoint union I3).

For i=4 the upper sequence is

    (3,3,3,3,5,5,5,9,9,9).

Again its sum is 54, forcing

    J10 = K3 join (K3 disjoint union I4).

For i=5, choose B to be six vertices of degree at most five in Q11 and
A the remaining five. The total degree is 74; the upper bound from these
classes is 6*5+5*10=80, leaving total deficit six. If two A vertices were
nonadjacent, closure would give degree sum at most ten, producing deficit
at least ten just on those two vertices. Thus A is a clique.

Let b=e(Q11[B]) and let m be the number of absent A-B edges. The edge
count gives m=b+3. For v in B put

    s_v = number of absent A-B edges at v,
    t_v = degree of v inside B,
    q_v = s_v-t_v >=0.

The last inequality follows from d(v)<=5. Consequently
sum(q_v)=m-2b=3-b and 0<=b<=3. Let r_a be the number of missing cross
edges at a in A. For every absent pair av, closedness implies

    (10-r_a)+(5-q_v)<=10, so r_a+q_v>=5.

If b=1,2,3 then every nonempty missing row has at least 2+b entries,
while m=b+3; hence only one row can be nonempty. Therefore each s_v is
at most one, and B's edges form a matching. For b=1, the two matching
endpoints have q_v=0, demanding r_a>=5, but m=4, impossible.

For b=2, the unique row misses the four matching endpoints and one of
the two isolated B vertices. For b=3 it misses all six B vertices.
In both cases Q11 is isomorphic to K4 join (3K2 disjoint union K1),
which is Hamiltonian: place the three two-vertex blocks and the singleton
between successive vertices of K4 in a cycle. This is impossible.

Thus b=0 and Q11 is a subgraph of K5 join I6. Its universal vertex belongs
to the K5 side, so J10 is again a subgraph of K4 join I6.

These are the only three core possibilities.

## 4. Reconstructing the seven vertices

The K2 join (K5 union I3) case is impossible. All three degree-two core
vertices must have been neighbors of the last deleted vertex, because
the predecessor J11 had minimum degree at least three. But these three
vertices are independent, whereas the deleted vertex's three neighbors
form a clique.

For J10=K3 join (K3 union I4), write A for the joining triangle, C for
the second triangle, and B for the independent set. Every vertex outside
A starts a nine-vertex path. Representative paths are

    c1,c2,c3,a1,b1,a2,b2,a3,b3,
    b1,a1,c1,c2,c3,a2,b2,a3,b3.

Adding a vertex adjacent to any such endpoint would create P10. Thus
the first reconstructed vertex has neighborhood exactly A. The same
templates show that this new vertex also starts a nine-vertex path.
Induction forces all seven new neighborhoods to equal A, giving exactly
K3 join (K3 union I11), as claimed.

Finally suppose J10 is a subgraph of K4 join I6, with sides A and B.
The complete container has 30 edges, so at most three cross edges are
missing. Every vertex of B starts a nine-vertex path, as does any added
vertex having at least one neighbor in A. Here is a Hall argument.

For a chosen starting vertex z, choose a neighbor a1 in A and order the
remaining vertices a2,a3,a4. If z belongs to B, reserve it and use the
other five vertices of B. If z is new, use any five original B vertices.
We seek distinct B representatives for the four slots

    {a1,a2}, {a2,a3}, {a3,a4}, {a4}.

A vertex is eligible for a slot when all required cross edges are
present. Every slot has at least two eligible vertices. A B vertex
ineligible for every slot in any three- or four-slot collection requires
at least two missing edges, since one missing edge affects at most two
slots. With at most three missing edges, at most one B vertex can be
excluded from such a union. These unions therefore have at least four
vertices, and Hall's condition holds for every subset of slots. The
resulting path is

    z,a1,b1,a2,b2,a3,b3,a4,b4.

Consider the first reconstructed vertex whose clique neighborhood is not
contained in A. It is adjacent to an earlier vertex outside A, which by
the preceding argument starts a nine-vertex path in the earlier graph.
Prepending the new vertex gives P10. Thus no such first vertex exists:
all reconstructed neighborhoods lie in A, and A is a four-vertex cover
of the final graph. This contradicts the standing no-four-cover assumption.

The classification follows. In its second case delete A and one vertex
of C, leaving the single edge on the other two C vertices.

