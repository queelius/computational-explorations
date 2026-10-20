"""Validate contribution metadata and package explicitly pinned Git evidence.

Records are JSON, validated against the repository's JSON Schema. The packet
builder never walks a working directory to decide what to publish.
"""

import argparse
from hashlib import sha256
import io
import json
from pathlib import Path, PurePosixPath
import shlex
import subprocess
import sys
from typing import Any
from urllib.parse import urlsplit
import zipfile

from jsonschema import Draft202012Validator, FormatChecker
import yaml


class RecordError(ValueError):
    """A record cannot substantiate its metadata or evidence identity."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise RecordError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    """Read JSON without silently accepting duplicate object keys."""
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, json.JSONDecodeError) as error:
        raise RecordError(f"Cannot read {path}: {error}") from error


def _path(root: Path, relative: str) -> Path:
    parts = PurePosixPath(relative).parts
    if (not parts or PurePosixPath(relative).is_absolute()
            or "\\" in relative or any(p.startswith(".") for p in parts)
            or PurePosixPath(relative).as_posix() != relative):
        raise RecordError(f"Unsafe repository-relative path: {relative}")
    result = root / relative
    if not result.resolve().is_relative_to(root.resolve()):
        raise RecordError(f"Path leaves repository: {relative}")
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise RecordError(f"Symlink is not an archival file: {relative}")
    return result


def _git_bytes(root: Path, commit: str, path: str) -> bytes:
    _path(root, path)
    try:
        entry = subprocess.check_output(
            ["git", "-C", str(root), "ls-tree", "-z", commit, "--", path],
            stderr=subprocess.PIPE,
        )
        if not entry.startswith((b"100644 blob ", b"100755 blob ")):
            raise RecordError(f"Not a regular pinned file: {commit}:{path}")
        return subprocess.check_output(
            ["git", "-C", str(root), "cat-file", "blob", f"{commit}:{path}"],
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as error:
        raise RecordError(f"Missing Git evidence {commit}:{path}; fetch full history") from error


def _identity(data: bytes) -> dict[str, Any]:
    return {"sha256": sha256(data).hexdigest(), "bytes": len(data)}


def _unique(values: list[str], description: str) -> None:
    if len(set(values)) != len(values):
        raise RecordError(f"Duplicate {description}")


def _validate_record(root: Path, record: dict[str, Any], schema: dict[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record),
        key=lambda error: str(list(error.path)),
    )
    if errors:
        error = errors[0]
        raise RecordError(f"Record schema at {list(error.path)}: {error.message}")
    for key in ("commit", "evidence_commit"):
        if key in record["source"]:
            try:
                kind = subprocess.check_output(
                    ["git", "-C", str(root), "cat-file", "-t", record["source"][key]],
                    stderr=subprocess.PIPE, text=True,
                ).strip()
            except subprocess.CalledProcessError as error:
                raise RecordError(f"Missing {key}: {record['source'][key]}") from error
            if kind != "commit":
                raise RecordError(f"{key} does not identify a Git commit")
    for collection in ("artifacts", "claims", "reproduction"):
        _unique([item["id"] for item in record[collection]], f"{collection} identifiers")
    _unique([item["path"] for item in record["artifacts"]], "artifact paths")
    artifact_ids = {item["id"] for item in record["artifacts"]}
    for claim in record["claims"]:
        if not set(claim["evidence"]) <= artifact_ids:
            raise RecordError(f"Unknown evidence in claim {claim['id']}")
    for command in record["reproduction"]:
        if command["cwd"] != ".":
            _path(root, command["cwd"])
    if record["publication"]["state"] == "published":
        if not record["publication"]["version_doi"]:
            raise RecordError("Published record requires an exact version DOI")
        if not any(e["kind"] == "archive_publication" for e in record["events"]):
            raise RecordError("Published record requires a separate archive-publication event")
    for artifact in record["artifacts"]:
        expected = {key: artifact[key] for key in ("sha256", "bytes")}
        try:
            working = _path(root, artifact["path"]).read_bytes()
        except OSError as error:
            raise RecordError(f"Missing working evidence: {artifact['path']}") from error
        if _identity(working) != expected:
            raise RecordError(f"Working evidence changed: {artifact['path']}")
        pinned = _git_bytes(root, artifact["source_commit"], artifact["path"])
        if _identity(pinned) != expected:
            raise RecordError(f"Pinned evidence differs: {artifact['path']}")


def validate_catalog(root: Path) -> list[dict[str, Any]]:
    """Validate all registered records, references, working bytes, and Git pins."""
    catalog = load_json(root / "research/catalog.json")
    schema = load_json(root / "research/record.schema.json")
    if (not isinstance(catalog, dict) or set(catalog) != {"schema_version", "records"}
            or type(catalog["schema_version"]) is not int or catalog["schema_version"] != 1
            or not isinstance(catalog["records"], list) or not catalog["records"]):
        raise RecordError("Invalid or empty catalog")
    records, ids, paths = [], [], []
    for entry in catalog["records"]:
        if (not isinstance(entry, dict) or set(entry) != {"id", "metadata"}
                or not all(isinstance(value, str) for value in entry.values())):
            raise RecordError("Catalog entries require id and metadata strings")
        record = load_json(_path(root, entry["metadata"]))
        _validate_record(root, record, schema)
        if record["id"] != entry["id"]:
            raise RecordError("Catalog identifier differs from record identifier")
        ids.append(entry["id"])
        paths.append(entry["metadata"])
        records.append(record)
    _unique(ids, "catalog identifiers")
    _unique(paths, "catalog metadata paths")
    return records


def citation(record: dict[str, Any]) -> str:
    """Generate CFF metadata without assigning an unrelated or reserved DOI."""
    source = record["source"]
    result = {
        "cff-version": "1.2.0",
        "message": "Cite this exact research record and its pinned evidence; review status is explicit.",
        "type": "dataset",
        "title": record["title"],
        "version": record["version"],
        "authors": [{
            "given-names": author["given_names"],
            "family-names": author["family_names"],
            "orcid": f"https://orcid.org/{author['orcid']}",
            "affiliation": author["affiliation"],
        } for author in record["authors"]],
        "abstract": record["abstract"],
        "keywords": record["keywords"],
        "repository-code": source["repository"],
        "url": f"{source['repository']}/tree/{source['commit']}",
        "commit": source["commit"],
        "license": sorted(set(record["licenses"].values())),
    }
    if record["publication"]["state"] == "published":
        result["doi"] = record["publication"]["version_doi"]
    return yaml.safe_dump(result, sort_keys=False, allow_unicode=True)


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def export_index(root: Path, record_id: str, metadata_commit: str) -> dict[str, Any]:
    """Derive a cross-project entry from committed, currently validated metadata."""
    if len(metadata_commit) != 40 or any(c not in "0123456789abcdef" for c in metadata_commit):
        raise RecordError("Index export requires a full immutable metadata commit")
    records = {record["id"]: record for record in validate_catalog(root)}
    if record_id not in records:
        raise RecordError(f"Unknown record: {record_id}")
    entries = load_json(root / "research/catalog.json")["records"]
    path = next(e["metadata"] for e in entries if e["id"] == record_id)
    pinned = _git_bytes(root, metadata_commit, path)
    if pinned != _path(root, path).read_bytes():
        raise RecordError("Commit the current metadata before exporting the index")
    record = records[record_id]
    repository = record["source"]["repository"]
    project = PurePosixPath(urlsplit(repository).path).name.removesuffix(".git")
    return {
        "schema_version": 1,
        "id": f"{project}-{record_id}",
        "title": record["title"],
        "contribution_type": "scoped research record with reproducible evidence",
        "authors": [{
            "name": f"{a['given_names']} {a['family_names']}",
            "orcid": a["orcid"], "affiliation": a["affiliation"],
        } for a in record["authors"]],
        "canonical_record": {
            "repository": repository, "commit": metadata_commit, "path": path,
            "url": f"{repository}/blob/{metadata_commit}/{path}",
            "sha256": sha256(pinned).hexdigest(),
        },
        "sources": record["source"],
        "claims": [{k: c[k] for k in ("id", "statement", "status")} for c in record["claims"]],
        "public_disclosures": [e for e in record["events"] if e["kind"] == "public_disclosure"],
        "acceptance_events": [e for e in record["events"] if e["kind"] == "repository_acceptance"],
        "review": record["review"],
        "publication": record["publication"],
        "licenses": record["licenses"],
        "keywords": record["keywords"],
        "ai_assistance": record["ai_assistance"],
        "predecessor_credit": record["credits"],
        "limitations": record["limitations"],
    }


def build_packet(root: Path, record: dict[str, Any]) -> bytes:
    """Build identical ZIP bytes from metadata and an explicit pinned allowlist.

    The caller validates metadata first. Evidence is read again from Git,
    never from mutable working files. No commands from records are executed.
    """
    prefix = record["id"]
    payload = {
        f"{prefix}/record.json": _json_bytes(record),
        f"{prefix}/CITATION.cff": citation(record).encode("utf-8"),
    }
    for artifact in record["artifacts"]:
        data = _git_bytes(root, artifact["source_commit"], artifact["path"])
        if _identity(data) != {key: artifact[key] for key in ("bytes", "sha256")}:
            raise RecordError(f"Pinned evidence differs: {artifact['path']}")
        payload[f"{prefix}/source/{artifact['path']}"] = data
    lines = [
        f"# {record['title']}", "", record["abstract"], "",
        "## Scope", "", *[f"- {c['statement']} ({c['status']})" for c in record["claims"]],
        "", "## Reproduce", "", "Run from `source/` with the environment described in record.json.",
    ]
    for command in record["reproduction"]:
        lines.extend([
            "", f"### {command['id']}", "", command["scope"], "", "```sh",
            f"(cd {shlex.quote(command['cwd'])} && {shlex.join(command['argv'])})",
            "```", "", f"Expected: {command['expected']}",
        ])
    lines.extend([
        "", "## Limits and credit", "",
        *[f"- {item}" for item in record["limitations"]], "",
        *record["credits"], "", record["ai_assistance"], "",
        "Licenses: " + "; ".join(f"{k}: {v}" for k, v in record["licenses"].items()),
        "", "Per-file licensing and third-party attribution are in record.json.",
        "The inventory hashes every payload file except the inventory itself.",
    ])
    payload[f"{prefix}/README.md"] = ("\n".join(lines) + "\n").encode("utf-8")
    payload[f"{prefix}/manifest.json"] = _json_bytes({
        "algorithm": "sha256",
        "files": {name: _identity(data) for name, data in sorted(payload.items())},
    })
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return output.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    for name in ("cite", "package", "export-index"):
        command = sub.add_parser(name)
        command.add_argument("record")
        if name == "package":
            command.add_argument("--output", type=Path, required=True)
        if name == "export-index":
            command.add_argument("--metadata-commit", required=True)
    args = parser.parse_args()
    try:
        if args.command == "export-index":
            print(_json_bytes(export_index(args.root, args.record, args.metadata_commit)).decode(), end="")
            return 0
        records = validate_catalog(args.root)
        if args.command == "validate":
            print(json.dumps({"valid": True, "records": [r["id"] for r in records]}))
        else:
            record = next((r for r in records if r["id"] == args.record), None)
            if record is None:
                raise RecordError(f"Unknown record: {args.record}")
            if args.command == "cite":
                print(citation(record), end="")
            else:
                data = build_packet(args.root, record)
                with args.output.open("xb") as stream:
                    stream.write(data)
                print(json.dumps({"output": str(args.output), **_identity(data)}))
    except (RecordError, OSError) as error:
        print(json.dumps({"valid": False, "error": str(error)}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
