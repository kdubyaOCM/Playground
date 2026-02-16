"""Integration tests using the real .eml fixtures in tests/fixtures/."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from outlook_toolbox.core.scanner import scan_path

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURE_FILES = sorted(FIXTURES_DIR.glob("*.eml"))


@pytest.fixture()
def fixture_records():
    return scan_path(FIXTURES_DIR)


class TestFixtureDirectoryScan:
    def test_returns_three_records(self, fixture_records):
        assert len(fixture_records) == 3

    def test_all_parse_ok(self, fixture_records):
        for rec in fixture_records:
            assert rec.parse_ok is True, f"{rec.path}: {rec.error}"

    def test_sha256_format(self, fixture_records):
        for rec in fixture_records:
            assert len(rec.sha256) == 64
            assert all(c in "0123456789abcdef" for c in rec.sha256)

    def test_size_bytes_positive(self, fixture_records):
        for rec in fixture_records:
            assert rec.size_bytes > 0

    def test_attachments_count_non_negative(self, fixture_records):
        for rec in fixture_records:
            assert rec.attachments_count >= 0
            assert rec.attachments_total_bytes >= 0

    def test_to_dict_json_serializable(self, fixture_records):
        for rec in fixture_records:
            text = json.dumps(rec.to_dict())
            parsed = json.loads(text)
            assert isinstance(parsed, dict)


class TestFixtureCLI:
    def _cli(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "outlook_toolbox", *args],
            capture_output=True,
            text=True,
        )

    def test_jsonl_output_valid(self):
        result = self._cli(["scan", str(FIXTURES_DIR)])
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) == 3
        for line in lines:
            obj = json.loads(line)
            assert obj["parse_ok"] is True

    def test_json_output_valid(self):
        result = self._cli(["scan", str(FIXTURES_DIR), "--format", "json"])
        assert result.returncode == 0
        arr = json.loads(result.stdout)
        assert isinstance(arr, list)
        assert len(arr) == 3

    def test_include_body_flag(self):
        result = self._cli(["scan", str(FIXTURES_DIR), "--include-body"])
        assert result.returncode == 0
        for line in result.stdout.strip().splitlines():
            obj = json.loads(line)
            # body_text_preview may be null if message has no body parts,
            # but the field must exist
            assert "body_text_preview" in obj
