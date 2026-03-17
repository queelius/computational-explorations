"""Tests for ramsey_games.py -- Game-theoretic coprime Ramsey formulations."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ramsey_games import (
    _clique_edges,
    _edge,
    comparison_table,
    coprime_adj,
    coprime_edges,
    find_coprime_cliques,
    format_comparison_table,
    GameOutcome,
    GameState,
    maker_breaker_threshold,
    maker_breaker_winner,
    Player,
    random_turn_simulate,
    random_turn_sweep,
    strong_game_outcome,
    strong_game_threshold,
    waiter_client_threshold,
    waiter_client_winner,
)


# ---------------------------------------------------------------------------
# Infrastructure tests
# ---------------------------------------------------------------------------

class TestEdgeCanonical:
    def test_ordered(self):
        assert _edge(3, 1) == (1, 3)
        assert _edge(1, 3) == (1, 3)

    def test_equal(self):
        assert _edge(5, 5) == (5, 5)


class TestCoprimeEdges:
    def test_n3_complete(self):
        """[3] is a coprime clique: all pairs coprime."""
        edges = coprime_edges(3)
        assert set(edges) == {(1, 2), (1, 3), (2, 3)}

    def test_n4_missing_24(self):
        """gcd(2,4)=2, so (2,4) absent."""
        edges = coprime_edges(4)
        assert (2, 4) not in edges
        assert (1, 4) in edges

    def test_n1_empty(self):
        assert coprime_edges(1) == []

    def test_edge_count_matches_manual(self):
        """Verify edge count for n=6 by manual gcd computation."""
        expected = sum(1 for i in range(1, 7) for j in range(i + 1, 7)
                       if math.gcd(i, j) == 1)
        assert len(coprime_edges(6)) == expected


class TestCoprimeAdj:
    def test_symmetric(self):
        adj = coprime_adj(8)
        for v, nbrs in adj.items():
            for w in nbrs:
                assert v in adj[w]

    def test_vertex_1_universal(self):
        adj = coprime_adj(10)
        assert adj[1] == set(range(2, 11))


class TestFindCoprimeCliques:
    def test_triangles_n5(self):
        cliques = find_coprime_cliques(5, 3)
        for c in cliques:
            assert len(c) == 3
            for i in range(3):
                for j in range(i + 1, 3):
                    assert math.gcd(c[i], c[j]) == 1

    def test_no_large_clique_small_graph(self):
        assert find_coprime_cliques(3, 5) == []

    def test_k1_singletons(self):
        assert len(find_coprime_cliques(6, 1)) == 6

    def test_k0_empty(self):
        assert find_coprime_cliques(6, 0) == []

    def test_clique_count_n5_k3(self):
        """n=5 has 7 triangles in the coprime graph."""
        cliques = find_coprime_cliques(5, 3)
        assert len(cliques) == 7


class TestCliqueEdges:
    def test_triangle(self):
        edges = _clique_edges((1, 3, 5))
        assert set(edges) == {(1, 3), (1, 5), (3, 5)}

    def test_k4(self):
        edges = _clique_edges((1, 2, 3, 5))
        assert len(edges) == 6  # C(4,2) = 6


class TestGameState:
    def test_initial_state(self):
        gs = GameState(5, 3)
        assert len(gs.edges) == 9
        assert len(gs.unclaimed) == 9
        assert len(gs.claimed[0]) == 0
        assert len(gs.claimed[1]) == 0

    def test_claim_unclaim(self):
        gs = GameState(5, 3)
        e = gs.edges[0]
        gs.claim(0, e)
        assert e in gs.claimed[0]
        assert e not in gs.unclaimed
        gs.unclaim(0, e)
        assert e not in gs.claimed[0]
        assert e in gs.unclaimed

    def test_has_monochromatic_clique_empty(self):
        gs = GameState(5, 3)
        assert not gs.has_monochromatic_clique(0)
        assert not gs.has_monochromatic_clique(1)

    def test_has_monochromatic_clique_after_triangle(self):
        """Claiming all edges of a coprime triangle creates a mono K_3."""
        gs = GameState(5, 3)
        # Triangle {1, 2, 3}: edges (1,2), (1,3), (2,3)
        gs.claim(0, (1, 2))
        gs.claim(0, (1, 3))
        assert not gs.has_monochromatic_clique(0)
        gs.claim(0, (2, 3))
        assert gs.has_monochromatic_clique(0)

    def test_compact_key_deterministic(self):
        gs = GameState(4, 3)
        gs.claim(0, (1, 2))
        gs.claim(1, (1, 3))
        k1 = gs.compact_key()
        k2 = gs.compact_key()
        assert k1 == k2

    def test_no_cliques_small_k(self):
        """GameState with k larger than max clique should have empty cliques."""
        gs = GameState(3, 10)
        assert gs.cliques == []


# ---------------------------------------------------------------------------
# 1. Maker-Breaker game tests
# ---------------------------------------------------------------------------

class TestMakerBreaker:
    def test_n3_breaker_wins(self):
        """n=3: only 3 edges and 1 triangle. With alternating play,
        Breaker claims 1 edge from the triangle, preventing Maker."""
        assert maker_breaker_winner(3, 3) == GameOutcome.BREAKER_WIN

    def test_n4_breaker_wins(self):
        """n=4: 5 edges, still too few for Maker to force a triangle."""
        assert maker_breaker_winner(4, 3) == GameOutcome.BREAKER_WIN

    def test_n5_maker_wins(self):
        """n=5: 9 edges, 7 triangles. Maker can force a triangle."""
        assert maker_breaker_winner(5, 3) == GameOutcome.MAKER_WIN

    def test_n6_maker_wins(self):
        """Once Maker wins at n, they also win at n+1 (more edges help Maker)."""
        assert maker_breaker_winner(6, 3) == GameOutcome.MAKER_WIN

    def test_no_cliques_breaker_wins(self):
        """If k exceeds max clique, Breaker trivially wins."""
        assert maker_breaker_winner(3, 10) == GameOutcome.BREAKER_WIN

    def test_threshold_k3(self):
        """Maker-Breaker threshold for K_3 is n=5."""
        assert maker_breaker_threshold(3, max_n=8) == 5

    def test_threshold_not_found(self):
        """Large k with small max_n: threshold not found."""
        assert maker_breaker_threshold(10, max_n=5) == -1

    def test_k2_trivial(self):
        """K_2: Maker wins immediately by claiming any edge (n >= 2)."""
        # At n=2, there's 1 edge (1,2). Maker claims it -> mono K_2.
        assert maker_breaker_winner(2, 2) == GameOutcome.MAKER_WIN

    def test_monotone_maker_advantage(self):
        """If Maker wins at n, they should also win at n+1.

        More edges only help Maker (superset of strategies).
        We verify this for a range near the threshold.
        """
        results = [maker_breaker_winner(n, 3) for n in range(3, 8)]
        # Once MAKER_WIN appears, it should stay
        found_win = False
        for r in results:
            if r == GameOutcome.MAKER_WIN:
                found_win = True
            if found_win:
                assert r == GameOutcome.MAKER_WIN


# ---------------------------------------------------------------------------
# 2. Strong game tests
# ---------------------------------------------------------------------------

class TestStrongGame:
    def test_n3_draw(self):
        """n=3: 3 edges, 1 triangle. With 2 turns each (3 edges, Maker
        gets 2, Breaker gets 1), neither completes the triangle alone."""
        assert strong_game_outcome(3, 3) == GameOutcome.DRAW

    def test_n4_draw(self):
        assert strong_game_outcome(4, 3) == GameOutcome.DRAW

    def test_n5_first_player_wins(self):
        """n=5: enough triangles that first player can force a win."""
        assert strong_game_outcome(5, 3) == GameOutcome.MAKER_WIN

    def test_no_cliques_draw(self):
        """If no K_k cliques exist, the strong game is a draw."""
        assert strong_game_outcome(3, 10) == GameOutcome.DRAW

    def test_threshold_k3(self):
        """Strong game threshold for K_3 is n=5."""
        assert strong_game_threshold(3, max_n=8) == 5

    def test_threshold_not_found(self):
        assert strong_game_threshold(10, max_n=5) == -1

    def test_strategy_stealing_no_p2_win(self):
        """By strategy-stealing, P2 cannot have a winning strategy in
        the strong game. So outcome is either P1 WIN or DRAW, never P2 WIN.

        This is a fundamental theorem: if P2 had a winning strategy,
        P1 could 'steal' it by making an arbitrary first move, then
        following P2's strategy (an extra edge never hurts).
        """
        for n in range(3, 8):
            outcome = strong_game_outcome(n, 3)
            assert outcome != GameOutcome.BREAKER_WIN, (
                f"Strategy-stealing violated at n={n}: "
                f"second player should never win the strong game"
            )

    def test_monotone_first_player(self):
        """Once first player wins, they should continue winning at larger n."""
        results = [strong_game_outcome(n, 3) for n in range(3, 8)]
        found_win = False
        for r in results:
            if r == GameOutcome.MAKER_WIN:
                found_win = True
            if found_win:
                assert r == GameOutcome.MAKER_WIN


# ---------------------------------------------------------------------------
# 3. Waiter-Client game tests
# ---------------------------------------------------------------------------

class TestWaiterClient:
    def test_n3_client_wins(self):
        """n=3: 3 edges, 1 triangle. Waiter offers 1 pair, Client avoids."""
        assert waiter_client_winner(3, 3) == GameOutcome.BREAKER_WIN

    def test_n4_client_wins(self):
        assert waiter_client_winner(4, 3) == GameOutcome.BREAKER_WIN

    def test_n5_waiter_wins(self):
        """n=5: Waiter can force Client into a triangle."""
        assert waiter_client_winner(5, 3) == GameOutcome.MAKER_WIN

    def test_no_cliques_client_wins(self):
        assert waiter_client_winner(3, 10) == GameOutcome.BREAKER_WIN

    def test_threshold_k3(self):
        assert waiter_client_threshold(3, max_n=6) == 5

    def test_threshold_not_found(self):
        assert waiter_client_threshold(10, max_n=5) == -1

    def test_waiter_at_least_as_strong_as_maker_breaker(self):
        """Waiter-Client threshold <= Maker-Breaker threshold.

        Waiter controls the pair offerings, giving a stronger offensive
        position than Maker who just picks one edge per turn.
        """
        wc = waiter_client_threshold(3, max_n=8)
        mb = maker_breaker_threshold(3, max_n=8)
        assert wc <= mb


# ---------------------------------------------------------------------------
# 4. Random-turn game tests
# ---------------------------------------------------------------------------

class TestRandomTurn:
    def test_deterministic_seed(self):
        """Same seed produces same results."""
        r1 = random_turn_simulate(8, 3, num_sims=100, seed=123)
        r2 = random_turn_simulate(8, 3, num_sims=100, seed=123)
        assert r1["maker_wins"] == r2["maker_wins"]
        assert r1["avg_game_length"] == r2["avg_game_length"]

    def test_counts_sum(self):
        """maker_wins + breaker_wins = num_sims."""
        r = random_turn_simulate(8, 3, num_sims=500, seed=42)
        assert r["maker_wins"] + r["breaker_wins"] == 500

    def test_probability_range(self):
        r = random_turn_simulate(8, 3, num_sims=500, seed=42)
        assert 0.0 <= r["maker_win_prob"] <= 1.0

    def test_avg_length_positive(self):
        r = random_turn_simulate(8, 3, num_sims=100, seed=42)
        assert r["avg_game_length"] > 0

    def test_no_cliques_zero_wins(self):
        """When no K_k cliques exist, Maker never wins."""
        r = random_turn_simulate(3, 10, num_sims=100, seed=42)
        assert r["maker_wins"] == 0
        assert r["maker_win_prob"] == 0.0

    def test_no_edges_zero_length(self):
        """n=1 has no edges; avg game length should be 0."""
        r = random_turn_simulate(1, 3, num_sims=100, seed=42)
        assert r["avg_game_length"] == 0.0

    def test_maker_wins_more_at_larger_n(self):
        """More edges at larger n should give Maker a higher win rate
        (stochastically, not deterministically per trial)."""
        r_small = random_turn_simulate(5, 3, num_sims=2000, seed=42)
        r_large = random_turn_simulate(10, 3, num_sims=2000, seed=42)
        assert r_large["maker_win_prob"] >= r_small["maker_win_prob"]

    def test_n5_crossover(self):
        """n=5 is near the 50% mark for random-turn with k=3."""
        r = random_turn_simulate(5, 3, num_sims=5000, seed=42)
        # Should be roughly near 50% (between 30% and 70%)
        assert 0.30 < r["maker_win_prob"] < 0.70

    def test_n11_almost_certain(self):
        """At n=11 = R_cop(3), Maker should almost always win randomly."""
        r = random_turn_simulate(11, 3, num_sims=2000, seed=42)
        assert r["maker_win_prob"] > 0.95


class TestRandomTurnSweep:
    def test_sweep_returns_all_n(self):
        results = random_turn_sweep(3, n_range=(8, 10), num_sims=50, seed=42)
        assert set(results.keys()) == {8, 9, 10}

    def test_sweep_contents(self):
        results = random_turn_sweep(3, n_range=(8, 9), num_sims=100, seed=42)
        for n, data in results.items():
            assert "maker_wins" in data
            assert "maker_win_prob" in data
            assert "avg_game_length" in data


# ---------------------------------------------------------------------------
# 5. Comparison table tests
# ---------------------------------------------------------------------------

class TestComparisonTable:
    @pytest.fixture(scope="class")
    def table_data(self):
        """Compute comparison once for all tests in this class."""
        return comparison_table(
            k=3, mb_max_n=6, strong_max_n=6, wc_max_n=6,
            rt_sims=500, rt_seed=42
        )

    def test_has_all_keys(self, table_data):
        required = {
            "k", "maker_breaker_threshold", "strong_game_threshold",
            "waiter_client_threshold", "random_turn_threshold",
            "random_turn_data", "rcop"
        }
        assert required.issubset(table_data.keys())

    def test_k_value(self, table_data):
        assert table_data["k"] == 3

    def test_rcop_value(self, table_data):
        assert table_data["rcop"] == 11

    def test_thresholds_positive(self, table_data):
        assert table_data["maker_breaker_threshold"] > 0
        assert table_data["strong_game_threshold"] > 0
        assert table_data["waiter_client_threshold"] > 0

    def test_ordering_wc_le_mb(self, table_data):
        """Waiter-Client <= Maker-Breaker (Waiter is stronger offensively)."""
        wc = table_data["waiter_client_threshold"]
        mb = table_data["maker_breaker_threshold"]
        assert wc <= mb

    def test_all_thresholds_le_rcop(self, table_data):
        """All game thresholds should be <= R_cop(3) = 11.

        In the game, the offensive player has active control, which is
        at least as powerful as every possible passive coloring being forced.
        """
        rcop = table_data["rcop"]
        assert table_data["maker_breaker_threshold"] <= rcop
        assert table_data["strong_game_threshold"] <= rcop
        assert table_data["waiter_client_threshold"] <= rcop

    def test_format_produces_string(self, table_data):
        s = format_comparison_table(table_data)
        assert isinstance(s, str)
        assert "COMPARISON" in s
        assert "Maker-Breaker" in s


# ---------------------------------------------------------------------------
# Cross-variant consistency tests
# ---------------------------------------------------------------------------

class TestCrossVariantConsistency:
    """Verify theoretical relationships between game variants."""

    def test_mb_threshold_equals_5(self):
        assert maker_breaker_threshold(3, max_n=8) == 5

    def test_strong_threshold_equals_5(self):
        assert strong_game_threshold(3, max_n=8) == 5

    def test_wc_threshold_equals_5(self):
        assert waiter_client_threshold(3, max_n=6) == 5

    def test_all_thresholds_below_rcop(self):
        """All game thresholds for k=3 are strictly below R_cop(3)=11."""
        mb = maker_breaker_threshold(3, max_n=8)
        sg = strong_game_threshold(3, max_n=8)
        wc = waiter_client_threshold(3, max_n=6)
        rcop = 11
        assert mb < rcop
        assert sg < rcop
        assert wc < rcop

    def test_game_thresholds_concordant(self):
        """For k=3, all three exact game variants agree on threshold = 5.

        This is remarkable: the coprime graph G([5]) is rich enough in
        triangles that the offensive player wins under all game protocols,
        while G([4]) is too sparse for any of them.
        """
        mb = maker_breaker_threshold(3, max_n=8)
        sg = strong_game_threshold(3, max_n=8)
        wc = waiter_client_threshold(3, max_n=6)
        assert mb == sg == wc == 5


class TestK2Games:
    """K_2 (edge) games: Maker always wins immediately at n=2."""

    def test_mb_k2(self):
        assert maker_breaker_winner(2, 2) == GameOutcome.MAKER_WIN

    def test_strong_k2(self):
        # First player claims the only edge -> wins
        assert strong_game_outcome(2, 2) == GameOutcome.MAKER_WIN

    def test_random_k2(self):
        r = random_turn_simulate(2, 2, num_sims=200, seed=42)
        # n=2 has 1 coprime edge (1,2). Whoever gets it wins K_2.
        # In random turn, maker gets it ~50% of the time.
        assert r["maker_win_prob"] > 0.3  # reasonable even with randomness


class TestEdgeCases:
    """Boundary and degenerate cases."""

    def test_n_equals_k_minus_1(self):
        """n < k: no K_k clique possible."""
        assert maker_breaker_winner(2, 3) == GameOutcome.BREAKER_WIN
        assert strong_game_outcome(2, 3) == GameOutcome.DRAW

    def test_single_triangle_graph(self):
        """n=3, k=3: exactly 1 triangle, 3 edges."""
        gs = GameState(3, 3)
        assert len(gs.cliques) == 1
        assert len(gs.edges) == 3

    def test_game_state_no_double_claim(self):
        """Claiming same edge twice should not duplicate in sets."""
        gs = GameState(5, 3)
        e = gs.edges[0]
        gs.claim(0, e)
        gs.claim(0, e)  # second claim is a no-op
        assert len(gs.claimed[0]) == 1

    def test_player_enum(self):
        assert Player.MAKER == 0
        assert Player.BREAKER == 1

    def test_outcome_enum(self):
        assert GameOutcome.MAKER_WIN == 0
        assert GameOutcome.BREAKER_WIN == 1
        assert GameOutcome.DRAW == 2
