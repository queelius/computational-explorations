"""Independent integer acceptor for Crocker's disk-cover witnesses.

Alexander Richard Towell, with substantial OpenAI Codex assistance.
The witness search is not part of the trusted acceptance logic.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from math import factorial
from typing import Sequence

BITS = 40
SCALE = 1 << BITS
DEGREE = 32


class InvalidCertificate(ValueError):
    """The supplied data do not establish the requested cover."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidCertificate(message)


def bounds(q: Q) -> tuple[int, int]:
    """Outward rounding of SCALE*q, using integers only."""
    a = q.numerator * SCALE
    b = q.denominator
    return a // b, -((-a) // b)


def trig_bounds(x: Q) -> tuple[tuple[int, int], tuple[int, int]]:
    """Enclose SCALE*(cos(x), sin(x)) by Taylor with Lagrange remainder.

    Degree32 has remainder at most |x|^33/33! for either function.
    Polynomial evaluation and the remainder are exact rational arithmetic.
    """
    require(isinstance(x, Q) and 0 <= x <= 4, "angle outside Taylor domain")
    a, b = x.numerator, x.denominator
    f = factorial(DEGREE)
    denominator = f * b ** DEGREE
    rem = Q(a ** (DEGREE + 1), b ** (DEGREE + 1) * factorial(DEGREE + 1))
    result = []
    for parity in (0, 1):
        numerator = sum(
            (-1) ** ((n-parity)//2) * (f//factorial(n)) * a**n * b**(DEGREE-n)
            for n in range(parity, DEGREE+1, 2)
        )
        p = Q(numerator, denominator)
        result.append((bounds(p-rem)[0], bounds(p+rem)[1]))
    return result[0], result[1]


def pi_bounds() -> tuple[Q, Q]:
    """Machin's identity and alternating arctangent series, ten terms."""
    def atan(q: Q) -> tuple[Q, Q]:
        p = sum(((-1)**n * q**(2*n+1) / (2*n+1) for n in range(10)), Q(0))
        return p, p + q**21/21
    a, b = atan(Q(1, 5)), atan(Q(1, 239))
    return 16*a[0]-4*b[1], 16*a[1]-4*b[0]


@dataclass(frozen=True)
class Config:
    p1: tuple[Q, Q]
    p2: tuple[Q, Q]
    centres: tuple[tuple[Q, Q], ...]
    radii: tuple[Q, ...]

    def __post_init__(self) -> None:
        require(len(self.p1) == len(self.p2) == 2, "lattice dimensions")
        require(all(isinstance(x, Q) for x in (*self.p1, *self.p2)), "rational lattice required")
        require(self.p1[1] == 0 and self.p1[0] > 0 and self.p2[1] > 0, "positive triangular lattice required")
        require(bool(self.centres) and len(self.centres) == len(self.radii), "cell/radius dimensions")
        require(all(len(c) == 2 and all(isinstance(x, Q) for x in c) for c in self.centres), "rational centres required")
        require(all(isinstance(h, Q) and h > 0 for h in self.radii), "positive rational radii required")

    @classmethod
    def from_json(cls, data: dict) -> "Config":
        require(type(data['k']) is int and data['k'] == 24, "expected24-gons")
        centres = tuple(tuple(Q(x) for x in c) for c in data['centres'])
        h = data['h']
        radii = tuple(Q(h) for _ in centres) if isinstance(h, str) else tuple(Q(x) for x in h)
        return cls(tuple(Q(x) for x in data['P1']), tuple(Q(x) for x in data['P2']), centres, radii)

    @property
    def grid(self) -> tuple[int, int]:
        return tuple(-((-4*x.numerator)//x.denominator) for x in (self.p1[0], self.p2[1]))


def linear_bounds(c: tuple[int, int], a: int, p: tuple[int, int], b: int, q: tuple[int, int]) -> tuple[int, int]:
    ap = (a*p[0], a*p[1]) if a >= 0 else (a*p[1], a*p[0])
    bq = (b*q[0], b*q[1]) if b >= 0 else (b*q[1], b*q[0])
    return c[0]+ap[0]+bq[0], c[1]+ap[1]+bq[1]


class Verifier:
    """Caches only outward-rounded rational lattice translations."""
    def __init__(self, config: Config):
        self.config = config
        self.p1 = tuple(bounds(x) for x in config.p1)
        self.p2 = tuple(bounds(x) for x in config.p2)
        self.centres = tuple(tuple(bounds(x) for x in c) for c in config.centres)
        self.radii = tuple(bounds(h)[0] for h in config.radii)
        self.translations: dict = {}

    def verify(self, box: tuple[Q, Q, Q], codes: Sequence[int], witness: tuple[Sequence[int], ...], nj: int, depth: int) -> dict:
        lo, hi, mid = box
        require(all(isinstance(x, Q) for x in box) and 0 <= lo <= mid <= hi <= 4 and lo < hi, "invalid angle box")
        require(type(nj) is int and nj > 0 and type(depth) is int and 0 <= depth <= BITS-2, "invalid visit parameters")
        require(len(witness) == 4 and len({len(v) for v in witness}) == 1, "witness dimensions")
        cosine, sine = trig_bounds(mid)
        delta = bounds(max(hi-mid, mid-lo))[1]
        disk = {}
        pos = leaves = 0
        minimum = None
        worst_j = -1
        nx, ny = self.config.grid
        root_side = SCALE//4
        for ix in range(nx):
            for iy in range(ny):
                stack = [(ix*root_side, iy*root_side, root_side, 0)]
                while stack:
                    x, y, side, dep = stack.pop()
                    require(pos < len(codes), "missing tree node")
                    code = codes[pos]
                    pos += 1
                    require(type(code) is int, "noninteger tree node")
                    if code == -1:
                        require(dep < depth, "split beyond depth limit")
                        half = side//2
                        for a in range(2):
                            for b in range(2):
                                stack.append((x+a*half, y+b*half, half, dep+1))
                        continue
                    require(0 <= code < len(witness[0]), "invalid disk index")
                    if code not in disk:
                        i, j, a, b = (v[code] for v in witness)
                        require(all(type(v) is int for v in (i,j,a,b)), "noninteger disk witness")
                        require(0 <= i < len(self.centres) and 0 <= j < nj, "invalid cell/progression index")
                        key = i, a, b
                        if key not in self.translations:
                            self.translations[key] = tuple(linear_bounds(self.centres[i][k], a, self.p1[k], b, self.p2[k]) for k in range(2))
                        cx, cy = self.translations[key]
                        radius = self.radii[i] - j*delta
                        require(radius > 0, "nonpositive shrunken radius")
                        disk[code] = (cx[0]-j*cosine[1], cx[1]-j*cosine[0], cy[0]-j*sine[1], cy[1]-j*sine[0], radius*radius)
                        worst_j = max(worst_j, j)
                    xl, xh, yl, yh, r2 = disk[code]
                    dx = max(abs(x-xh), abs(x+side-xl))
                    dy = max(abs(y-yh), abs(y+side-yl))
                    margin = r2 - dx*dx - dy*dy
                    require(margin > 0, "square not strictly inside witness disk")
                    minimum = margin if minimum is None else min(minimum, margin)
                    leaves += 1
        require(pos == len(codes), "unused trailing tree nodes")
        return {'leaves': leaves, 'nodes': pos, 'minimum_integer_margin': minimum, 'worst_j': worst_j}


def verify_tree(config: Config, box: tuple[Q, Q, Q], codes: Sequence[int], witness: tuple[Sequence[int], ...], nj: int, depth: int) -> dict:
    return Verifier(config).verify(box, codes, witness, nj, depth)


def verify_directions(intervals: Sequence[tuple[Q, Q]]) -> int:
    require(bool(intervals), "empty direction certificate")
    ordered = sorted(intervals)
    end = Q(0)
    for lo, hi in ordered:
        require(isinstance(lo, Q) and isinstance(hi, Q) and lo == end and lo < hi <= 4, "gap/overlap/invalid direction interval")
        end = hi
    require(end > pi_bounds()[1], "directions do not reach pi")
    return len(ordered)
