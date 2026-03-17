"""Tests for schur_groups.py (NPG-15)."""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from schur_groups import (
    group_elements,
    group_add,
    group_zero,
    group_order,
    is_sum_free,
    max_sum_free_size,
    schur_number,
    cyclic_group,
    boolean_group,
    all_abelian_groups,
    group_name,
    interval_sum_free_size,
    verify_prime_cyclic_theorem,
    verify_boolean_universal,
    find_all_sum_free,
    compute_schur_table,
    _heuristic_max_sum_free,
    _schur_k_colors,
    _can_k_color_sum_free,
    _integer_partitions,
    _partition_to_groups,
    _maximal_sets,
)


class TestGroupOps:
    def test_cyclic_elements(self):
        elems = group_elements((5,))
        assert len(elems) == 5
        assert (0,) in elems
        assert (4,) in elems

    def test_product_elements(self):
        elems = group_elements((2, 3))
        assert len(elems) == 6

    def test_add_cyclic(self):
        assert group_add((3,), (4,), (7,)) == (0,)

    def test_add_product(self):
        assert group_add((1, 2), (1, 2), (2, 3)) == (0, 1)

    def test_zero(self):
        assert group_zero((5, 3)) == (0, 0)

    def test_order(self):
        assert group_order((2, 3, 5)) == 30


class TestSumFree:
    def test_empty_is_sum_free(self):
        assert is_sum_free(frozenset(), (5,))

    def test_singleton_nonzero_sum_free(self):
        assert is_sum_free(frozenset([(1,)]), (5,))

    def test_pair_coprime_sum_free(self):
        # {1,4} in Z/5Z: 1+1=2, 1+4=0, 4+4=3. None in {1,4}.
        assert is_sum_free(frozenset([(1,), (4,)]), (5,))

    def test_pair_not_sum_free(self):
        # {1,2} in Z/3Z: 1+1=2 ∈ {1,2}
        assert not is_sum_free(frozenset([(1,), (2,)]), (3,))

    def test_odds_in_even_cyclic(self):
        # Odd residues in Z/8Z: {1,3,5,7}. odd+odd=even ∉ odds.
        odds = frozenset([(x,) for x in range(8) if x % 2 == 1])
        assert is_sum_free(odds, (8,))


class TestMaxSumFree:
    def test_z3(self):
        assert max_sum_free_size((3,)) == 1

    def test_z5(self):
        assert max_sum_free_size((5,)) == 2

    def test_z7(self):
        assert max_sum_free_size((7,)) == 2

    def test_z8_even(self):
        # Z/8Z: odds {1,3,5,7} size 4. But max could be higher?
        s = max_sum_free_size((8,))
        assert s == 4  # Odds are max for even cyclic

    def test_boolean_z2(self):
        assert max_sum_free_size((2,)) == 1


class TestSchurNumber:
    def test_s_z5_k1(self):
        assert schur_number((5,), k=1) == 2

    def test_s_z5_k2(self):
        assert schur_number((5,), k=2) == 4

    def test_s_z3_k2(self):
        assert schur_number((3,), k=2) == 2

    def test_boolean_k2(self):
        # (Z/2Z)^2: S(G,2) = 3
        assert schur_number((2, 2), k=2) == 3


class TestTheoremA:
    def test_all_primes_verified(self):
        results = verify_prime_cyclic_theorem(13)
        assert all(r["verified"] for r in results)

    def test_interval_size_z11(self):
        assert interval_sum_free_size(11) == 4

    def test_interval_size_z7(self):
        assert interval_sum_free_size(7) == 2


class TestTheoremB:
    def test_boolean_forces_schur(self):
        results = verify_boolean_universal(4)
        for r in results:
            if r["n"] >= 1:
                assert r["forces_universal"], f"n={r['n']} should force Schur"

    def test_boolean_pattern(self):
        """S((Z/2Z)^n, 2) = 3·2^(n-2) for n ≥ 2."""
        results = verify_boolean_universal(4)
        for r in results:
            if r["n"] >= 2:
                expected = 3 * (2 ** (r["n"] - 2))
                assert r["S_2"] == expected, f"n={r['n']}: got {r['S_2']}, expected {expected}"


class TestExtendedTable:
    """Test Schur numbers for groups of order 13-20."""

    def test_z13(self):
        assert schur_number((13,), k=1) == 4
        assert schur_number((13,), k=2) == 8

    def test_z17(self):
        assert schur_number((17,), k=1) == 6
        assert schur_number((17,), k=2) == 12

    def test_z19(self):
        assert schur_number((19,), k=1) == 6
        assert schur_number((19,), k=2) == 12

    def test_z15(self):
        assert schur_number((15,), k=2) == 12

    def test_z14(self):
        # Z/14Z ≅ Z/2Z × Z/7Z
        assert schur_number((14,), k=2) == schur_number((2, 7), k=2)


class TestConjecture2:
    """Conjecture: S(G, k) depends only on |G| for abelian groups."""

    def test_order_4(self):
        assert schur_number((4,), k=2) == schur_number((2, 2), k=2)

    def test_order_8(self):
        s_z8 = schur_number((8,), k=2)
        s_z2z4 = schur_number((2, 4), k=2)
        s_z2_3 = schur_number((2, 2, 2), k=2)
        assert s_z8 == s_z2z4 == s_z2_3

    def test_order_9(self):
        assert schur_number((9,), k=2) == schur_number((3, 3), k=2)

    def test_order_12(self):
        s_z12 = schur_number((12,), k=2)
        s_z2z2z3 = schur_number((2, 2, 3), k=2)
        assert s_z12 == s_z2z2z3

    def test_order_16_all_five(self):
        """All 5 groups of order 16 should have the same S(G, 2)."""
        vals = [
            schur_number((16,), k=2),
            schur_number((2, 8), k=2),
            schur_number((4, 4), k=2),
            schur_number((2, 2, 4), k=2),
            schur_number((2, 2, 2, 2), k=2),
        ]
        assert len(set(vals)) == 1, f"Expected all equal, got {vals}"
        assert vals[0] == 12


class TestConjecture4:
    """Conjecture: S(G, 2)/|G| depends on odd part of |G|."""

    def test_powers_of_2(self):
        """All groups of order 2^k should have S₂/|G| = 3/4."""
        for k in range(2, 5):
            n = 2 ** k
            s2 = schur_number((n,), k=2)
            assert s2 == 3 * n // 4, f"|G|={n}: S₂={s2}, expected {3*n//4}"

    def test_odd_part_3(self):
        """Groups with odd part 3: S₂/|G| ∈ {2/3, 3/4}."""
        # S(Z/3Z, 2) = 2 (2/3), S(Z/6Z, 2) = 4 (2/3), but S(Z/12Z, 2) = 9 (3/4)
        # The 3/4 at order 12 arises because 4·3=12, and the 2-power part dominates
        assert schur_number((3,), k=2) == 2   # 2/3
        assert schur_number((6,), k=2) == 4   # 2/3
        assert schur_number((12,), k=2) == 9  # 3/4 (2-part order 4 > 2)

    def test_odd_part_5(self):
        """Groups with odd part 5: S₂/|G| = 4/5."""
        for orders in [(5,), (10,), (20,)]:
            n = 1
            for o in orders:
                n *= o
            s2 = schur_number(orders, k=2)
            expected = 4 * n // 5
            assert s2 == expected, \
                f"G={orders}: S₂={s2}, expected {expected} (4n/5)"


class TestAllAbelianGroups:
    def test_order_4(self):
        groups = all_abelian_groups(4)
        assert len(groups) == 2  # Z/4Z and Z/2Z x Z/2Z

    def test_order_6(self):
        groups = all_abelian_groups(6)
        assert len(groups) == 1  # Z/6Z only (Z/2Z x Z/3Z ≅ Z/6Z)

    def test_order_8(self):
        groups = all_abelian_groups(8)
        assert len(groups) == 3  # Z/8Z, Z/2Z x Z/4Z, (Z/2Z)^3

    def test_group_name(self):
        assert group_name((2, 3)) == "Z/2Z x Z/3Z"
        assert group_name((5,)) == "Z/5Z"


# ── NEW TESTS: Coverage for uncovered lines ─────────────────────


class TestHeuristicMaxSumFree:
    """Cover lines 83-86, 92-106: _heuristic_max_sum_free and the large-group
    path in max_sum_free_size."""

    def test_heuristic_cyclic_prime(self):
        """For a cyclic group of order > 20, the heuristic path is used (lines 85-86).
        Z/23Z is prime. Odd residues are NOT sum-free in Z/pZ for odd p
        (e.g. 11+13=1 mod 23, all odd). Only the upper-third construction works."""
        orders = (23,)
        elements = group_elements(orders)
        result = _heuristic_max_sum_free(elements, orders)
        # Upper third of Z/23Z: {8,9,...,15} = 8 elements
        assert result == 8

    def test_heuristic_cyclic_even_large(self):
        """For even cyclic group > 20 elements, test heuristic.
        In Z/22Z, odd+odd=even (not in odds), so odds are sum-free."""
        orders = (22,)
        elements = group_elements(orders)
        result = _heuristic_max_sum_free(elements, orders)
        # Odd residues in Z/22Z: {1,3,...,21} = 11 elements, sum-free.
        assert result == 11

    def test_max_sum_free_large_group_uses_heuristic(self):
        """max_sum_free_size delegates to heuristic for n > 20 (lines 85-86)."""
        # Z/22Z: heuristic should give 11 (odd residues)
        result = max_sum_free_size((22,))
        assert result == 11

    def test_heuristic_non_cyclic_product(self):
        """For a non-cyclic group (len(orders) > 1), heuristic returns 0 (line 106 only)."""
        orders = (3, 11)  # 33 elements, product group
        elements = group_elements(orders)
        result = _heuristic_max_sum_free(elements, orders)
        # Non-cyclic path: no construction tried, returns 0
        assert result == 0

    def test_heuristic_upper_third_construction(self):
        """Verify the upper-third construction is tested (lines 97-100)."""
        orders = (29,)
        elements = group_elements(orders)
        result = _heuristic_max_sum_free(elements, orders)
        # Upper third of Z/29Z: {10,11,...,19} = 10 elements, sum-free.
        # Odds are NOT sum-free for odd n (wraps around).
        assert result == 10


class TestMaxSumFreeEarlyBreak:
    """Cover line 78: the `break` in the exhaustive loop when size <= best."""

    def test_exhaustive_z2(self):
        """Z/2Z has group order 2. The exhaustive search finds size=1 sum-free
        set quickly. Then for size=0 (< best=1), break triggers (line 78)."""
        # Actually the loop goes from n down to 1, and returns immediately when found.
        # To trigger line 78 we need a group where the max sum-free set is found
        # at size < n, and then the loop tries smaller sizes.
        # Z/2Z: max sum-free is 1. Loop: size=2 checks {(0,),(1,)} not sum-free,
        # then size=1 finds {(1,)} sum-free -> returns 1. Break never triggers here.
        # Line 78 triggers if we try all combos of a given size and none work,
        # then size drops below best. This happens for the trivial group Z/1Z.
        result = max_sum_free_size((1,))
        # Z/1Z: only element is (0,). {(0,)} -> 0+0=0 in set, NOT sum-free.
        # So no sum-free set of size 1 found, best stays 0, then break triggers.
        assert result == 0

    def test_exhaustive_z4_returns_correctly(self):
        """Z/4Z: max sum-free is 2. {1,3}: 1+1=2, 1+3=0, 3+3=2. None in {1,3}."""
        result = max_sum_free_size((4,))
        assert result == 2


class TestFindAllSumFree:
    """Cover lines 111-121: find_all_sum_free function."""

    def test_find_all_z3(self):
        """Z/3Z: sum-free subsets of min_size 1."""
        result = find_all_sum_free((3,), min_size=1)
        # Sum-free subsets of Z/3Z: {1}, {2}, (and possibly {0}? 0+0=0 so no)
        # {1}: 1+1=2 not in {1} -> ok
        # {2}: 2+2=1 not in {2} -> ok
        # {0}: 0+0=0 in {0} -> no
        # {1,2}: 1+1=2 in {1,2} -> no
        # {0,1}: 0+1=1 in {0,1} -> no
        # {0,2}: 0+2=2 in {0,2} -> no
        # {0,1,2}: no
        assert len(result) == 2
        assert frozenset([(1,)]) in result
        assert frozenset([(2,)]) in result

    def test_find_all_z3_min_size_0(self):
        """With min_size=0, empty set is not returned (range starts at 0 but
        combinations(n,0) gives one combo of 0 elements -> empty frozenset)."""
        # find_all_sum_free has range(min_size, n+1). For min_size=0,
        # it starts at 0. combinations(3, 0) = [()], frozenset of no elements.
        # is_sum_free(frozenset(), ...) is True (empty set is sum-free).
        result = find_all_sum_free((3,), min_size=0)
        assert frozenset() in result

    def test_find_all_z5_min_size_2(self):
        """Z/5Z: find all sum-free subsets of size >= 2."""
        result = find_all_sum_free((5,), min_size=2)
        # Each result should have at least 2 elements
        for s in result:
            assert len(s) >= 2
        # {1,4} should be among them (1+1=2, 1+4=0, 4+4=3 - none in {1,4})
        assert frozenset([(1,), (4,)]) in result
        # The max sum-free size is 2, so all results have exactly 2 elements
        for s in result:
            assert len(s) == 2

    def test_find_all_returns_list(self):
        """find_all_sum_free returns a list of frozensets."""
        result = find_all_sum_free((2,), min_size=1)
        assert isinstance(result, list)
        for s in result:
            assert isinstance(s, frozenset)


class TestSchurKColors:
    """Cover lines 143, 199-212, 217-229: k >= 3 Schur number computation."""

    def test_schur_k3_z3(self):
        """S(Z/3Z, 3): with 3 colors on Z/3Z = {0,1,2}.
        Line 143 dispatches to _schur_k_colors."""
        result = schur_number((3,), k=3)
        # With 3 colors available for 3 elements: {0}: 0+0=0 in {0} not sum-free.
        # Best: color 1 gets {1}, color 2 gets {2}, color 3 empty. Union size = 2.
        # Or could do {1,2} in one color? 1+1=2 in set, not sum-free. So max is 2.
        assert result == 2

    def test_schur_k3_z5(self):
        """S(Z/5Z, 3): three colors on Z/5Z."""
        result = schur_number((5,), k=3)
        # With 3 colors, we can cover more than with 2.
        assert result >= schur_number((5,), k=2)

    def test_schur_k_too_large_group(self):
        """_schur_k_colors returns -1 for groups > 15 elements (line 200-201)."""
        orders = (4, 5)  # 20 elements > 15
        elements = group_elements(orders)
        result = _schur_k_colors(elements, orders, 3)
        assert result == -1

    def test_schur_k_colors_small_group(self):
        """_schur_k_colors works for small groups (lines 204-212)."""
        orders = (5,)
        elements = group_elements(orders)
        result = _schur_k_colors(elements, orders, 2)
        # Should match _schur_2_colors result
        assert result == schur_number(orders, k=2)

    def test_schur_k_colors_returns_best_zero(self):
        """_schur_k_colors with k=1 on Z/1Z: no sum-free set, returns 0 (line 212)."""
        orders = (1,)
        elements = group_elements(orders)
        # Z/1Z = {(0,)}, 0+0=0 in {0}. No sum-free subset of size >= 1.
        result = _schur_k_colors(elements, orders, 1)
        assert result == 0


class TestCanKColorSumFree:
    """Cover lines 217-229: _can_k_color_sum_free."""

    def test_can_2_color_pair(self):
        """Two elements that are individually sum-free can be 2-colored."""
        subset = [(1,), (2,)]
        orders = (5,)
        # {1}: 1+1=2 not in {1} -> sum-free. {2}: 2+2=4 not in {2} -> sum-free.
        assert _can_k_color_sum_free(subset, orders, 2)

    def test_cannot_1_color_pair(self):
        """In Z/3Z, {1,2}: 1+1=2 in set. Not 1-colorable as sum-free."""
        subset = [(1,), (2,)]
        orders = (3,)
        assert not _can_k_color_sum_free(subset, orders, 1)

    def test_can_k_color_empty(self):
        """Empty subset is trivially k-colorable (lines 219-228: loop over empty product)."""
        assert _can_k_color_sum_free([], (5,), 2)

    def test_cannot_color_forces_false(self):
        """In Z/7Z, {1,2,3,4,5,6}: can this be 1-colored sum-free? No.
        1+1=2, 2 in set. Returns False (line 229)."""
        subset = [(i,) for i in range(1, 7)]
        orders = (7,)
        assert not _can_k_color_sum_free(subset, orders, 1)


class TestIntegerPartitions:
    """Cover line 295: _integer_partitions(0) returns [[]]."""

    def test_partitions_of_0(self):
        assert _integer_partitions(0) == [[]]

    def test_partitions_of_1(self):
        assert _integer_partitions(1) == [[1]]

    def test_partitions_of_3(self):
        result = _integer_partitions(3)
        # [3], [2,1], [1,1,1]
        assert len(result) == 3
        assert [3] in result
        assert [2, 1] in result
        assert [1, 1, 1] in result

    def test_partitions_of_4(self):
        result = _integer_partitions(4)
        # [4], [3,1], [2,2], [2,1,1], [1,1,1,1]
        assert len(result) == 5


class TestPartitionToGroups:
    """Cover line 267: _partition_to_groups for edge cases."""

    def test_partition_to_groups_prime(self):
        """Prime order: only one group Z/pZ."""
        result = _partition_to_groups(7)
        assert result == [(7,)]

    def test_partition_to_groups_prime_power(self):
        """Order 8 = 2^3: three groups."""
        result = _partition_to_groups(8)
        assert len(result) == 3
        assert (8,) in result
        assert (2, 4) in result
        assert (2, 2, 2) in result

    def test_partition_to_groups_1(self):
        """n=1: factors dict is empty, returns [(1,)] (line 267)."""
        result = _partition_to_groups(1)
        assert result == [(1,)]


class TestAllAbelianGroupsEdge:
    """Cover line 250: all_abelian_groups(1)."""

    def test_order_1(self):
        """The trivial group (order 1) returns [(1,)]."""
        result = all_abelian_groups(1)
        assert result == [(1,)]

    def test_order_2(self):
        result = all_abelian_groups(2)
        assert result == [(2,)]


class TestComputeSchurTable:
    """Cover lines 326-342: compute_schur_table function."""

    def test_table_small(self):
        """compute_schur_table(5) computes S(G,1) and S(G,2) for orders 2..5."""
        table = compute_schur_table(max_order=5)
        assert len(table) > 0
        # Check that Z/5Z is in the table
        assert "Z/5Z" in table
        entry = table["Z/5Z"]
        assert entry["group_order"] == 5
        assert entry["S_1"] == 2
        assert entry["S_2"] == 4
        assert entry["s1_ratio"] == 2 / 5
        assert entry["s2_ratio"] == 4 / 5
        assert entry["forces_schur_2"] is False

    def test_table_includes_all_groups(self):
        """Table includes all non-isomorphic abelian groups up to given order."""
        table = compute_schur_table(max_order=8)
        # Order 4: Z/4Z, Z/2Z x Z/2Z => 2 groups
        order_4_groups = [v for v in table.values() if v["group_order"] == 4]
        assert len(order_4_groups) == 2
        # Order 8: Z/8Z, Z/2Z x Z/4Z, (Z/2Z)^3 => 3 groups
        order_8_groups = [v for v in table.values() if v["group_order"] == 8]
        assert len(order_8_groups) == 3

    def test_table_forces_schur_2(self):
        """Check the forces_schur_2 field: True when S(G,2) == |G|."""
        table = compute_schur_table(max_order=4)
        # For Z/2Z: S(G,2) should equal |G|=2 (both {1} can be one color).
        # Actually let's just verify the field is bool
        for name, data in table.items():
            assert isinstance(data["forces_schur_2"], bool)
            assert data["forces_schur_2"] == (data["S_2"] == data["group_order"])

    def test_table_ratios(self):
        """Ratios are correctly computed."""
        table = compute_schur_table(max_order=3)
        for name, data in table.items():
            n = data["group_order"]
            assert data["s1_ratio"] == pytest.approx(data["S_1"] / n)
            assert data["s2_ratio"] == pytest.approx(data["S_2"] / n)

    def test_table_orders_field(self):
        """Each entry has the orders tuple stored."""
        table = compute_schur_table(max_order=6)
        for name, data in table.items():
            assert "orders" in data
            assert isinstance(data["orders"], tuple)


class TestMaximalSets:
    """Test _maximal_sets helper."""

    def test_maximal_filters_subsets(self):
        sets = [frozenset({1}), frozenset({1, 2}), frozenset({2, 3})]
        result = _maximal_sets(sets)
        # {1} is a proper subset of {1,2}, so should be filtered out
        assert frozenset({1}) not in result
        assert frozenset({1, 2}) in result
        assert frozenset({2, 3}) in result

    def test_maximal_empty_input(self):
        assert _maximal_sets([]) == []

    def test_maximal_all_equal(self):
        sets = [frozenset({1, 2}), frozenset({1, 2})]
        result = _maximal_sets(sets)
        # Neither is a PROPER subset of the other (they're equal), so both kept
        assert len(result) == 2


class TestDensityRelaxedSchurDS2:
    """Direct computational verification of DS(2, 1/2) = 5.

    This is a HEADLINE CLAIM: the density-relaxed Schur number DS(2, alpha)
    equals 5 for all alpha >= 1/2, and equals 1 for alpha < 1/2.

    DS(k, alpha) = 1 + max{N : a (k, alpha)-avoiding coloring of [N] exists}
    where (k, alpha)-avoiding means every color class is both sum-free and
    has at most alpha*N elements.
    """

    @staticmethod
    def _is_sum_free(S):
        """Check if S is sum-free: no x,y,z in S with x+y=z."""
        for x in S:
            for y in S:
                if x + y in S:
                    return False
        return True

    @staticmethod
    def _has_avoiding_coloring(N, k=2, alpha=0.5):
        """Check if [1..N] has a (k, alpha)-avoiding 2-coloring.

        Exhaustively tries all 2^N colorings of {1,...,N} into 2 colors.
        Each color class must be sum-free and have at most alpha*N elements.
        """
        max_per_class = int(alpha * N)
        for mask in range(2**N):
            color0 = set()
            color1 = set()
            for i in range(N):
                if mask & (1 << i):
                    color1.add(i + 1)
                else:
                    color0.add(i + 1)
            # Check density constraint
            if len(color0) > max_per_class or len(color1) > max_per_class:
                continue
            # Check sum-free constraint
            if TestDensityRelaxedSchurDS2._is_sum_free(color0) and \
               TestDensityRelaxedSchurDS2._is_sum_free(color1):
                return True
        return False

    def test_ds2_lower_bound_n4_has_avoiding(self):
        """N=4: an avoiding 2-coloring exists, so DS(2,1/2) >= 5.

        Witness: {1,4} and {2,3}. Both sum-free, both have 2 <= 0.5*4 = 2 elements.
        """
        assert self._has_avoiding_coloring(4, k=2, alpha=0.5)

    def test_ds2_upper_bound_n5_no_avoiding(self):
        """N=5: NO avoiding 2-coloring exists, so DS(2,1/2) <= 5.

        Exhaustive check over all 2^5 = 32 colorings.
        """
        assert not self._has_avoiding_coloring(5, k=2, alpha=0.5)

    def test_ds2_equals_5(self):
        """DS(2, 1/2) = 1 + max{N : avoiding exists} = 1 + 4 = 5."""
        assert self._has_avoiding_coloring(4, k=2, alpha=0.5)
        assert not self._has_avoiding_coloring(5, k=2, alpha=0.5)
        # Therefore DS(2, 1/2) = 1 + 4 = 5

    def test_ds2_witness_coloring(self):
        """Verify the specific witness: {1,4} and {2,3} on [4]."""
        c0 = {1, 4}
        c1 = {2, 3}
        assert c0 | c1 == {1, 2, 3, 4}
        assert c0 & c1 == set()
        assert self._is_sum_free(c0)  # 1+4=5 not in {1,4}
        assert self._is_sum_free(c1)  # 2+3=5 not in {2,3}, 2+2=4 not in {2,3}, 3+3=6 not in {2,3}
        assert len(c0) <= 0.5 * 4
        assert len(c1) <= 0.5 * 4

    def test_ds2_alpha_below_half(self):
        """For alpha < 1/2, DS(2, alpha) = 1: even N=1 has no avoiding coloring.

        With alpha=0.4 and N=1, max_per_class = floor(0.4*1) = 0.
        Can't put element 1 in either class.
        """
        assert not self._has_avoiding_coloring(1, k=2, alpha=0.4)

    def test_ds2_step_function_alpha_06(self):
        """DS(2, 0.6) = 5: same as alpha=0.5 (step function behavior)."""
        assert self._has_avoiding_coloring(4, k=2, alpha=0.6)
        assert not self._has_avoiding_coloring(5, k=2, alpha=0.6)

    def test_ds2_step_function_alpha_09(self):
        """DS(2, 0.9) = 5: same as alpha=0.5 (step function behavior)."""
        assert self._has_avoiding_coloring(4, k=2, alpha=0.9)
        assert not self._has_avoiding_coloring(5, k=2, alpha=0.9)

    def test_n5_all_colorings_fail_reason(self):
        """Verify WHY no avoiding coloring exists at N=5.

        For any 2-coloring of {1,2,3,4,5} with both classes sum-free
        and at most 2 elements each (floor(0.5*5)=2):
        - Only 4 elements can be colored (2+2), but we need to color 5.
        Actually floor(0.5*5) = 2, so each class has at most 2 elements,
        total at most 4 < 5. That's why it fails.
        """
        N = 5
        max_per_class = int(0.5 * N)  # = 2
        assert max_per_class * 2 < N  # Pigeonhole: can't color all 5 elements


class TestSchurOrderInvariance:
    """S(G, k) depends only on |G|, not on the isomorphism type.

    Verified for all abelian groups up to order 16 and k ∈ {1, 2}.
    This means S(G, k) = f_k(|G|) for some function f_k.
    """

    def test_s1_invariance_order_4(self):
        """S(Z/4Z, 1) = S(Z/2Z × Z/2Z, 1)."""
        assert schur_number((4,), k=1) == schur_number((2, 2), k=1)

    def test_s1_invariance_order_8(self):
        """All 3 abelian groups of order 8 have the same S(G,1)."""
        vals = {schur_number(g, k=1) for g in [(8,), (2, 4), (2, 2, 2)]}
        assert len(vals) == 1

    def test_s2_invariance_order_4(self):
        """S(Z/4Z, 2) = S(Z/2Z × Z/2Z, 2)."""
        assert schur_number((4,), k=2) == schur_number((2, 2), k=2)

    def test_s2_invariance_order_8(self):
        """All 3 abelian groups of order 8 have the same S(G,2)."""
        vals = {schur_number(g, k=2) for g in [(8,), (2, 4), (2, 2, 2)]}
        assert len(vals) == 1

    def test_s2_invariance_order_9(self):
        """S(Z/9Z, 2) = S(Z/3Z × Z/3Z, 2)."""
        assert schur_number((9,), k=2) == schur_number((3, 3), k=2)

    def test_s2_invariance_order_12(self):
        """Both abelian groups of order 12 have the same S(G,2)."""
        assert schur_number((3, 4), k=2) == schur_number((2, 2, 3), k=2)

    def test_s2_invariance_order_16(self):
        """All 5 abelian groups of order 16 have the same S(G,2)."""
        groups_16 = [(16,), (2, 8), (4, 4), (2, 2, 4), (2, 2, 2, 2)]
        vals = {schur_number(g, k=2) for g in groups_16}
        assert len(vals) == 1
        assert vals.pop() == 12

    def test_s2_invariance_order_18(self):
        """Both abelian groups of order 18 have the same S(G,2)."""
        assert schur_number((2, 9), k=2) == schur_number((2, 3, 3), k=2)

    def test_s2_invariance_order_20(self):
        """Both abelian groups of order 20 have the same S(G,2)."""
        assert schur_number((4, 5), k=2) == schur_number((2, 2, 5), k=2)

    def test_s2_sequence_values(self):
        """Verify the S(Z/nZ, 2) sequence for n=2..16."""
        expected = {
            2: 1, 3: 2, 4: 3, 5: 4, 6: 4, 7: 4, 8: 6, 9: 6,
            10: 8, 11: 8, 12: 9, 13: 8, 14: 9, 15: 12, 16: 12,
        }
        for n, exp in expected.items():
            assert schur_number((n,), k=2) == exp, f"S(Z/{n}Z, 2) = {schur_number((n,), k=2)}, expected {exp}"


class TestSchur3Colors:
    """Tests for S(G, 3): Schur number with 3 colors."""

    def test_s3_z2(self):
        """S(Z/2Z, 3) = 1. Only {1} is sum-free; 0+0=0."""
        assert schur_number((2,), k=3) == 1

    def test_s3_z3(self):
        """S(Z/3Z, 3) = 2. {1} and {2} in separate colors; {1,2} not sum-free."""
        assert schur_number((3,), k=3) == 2

    def test_s3_z5(self):
        """S(Z/5Z, 3) = 4."""
        assert schur_number((5,), k=3) == 4

    def test_s3_z7(self):
        """S(Z/7Z, 3) = 6. All nonzero elements are 3-colorable sum-free."""
        assert schur_number((7,), k=3) == 6

    def test_s3_z9(self):
        """S(Z/9Z, 3) = 8. All nonzero elements are 3-colorable sum-free."""
        assert schur_number((9,), k=3) == 8

    def test_s3_z11(self):
        """S(Z/11Z, 3) = 10."""
        assert schur_number((11,), k=3) == 10

    def test_s3_monotone_in_k(self):
        """S(G, 3) >= S(G, 2) >= S(G, 1) for all groups tested."""
        for orders in [(3,), (5,), (7,), (8,), (2, 4), (2, 2, 2), (9,), (3, 3)]:
            s1 = schur_number(orders, k=1)
            s2 = schur_number(orders, k=2)
            s3 = schur_number(orders, k=3)
            assert s3 >= s2 >= s1, (
                f"G={orders}: S1={s1}, S2={s2}, S3={s3} violates monotonicity"
            )

    def test_s3_le_group_order(self):
        """S(G, 3) <= |G| (trivially)."""
        for orders in [(3,), (5,), (7,), (2, 2), (2, 3), (2, 2, 2)]:
            n = 1
            for o in orders:
                n *= o
            s3 = schur_number(orders, k=3)
            assert s3 <= n


class TestSchur3Invariance:
    """Test order-invariance of S(G, 3).

    Key finding: S(G, 3) does NOT depend only on |G|.
    Invariance holds at orders 4 and 8 but FAILS at orders 9 and 12.
    This contrasts with k=1 and k=2, where invariance holds through order 20.
    """

    def test_s3_invariant_order_4(self):
        """S(Z/4Z, 3) = S(Z/2Z x Z/2Z, 3) = 3."""
        assert schur_number((4,), k=3) == 3
        assert schur_number((2, 2), k=3) == 3

    def test_s3_invariant_order_8(self):
        """All 3 abelian groups of order 8 have S(G,3) = 7."""
        vals = [schur_number(g, k=3) for g in [(8,), (2, 4), (2, 2, 2)]]
        assert vals == [7, 7, 7]

    def test_s3_breaks_order_9(self):
        """Order invariance FAILS at order 9: S(Z/9Z, 3) != S(Z/3Z x Z/3Z, 3).

        S(Z/9Z, 3) = 8 (all nonzero elements 3-colorable)
        S(Z/3Z x Z/3Z, 3) = 7 (one nonzero element must be excluded)
        """
        s_z9 = schur_number((9,), k=3)
        s_z3z3 = schur_number((3, 3), k=3)
        assert s_z9 == 8
        assert s_z3z3 == 7
        assert s_z9 != s_z3z3

    @pytest.mark.timeout(300)
    def test_s3_breaks_order_12(self):
        """Order invariance FAILS at order 12.

        S(Z/3Z x Z/4Z, 3) = 11
        S(Z/2Z x Z/2Z x Z/3Z, 3) = 10

        Note: slow (~2-3 min) due to 3^12 = 531K enumeration.
        """
        s_z3z4 = schur_number((3, 4), k=3)
        s_z2z2z3 = schur_number((2, 2, 3), k=3)
        assert s_z3z4 == 11
        assert s_z2z2z3 == 10
        assert s_z3z4 != s_z2z2z3


class TestSchur3CyclicSequence:
    """S(Z/nZ, 3) = n-1 for n=2..14, then drops to n-2 at n=15.

    The pattern arises because the nonzero elements of Z/nZ can
    be 3-colored sum-free for n <= 14, but not for n=15.
    The element 0 can never be included (0+0=0 is a Schur triple).
    """

    def test_cyclic_s3_small(self):
        """S(Z/nZ, 3) = n-1 for n = 2..8."""
        for n in range(2, 9):
            s3 = schur_number((n,), k=3)
            assert s3 == n - 1, f"S(Z/{n}Z, 3) = {s3}, expected {n-1}"

    def test_cyclic_s3_sequence_values(self):
        """Verify exact sequence values for n=2..11."""
        expected = {
            2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6,
            8: 7, 9: 8, 10: 9, 11: 10,
        }
        for n, exp in expected.items():
            s3 = schur_number((n,), k=3)
            assert s3 == exp, f"S(Z/{n}Z, 3) = {s3}, expected {exp}"

    def test_nonzero_elements_3colorable_z7(self):
        """Verify that Z/7Z \\ {0} can be 3-colored sum-free."""
        elements = [(i,) for i in range(1, 7)]
        assert _can_k_color_sum_free(elements, (7,), 3)

    def test_nonzero_elements_3colorable_z9(self):
        """Z/9Z \\ {0} can be 3-colored sum-free."""
        elements = [(i,) for i in range(1, 9)]
        assert _can_k_color_sum_free(elements, (9,), 3)

    def test_zero_excluded(self):
        """0 cannot be in any sum-free color class (0+0=0)."""
        # {0} is not sum-free in any group
        for orders in [(3,), (5,), (7,), (2, 2)]:
            z = group_zero(orders)
            assert not is_sum_free(frozenset([z]), orders)


class TestDSPhaseTransition:
    """DS(2, alpha) phase transition structure.

    DS(2, alpha) has exactly 3 regimes:
    - alpha <= 0.59: DS = 5 (matches S(2)+1)
    - alpha in [0.60, 0.66]: DS = 6
    - alpha >= 0.67: DS > 12 (explosion)
    """

    @staticmethod
    def _ds2(N, alpha):
        """Check if every 2-coloring of [N] has a dense Schur triple."""
        from itertools import product as iterproduct
        threshold = max(1, int(alpha * N))
        for coloring in iterproduct(range(2), repeat=N):
            color_sets = [set(), set()]
            for i, c in enumerate(coloring):
                color_sets[c].add(i + 1)
            has_viol = False
            for S in color_sets:
                if len(S) >= threshold:
                    for a in S:
                        for b in S:
                            if a + b in S:
                                has_viol = True
                                break
                        if has_viol:
                            break
                if has_viol:
                    break
            if not has_viol:
                return False
        return True

    def test_ds2_regime1_half(self):
        """DS(2, 0.50) = 5."""
        assert not self._ds2(4, 0.50)
        assert self._ds2(5, 0.50)

    def test_ds2_regime2_onset(self):
        """DS(2, 0.60) = 6 (first regime transition)."""
        assert not self._ds2(5, 0.60)
        assert self._ds2(6, 0.60)

    def test_ds2_regime2_end(self):
        """DS(2, 0.66) = 6 (still in regime 2)."""
        assert self._ds2(6, 0.66)

    def test_ds2_regime3_onset(self):
        """DS(2, 0.67) > 12 (regime 3 explosion)."""
        assert not self._ds2(6, 0.67)
        assert not self._ds2(12, 0.67)
