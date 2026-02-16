"""Unit tests for the EML scanner using synthetic messages."""

from __future__ import annotations

import json
import subprocess
import sys
from email.message import EmailMessage
from pathlib import Path

from outlook_toolbox.core.scanner import scan_eml, scan_path


def _write_eml(tmp_path: Path, name: str, msg: EmailMessage) -> Path:
    p = tmp_path / name
    p.write_bytes(msg.as_bytes())
    return p


def _simple_msg() -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = "alice@example.com"
    msg["To"] = "bob@example.com, carol@example.com"
    msg["Cc"] = "dave@example.com"
    msg["Subject"] = "Hello World"
    msg["Date"] = "Mon, 01 Jan 2024 12:00:00 +0000"
    msg["Message-ID"] = "<test-001@example.com>"
    msg.set_content("This is the body.")
    return msg


# -- scan_eml tests --


def test_basic_fields(tmp_path: Path):
    msg = _simple_msg()
    p = _write_eml(tmp_path, "basic.eml", msg)
    rec = scan_eml(p)

    assert rec.parse_ok is True
    assert rec.error is None
    assert rec.size_bytes > 0
    assert len(rec.sha256) == 64
    assert rec.message_id == "<test-001@example.com>"
    assert rec.subject == "Hello World"
    assert rec.from_ == "alice@example.com"
    assert len(rec.to) == 2
    assert len(rec.cc) == 1
    assert rec.bcc == []
    assert rec.has_text is True
    assert rec.date_iso is not None
    assert rec.date_iso.startswith("2024-01-01")


def test_body_preview_off_by_default(tmp_path: Path):
    p = _write_eml(tmp_path, "nobody.eml", _simple_msg())
    rec = scan_eml(p)
    assert rec.body_text_preview is None


def test_body_preview_on(tmp_path: Path):
    p = _write_eml(tmp_path, "body.eml", _simple_msg())
    rec = scan_eml(p, include_body=True)
    assert rec.body_text_preview is not None
    assert "This is the body." in rec.body_text_preview


def test_body_preview_truncated(tmp_path: Path):
    msg = EmailMessage()
    msg["From"] = "a@b.com"
    msg.set_content("x" * 5000)
    p = _write_eml(tmp_path, "long.eml", msg)
    rec = scan_eml(p, include_body=True, max_body_chars=100)
    assert rec.body_text_preview is not None
    assert len(rec.body_text_preview) == 100


def test_html_only_message(tmp_path: Path):
    msg = EmailMessage()
    msg["From"] = "a@b.com"
    msg["Subject"] = "HTML only"
    msg.set_content("<html><body><b>Bold</b> text</body></html>", subtype="html")
    p = _write_eml(tmp_path, "html.eml", msg)
    rec = scan_eml(p, include_body=True)

    assert rec.has_html is True
    assert rec.body_text_preview is not None
    assert "Bold" in rec.body_text_preview
    assert "<b>" not in rec.body_text_preview


def test_attachment_detection(tmp_path: Path):
    msg = EmailMessage()
    msg["From"] = "a@b.com"
    msg["Subject"] = "With attachment"
    msg.set_content("See attached.")
    msg.add_attachment(
        b"fake-pdf-content",
        maintype="application",
        subtype="pdf",
        filename="doc.pdf",
    )
    p = _write_eml(tmp_path, "attach.eml", msg)
    rec = scan_eml(p)

    assert rec.attachments_count == 1
    assert rec.attachments_total_bytes == len(b"fake-pdf-content")
    assert rec.has_text is True


def test_malformed_file(tmp_path: Path):
    p = tmp_path / "bad.eml"
    p.write_bytes(b"\x00\x01\x02 not valid email at all")
    rec = scan_eml(p)
    # Should not crash — parse_ok may be True (email lib is lenient)
    # but it must return a record with no crash
    assert isinstance(rec.parse_ok, bool)
    assert rec.size_bytes > 0
    assert len(rec.sha256) == 64


def test_missing_file(tmp_path: Path):
    p = tmp_path / "nonexistent.eml"
    rec = scan_eml(p)
    assert rec.parse_ok is False
    assert rec.error is not None
    assert "read error" in rec.error


# -- scan_path tests --


def test_scan_path_single_file(tmp_path: Path):
    p = _write_eml(tmp_path, "single.eml", _simple_msg())
    records = scan_path(p)
    assert len(records) == 1
    assert records[0].parse_ok is True


def test_scan_path_directory(tmp_path: Path):
    _write_eml(tmp_path, "a.eml", _simple_msg())
    _write_eml(tmp_path, "b.eml", _simple_msg())
    (tmp_path / "not-email.txt").write_text("ignore me")
    records = scan_path(tmp_path)
    assert len(records) == 2


def test_scan_path_case_insensitive_extension(tmp_path: Path):
    _write_eml(tmp_path, "upper.EML", _simple_msg())
    records = scan_path(tmp_path)
    assert len(records) == 1


def test_scan_path_nonexistent():
    records = scan_path(Path("/nonexistent/dir"))
    assert len(records) == 1
    assert records[0].parse_ok is False


def test_to_dict_keys(tmp_path: Path):
    p = _write_eml(tmp_path, "dict.eml", _simple_msg())
    rec = scan_eml(p)
    d = rec.to_dict()
    expected_keys = {
        "path", "size_bytes", "sha256", "parse_ok", "error",
        "message_id", "subject", "date_raw", "date_iso",
        "from", "to", "cc", "bcc",
        "attachments_count", "attachments_total_bytes",
        "has_html", "has_text", "body_text_preview",
    }
    assert set(d.keys()) == expected_keys


def test_to_dict_is_json_serializable(tmp_path: Path):
    p = _write_eml(tmp_path, "ser.eml", _simple_msg())
    rec = scan_eml(p)
    text = json.dumps(rec.to_dict())
    parsed = json.loads(text)
    assert parsed["parse_ok"] is True


# -- CLI integration --


def _cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "outlook_toolbox", *args],
        capture_output=True,
        text=True,
    )


def test_cli_scan_jsonl(tmp_path: Path):
    _write_eml(tmp_path, "msg.eml", _simple_msg())
    result = _cli(["scan", str(tmp_path)])
    assert result.returncode == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert obj["parse_ok"] is True


def test_cli_scan_json(tmp_path: Path):
    _write_eml(tmp_path, "msg.eml", _simple_msg())
    result = _cli(["scan", str(tmp_path), "--format", "json"])
    assert result.returncode == 0
    arr = json.loads(result.stdout)
    assert isinstance(arr, list)
    assert len(arr) == 1


def test_cli_scan_include_body(tmp_path: Path):
    _write_eml(tmp_path, "msg.eml", _simple_msg())
    result = _cli(["scan", str(tmp_path), "--include-body"])
    assert result.returncode == 0
    obj = json.loads(result.stdout.strip())
    assert obj["body_text_preview"] is not None
