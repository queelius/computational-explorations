# Research organization verification — October 20, 2026

The [verification receipt](verification.json) records metadata tests, coverage,
an independently reviewed schema correction, packet identity, reproduction
from an extracted packet in a fresh environment, and preservation checks.
The [public-event receipt](public-events.json) retains selected public GitHub
timestamps observed through the connector, separately from local file dates.
The [integration receipt](integration.json) records the completed merges and
the final 6,224-test CI result.

The source packet rebuilt byte for byte:

```
coprime-paths-2026.10.20.zip
SHA-256: 04b35951d853da7d2c865038b277038b4570c5ea895971ac8b6db78ff79fa574
Bytes:   16080657
```

Rebuild it with:

```sh
python src/research_records.py package coprime-paths --output /tmp/coprime-paths.zip
```

The packet contains 80 pinned source files plus generated metadata, citation,
README, and inventory. All 83 payload hashes were checked independently of
the builder. Its extracted source passed 114 focused tests; the isolated
optimized witness and three structural checkers returned the expected
complete case counts. Its manuscript rebuilt to 16 pages. PDF byte identity
is not asserted: TeX embeds build metadata.

The new record tooling passed 28 unit and integration tests, including
tampering, missing Git pins, duplicate keys, path escapes, citation provenance,
deterministic packaging, and central-index export. Measured statement coverage
was 92% under existing exclusions; CLI behavior has subprocess tests.
The auxiliary historical validators passed their 3 + 7 regression tests.

These checks concern organization and finite computation. They do not replace
the written proof, human review, or novelty assessment. All five implementation
CI jobs passed, including 6,224 routine tests. The GitHub-built packet matched
the local packet byte for byte. The final receipt-only commit does not change
source, tests, metadata, or packet contents.
