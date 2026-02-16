"""Smoke tests for the outlook-toolbox CLI."""

from __future__ import annotations

import subprocess
import sys


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "outlook_toolbox", *args],
        capture_output=True,
        text=True,
    )


def test_help_exits_zero():
    result = _run(["--help"])
    assert result.returncode == 0
    assert "outlook-toolbox" in result.stdout


def test_version_exits_zero():
    result = _run(["--version"])
    assert result.returncode == 0
    assert "0.1.0" in result.stdout


def test_scan_help_exits_zero():
    result = _run(["scan", "--help"])
    assert result.returncode == 0


def test_dedupe_help_exits_zero():
    result = _run(["dedupe", "--help"])
    assert result.returncode == 0


def test_export_pdf_help_exits_zero():
    result = _run(["export-pdf", "--help"])
    assert result.returncode == 0


def test_dedupe_stub_prints_not_implemented():
    result = _run(["dedupe"])
    assert result.returncode == 0
    assert "not implemented yet" in result.stdout


def test_no_args_shows_help():
    result = _run([])
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
