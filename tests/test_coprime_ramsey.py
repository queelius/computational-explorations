"""Tests for coprime_ramsey.py (NPG-26)."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from coprime_ramsey import (
    coprime_edges,
    is_clique_in_color,
    has_monochromatic_clique,
    coprime_clique_number,
    coprime_ramsey_lower_bound,
    compute_coprime_ramsey,
)


class TestCoprimeEdges:
    def test_n3(self):
        edges = coprime_edges(3)
        # (1,2), (1,3), (2,3)
        assert (1, 2) in edges
        assert (1, 3) in edges
        assert (2, 3) in edges
        assert len(edges) == 3

    def test_n4(self):
        edges = coprime_edges(4)
        # (1,2),(1,3),(1,4),(2,3),(3,4) — NOT (2,4) since gcd=2
        assert (2, 4) not in edges
        assert (1, 4) in edges

    def test_edge_count_n5(self):
        edges = coprime_edges(5)
        # 1 coprime with all: 4 edges
        # 2-3: gcd=1, 2-5: gcd=1, 3-4: gcd=1, 3-5: gcd=1, 4-5: gcd=1
        # Total: 4 + 3 + 2 - non-coprime... let me just count
        expected = sum(1 for i in range(1, 6)
                       for j in range(i + 1, 6) if math.gcd(i, j) == 1)
        assert len(edges) == expected

    def test_monotone(self):
        assert len(coprime_edges(5)) <= len(coprime_edges(10))


class TestIsCliqueInColor:
    def test_coprime_triple_same_color(self):
        coloring = {(1, 2): 0, (1, 3): 0, (2, 3): 0}
        assert is_clique_in_color({1, 2, 3}, coloring, 0)

    def test_coprime_triple_mixed_color(self):
        coloring = {(1, 2): 0, (1, 3): 1, (2, 3): 0}
        assert not is_clique_in_color({1, 2, 3}, coloring, 0)
        assert not is_clique_in_color({1, 2, 3}, coloring, 1)

    def test_non_coprime_vertices(self):
        coloring = {(2, 4): 0}
        # gcd(2,4)=2, not coprime, so not a clique
        assert not is_clique_in_color({2, 4}, coloring, 0)


class TestHasMonochromaticClique:
    def test_all_one_color_has_triangle(self):
        n = 5
        edges = coprime_edges(n)
        coloring = {e: 0 for e in edges}
        result = has_monochromatic_clique(n, 3, coloring)
        assert result is not None
        color, verts = result
        assert color == 0
        assert len(verts) == 3

    def test_k2_always_exists(self):
        # For k=2 (edges), any coloring has a monochromatic edge if n ≥ 2
        n = 3
        edges = coprime_edges(n)
        for bits in range(2 ** len(edges)):
            coloring = {e: (bits >> i) & 1 for i, e in enumerate(edges)}
            result = has_monochromatic_clique(n, 2, coloring)
            assert result is not None


class TestCoprimeCliqueNumber:
    def test_n5(self):
        omega = coprime_clique_number(5)
        # {1, 2, 3, 5} are mutually coprime? 1 is coprime with all.
        # 2,3: gcd=1. 2,5: gcd=1. 3,5: gcd=1. So {1,2,3,5} works. Size 4.
        assert omega >= 4

    def test_n10(self):
        omega = coprime_clique_number(10)
        # {1} + primes {2,3,5,7} = size 5
        assert omega >= 5

    def test_monotone(self):
        assert coprime_clique_number(5) <= coprime_clique_number(10)


class TestLowerBound:
    def test_lower_bound_k3(self):
        lb = coprime_ramsey_lower_bound(3, max_n=10)
        # R_cop(3) > some value; lower bound should be ≥ 3
        assert lb >= 3

    def test_lower_bound_k2(self):
        # R_cop(2) = 2 (trivial: any edge is monochromatic)
        # So lower bound = 1 (n=1 has no edges)
        lb = coprime_ramsey_lower_bound(2, max_n=5)
        assert lb == 1


class TestExactRCop3:
    """Test the exact value R_cop(3) = 11, computed by extension method.

    Strategy: start with 36 avoiding colorings at n=8 (exhaustive),
    extend through n=9,10,11. At n=11 no extension avoids mono K_3.
    """

    def test_n8_has_avoiding_colorings(self):
        """n=8 has exactly 36 colorings avoiding monochromatic K_3."""
        edges = coprime_edges(8)
        count = 0
        for bits in range(2 ** len(edges)):
            coloring = {e: (bits >> i) & 1 for i, e in enumerate(edges)}
            if has_monochromatic_clique(8, 3, coloring) is None:
                count += 1
        assert count == 36

    def test_n10_has_avoiding_colorings(self):
        """n=10 still has avoiding colorings (R_cop(3) > 10)."""
        import math
        # Build from n=8 avoiding colorings
        edges_8 = coprime_edges(8)
        avoiding = []
        for bits in range(2 ** len(edges_8)):
            col = {e: (bits >> i) & 1 for i, e in enumerate(edges_8)}
            if has_monochromatic_clique(8, 3, col) is None:
                avoiding.append(col)

        for n in [9, 10]:
            new_edges = [(i, n) for i in range(1, n) if math.gcd(i, n) == 1]
            next_avoiding = []
            for col in avoiding:
                for bits in range(2 ** len(new_edges)):
                    new_col = dict(col)
                    for i, e in enumerate(new_edges):
                        new_col[e] = (bits >> i) & 1
                    if has_monochromatic_clique(n, 3, new_col) is None:
                        next_avoiding.append(new_col)
            avoiding = next_avoiding

        assert len(avoiding) == 156, f"Expected 156 avoiding at n=10, got {len(avoiding)}"

    def test_rcop3_equals_11(self):
        """R_cop(3) = 11: no 2-coloring at n=11 avoids monochromatic K_3."""
        import math
        edges_8 = coprime_edges(8)
        avoiding = []
        for bits in range(2 ** len(edges_8)):
            col = {e: (bits >> i) & 1 for i, e in enumerate(edges_8)}
            if has_monochromatic_clique(8, 3, col) is None:
                avoiding.append(col)

        for n in [9, 10, 11]:
            new_edges = [(i, n) for i in range(1, n) if math.gcd(i, n) == 1]
            next_avoiding = []
            for col in avoiding:
                for bits in range(2 ** len(new_edges)):
                    new_col = dict(col)
                    for i, e in enumerate(new_edges):
                        new_col[e] = (bits >> i) & 1
                    if has_monochromatic_clique(n, 3, new_col) is None:
                        next_avoiding.append(new_col)
            avoiding = next_avoiding

        assert len(avoiding) == 0, f"Expected 0 avoiding at n=11, got {len(avoiding)}"


class TestComputeCoprimeRamsey:
    """Test the compute_coprime_ramsey function."""

    def test_rcop2(self):
        # R_cop(2) = 2: any 2-coloring of coprime edges on {1,2} has a
        # monochromatic edge (since gcd(1,2)=1, the single edge must be
        # one color).
        result = compute_coprime_ramsey(2, max_n=5)
        assert result == 2

    def test_rcop3_not_found_below_9(self):
        # R_cop(3) = 11 (known). At n=8 there are 21 coprime edges (<=25),
        # and avoiding colorings exist, so compute should return -1 for max_n=8.
        result = compute_coprime_ramsey(3, max_n=8)
        assert result == -1  # not found: avoiding colorings exist up to n=8

    def test_rcop3_exact(self):
        """compute_coprime_ramsey(3) should return exactly 11."""
        result = compute_coprime_ramsey(3, max_n=15)
        assert result == 11

    def test_rcop_not_found(self):
        # If max_n is too small to find R_cop(k), should return -1
        result = compute_coprime_ramsey(3, max_n=3)
        assert result == -1 or result >= 3  # either not found or found small


class TestCoprimeLowerBoundHeuristic:
    """Test the heuristic branch of coprime_ramsey_lower_bound."""

    def test_lower_bound_k3_medium(self):
        """Lower bound for k=3 with max_n=10 should find avoiding colorings."""
        lb = coprime_ramsey_lower_bound(3, max_n=10)
        # R_cop(3) = 11, so avoiding colorings exist at n≤10
        # Heuristic may not find all — just check it finds something reasonable
        assert lb >= 6
        assert lb <= 10

    def test_lower_bound_k2_trivial(self):
        """k=2: any edge is K_2, so lower bound should be small."""
        lb = coprime_ramsey_lower_bound(2, max_n=10)
        assert lb >= 1

    def test_lower_bound_monotone(self):
        """Larger max_n should give same or larger lower bound."""
        lb1 = coprime_ramsey_lower_bound(3, max_n=8)
        lb2 = coprime_ramsey_lower_bound(3, max_n=12)
        assert lb2 >= lb1


class TestComputeRamseyHeuristicBranch:
    """Tests for the heuristic branch (edges > 25) of compute_coprime_ramsey."""

    def test_rcop_k2_heuristic(self):
        """k=2 with max_n=5 exercises the exhaustive branch (<= 25 edges).

        At small n, all edges fit in the exhaustive branch.
        """
        result = compute_coprime_ramsey(2, max_n=5)
        assert result >= 2
        assert result <= 3

    def test_rcop_k2_fast(self):
        """k=2 should be found quickly (any coprime pair forces K_2)."""
        result = compute_coprime_ramsey(2, max_n=5)
        assert result >= 2
        assert result <= 3  # (1,2) is coprime, any 2-coloring has monochromatic K_2 at n=3


class TestCoprimeCliqueNumberExtended:
    """Additional tests for coprime_clique_number."""

    def test_clique_small_values(self):
        """Known clique numbers for small n."""
        # n=2: {1,2} coprime → clique of size 2
        assert coprime_clique_number(2) == 2
        # n=3: {1,2,3} all pairwise coprime → clique of size 3
        assert coprime_clique_number(3) == 3

    def test_clique_n1(self):
        """Single vertex has clique number 1."""
        assert coprime_clique_number(1) == 1

    def test_clique_n10(self):
        """n=10: clique includes 1 + primes {2,3,5,7} = 5."""
        result = coprime_clique_number(10)
        assert result >= 5  # at least {1,2,3,5,7}

    def test_clique_n15(self):
        """n=15: clique includes 1 + primes {2,3,5,7,11,13} = 7."""
        result = coprime_clique_number(15)
        assert result >= 7


class TestEdgeEmptyCase:
    """Test edge case where coprime_edges returns empty (line 88)."""

    def test_n1_no_edges(self):
        """n=1 has no edges."""
        edges = coprime_edges(1)
        assert len(edges) == 0

    def test_compute_with_n1_start(self):
        """compute_coprime_ramsey with very small k should handle empty edges."""
        result = compute_coprime_ramsey(2, max_n=2)
        # At n=2, there's one coprime edge (1,2). Any 2-coloring of it
        # has a monochromatic K_2.
        assert result >= 2
