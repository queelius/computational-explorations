#!/usr/bin/env python3
"""
Game-Theoretic Formulations of Coprime Ramsey Theory

Ramsey theory has natural game-theoretic formulations where two players
alternately claim edges and try to build (or avoid) monochromatic cliques.
This module studies four game variants on the coprime graph G([n]):

1. Maker-Breaker game: Maker tries to complete a mono K_k, Breaker blocks.
2. Strong game: Both players try to complete K_k first. Draw possible.
3. Waiter-Client game: Waiter offers edge pairs, Client must take one.
4. Random-turn game: Coin flip decides who moves each turn.

All games are played on the coprime graph G([n]) = {1,...,n} with edges
between coprime pairs. The central question: for each variant and k=3,
what is the critical n where the "offensive" player wins?

Key result: R_cop(3) = 11 (from coprime_ramsey.py). How do the game
thresholds compare?

Theory:
- In Maker-Breaker, Maker only needs one mono K_k, Breaker must block all.
  So Maker wins at smaller n than in the strong game.
- By Erdos-Selfridge / strategy-stealing, first player in the strong game
  has a non-losing strategy. The question is: winning or drawing?
- Waiter-Client games are biased: Waiter controls which edges are offered.
  This is stronger than Maker-Breaker for the offensive player.
- Random-turn games interpolate between adversarial and probabilistic.
"""

import math
import random
from enum import IntEnum
from itertools import combinations
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Shared graph infrastructure
# ---------------------------------------------------------------------------

# Canonical edge representation: always (min, max)
Edge = Tuple[int, int]


def _edge(a: int, b: int) -> Edge:
    """Canonical edge with smaller vertex first."""
    return (min(a, b), max(a, b))


def coprime_edges(n: int) -> List[Edge]:
    """Return all coprime pairs (i,j) with 1 <= i < j <= n."""
    return [(i, j) for i in range(1, n + 1)
            for j in range(i + 1, n + 1)
            if math.gcd(i, j) == 1]


def coprime_adj(n: int) -> Dict[int, Set[int]]:
    """Build adjacency sets for the coprime graph on [n]."""
    adj: Dict[int, Set[int]] = {v: set() for v in range(1, n + 1)}
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if math.gcd(i, j) == 1:
                adj[i].add(j)
                adj[j].add(i)
    return adj


def find_coprime_cliques(n: int, k: int) -> List[Tuple[int, ...]]:
    """Enumerate all k-cliques in the coprime graph on [n]."""
    if k < 1:
        return []
    if k == 1:
        return [(v,) for v in range(1, n + 1)]

    adj = coprime_adj(n)
    vertices = list(range(1, n + 1))
    cliques: List[Tuple[int, ...]] = []

    def extend(current: List[int], candidates: List[int]):
        if len(current) == k:
            cliques.append(tuple(current))
            return
        needed = k - len(current)
        for idx, v in enumerate(candidates):
            if len(candidates) - idx < needed:
                break
            if all(v in adj[u] for u in current):
                new_cands = [w for w in candidates[idx + 1:] if w in adj[v]]
                extend(current + [v], new_cands)

    extend([], vertices)
    return cliques


def _clique_edges(clique: Tuple[int, ...]) -> List[Edge]:
    """Return the edges of a clique in canonical order."""
    vl = sorted(clique)
    return [(vl[i], vl[j]) for i in range(len(vl))
            for j in range(i + 1, len(vl))]


# ---------------------------------------------------------------------------
# Game state representation
# ---------------------------------------------------------------------------

class Player(IntEnum):
    """Game participants."""
    MAKER = 0     # or First player in strong game
    BREAKER = 1   # or Second player in strong game


class GameOutcome(IntEnum):
    """Possible outcomes."""
    MAKER_WIN = 0
    BREAKER_WIN = 1
    DRAW = 2
    UNKNOWN = 3


class GameState:
    """State of a positional game on the coprime graph.

    Edges are partitioned into three sets:
    - claimed[0]: edges claimed by player 0 (Maker / First)
    - claimed[1]: edges claimed by player 1 (Breaker / Second)
    - unclaimed: edges not yet taken

    Attributes:
        n: graph parameter [n]
        k: target clique size
        edges: all coprime edges of G([n])
        claimed: dict mapping player index to set of edges
        unclaimed: set of unclaimed edges
        cliques: all k-cliques in G([n])
        clique_edge_sets: precomputed frozensets for each clique
    """

    def __init__(self, n: int, k: int):
        self.n = n
        self.k = k
        self.edges = coprime_edges(n)
        self.claimed: Dict[int, Set[Edge]] = {0: set(), 1: set()}
        self.unclaimed: Set[Edge] = set(self.edges)
        self.cliques = find_coprime_cliques(n, k)
        self.clique_edge_sets: List[FrozenSet[Edge]] = [
            frozenset(_clique_edges(c)) for c in self.cliques
        ]

    def claim(self, player: int, edge: Edge):
        """Player claims an unclaimed edge."""
        self.unclaimed.discard(edge)
        self.claimed[player].add(edge)

    def unclaim(self, player: int, edge: Edge):
        """Undo a claim (for backtracking in minimax)."""
        self.claimed[player].discard(edge)
        self.unclaimed.add(edge)

    def has_monochromatic_clique(self, player: int) -> bool:
        """Check if the given player has completed a mono K_k."""
        owned = self.claimed[player]
        for es in self.clique_edge_sets:
            if es.issubset(owned):
                return True
        return False

    def compact_key(self) -> Tuple[FrozenSet[Edge], FrozenSet[Edge]]:
        """A hashable key for transposition table lookups."""
        return (frozenset(self.claimed[0]), frozenset(self.claimed[1]))


# ---------------------------------------------------------------------------
# 1. Maker-Breaker game on coprime graph
# ---------------------------------------------------------------------------

def _mb_minimax(state: GameState, is_maker_turn: bool,
                alpha: int, beta: int,
                cache: Dict) -> int:
    """Minimax with alpha-beta pruning for the Maker-Breaker game.

    Maker (player 0) maximizes: +1 = Maker wins, -1 = Breaker wins.
    Breaker (player 1) minimizes.

    Maker wins if they complete a monochromatic K_k in their color.
    Breaker wins if the board fills with no such clique.
    """
    key = (state.compact_key(), is_maker_turn)
    if key in cache:
        return cache[key]

    # Terminal checks
    if state.has_monochromatic_clique(0):
        cache[key] = 1
        return 1

    if not state.unclaimed:
        cache[key] = -1
        return -1

    # Move ordering: edges involved in more incomplete cliques first
    # (for Maker, these are more promising; for Breaker, more urgent)
    unclaimed_list = sorted(state.unclaimed)

    if is_maker_turn:
        best = -2
        for edge in unclaimed_list:
            state.claim(0, edge)
            val = _mb_minimax(state, False, alpha, beta, cache)
            state.unclaim(0, edge)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        cache[key] = best
        return best
    else:
        best = 2
        for edge in unclaimed_list:
            state.claim(1, edge)
            val = _mb_minimax(state, True, alpha, beta, cache)
            state.unclaim(1, edge)
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break
        cache[key] = best
        return best


def maker_breaker_winner(n: int, k: int) -> GameOutcome:
    """Determine the winner of the Maker-Breaker game on G([n]) for K_k.

    Maker moves first. Uses exact minimax with alpha-beta pruning
    and transposition tables. Feasible for small n (up to ~10 for k=3).

    Returns:
        GameOutcome.MAKER_WIN if Maker has a winning strategy.
        GameOutcome.BREAKER_WIN if Breaker can prevent Maker from winning.
    """
    state = GameState(n, k)

    # Quick check: if no k-cliques exist, Breaker trivially wins
    if not state.cliques:
        return GameOutcome.BREAKER_WIN

    cache: Dict = {}
    val = _mb_minimax(state, True, -2, 2, cache)
    return GameOutcome.MAKER_WIN if val > 0 else GameOutcome.BREAKER_WIN


def maker_breaker_threshold(k: int, max_n: int = 15) -> int:
    """Find the smallest n where Maker wins the Maker-Breaker game for K_k.

    Returns -1 if not found within max_n.
    """
    for n in range(k, max_n + 1):
        if maker_breaker_winner(n, k) == GameOutcome.MAKER_WIN:
            return n
    return -1


# ---------------------------------------------------------------------------
# 2. Strong game (both players try to complete K_k)
# ---------------------------------------------------------------------------

def _strong_minimax(state: GameState, is_first_turn: bool,
                    alpha: int, beta: int,
                    cache: Dict) -> int:
    """Minimax for the strong game.

    First player (0) maximizes: +1 = P1 wins, -1 = P2 wins, 0 = draw.
    Second player (1) minimizes.

    Either player wins by completing a monochromatic K_k in their color.
    If the board fills with no winner, it is a draw.
    """
    key = (state.compact_key(), is_first_turn)
    if key in cache:
        return cache[key]

    # Check if the player who just moved won
    # (The player who just moved is the opposite of whose turn it is now)
    just_moved = 1 if is_first_turn else 0
    if state.has_monochromatic_clique(just_moved):
        val = 1 if just_moved == 0 else -1
        cache[key] = val
        return val

    if not state.unclaimed:
        cache[key] = 0  # draw
        return 0

    current_player = 0 if is_first_turn else 1
    unclaimed_list = sorted(state.unclaimed)

    if is_first_turn:
        # First player maximizes
        best = -2
        for edge in unclaimed_list:
            state.claim(current_player, edge)
            val = _strong_minimax(state, False, alpha, beta, cache)
            state.unclaim(current_player, edge)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
            if best == 1:
                break  # can't do better
        cache[key] = best
        return best
    else:
        # Second player minimizes
        best = 2
        for edge in unclaimed_list:
            state.claim(current_player, edge)
            val = _strong_minimax(state, True, alpha, beta, cache)
            state.unclaim(current_player, edge)
            if val < best:
                best = val
            if best < beta:
                beta = best
            if alpha >= beta:
                break
            if best == -1:
                break  # can't do better for minimizer
        cache[key] = best
        return best


def strong_game_outcome(n: int, k: int) -> GameOutcome:
    """Determine the outcome of the strong game on G([n]) for K_k.

    First player moves first. Both try to complete K_k.

    Returns:
        GameOutcome.MAKER_WIN (= first player wins)
        GameOutcome.BREAKER_WIN (= second player wins)
        GameOutcome.DRAW
    """
    state = GameState(n, k)

    if not state.cliques:
        return GameOutcome.DRAW

    cache: Dict = {}
    val = _strong_minimax(state, True, -2, 2, cache)
    if val > 0:
        return GameOutcome.MAKER_WIN
    elif val < 0:
        return GameOutcome.BREAKER_WIN
    else:
        return GameOutcome.DRAW


def strong_game_threshold(k: int, max_n: int = 15) -> int:
    """Find smallest n where first player WINS the strong game for K_k.

    By strategy-stealing, first player always has a non-losing strategy
    (win or draw). This finds where "draw" becomes "win".

    Returns -1 if not found within max_n.
    """
    for n in range(k, max_n + 1):
        if strong_game_outcome(n, k) == GameOutcome.MAKER_WIN:
            return n
    return -1


# ---------------------------------------------------------------------------
# 3. Waiter-Client game
# ---------------------------------------------------------------------------

def _wc_minimax(state: GameState, unclaimed_list: List[Edge],
                alpha: int, beta: int,
                cache: Dict) -> int:
    """Minimax for Waiter-Client game.

    Waiter (maximizer) offers pairs of unclaimed edges.
    Client (minimizer) must take one from each pair.
    Waiter wins (+1) if Client is forced into a mono K_k.
    Client wins (-1) if they avoid all mono K_k.

    Client's edges go into player 0's set (the "danger" set).
    The edges Client does not pick go to the discard pile (player 1).
    """
    key = (state.compact_key(), True)
    if key in cache:
        return cache[key]

    # Check if Client already has a mono K_k (Waiter wins)
    if state.has_monochromatic_clique(0):
        cache[key] = 1
        return 1

    remaining = [e for e in unclaimed_list if e in state.unclaimed]

    # If fewer than 2 edges remain, game ends without Waiter winning
    if len(remaining) < 2:
        # Client might still be forced to take the last edge alone
        if len(remaining) == 1:
            edge = remaining[0]
            state.claim(0, edge)
            won = state.has_monochromatic_clique(0)
            state.unclaim(0, edge)
            val = 1 if won else -1
            cache[key] = val
            return val
        cache[key] = -1
        return -1

    # Waiter picks a pair; Client picks one edge from the pair.
    # Waiter maximizes over pair choices; Client minimizes over which to take.
    best_waiter = -2
    for i in range(len(remaining)):
        for j in range(i + 1, len(remaining)):
            e1, e2 = remaining[i], remaining[j]

            # Client chooses the better (for Client) of e1 vs e2
            # Option A: Client takes e1, Waiter gets e2
            state.claim(0, e1)
            state.claim(1, e2)
            val_a = _wc_minimax(state, unclaimed_list, alpha, beta, cache)
            state.unclaim(0, e1)
            state.unclaim(1, e2)

            # Option B: Client takes e2, Waiter gets e1
            state.claim(0, e2)
            state.claim(1, e1)
            val_b = _wc_minimax(state, unclaimed_list, alpha, beta, cache)
            state.unclaim(0, e2)
            state.unclaim(1, e1)

            # Client minimizes
            client_choice = min(val_a, val_b)

            if client_choice > best_waiter:
                best_waiter = client_choice
            if best_waiter > alpha:
                alpha = best_waiter
            if alpha >= beta:
                cache[key] = best_waiter
                return best_waiter

    cache[key] = best_waiter
    return best_waiter


def waiter_client_winner(n: int, k: int) -> GameOutcome:
    """Determine winner of Waiter-Client game on G([n]) for K_k.

    Waiter offers pairs of unclaimed edges each turn.
    Client must take exactly one from each offered pair.
    Waiter wins if Client's collection contains a mono K_k.

    Returns:
        GameOutcome.MAKER_WIN if Waiter wins (can force Client into K_k).
        GameOutcome.BREAKER_WIN if Client can avoid K_k.
    """
    state = GameState(n, k)

    if not state.cliques:
        return GameOutcome.BREAKER_WIN

    cache: Dict = {}
    unclaimed_list = sorted(state.edges)
    val = _wc_minimax(state, unclaimed_list, -2, 2, cache)
    return GameOutcome.MAKER_WIN if val > 0 else GameOutcome.BREAKER_WIN


def waiter_client_threshold(k: int, max_n: int = 12) -> int:
    """Find smallest n where Waiter wins for K_k. Returns -1 if not found."""
    for n in range(k, max_n + 1):
        if waiter_client_winner(n, k) == GameOutcome.MAKER_WIN:
            return n
    return -1


# ---------------------------------------------------------------------------
# 4. Random-turn game (Monte Carlo)
# ---------------------------------------------------------------------------

def random_turn_simulate(n: int, k: int, num_sims: int = 10000,
                         seed: Optional[int] = None) -> Dict:
    """Simulate the random-turn Ramsey game on G([n]) for K_k.

    Each turn, a fair coin flip decides who moves.
    The chosen player claims a uniformly random unclaimed edge.
    Maker (player 0) wins if they complete a mono K_k.
    Breaker (player 1) wins if the board fills without Maker completing K_k.

    Returns dict with:
        maker_wins: count of Maker victories
        breaker_wins: count of Breaker victories
        maker_win_prob: estimated probability
        avg_game_length: average number of turns
        avg_maker_edges: average edges Maker claims
    """
    rng = random.Random(seed)
    edges = coprime_edges(n)
    cliques = find_coprime_cliques(n, k)
    clique_edge_sets = [frozenset(_clique_edges(c)) for c in cliques]

    if not cliques or not edges:
        return {
            "maker_wins": 0,
            "breaker_wins": num_sims,
            "maker_win_prob": 0.0,
            "avg_game_length": 0.0,
            "avg_maker_edges": 0.0,
        }

    maker_wins = 0
    total_length = 0
    total_maker_edges = 0

    for _ in range(num_sims):
        # Shuffle edges to define the sequence of claims
        perm = list(edges)
        rng.shuffle(perm)

        maker_set: Set[Edge] = set()
        game_length = 0
        maker_won = False

        for edge in perm:
            # Coin flip: 0 = Maker, 1 = Breaker
            player = rng.randint(0, 1)
            game_length += 1

            if player == 0:
                maker_set.add(edge)
                # Check if Maker just completed a K_k
                for es in clique_edge_sets:
                    if es.issubset(maker_set):
                        maker_won = True
                        break
                if maker_won:
                    break

        if maker_won:
            maker_wins += 1
        total_length += game_length
        total_maker_edges += len(maker_set)

    return {
        "maker_wins": maker_wins,
        "breaker_wins": num_sims - maker_wins,
        "maker_win_prob": maker_wins / num_sims,
        "avg_game_length": total_length / num_sims,
        "avg_maker_edges": total_maker_edges / num_sims,
    }


def random_turn_sweep(k: int, n_range: Tuple[int, int] = (8, 15),
                      num_sims: int = 10000,
                      seed: Optional[int] = None) -> Dict[int, Dict]:
    """Run random-turn simulations across a range of n values.

    Returns {n: simulation_results_dict}.
    """
    results = {}
    for n in range(n_range[0], n_range[1] + 1):
        results[n] = random_turn_simulate(n, k, num_sims=num_sims, seed=seed)
    return results


# ---------------------------------------------------------------------------
# 5. Comparison table
# ---------------------------------------------------------------------------

def comparison_table(k: int = 3, mb_max_n: int = 10,
                     strong_max_n: int = 10,
                     wc_max_n: int = 8,
                     rt_sims: int = 10000,
                     rt_seed: Optional[int] = 42) -> Dict:
    """Compute comparison data for all game variants at given k.

    Returns a dict with thresholds and Monte Carlo results:
        maker_breaker_threshold: n where Maker wins MB game
        strong_game_threshold: n where first player wins strong game
        waiter_client_threshold: n where Waiter wins WC game
        random_turn_data: {n: simulation_dict} for n=8..15
        rcop: R_cop(k) for reference (passive coloring Ramsey number)
    """
    rcop_known = {3: 11, 4: 59}

    mb_thresh = maker_breaker_threshold(k, max_n=mb_max_n)
    strong_thresh = strong_game_threshold(k, max_n=strong_max_n)
    wc_thresh = waiter_client_threshold(k, max_n=wc_max_n)

    # Random-turn sweep
    rt_lo = max(k + 1, 8)
    rt_hi = 15
    rt_data = random_turn_sweep(k, n_range=(rt_lo, rt_hi),
                                num_sims=rt_sims, seed=rt_seed)

    # Identify random-turn "critical n" as where Maker win prob > 0.5
    rt_threshold = -1
    for n in range(rt_lo, rt_hi + 1):
        if rt_data[n]["maker_win_prob"] > 0.5:
            rt_threshold = n
            break

    return {
        "k": k,
        "maker_breaker_threshold": mb_thresh,
        "strong_game_threshold": strong_thresh,
        "waiter_client_threshold": wc_thresh,
        "random_turn_threshold": rt_threshold,
        "random_turn_data": rt_data,
        "rcop": rcop_known.get(k, -1),
    }


def format_comparison_table(data: Dict) -> str:
    """Format comparison data as a human-readable table."""
    k = data["k"]
    lines = []
    lines.append("=" * 72)
    lines.append(f"GAME-THEORETIC COPRIME RAMSEY COMPARISON (k={k})")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"  R_cop({k}) = {data['rcop']}  (passive coloring threshold)")
    lines.append("")
    lines.append("  Game Variant              | Critical n | Relation to R_cop")
    lines.append("  --------------------------+------------+-------------------")

    mb = data["maker_breaker_threshold"]
    sg = data["strong_game_threshold"]
    wc = data["waiter_client_threshold"]
    rt = data["random_turn_threshold"]
    rcop = data["rcop"]

    def rel(val):
        if val == -1 or rcop == -1:
            return "?"
        if val < rcop:
            return f"< R_cop  (ratio {val}/{rcop} = {val/rcop:.2f})"
        elif val == rcop:
            return "= R_cop"
        else:
            return f"> R_cop  (ratio {val}/{rcop} = {val/rcop:.2f})"

    mb_str = str(mb) if mb != -1 else ">max_n"
    sg_str = str(sg) if sg != -1 else ">max_n"
    wc_str = str(wc) if wc != -1 else ">max_n"
    rt_str = str(rt) if rt != -1 else ">15"

    lines.append(f"  Maker-Breaker             | {mb_str:>10s} | {rel(mb)}")
    lines.append(f"  Strong (first-player-win) | {sg_str:>10s} | {rel(sg)}")
    lines.append(f"  Waiter-Client             | {wc_str:>10s} | {rel(wc)}")
    lines.append(f"  Random-turn (p>0.5)       | {rt_str:>10s} | {rel(rt)}")
    lines.append("")

    # Random-turn details
    lines.append("  Random-Turn Simulation Details:")
    lines.append("  n  | Maker win % | Avg length | Avg Maker edges")
    lines.append("  ---+-------------+------------+----------------")
    for n in sorted(data["random_turn_data"]):
        d = data["random_turn_data"][n]
        lines.append(
            f"  {n:2d} | {d['maker_win_prob']:>10.3f}% |"
            f" {d['avg_game_length']:>10.1f} | {d['avg_maker_edges']:>10.1f}"
        )
    lines.append("")

    # Theoretical notes
    lines.append("  Theoretical ordering (expected):")
    lines.append("    Waiter-Client <= Maker-Breaker <= Strong <= R_cop")
    lines.append("")
    lines.append("  Waiter-Client: Waiter controls pair offerings, strongest")
    lines.append("    offensive position. Should win at smallest n.")
    lines.append("  Maker-Breaker: Maker only needs one mono K_k. Easier than")
    lines.append("    avoiding all mono K_k (passive Ramsey). MB threshold < R_cop.")
    lines.append("  Strong: Both players try. First player advantage (strategy-")
    lines.append("    stealing), but second player can also threaten. Threshold")
    lines.append("    between MB and passive Ramsey.")
    lines.append("  Random-turn: probabilistic; threshold near R_cop due to")
    lines.append("    random edge ownership approaching 50/50 coloring.")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("GAME-THEORETIC COPRIME RAMSEY EXPERIMENTS")
    print("=" * 72)
    print()

    k = 3
    print(f"All experiments for k = {k} (triangles)")
    print(f"Reference: R_cop({k}) = 11")
    print()

    # 1. Maker-Breaker
    print("-" * 72)
    print("1. MAKER-BREAKER GAME")
    print("   Maker claims edges trying to build mono K_3.")
    print("   Breaker claims edges to block.")
    print("-" * 72)
    for n in range(3, 11):
        result = maker_breaker_winner(n, k)
        winner = "MAKER" if result == GameOutcome.MAKER_WIN else "BREAKER"
        print(f"  n={n:2d}: {winner} wins")
        if result == GameOutcome.MAKER_WIN:
            print(f"  => Maker-Breaker threshold for K_3: n = {n}")
            break
    print()

    # 2. Strong game
    print("-" * 72)
    print("2. STRONG GAME")
    print("   Both players try to complete K_3 first.")
    print("   Draw if board fills with no winner.")
    print("-" * 72)
    for n in range(3, 11):
        result = strong_game_outcome(n, k)
        if result == GameOutcome.MAKER_WIN:
            label = "FIRST PLAYER WINS"
        elif result == GameOutcome.BREAKER_WIN:
            label = "SECOND PLAYER WINS"
        else:
            label = "DRAW"
        print(f"  n={n:2d}: {label}")
        if result == GameOutcome.MAKER_WIN:
            print(f"  => Strong game threshold for K_3: n = {n}")
            break
    print()

    # 3. Waiter-Client
    print("-" * 72)
    print("3. WAITER-CLIENT GAME")
    print("   Waiter offers edge pairs, Client must take one.")
    print("   Waiter wins if Client forced into mono K_3.")
    print("-" * 72)
    for n in range(3, 9):
        result = waiter_client_winner(n, k)
        winner = "WAITER" if result == GameOutcome.MAKER_WIN else "CLIENT"
        print(f"  n={n:2d}: {winner} wins")
        if result == GameOutcome.MAKER_WIN:
            print(f"  => Waiter-Client threshold for K_3: n = {n}")
            break
    print()

    # 4. Random-turn
    print("-" * 72)
    print("4. RANDOM-TURN GAME (Monte Carlo, 10000 simulations)")
    print("   Each turn, coin flip decides who moves.")
    print("-" * 72)
    rt = random_turn_sweep(k, n_range=(8, 15), num_sims=10000, seed=42)
    print("  n  | Maker win % | Avg length | Avg Maker edges")
    print("  ---+-------------+------------+----------------")
    for n in sorted(rt):
        d = rt[n]
        print(
            f"  {n:2d} | {100*d['maker_win_prob']:>10.2f}% |"
            f" {d['avg_game_length']:>10.1f} | {d['avg_maker_edges']:>10.1f}"
        )
    print()

    # 5. Comparison
    print("-" * 72)
    print("5. COMPARISON TABLE")
    print("-" * 72)
    data = comparison_table(k=3, mb_max_n=10, strong_max_n=10,
                            wc_max_n=8, rt_sims=10000, rt_seed=42)
    print(format_comparison_table(data))


if __name__ == "__main__":
    main()
