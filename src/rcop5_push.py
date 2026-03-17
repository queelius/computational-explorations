#!/usr/bin/env python3
"""
R_cop(5) lower bound push via incremental SAT solving.

Computes R_cop(5) = min n such that every 2-coloring of coprime edges
in [n] has a monochromatic K_5.

Uses CaDiCaL (via pysat) with:
  - Fully incremental clause addition (one vertex at a time)
  - Phase warm-start from previous satisfying assignment
  - Symmetry breaking: fix edge(1,2) and edge(1,3) to color 0
  - Full 5-clique enumeration via adjacency-set intersection

Results (2026-03-16):
  R_cop(5) > 138  (SAT confirmed for all n in [5..138])
  Solve times for hard primes:
    n=113:  62s    n=127: 179s    n=131: ~142s    n=137: 179s
  n=139 unsolved after 60+ min with both CaDiCaL and Glucose4.

The bound R_cop(5) > 138 improves the previous best of R_cop(5) > 103.
This is far beyond the density-adjusted prediction of ~74 and
definitively rules out the quadratic model (which predicted ~31).

Note: CaDiCaL's C++ solver cannot be reliably interrupted from Python
(SIGALRM, threading.Timer, and solver.interrupt() all fail), so there
is no per-n timeout. The solver simply runs until completion.
"""

import math
import sys
import time
from typing import Dict, List, Optional, Set, Tuple

from pysat.solvers import Cadical195


class RCop5Solver:
    K = 5

    def __init__(self):
        self.solver = Cadical195()
        self.edge_to_var: Dict[Tuple[int, int], int] = {}
        self.next_var = 1
        self.adj: Dict[int, Set[int]] = {1: set()}
        self.current_n = 1
        self.num_clauses = 0
        self.num_cliques = 0
        self.last_model: Optional[List[int]] = None

    def _get_var(self, i: int, j: int) -> int:
        key = (min(i, j), max(i, j))
        v = self.edge_to_var.get(key)
        if v is None:
            v = self.next_var
            self.edge_to_var[key] = v
            self.next_var += 1
        return v

    def _add_clique(self, a, b, c, d, e):
        vlist = sorted([a, b, c, d, e])
        vars_ = []
        for i in range(5):
            for j in range(i + 1, 5):
                vars_.append(self._get_var(vlist[i], vlist[j]))
        self.solver.add_clause([-v for v in vars_])
        self.solver.add_clause([v for v in vars_])
        self.num_clauses += 2
        self.num_cliques += 1

    def _enumerate_cliques_with(self, n: int):
        nbrs = sorted(self.adj[n] & set(range(1, n)))
        if len(nbrs) < 4:
            return

        adj = self.adj
        for i_a, a in enumerate(nbrs):
            cand_b = [x for x in nbrs[i_a + 1:] if x in adj[a]]
            for i_b, b in enumerate(cand_b):
                cand_c = [x for x in cand_b[i_b + 1:] if x in adj[b]]
                for i_c, c in enumerate(cand_c):
                    if c not in adj[a]:
                        continue
                    cand_d = [x for x in cand_c[i_c + 1:]
                              if x in adj[c] and x in adj[a] and x in adj[b]]
                    for d in cand_d:
                        self._add_clique(a, b, c, d, n)

    def extend_and_solve(self, n: int) -> Tuple[bool, float, float]:
        """Returns (sat, enum_time, solve_time)."""
        t_enum = time.time()
        self.adj[n] = set()
        for u in range(1, n):
            if math.gcd(u, n) == 1:
                self.adj[n].add(u)
                self.adj[u].add(n)
                self._get_var(u, n)

        if n == 2:
            self.solver.add_clause([self.edge_to_var[(1, 2)]])
            self.num_clauses += 1
        elif n == 3:
            self.solver.add_clause([self.edge_to_var[(1, 3)]])
            self.num_clauses += 1

        self._enumerate_cliques_with(n)
        self.current_n = n
        dt_enum = time.time() - t_enum

        if self.last_model is not None:
            self.solver.set_phases(self.last_model)

        t_solve = time.time()
        sat = self.solver.solve()
        dt_solve = time.time() - t_solve

        if sat:
            self.last_model = self.solver.get_model()

        return sat, dt_enum, dt_solve

    def close(self):
        self.solver.delete()


def main():
    max_n = 300

    print("=" * 85, flush=True)
    print("R_cop(5) LOWER BOUND PUSH  --  Incremental CaDiCaL (unlimited time)",
          flush=True)
    print("=" * 85, flush=True)
    print(f"Target: push past n=157 (rules out quadratic model)", flush=True)
    print(f"{'n':>5s}  {'vars':>7s}  {'clauses':>10s}  {'5-clqs':>9s}  "
          f"{'result':>8s}  {'enum':>8s}  {'solve':>9s}  {'cumul':>9s}",
          flush=True)
    print("-" * 80, flush=True)

    solver = RCop5Solver()
    t_total = time.time()
    last_sat_n = 4

    for n in range(2, max_n + 1):
        sat, dt_enum, dt_solve = solver.extend_and_solve(n)
        t_cumul = time.time() - t_total
        nv = solver.next_var - 1
        nc = solver.num_clauses
        nq = solver.num_cliques

        status = "SAT" if sat else "UNSAT"
        if sat:
            last_sat_n = n

        # Print: every n from 100 onward, every 10th before that, or hard instances
        if n >= 100 or n % 10 == 0 or not sat or dt_solve > 10:
            print(f"{n:5d}  {nv:7d}  {nc:10d}  {nq:9d}  "
                  f"{status:>8s}  {dt_enum:7.2f}s  {dt_solve:8.2f}s  {t_cumul:8.1f}s",
                  flush=True)

        if not sat:
            print(f"\n*** R_cop(5) = {n} ***", flush=True)
            print(f"Total time: {t_cumul:.1f}s", flush=True)
            solver.close()
            return

    print(f"\n*** R_cop(5) > {last_sat_n}  (reached max_n={max_n}) ***",
          flush=True)
    print(f"Total time: {time.time() - t_total:.1f}s", flush=True)
    solver.close()


if __name__ == "__main__":
    main()
