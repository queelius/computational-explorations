# BL85 blind verifier -- Claim B (no blue l_NJ) for cfg_a42.json, with an arb-rigorous acceptance test.
#
# Method (same reduction as BL107 claimB.py, see REPORT.txt):
#  * Red contains the closed disks D(c + g, h), c a listed centre, g in Gamma (any orientation of the 24-gons).
#  * theta in [0, 3.1416] covers [0, pi]; u and -u give the same point sets.
#  * A blue l_NJ with step u exists iff the NJ translates Red - j u (j = 0..NJ-1) fail to cover R^2/Gamma.
#    The dyadic grid [0, nx/4] x [0, ny/4] (w0 = 1/4) contains [0,L] x [0,H], which contains a fundamental domain.
#  * For theta in [tl, th] and any float tm, with delta >= max(th - tm, tm - tl):  |u(theta) - u(tm)| <= delta, so
#    D(c + g - j u(tm), h - j delta) is inside D(c + g - j u(theta), h) for every theta in the box.
#  * A dyadic square with centre q and half-diagonal rq is inside D(z, r) if rq <= r and |q - z|^2 <= (r - rq)^2.
#
# Stage 1 (numba, floats, NOT trusted): builds a quadtree for each theta box and records, for every leaf, one disk
#   (i, j, a, b) meaning centre_i + a P1 + b P2 - j u(tm), radius h - j delta.  The tree is written as a preorder
#   list of codes (-1 = split, k >= 0 = leaf certified by disk k).
# Stage 2 (python-flint arb, TRUSTED): re-walks the tree from the root grid (so coverage of the grid is by
#   construction of the walker, independent of stage 1), recomputes every leaf square exactly from integers, and
#   checks the inclusion with arb balls: s = h - j*delta - rq > 0 and s*s - |q - z|^2 > 0 must both be certain.
#   cos(tm), sin(tm) are arb enclosures; all centres, P1, P2, h are exact rationals.  No float enters stage 2 except
#   tl, th, tm, which are exact binary numbers and are converted to arb exactly.
#   v4 (2026-09-30, referee report): stage 2 also asserts that tl, tm, th and delta = max(th - tm, tm - tl) are exact
#   (zero radius), so h - j*delta is an Arb enclosure of the exact radius; and a final TRUSTED direction check
#   (check_direction_cover, exact rationals) verifies that the boxes that passed stage 2 tile [0, 3.1416] exactly
#   (consecutive boxes share endpoints, first starts at 0, last ends at 3.1416 > pi, certified in Arb), which also
#   checks that every bisection replaced its parent by two children covering it.  The v3 code is in original_v3/.
#   V2MIX (2026-10-01): cell i may have its own apothem h_i (cfg "h" = string or per-centre list); everywhere "h"
#   above read h_i for the disk's own cell i.  Config path from env var V2CFG.  See DIFF_NOTES.txt.
import json, math, sys, time, os
import numpy as np
from fractions import Fraction as F
import numba as nb

CFG = os.environ['V2CFG']   # V2MIX: config path from env var (inherited by the spawned pool workers)
d = json.load(open(CFG))
P1q = [F(x) for x in d['P1']]; P2q = [F(x) for x in d['P2']]
Cq = [(F(a), F(b)) for a, b in d['centres']]
assert int(d['k']) == 24 and P1q[1] == 0
# V2MIX: "h" is one string (all cells) or a list with one string per centre; each is parsed exactly (Fraction).
hqs = [F(str(d['h']))] * len(Cq) if isinstance(d['h'], str) else [F(str(x)) for x in d['h']]
assert len(hqs) == len(Cq) and all(x > 0 for x in hqs)
P1 = np.array([float(x) for x in P1q]); P2 = np.array([float(x) for x in P2q])
CEN = np.array([[float(a), float(b)] for a, b in Cq])
HR = np.array([float(x) for x in hqs]); HMAX = float(max(hqs)); L = P1[0]; HH = P2[1]
W0 = 0.25
NX = math.ceil(P1q[0] / F(1, 4)); NY = math.ceil(P2q[1] / F(1, 4))
assert F(NX, 4) >= P1q[0] and F(NY, 4) >= P2q[1]
EPS_R = 1e-9      # float safety margin in stage 1 only
BS = 0.5; PAD = 0.6


@nb.njit(cache=True)
def stage1(tl, th, tm, hr, h, cen, L, HH, P2x, nj, maxdepth, NX, NY, W0):
    # V2MIX: hr[i] = radius of cell i; h = max(hr) is used only for the bin search window below.
    ux = math.cos(tm); uy = math.sin(tm)
    delta = max(th - tm, tm - tl)
    nc = cen.shape[0]
    cap = nc * nj * 16
    zx = np.empty(cap); zy = np.empty(cap); zr = np.empty(cap)
    zi = np.empty(cap, np.int64); zj = np.empty(cap, np.int64); za = np.empty(cap, np.int64); zb = np.empty(cap, np.int64)
    n = 0
    for j in range(nj):
        for i in range(nc):
            r = hr[i] - j * delta - EPS_R
            if r <= 0:
                continue
            x = cen[i, 0] - j * ux; y = cen[i, 1] - j * uy
            B = -math.floor(y / HH)
            x1 = x + B * P2x
            A = -math.floor(x1 / L)
            for bb in range(-1, 2):
                for aa in range(-2, 3):
                    X = x + (A + aa) * L + (B + bb) * P2x; Y = y + (B + bb) * HH
                    if X > -PAD and X < NX * W0 + PAD and Y > -PAD and Y < NY * W0 + PAD:
                        zx[n] = X; zy[n] = Y; zr[n] = r; zi[n] = i; zj[n] = j; za[n] = A + aa; zb[n] = B + bb; n += 1
    nbx = int((NX * W0 + 2 * PAD) / BS) + 2; nby = int((NY * W0 + 2 * PAD) / BS) + 2
    cnt = np.zeros(nbx * nby + 1, np.int64)
    for k in range(n):
        bx = int((zx[k] + PAD) / BS); by = int((zy[k] + PAD) / BS)
        cnt[bx * nby + by + 1] += 1
    for k in range(nbx * nby):
        cnt[k + 1] += cnt[k]
    fill = cnt.copy(); idx = np.empty(n, np.int64)
    for k in range(n):
        bx = int((zx[k] + PAD) / BS); by = int((zy[k] + PAD) / BS)
        t = bx * nby + by; idx[fill[t]] = k; fill[t] += 1
    codes = np.empty(4000000, np.int64); nco = 0
    sx = np.empty(4 * maxdepth + 16); sy = np.empty_like(sx); sd = np.empty(sx.shape[0], np.int64)
    leaves = 0; jworst = -1
    for ix in range(NX):
        for iy in range(NY):
            sx[0] = ix * W0; sy[0] = iy * W0; sd[0] = 0; top = 1
            while top > 0:
                top -= 1
                x0 = sx[top]; y0 = sy[top]; dep = sd[top]
                w = W0 / (1 << dep)
                qx = x0 + 0.5 * w; qy = y0 + 0.5 * w
                rq = 0.7071067811865476 * w + 1e-12
                best = -1; bj = 1 << 30
                bx0 = int((qx + PAD - h) / BS); bx1 = int((qx + PAD + h) / BS)
                by0 = int((qy + PAD - h) / BS); by1 = int((qy + PAD + h) / BS)
                for bx in range(bx0, bx1 + 1):
                    for by in range(by0, by1 + 1):
                        t = bx * nby + by
                        for m in range(cnt[t], cnt[t + 1]):
                            k = idx[m]
                            if zj[k] >= bj:
                                continue
                            s = zr[k] - rq
                            if s <= 0:
                                continue
                            dx = qx - zx[k]; dy = qy - zy[k]
                            if dx * dx + dy * dy <= s * s:
                                bj = zj[k]; best = k
                if best >= 0:
                    codes[nco] = best; nco += 1
                    leaves += 1
                    if bj > jworst:
                        jworst = bj
                elif dep >= maxdepth:
                    return -1, jworst, leaves, qx, qy, codes[:0], zi[:0], zj[:0], za[:0], zb[:0]
                else:
                    codes[nco] = -1; nco += 1
                    for a2 in range(2):
                        for b2 in range(2):
                            sx[top] = x0 + a2 * 0.5 * w; sy[top] = y0 + b2 * 0.5 * w; sd[top] = dep + 1; top += 1
    return 1, jworst, leaves, 0.0, 0.0, codes[:nco].copy(), zi[:n].copy(), zj[:n].copy(), za[:n].copy(), zb[:n].copy()


# ---------------- stage 2: arb ----------------
_ARB = {}


def arb_setup():
    from flint import arb, ctx
    ctx.prec = 96
    A = lambda q: arb(q.numerator) / arb(q.denominator)
    _ARB['arb'] = arb
    _ARB['h'] = [A(x) for x in hqs]      # V2MIX: exact per-cell radii
    _ARB['C'] = [(A(a), A(b)) for a, b in Cq]
    _ARB['P1'] = (A(P1q[0]), A(P1q[1])); _ARB['P2'] = (A(P2q[0]), A(P2q[1]))
    _ARB['sq2h'] = arb(2).sqrt() / 2
    _ARB['cache'] = {}


def arb_float(x):
    arb = _ARB['arb']
    fr = F(x)  # exact value of the binary float
    return arb(fr.numerator) / arb(fr.denominator)


def stage2(tl, th, tm, codes, zi, zj, za, zb, maxdepth, nj):
    """Return (ok, nleaves, min certified margin lower bound).  Trusted."""
    arb = _ARB['arb']
    TL, TH, TM = arb_float(tl), arb_float(th), arb_float(tm)
    e1 = TH - TM; e2 = TM - TL          # exact (differences of doubles at 96 bits)
    delta = e1 if (e1 >= e2) else e2
    assert (delta >= e1) and (delta >= e2) and (TL <= TM) and (TM <= TH)
    assert TL.is_exact() and TM.is_exact() and TH.is_exact() and delta.is_exact()   # v4: delta is exact
    ux = TM.cos(); uy = TM.sin()
    h = _ARB['h']; C = _ARB['C']; P1a = _ARB['P1']; P2a = _ARB['P2']; cache = _ARB['cache']
    D = maxdepth
    unit = arb(1) / arb(2) ** (D + 2)            # grid unit: W0 / 2^D = 2^-(D+2)
    rq = [_ARB['sq2h'] * (arb(1) / arb(2) ** (dep + 2)) for dep in range(D + 1)]   # half-diagonal of a side-2^-(dep+2) square
    disk = {}
    pos = 0; nleaf = 0; minm = None
    for ix in range(NX):
        for iy in range(NY):
            stack = [(ix << D, iy << D, 0)]
            while stack:
                X0, Y0, dep = stack.pop()
                code = int(codes[pos]); pos += 1
                side = 1 << (D - dep)
                if code == -1:
                    if dep >= D:
                        return False, nleaf, None
                    hs = side >> 1
                    for a2 in range(2):
                        for b2 in range(2):
                            stack.append((X0 + a2 * hs, Y0 + b2 * hs, dep + 1))
                    continue
                if code not in disk:
                    i, j, a, b = int(zi[code]), int(zj[code]), int(za[code]), int(zb[code])
                    assert 0 <= j < nj and 0 <= i < len(C)   # only the NJ translates j = 0..NJ-1 may be used
                    key = (i, a, b)
                    if key not in cache:
                        cache[key] = (C[i][0] + a * P1a[0] + b * P2a[0], C[i][1] + b * P2a[1])
                    cx, cy = cache[key]
                    disk[code] = (cx - j * ux, cy - j * uy, h[i] - j * delta)   # V2MIX: radius of cell i
                zx, zy, r = disk[code]
                s = r - rq[dep]
                qx = arb(2 * X0 + side) * unit / 2; qy = arb(2 * Y0 + side) * unit / 2
                dx = qx - zx; dy = qy - zy
                m = s * s - (dx * dx + dy * dy)
                if not (s.is_finite() and m.is_finite() and s > 0 and m > 0):
                    return False, nleaf, None
                ml = float(m.lower())
                if minm is None or ml < minm:
                    minm = ml
                nleaf += 1
    assert pos == len(codes)
    return True, nleaf, minm


def check_direction_cover(passed, lo, hi, full):
    """TRUSTED (exact rationals + Arb): the closed boxes [tl, th] in `passed` tile [lo, hi] exactly, and for a full
    run lo = 0 and hi > pi.  Every box in `passed` was certified by stage 2 for all theta in [tl, th]."""
    from flint import arb
    iv = sorted((F(tl), F(th)) for tl, th in passed)       # F(float) is the exact value of the binary float
    if not iv or iv[0][0] != F(lo) or iv[-1][1] != F(hi):
        return False
    for k in range(len(iv)):
        if not iv[k][0] < iv[k][1]:
            return False
        if k and iv[k][0] != iv[k - 1][1]:
            return False
    if full:
        q = F(hi)
        if not (F(lo) == 0 and arb.pi() < arb(q.numerator) / arb(q.denominator)):
            return False
    return True


def work(args):
    """Process a list of boxes; returns per box (tl, th, status, jworst, leaves, arb_ok, arb_leaves, minmargin, fx, fy)."""
    boxes, nj, maxdepth, do_arb = args
    if do_arb and not _ARB:
        arb_setup()
    out = []
    for tl, th in boxes:
        tm = 0.5 * (tl + th)
        st, jw, lv, fx, fy, codes, zi, zj, za, zb = stage1(tl, th, tm, HR, HMAX, CEN, L, HH, P2[0], nj, maxdepth, NX, NY, W0)
        if st == 1 and do_arb:
            ok, nl, mm = stage2(tl, th, tm, codes, zi, zj, za, zb, maxdepth, nj)
        else:
            ok, nl, mm = None, 0, None
        out.append((tl, th, st, jw, lv, ok, nl, mm, fx, fy))
    return out


if __name__ == '__main__':
    import multiprocessing as mp
    N = int(sys.argv[1]); NJ = int(sys.argv[2]); MAXD = int(sys.argv[3]); MAXSPLIT = int(sys.argv[4])
    DO_ARB = int(sys.argv[5]); LO = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
    HI = float(sys.argv[7]) if len(sys.argv) > 7 else 3.1416
    if len(sys.argv) <= 6:
        assert LO == 0.0 and HI - 3.14159266 > 0   # [0, 3.1416] contains [0, pi]
    edges = np.linspace(LO, HI, N + 1); edges[0] = LO; edges[-1] = HI
    assert all(edges[k] < edges[k + 1] for k in range(N))
    boxes = list(zip(edges[:-1].tolist(), edges[1:].tolist()))
    passed = []     # v4: boxes certified (stage 1 and, if arb, stage 2); checked exactly by check_direction_cover
    print('BL85 claimB_arb: N=%d NJ=%d maxdepth=%d maxsplit=%d arb=%d theta [%r, %r] grid %dx%d of 1/4' % (
        N, NJ, MAXD, MAXSPLIT, DO_ARB, LO, HI, NX, NY), flush=True)
    import hashlib   # V2MIX: record the input and its radii
    print('V2MIX cfg %s sha256 %s; %d centres; radii %s' % (CFG, hashlib.sha256(open(CFG, 'rb').read()).hexdigest(),
          len(Cq), sorted(set(str(x) for x in hqs))), flush=True)
    t0 = time.time(); level = 0
    tot = dict(leaves=0, arb_leaves=0, arb_boxes=0, arb_fail=0); worst = (-1, None); minm = None
    unresolved = []
    with mp.Pool(8) as pool:
        while boxes:
            NCH = 400
            chunks = [boxes[k::NCH] for k in range(NCH)]
            res = []
            for ci, part in enumerate(pool.imap_unordered(work, [(c, NJ, MAXD, DO_ARB) for c in chunks if c])):
                res += part
                if ci % 50 == 49:
                    print('   ... %d/%d chunks, t=%.0fs' % (ci + 1, NCH, time.time() - t0), flush=True)
            bad = []
            for (tl, th, st, jw, lv, ok, nl, mm, fx, fy) in res:
                if st != 1:
                    bad.append((tl, th, fx, fy)); continue
                tot['leaves'] += lv
                if jw > worst[0]:
                    worst = (jw, (tl, th))
                if DO_ARB:
                    tot['arb_boxes'] += 1; tot['arb_leaves'] += nl
                    if not ok:
                        tot['arb_fail'] += 1; bad.append((tl, th, fx, fy)); print('   ARB FAIL box', tl, th, flush=True)
                        continue
                    elif minm is None or mm < minm:
                        minm = mm
                passed.append((tl, th))
            print('level %d: %d boxes, %d stage-1/arb failures, t=%.0fs' % (level, len(res), len(bad), time.time() - t0), flush=True)
            for (tl, th, fx, fy) in bad[:12]:
                print('   fail box [%.12f, %.12f] rad = [%.7f, %.7f] deg, width %.2e, uncovered near (%.5f, %.5f)' % (
                    tl, th, math.degrees(tl), math.degrees(th), th - tl, fx, fy), flush=True)
            if not bad:
                break
            if level >= MAXSPLIT:
                unresolved = bad; break
            boxes = []
            for (tl, th, fx, fy) in bad:
                mid = 0.5 * (tl + th)
                assert tl < mid < th        # the two children [tl, mid], [mid, th] cover the parent exactly
                boxes += [(tl, mid), (mid, th)]
            level += 1
    cover_ok = (not unresolved) and check_direction_cover(passed, LO, HI, len(sys.argv) <= 6)
    if not unresolved:
        print('direction cover (exact): %d certified boxes tile [%r, %r]%s: %s' % (
            len(passed), LO, HI, ' and 3.1416 > pi' if len(sys.argv) <= 6 else '', cover_ok), flush=True)
        if not cover_ok:
            unresolved = ['direction cover']
    print('RESULT: %s. stage-1 leaves %d; arb boxes %d, arb leaves %d, arb failures %d; min arb margin lower bound '
          '(s^2 - |q-z|^2) %s; worst j used %d in box %s; time %.0fs' % (
              'PASS' if not unresolved else 'FAIL/UNRESOLVED %d boxes' % len(unresolved), tot['leaves'], tot['arb_boxes'],
              tot['arb_leaves'], tot['arb_fail'], minm, worst[0], worst[1], time.time() - t0), flush=True)
    if worst[1]:
        print('worst box deg %.8f .. %.8f' % (math.degrees(worst[1][0]), math.degrees(worst[1][1])))
    sys.exit(0 if not unresolved else 1)   # release copy: nonzero exit status on failure
