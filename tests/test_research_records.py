"""Records must preserve evidence identity and produce portable packets."""

import copy
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest
import yaml

from research_records import (
    RecordError,
    build_packet,
    citation,
    export_index,
    load_json,
    validate_catalog,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "src/research_records.py"


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.name", "Test Author")
    git(root, "config", "user.email", "test@example.org")
    (root / "proof.txt").write_bytes(b"checkable evidence\n")
    git(root, "add", "proof.txt")
    git(root, "commit", "-qm", "Initial evidence")
    commit = git(root, "rev-parse", "HEAD")
    record = {
        "schema_version": 1,
        "id": "example",
        "title": "Example contribution",
        "version": "1.0.0",
        "authors": [{
            "given_names": "Alex", "family_names": "Towell",
            "orcid": "0000-0001-6443-9897",
            "affiliation": "SIUE",
        }],
        "abstract": "A narrowly scoped example.",
        "keywords": ["combinatorics"],
        "licenses": {"code": "MIT", "papers": "CC-BY-4.0"},
        "source": {"repository": "https://github.com/example/repo", "commit": commit},
        "claims": [{
            "id": "result", "statement": "The example is finite.",
            "status": "finite_computation", "evidence": ["proof"],
        }],
        "assumptions": ["Only the example input."],
        "limitations": ["No general theorem."],
        "credits": ["Prior methods are credited in the proof."],
        "ai_assistance": "AI assisted preparation.",
        "review": {"human": "pending", "formal_proof": False, "novelty": "not_assessed"},
        "events": [{
            "kind": "public_disclosure", "date": "2026-10-18",
            "url": "https://github.com/example/repo/pull/1",
            "scope": "The finite example.",
        }],
        "publication": {"state": "not_archived", "version_doi": None, "concept_doi": None},
        "artifacts": [{
            "id": "proof", "path": "proof.txt", "source_commit": commit,
            "sha256": hashlib.sha256(b"checkable evidence\n").hexdigest(),
            "bytes": 19, "role": "proof", "license": "CC-BY-4.0",
        }],
        "reproduction": [{
            "id": "read-proof", "argv": ["python", "-c", "print('checked')"],
            "cwd": ".", "expected_exit_code": 0,
            "expected": "checked", "scope": "Demonstration only.",
        }],
        "next_steps": ["Human review."],
    }
    directory = root / "research"
    directory.mkdir()
    shutil.copyfile(ROOT / "research/record.schema.json", directory / "record.schema.json")
    write_json(directory / "catalog.json", {
        "schema_version": 1,
        "records": [{"id": "example", "metadata": "research/records/example/record.json"}],
    })
    write_json(directory / "records/example/record.json", record)
    return root, record


def store_record(root, record):
    write_json(root / "research/records/example/record.json", record)


def test_valid_record_has_pinned_evidence(repository):
    root, _ = repository
    records = validate_catalog(root)
    assert len(records) == 1
    assert records[0]["id"] == "example"


@pytest.mark.parametrize("field,value", [
    ("sha256", "0" * 64), ("bytes", 20), ("source_commit", "0" * 40),
])
def test_incorrect_evidence_identity_is_rejected(repository, field, value):
    root, record = repository
    record["artifacts"][0][field] = value
    store_record(root, record)
    with pytest.raises(RecordError):
        validate_catalog(root)


def test_changed_working_file_cannot_masquerade_as_pinned_evidence(repository):
    root, record = repository
    (root / "proof.txt").write_bytes(b"changed evidence\n")
    with pytest.raises(RecordError):
        validate_catalog(root)
    record["artifacts"][0].update(
        bytes=17, sha256=hashlib.sha256(b"changed evidence\n").hexdigest()
    )
    store_record(root, record)
    with pytest.raises(RecordError):
        validate_catalog(root)


def test_citation_source_commit_must_exist(repository):
    root, record = repository
    record["source"]["commit"] = "0" * 40
    store_record(root, record)
    with pytest.raises(RecordError):
        validate_catalog(root)


def test_reproduction_preserves_repeated_flags_and_empty_argument_values(repository):
    root, record = repository
    argv = ["python", "-m", "pip", "install", "-r", "requirements.txt", "-r", ""]
    record["reproduction"][0]["argv"] = argv
    store_record(root, record)
    assert validate_catalog(root)[0]["reproduction"][0]["argv"] == argv


def test_reproduction_requires_a_nonempty_executable(repository):
    root, record = repository
    record["reproduction"][0]["argv"] = ["", "argument"]
    store_record(root, record)
    with pytest.raises(RecordError):
        validate_catalog(root)


@pytest.mark.parametrize("path", ["../secret", "/tmp/secret", "a/../proof.txt", ".git/config"])
def test_unsafe_artifact_paths_are_rejected(repository, path):
    root, record = repository
    record["artifacts"][0]["path"] = path
    store_record(root, record)
    with pytest.raises(RecordError):
        validate_catalog(root)


def test_symlinks_cannot_import_unlisted_material(repository, tmp_path):
    root, _ = repository
    outside = tmp_path / "outside"
    outside.write_bytes(b"checkable evidence\n")
    (root / "proof.txt").unlink()
    (root / "proof.txt").symlink_to(outside)
    with pytest.raises(RecordError):
        validate_catalog(root)


@pytest.mark.parametrize("mutation", [
    lambda r: r["artifacts"].append(copy.deepcopy(r["artifacts"][0])),
    lambda r: r["claims"][0].update(evidence=["missing"]),
    lambda r: r["review"].update(human="accepted_by_ai"),
    lambda r: r["events"][0].update(date="2026-02-30"),
    lambda r: r["publication"].update(state="published"),
    lambda r: r.update(unrecognized_status="proven"),
])
def test_invalid_or_misleading_metadata_is_rejected(repository, mutation):
    root, record = repository
    mutation(record)
    store_record(root, record)
    with pytest.raises(RecordError):
        validate_catalog(root)


def test_duplicate_catalog_ids_are_rejected(repository):
    root, _ = repository
    path = root / "research/catalog.json"
    catalog = json.loads(path.read_text())
    catalog["records"] *= 2
    write_json(path, catalog)
    with pytest.raises(RecordError):
        validate_catalog(root)


def test_catalog_record_id_must_match(repository):
    root, record = repository
    record["id"] = "other"
    store_record(root, record)
    with pytest.raises(RecordError):
        validate_catalog(root)


def test_duplicate_json_keys_are_not_silently_overwritten(tmp_path):
    path = tmp_path / "duplicate.json"
    path.write_text('{"status": "pending", "status": "proved"}')
    with pytest.raises(RecordError):
        load_json(path)


def test_packet_is_reproducible_complete_and_excludes_unlisted_files(repository):
    root, _ = repository
    record = validate_catalog(root)[0]
    (root / "private-token.txt").write_text("must never enter packet")
    first = build_packet(root, record)
    (root / "proof.txt").touch()
    assert build_packet(root, record) == first
    with zipfile.ZipFile(io.BytesIO(first)) as packet:
        names = packet.namelist()
        assert "example/source/proof.txt" in names
        assert not any("private-token" in name for name in names)
        assert packet.read("example/source/proof.txt") == b"checkable evidence\n"
        manifest = json.loads(packet.read("example/manifest.json"))
        assert set(manifest["files"]) == set(names) - {"example/manifest.json"}
        for name, identity in manifest["files"].items():
            content = packet.read(name)
            assert identity["sha256"] == hashlib.sha256(content).hexdigest()
            assert identity["bytes"] == len(content)
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in packet.infolist())


def test_packet_uses_git_objects_even_after_working_file_changes(repository):
    root, _ = repository
    record = validate_catalog(root)[0]
    (root / "proof.txt").write_text("unreviewed edit")
    with zipfile.ZipFile(io.BytesIO(build_packet(root, record))) as packet:
        assert packet.read("example/source/proof.txt") == b"checkable evidence\n"


def test_citation_uses_exact_commit_without_borrowing_an_older_doi(repository):
    _, record = repository
    cff = yaml.safe_load(citation(record))
    assert cff["commit"] == record["source"]["commit"]
    assert "doi" not in cff
    assert cff["authors"][0]["orcid"] == "https://orcid.org/0000-0001-6443-9897"
    record["publication"].update(state="published", version_doi="10.5281/zenodo.12345")
    assert yaml.safe_load(citation(record))["doi"] == "10.5281/zenodo.12345"


def test_cli_validates_builds_and_refuses_to_overwrite(repository, tmp_path):
    root, _ = repository
    command = [sys.executable, str(SCRIPT), "--root", str(root)]
    result = subprocess.run(command + ["validate"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["records"] == ["example"]
    output = tmp_path / "packet.zip"
    args = command + ["package", "example", "--output", str(output)]
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    original = output.read_bytes()
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode != 0
    assert output.read_bytes() == original
    (root / "proof.txt").write_text("bad")
    result = subprocess.run(command + ["validate"], capture_output=True, text=True)
    assert result.returncode != 0


def test_repository_records_validate():
    assert validate_catalog(ROOT)


def test_index_export_pins_metadata_and_does_not_invent_publication(repository):
    root, _ = repository
    git(root, "add", "research")
    git(root, "commit", "-qm", "Register contribution")
    commit = git(root, "rev-parse", "HEAD")
    entry = export_index(root, "example", commit)
    assert entry["id"] == "repo-example"
    assert entry["canonical_record"]["commit"] == commit
    assert entry["publication"]["state"] == "not_archived"
    assert entry["publication"]["version_doi"] is None
    assert entry["authors"][0]["name"] == "Alex Towell"
    assert entry["public_disclosures"][0]["date"] == "2026-10-18"
    path = root / entry["canonical_record"]["path"]
    assert entry["canonical_record"]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    record = json.loads(path.read_text())
    record["title"] = "Uncommitted revision"
    store_record(root, record)
    with pytest.raises(RecordError):
        export_index(root, "example", commit)
