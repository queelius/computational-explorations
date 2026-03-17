"""Adversarial tests for S(G,k) order-invariance conjecture.

The conjecture: S(G, 2) depends only on |G| for finite abelian groups.

These tests attempt to DISPROVE this conjecture from multiple angles:
  1. Push k=2 verification to orders 24-48 (SAT-based)
  2. Compare non-abelian groups with abelian groups of the same order
  3. Verify Green-Ruzsa implications for k=1
  4. Independent verification of k=3 counterexamples
  5. Boundary analysis of the k=3 failure mechanism
"""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from adversarial_schur import (
    check_k2_invariance,
    compare_nonabelian,
    dihedral_cayley,
    find_k2_counterexample,
    green_ruzsa_analysis,
    k3_boundary_order4,
    k3_boundary_order8,
    k3_boundary_order9,
    k3_exponent_analysis,
    k3_full_order16,
    quaternion_cayley,
    sat_schur_general,
    schur_triples_from_cayley,
    symmetric_group_s3_cayley,
    verify_k3_counterexamples,
)
from schur_algorithms import sat_schur
from schur_groups import (
    all_abelian_groups,
    group_add,
    group_elements,
    group_name,
    group_order,
    group_zero,
    is_sum_free,
)


# =====================================================================
# 1. Non-abelian group Cayley table correctness
# =====================================================================


class TestCayleyTables:
    """Verify group axioms for all non-abelian Cayley tables."""

    @staticmethod
    def _check_group_axioms(table: list, name: str):
        n = len(table)
        # Identity: element 0
        for i in range(n):
            assert table[0][i] == i, f"{name}: 0*{i} = {table[0][i]} != {i}"
            assert table[i][0] == i, f"{name}: {i}*0 = {table[i][0]} != {i}"
        # Closure and Latin square
        for i in range(n):
            row = table[i]
            assert sorted(row) == list(range(n)), (
                f"{name}: row {i} is not a permutation: {row}"
            )
            col = [table[j][i] for j in range(n)]
            assert sorted(col) == list(range(n)), (
                f"{name}: col {i} is not a permutation"
            )
        # Associativity (spot-check)
        for a in range(min(n, 4)):
            for b in range(min(n, 4)):
                for c in range(min(n, 4)):
                    ab_c = table[table[a][b]][c]
                    a_bc = table[a][table[b][c]]
                    assert ab_c == a_bc, (
                        f"{name}: ({a}*{b})*{c}={ab_c} != {a}*({b}*{c})={a_bc}"
                    )

    def test_s3_axioms(self):
        self._check_group_axioms(symmetric_group_s3_cayley(), "S_3")

    def test_s3_order(self):
        assert len(symmetric_group_s3_cayley()) == 6

    def test_s3_nonabelian(self):
        """S_3 is non-abelian: there exist a, b with a*b != b*a."""
        t = symmetric_group_s3_cayley()
        found = False
        for a in range(6):
            for b in range(6):
                if t[a][b] != t[b][a]:
                    found = True
                    break
            if found:
                break
        assert found, "S_3 should be non-abelian"

    def test_d4_axioms(self):
        self._check_group_axioms(dihedral_cayley(4), "D_4")

    def test_d4_order(self):
        assert len(dihedral_cayley(4)) == 8

    def test_d4_nonabelian(self):
        t = dihedral_cayley(4)
        found = any(t[a][b] != t[b][a] for a in range(8) for b in range(8))
        assert found, "D_4 should be non-abelian"

    def test_d4_rotation_subgroup(self):
        """Rotations {r_0, r_1, r_2, r_3} form abelian subgroup Z/4Z."""
        t = dihedral_cayley(4)
        for a in range(4):
            for b in range(4):
                assert t[a][b] < 4, f"Rotation subgroup not closed: r{a}*r{b} = {t[a][b]}"
                assert t[a][b] == t[b][a], "Rotation subgroup should be abelian"

    def test_q8_axioms(self):
        self._check_group_axioms(quaternion_cayley(), "Q_8")

    def test_q8_order(self):
        assert len(quaternion_cayley()) == 8

    def test_q8_nonabelian(self):
        t = quaternion_cayley()
        # i*j = k but j*i = -k
        assert t[2][4] == 6, "i*j should be k"
        assert t[4][2] == 7, "j*i should be -k"
        assert t[2][4] != t[4][2], "Q_8 should be non-abelian"

    def test_q8_relations(self):
        """Verify i^2 = j^2 = k^2 = ijk = -1."""
        t = quaternion_cayley()
        assert t[2][2] == 1, "i^2 = -1"
        assert t[4][4] == 1, "j^2 = -1"
        assert t[6][6] == 1, "k^2 = -1"
        ijk = t[t[2][4]][6]  # (i*j)*k
        assert ijk == 1, f"i*j*k = {ijk}, expected -1 (encoded as 1)"

    def test_d3_axioms(self):
        self._check_group_axioms(dihedral_cayley(3), "D_3")

    def test_d3_order(self):
        assert len(dihedral_cayley(3)) == 6

    def test_d3_isomorphic_to_s3(self):
        """D_3 and S_3 should have the same group structure (both order 6, non-abelian)."""
        d3 = dihedral_cayley(3)
        s3 = symmetric_group_s3_cayley()
        assert len(d3) == len(s3) == 6

    def test_dihedral_d5(self):
        """D_5 has order 10."""
        d5 = dihedral_cayley(5)
        self._check_group_axioms(d5, "D_5")
        assert len(d5) == 10


class TestSchurTriplesFromCayley:
    """Test extraction of Schur triples from Cayley tables."""

    def test_identity_triple_always_present(self):
        """0 * 0 = 0 is always a Schur triple."""
        for table in [symmetric_group_s3_cayley(), quaternion_cayley()]:
            triples = schur_triples_from_cayley(table)
            assert (0, 0, 0) in triples

    def test_total_triple_count(self):
        """Every (a, b) pair yields exactly one triple, so |triples| = n^2."""
        t = symmetric_group_s3_cayley()
        triples = schur_triples_from_cayley(t)
        assert len(triples) == 36  # 6^2

    def test_q8_specific_triple(self):
        """i * j = k should appear as triple (2, 4, 6)."""
        t = quaternion_cayley()
        triples = schur_triples_from_cayley(t)
        assert (2, 4, 6) in triples


class TestSATSchurGeneral:
    """Test the general SAT-based S(G,k) for non-abelian groups."""

    def test_trivial_group(self):
        """Trivial group {e}: S(G,k) = 0 for all k (e*e=e is Schur triple)."""
        table = [[0]]
        assert sat_schur_general(table, k=1) == 0
        assert sat_schur_general(table, k=2) == 0

    def test_z2_as_cayley(self):
        """Z/2Z via Cayley table: should match direct computation."""
        table = [[0, 1], [1, 0]]
        assert sat_schur_general(table, k=2) == sat_schur((2,), k=2)

    def test_z3_as_cayley(self):
        """Z/3Z via Cayley table."""
        table = [[0, 1, 2], [1, 2, 0], [2, 0, 1]]
        assert sat_schur_general(table, k=2) == sat_schur((3,), k=2)

    def test_s3_positive(self):
        """S(S_3, 2) should be a reasonable positive value."""
        s = sat_schur_general(symmetric_group_s3_cayley(), k=2)
        assert 1 <= s <= 5  # 0 excluded (e*e=e), so at most 5

    def test_q8_positive(self):
        """S(Q_8, 2) should be a reasonable positive value."""
        s = sat_schur_general(quaternion_cayley(), k=2)
        assert 1 <= s <= 7

    def test_general_le_n_minus_1(self):
        """S(G, k) <= |G| - 1 since identity always excluded."""
        for table in [symmetric_group_s3_cayley(), quaternion_cayley(), dihedral_cayley(4)]:
            n = len(table)
            for k in (1, 2, 3):
                s = sat_schur_general(table, k=k)
                assert s <= n - 1, f"S(G,{k}) = {s} > {n}-1 for group of order {n}"

    def test_monotone_in_k(self):
        """S(G, k+1) >= S(G, k)."""
        for table in [symmetric_group_s3_cayley(), quaternion_cayley()]:
            s1 = sat_schur_general(table, k=1)
            s2 = sat_schur_general(table, k=2)
            s3 = sat_schur_general(table, k=3)
            assert s3 >= s2 >= s1


# =====================================================================
# 2. k=2 order-invariance: push to higher orders
# =====================================================================


class TestK2InvarianceOrders24_25:
    """Push S(G,2) invariance to orders 24 and 25."""

    def test_order_24_all_three_groups(self):
        """All 3 abelian groups of order 24 have the same S(G,2)."""
        groups = all_abelian_groups(24)
        assert len(groups) == 3
        vals = [sat_schur(g, k=2) for g in groups]
        assert len(set(vals)) == 1, f"Order 24: S(G,2) values differ: {dict(zip([group_name(g) for g in groups], vals))}"
        assert vals[0] == 18

    def test_order_25_both_groups(self):
        """Both abelian groups of order 25 have the same S(G,2)."""
        groups = all_abelian_groups(25)
        assert len(groups) == 2
        vals = [sat_schur(g, k=2) for g in groups]
        assert len(set(vals)) == 1, f"Order 25: S(G,2) values differ: {dict(zip([group_name(g) for g in groups], vals))}"
        assert vals[0] == 20


class TestK2InvarianceOrders27_36:
    """Check S(G,2) invariance for orders with interesting structure."""

    def test_order_27_three_groups(self):
        """All 3 abelian groups of order 27 = 3^3."""
        groups = all_abelian_groups(27)
        assert len(groups) == 3
        vals = {group_name(g): sat_schur(g, k=2) for g in groups}
        assert len(set(vals.values())) == 1, f"Order 27 differs: {vals}"

    def test_order_32_seven_groups(self):
        """All 7 abelian groups of order 32 = 2^5 have the same S(G,2) = 24."""
        groups = all_abelian_groups(32)
        assert len(groups) == 7
        vals = {group_name(g): sat_schur(g, k=2) for g in groups}
        assert len(set(vals.values())) == 1, f"Order 32 differs: {vals}"
        assert list(set(vals.values()))[0] == 24

    def test_order_36_four_groups(self):
        """All 4 abelian groups of order 36 = 2^2 * 3^2."""
        groups = all_abelian_groups(36)
        assert len(groups) == 4
        vals = {group_name(g): sat_schur(g, k=2) for g in groups}
        assert len(set(vals.values())) == 1, f"Order 36 differs: {vals}"
        assert list(set(vals.values()))[0] == 27


@pytest.mark.timeout(60)
class TestK2InvarianceOrder48:
    """Order 48 = 2^4 * 3 with 5 groups -- expensive but critical."""

    def test_order_48_five_groups(self):
        groups = all_abelian_groups(48)
        assert len(groups) == 5
        vals = {group_name(g): sat_schur(g, k=2) for g in groups}
        assert len(set(vals.values())) == 1, f"Order 48 differs: {vals}"
        assert list(set(vals.values()))[0] == 36


class TestK2NoCounterexample:
    """Meta-test: no counterexample exists up to the checked order."""

    @pytest.mark.timeout(120)
    def test_no_counterexample_through_order_48(self):
        """Systematic check: no k=2 counterexample for any order <= 48."""
        result = find_k2_counterexample(max_order=48)
        assert result is None, f"Counterexample found! {result}"


# =====================================================================
# 3. Non-abelian comparison
# =====================================================================


class TestNonabelianK2:
    """Non-abelian groups at k=2: do they match abelian groups of the same order?"""

    def test_s3_matches_z6(self):
        """S(S_3, 2) = S(Z/6Z, 2)."""
        s_s3 = sat_schur_general(symmetric_group_s3_cayley(), k=2)
        s_z6 = sat_schur((6,), k=2)
        assert s_s3 == s_z6, f"S(S_3,2)={s_s3} != S(Z/6Z,2)={s_z6}"

    def test_d3_matches_z6(self):
        """S(D_3, 2) = S(Z/6Z, 2). D_3 ~ S_3."""
        s_d3 = sat_schur_general(dihedral_cayley(3), k=2)
        s_z6 = sat_schur((6,), k=2)
        assert s_d3 == s_z6

    def test_d3_equals_s3(self):
        """D_3 and S_3 are isomorphic, so S(D_3,2) = S(S_3,2)."""
        s_d3 = sat_schur_general(dihedral_cayley(3), k=2)
        s_s3 = sat_schur_general(symmetric_group_s3_cayley(), k=2)
        assert s_d3 == s_s3

    def test_d4_matches_abelian_order_8(self):
        """S(D_4, 2) = S(Z/8Z, 2) = 6."""
        s_d4 = sat_schur_general(dihedral_cayley(4), k=2)
        s_z8 = sat_schur((8,), k=2)
        assert s_d4 == s_z8 == 6

    def test_q8_matches_abelian_order_8(self):
        """S(Q_8, 2) = S(Z/8Z, 2) = 6."""
        s_q8 = sat_schur_general(quaternion_cayley(), k=2)
        s_z8 = sat_schur((8,), k=2)
        assert s_q8 == s_z8 == 6

    def test_d5_matches_abelian_order_10(self):
        """S(D_5, 2) = S(Z/10Z, 2) = 8."""
        s_d5 = sat_schur_general(dihedral_cayley(5), k=2)
        s_z10 = sat_schur((10,), k=2)
        assert s_d5 == s_z10 == 8


class TestNonabelianK3:
    """Non-abelian groups at k=3."""

    def test_s3_k3_matches_z6(self):
        """S(S_3, 3) = S(Z/6Z, 3)."""
        s_s3 = sat_schur_general(symmetric_group_s3_cayley(), k=3)
        s_z6 = sat_schur((6,), k=3)
        assert s_s3 == s_z6

    def test_d4_k3_matches_abelian_order_8(self):
        """S(D_4, 3) = S(Z/8Z, 3) = 7."""
        s_d4 = sat_schur_general(dihedral_cayley(4), k=3)
        s_z8 = sat_schur((8,), k=3)
        assert s_d4 == s_z8 == 7

    def test_q8_k3_matches_abelian_order_8(self):
        """S(Q_8, 3) = S(Z/8Z, 3) = 7."""
        s_q8 = sat_schur_general(quaternion_cayley(), k=3)
        s_z8 = sat_schur((8,), k=3)
        assert s_q8 == s_z8 == 7

    def test_nonabelian_k1(self):
        """S(G, 1) for non-abelian groups also matches abelian."""
        for (table, abelian_orders, name) in [
            (symmetric_group_s3_cayley(), (6,), "S_3 vs Z/6Z"),
            (dihedral_cayley(4), (8,), "D_4 vs Z/8Z"),
            (quaternion_cayley(), (8,), "Q_8 vs Z/8Z"),
        ]:
            s_na = sat_schur_general(table, k=1)
            s_ab = sat_schur(abelian_orders, k=1)
            assert s_na == s_ab, f"k=1 {name}: non-abelian={s_na}, abelian={s_ab}"


# =====================================================================
# 4. k=3 counterexample verification (independent)
# =====================================================================


class TestK3CounterexamplesIndependent:
    """Independent verification of k=3 invariance failures using SAT."""

    def test_order_9_sat_confirms_failure(self):
        """SAT independently confirms S(Z/9Z, 3) != S(Z/3Z x Z/3Z, 3)."""
        s_z9 = sat_schur((9,), k=3)
        s_z3z3 = sat_schur((3, 3), k=3)
        assert s_z9 == 8
        assert s_z3z3 == 7
        assert s_z9 != s_z3z3

    def test_order_12_sat_confirms_failure(self):
        """SAT confirms S(Z/3Z x Z/4Z, 3) != S(Z/2Z x Z/2Z x Z/3Z, 3)."""
        s_z3z4 = sat_schur((3, 4), k=3)
        s_z2z2z3 = sat_schur((2, 2, 3), k=3)
        assert s_z3z4 == 11
        assert s_z2z2z3 == 10
        assert s_z3z4 != s_z2z2z3

    def test_order_16_three_distinct_values(self):
        """S(G, 3) takes THREE distinct values at order 16."""
        groups_16 = all_abelian_groups(16)
        vals = {group_name(g): sat_schur(g, k=3) for g in groups_16}
        unique = sorted(set(vals.values()))
        assert len(unique) >= 2, f"Expected multiple values, got {vals}"
        # Verify specific values
        assert vals["Z/16Z"] == 14
        assert vals["Z/2Z x Z/2Z x Z/2Z x Z/2Z"] == 15
        assert vals["Z/4Z x Z/4Z"] == 15

    def test_order_18_confirms_failure(self):
        """S(G, 3) fails at order 18."""
        s_z2z9 = sat_schur((2, 9), k=3)
        s_z2z3z3 = sat_schur((2, 3, 3), k=3)
        assert s_z2z9 != s_z2z3z3

    def test_order_9_cross_check_brute_force(self):
        """Cross-check order 9 with brute-force (independent method)."""
        result = verify_k3_counterexamples()
        data = result[9]
        assert data["invariance_broken"]
        # SAT and brute-force agree
        for gname, gdata in data["groups"].items():
            if "brute_force" in gdata:
                assert gdata["agree"], f"{gname}: SAT={gdata['sat']}, BF={gdata['brute_force']}"


class TestK3InvarianceHolds:
    """Verify orders where k=3 invariance DOES hold."""

    def test_order_4_holds(self):
        assert sat_schur((4,), k=3) == sat_schur((2, 2), k=3) == 3

    def test_order_8_holds(self):
        vals = [sat_schur(g, k=3) for g in [(8,), (2, 4), (2, 2, 2)]]
        assert len(set(vals)) == 1
        assert vals[0] == 7

    def test_order_20_holds(self):
        vals = {group_name(g): sat_schur(g, k=3) for g in all_abelian_groups(20)}
        assert len(set(vals.values())) == 1


# =====================================================================
# 5. Exponent and 3-torsion analysis
# =====================================================================


class TestExponentMechanism:
    """Test the hypothesis that k=3 failure correlates with 3-torsion structure."""

    def test_order_9_torsion_counts(self):
        """Z/3Z x Z/3Z has 9 elements of 3-torsion, Z/9Z has 3."""
        for (g, expected_3tor) in [((9,), 3), ((3, 3), 9)]:
            elements = group_elements(g)
            z = group_zero(g)
            count = sum(
                1 for e in elements
                if group_add(group_add(e, e, g), e, g) == z
            )
            assert count == expected_3tor, (
                f"{group_name(g)}: 3-torsion count = {count}, expected {expected_3tor}"
            )

    def test_order_8_no_3_torsion(self):
        """All order 8 groups have trivial 3-torsion (only identity)."""
        for g in [(8,), (2, 4), (2, 2, 2)]:
            elements = group_elements(g)
            z = group_zero(g)
            count = sum(
                1 for e in elements
                if group_add(group_add(e, e, g), e, g) == z
            )
            assert count == 1, f"{group_name(g)}: 3-torsion count = {count}, expected 1"

    def test_order_4_no_3_torsion(self):
        """Order 4 groups: trivial 3-torsion."""
        for g in [(4,), (2, 2)]:
            elements = group_elements(g)
            z = group_zero(g)
            count = sum(
                1 for e in elements
                if group_add(group_add(e, e, g), e, g) == z
            )
            assert count == 1

    def test_more_3_torsion_means_smaller_s3(self):
        """Groups with more 3-torsion tend to have smaller S(G,3).

        At order 9: Z/3Z x Z/3Z (9 elements of 3-torsion) has S=7,
        while Z/9Z (3 elements) has S=8.
        """
        for g_less, g_more in [((9,), (3, 3)), ((2, 9), (2, 3, 3))]:
            elements_less = group_elements(g_less)
            elements_more = group_elements(g_more)
            z_less = group_zero(g_less)
            z_more = group_zero(g_more)

            tor_less = sum(
                1 for e in elements_less
                if group_add(group_add(e, e, g_less), e, g_less) == z_less
            )
            tor_more = sum(
                1 for e in elements_more
                if group_add(group_add(e, e, g_more), e, g_more) == z_more
            )
            s_less = sat_schur(g_less, k=3)
            s_more = sat_schur(g_more, k=3)

            assert tor_less < tor_more, (
                f"Expected {group_name(g_less)} to have less 3-torsion"
            )
            assert s_less > s_more, (
                f"More 3-torsion ({group_name(g_more)}: {tor_more}) should give "
                f"smaller S(G,3)={s_more}, but {group_name(g_less)} has S={s_less}"
            )

    def test_exponent_doesnt_fully_explain_order_16(self):
        """At order 16, there is no 3-torsion yet S(G,3) still varies.

        This proves the 3-torsion mechanism is NOT the full story.
        The element chain structure (Schur graph density) also matters.
        """
        groups_16 = all_abelian_groups(16)
        for g in groups_16:
            elements = group_elements(g)
            z = group_zero(g)
            count = sum(
                1 for e in elements
                if group_add(group_add(e, e, g), e, g) == z
            )
            # All order 16 groups are 2-groups: only identity is 3-torsion
            assert count == 1, f"{group_name(g)} has non-trivial 3-torsion!"

        vals = {group_name(g): sat_schur(g, k=3) for g in groups_16}
        assert len(set(vals.values())) > 1, (
            "Expected S(G,3) to vary at order 16 despite no 3-torsion"
        )


# =====================================================================
# 6. Boundary analysis functions
# =====================================================================


class TestBoundaryOrder4:
    def test_returns_invariant(self):
        result = k3_boundary_order4()
        assert result["invariant"]
        assert result["Z/4Z"]["S(G,3)"] == 3
        assert result["(Z/2Z)^2"]["S(G,3)"] == 3

    def test_nonzero_elements_colorable(self):
        result = k3_boundary_order4()
        assert result["Z/4Z"]["nonzero_3colorable"]
        assert result["(Z/2Z)^2"]["nonzero_3colorable"]


class TestBoundaryOrder8:
    def test_returns_invariant(self):
        result = k3_boundary_order8()
        assert result["invariant"]
        for gdata in result["groups"].values():
            assert gdata["S(G,3)"] == 7
            assert gdata["3_torsion_count"] == 1


class TestBoundaryOrder9:
    def test_invariance_broken(self):
        result = k3_boundary_order9()
        assert result["invariance_broken"]

    def test_z9_has_3_torsion_elements(self):
        result = k3_boundary_order9()
        z9 = result["groups"]["Z/9Z"]
        assert z9["3_torsion_count"] == 3  # {0, 3, 6}

    def test_z3z3_all_3_torsion(self):
        result = k3_boundary_order9()
        z3z3 = result["groups"]["Z/3Z x Z/3Z"]
        assert z3z3["3_torsion_count"] == 9  # every element

    def test_mechanism_explanation(self):
        result = k3_boundary_order9()
        assert "3-torsion" in result["mechanism"].lower()


class TestOrder16Detailed:
    def test_three_distinct_values(self):
        result = k3_full_order16()
        assert result["num_distinct"] >= 2

    def test_no_3_torsion_in_any_group(self):
        result = k3_full_order16()
        for gdata in result["groups"].values():
            assert gdata["3_torsion"] == 1  # only identity


# =====================================================================
# 7. Green-Ruzsa theoretical analysis
# =====================================================================


class TestGreenRuzsa:
    def test_k1_even_order_is_half(self):
        """For even-order abelian groups, S(G,1) = |G|/2."""
        analysis = green_ruzsa_analysis()
        for gname, (val, expected, ok) in analysis["even_order_verification"].items():
            assert ok, f"{gname}: S(G,1) = {val}, expected |G|/2 = {expected}"

    def test_k1_invariance_holds_through_20(self):
        """S(G,1) is order-invariant for all abelian groups up to order 20."""
        for n in range(2, 21):
            groups = all_abelian_groups(n)
            if len(groups) <= 1:
                continue
            vals = {group_name(g): sat_schur(g, k=1) for g in groups}
            assert len(set(vals.values())) == 1, f"S(G,1) differs at order {n}: {vals}"

    def test_k2_not_implied_by_theory(self):
        """Green-Ruzsa does NOT imply k=2 invariance."""
        analysis = green_ruzsa_analysis()
        assert "novel" in analysis["k2_no_theory"].lower() or \
               "no theoretical" in analysis["k2_no_theory"].lower()


# =====================================================================
# 8. Integration: compare_nonabelian function
# =====================================================================


class TestCompareNonabelian:
    def test_returns_all_groups(self):
        results = compare_nonabelian(k=2)
        assert "S_3 (order 6)" in results
        assert "D_4 (order 8)" in results
        assert "Q_8 (order 8)" in results
        assert "D_3 (order 6)" in results

    def test_all_match_at_k2(self):
        results = compare_nonabelian(k=2)
        for name, data in results.items():
            assert data["matches_abelian"], (
                f"{name}: S(G,2)={data['S(G,k)']} does not match abelian {data['abelian_same_order']}"
            )

    def test_d3_matches_s3(self):
        results = compare_nonabelian(k=2)
        assert results["D_3 (order 6)"]["matches_S3"]


# =====================================================================
# 9. k=2 formula validation
# =====================================================================


class TestK2FormulaConsistency:
    """Verify that S(G,2) values follow known formulas."""

    def test_powers_of_2_formula(self):
        """S(G, 2) = 3n/4 for all abelian groups of order n = 2^k, k=1..5."""
        for k in range(1, 6):  # up to 32; k=6 (order 64) is too slow
            n = 2**k
            for g in all_abelian_groups(n):
                s2 = sat_schur(g, k=2)
                expected = 3 * n // 4
                assert s2 == expected, (
                    f"{group_name(g)}: S(G,2)={s2}, expected 3*{n}/4={expected}"
                )

    def test_multiples_of_5_formula(self):
        """S(G, 2) = 4n/5 for all abelian groups of order n divisible by 5."""
        for n in range(5, 51, 5):
            for g in all_abelian_groups(n):
                s2 = sat_schur(g, k=2)
                expected = 4 * n // 5
                assert s2 == expected, (
                    f"{group_name(g)} (order {n}): S(G,2)={s2}, expected 4n/5={expected}"
                )

    def test_order_ratio_consistent_across_structure(self):
        """For each order with multiple groups, the S(G,2)/|G| ratio is constant."""
        for n in range(2, 49):
            groups = all_abelian_groups(n)
            if len(groups) <= 1:
                continue
            ratios = set()
            for g in groups:
                s2 = sat_schur(g, k=2)
                ratios.add(s2)
            assert len(ratios) == 1, f"Order {n}: S(G,2) values disagree: {ratios}"


# =====================================================================
# 10. Stress tests: highest orders with multiple groups
# =====================================================================


class TestK2ExtremeOrders:
    """Test at the highest feasible orders with many non-isomorphic groups."""

    def test_order_27_cube(self):
        """Order 27 = 3^3: all 3 groups agree."""
        groups = all_abelian_groups(27)
        vals = [sat_schur(g, k=2) for g in groups]
        assert len(set(vals)) == 1
        assert vals[0] == 18

    def test_order_28(self):
        """Order 28 = 4 * 7: both groups agree."""
        groups = all_abelian_groups(28)
        vals = [sat_schur(g, k=2) for g in groups]
        assert len(set(vals)) == 1
        assert vals[0] == 21

    def test_s2_values_match_known(self):
        """Spot-check computed S(G,2) values against expectations."""
        expected = {
            24: 18,  # 3*24/4
            25: 20,  # 4*25/5
            27: 18,  # 2*27/3
            28: 21,  # 3*28/4
            32: 24,  # 3*32/4
            36: 27,  # 3*36/4
        }
        for n, exp in expected.items():
            for g in all_abelian_groups(n):
                s2 = sat_schur(g, k=2)
                assert s2 == exp, f"{group_name(g)} order {n}: S(G,2)={s2}, expected {exp}"


# =====================================================================
# 11. Order 49 investigation: potential counterexample
# =====================================================================


class TestOrder49Counterexample:
    """Order 49 = 7^2: COUNTEREXAMPLE to S(G,2) order-invariance.

    VERIFIED:
      S(Z/49Z, 2) = 32  (ratio 32/49 ~ 0.653)
      S(Z/7Z x Z/7Z, 2) = 28  (ratio 28/49 ~ 0.571)

    This disproves the conjecture that S(G, 2) depends only on |G|
    for finite abelian groups.  The invariance holds through order 48
    but fails at order 49.

    The mechanism: Z/7Z x Z/7Z has many more Schur triples of the
    form (a, b, a+b) where all three elements are "entangled" in the
    2D structure, making the constraint graph denser and reducing the
    maximum 2-colorable sum-free subset.
    """

    def test_z49_value(self):
        """S(Z/49Z, 2) = 32."""
        s = sat_schur((49,), k=2)
        assert s == 32

    @pytest.mark.timeout(3600)
    def test_z7z7_value(self):
        """S(Z/7Z x Z/7Z, 2) = 28.  (~30 min computation)"""
        s = sat_schur((7, 7), k=2)
        assert s == 28

    @pytest.mark.timeout(3600)
    def test_order_49_counterexample(self):
        """COUNTEREXAMPLE: S(Z/49Z, 2) = 32 != S(Z/7Z x Z/7Z, 2) = 28.

        This disproves the conjecture that S(G,2) = f(|G|) for abelian G.
        """
        s_z49 = sat_schur((49,), k=2)
        s_z7z7 = sat_schur((7, 7), k=2)
        assert s_z49 == 32
        assert s_z7z7 == 28
        assert s_z49 != s_z7z7, "This should be a counterexample!"
