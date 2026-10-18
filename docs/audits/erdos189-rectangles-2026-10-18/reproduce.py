#!/usr/bin/env python3
"""Fetch pinned data, run controls, then independently check the full certificate.

Copyright (c) 2026 Alexander Richard Towell. MIT license.
Substantial OpenAI Codex assistance. No source-deposit program is executed.
"""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.request import urlopen
from zipfile import ZipFile

from audit import AuditError, file_digest

ARCHIVE_SHA256 = '7b5dbdf14a96a29f6c4cb7b3176002d185776a85fd51747da6f693259b582e18'
ARCHIVE_URL = ('https://zenodo.org/api/records/23178517/files/'
               'FINAL_189_release_189_lb.zip/content')
MEMBERS = ('cert180.pts', 'cert180.cnf', 'cert180.lrat')


def extract_pinned(archive: Path, destination: Path) -> None:
    actual = file_digest(archive)
    if actual != ARCHIVE_SHA256:
        raise AuditError(
            f'source archive SHA-256 mismatch: expected {ARCHIVE_SHA256}, '
            f'got {actual} ({archive.stat().st_size} bytes); no source data accepted')
    with ZipFile(archive) as source:
        for name in MEMBERS:
            with source.open('release_189_lb/cert/' + name) as reader:
                with (destination/name).open('wb') as writer:
                    shutil.copyfileobj(reader, writer)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, help='use a downloaded zip instead of fetching')
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    subprocess.run([sys.executable, '-m', 'unittest', '-v', 'test_audit'],
                   cwd=here, check=True)
    with tempfile.TemporaryDirectory(prefix='rectangle189-') as temp:
        directory = Path(temp)
        archive = args.archive
        if archive is None:
            archive = directory/'source.zip'
            print('Downloading pinned source archive (48.7 MB)', file=sys.stderr, flush=True)
            with urlopen(ARCHIVE_URL, timeout=60) as reader, archive.open('wb') as writer:
                shutil.copyfileobj(reader, writer)
        extract_pinned(archive, directory)
        subprocess.run([sys.executable, str(here/'controls.py'), str(directory)], check=True)
        subprocess.run([sys.executable, str(here/'reviewer_checks.py'), str(directory)],
                       stdout=sys.stderr, check=True)
        subprocess.run([sys.executable, str(here/'audit.py'), str(directory)], check=True)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (AuditError, OSError, subprocess.CalledProcessError) as error:
        print(f'REPRODUCTION FAIL: {error}', file=sys.stderr)
        raise SystemExit(1)
