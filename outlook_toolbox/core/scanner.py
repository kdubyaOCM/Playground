"""Scan .eml files and extract structured metadata."""

from __future__ import annotations

import email
import email.policy
import email.utils
import hashlib
import re
from dataclasses import dataclass, field
from datetime import timezone
from email.message import EmailMessage
from pathlib import Path, PurePosixPath
from typing import Any


@dataclass
class ScanRecord:
    """Metadata extracted from a single email file."""

    path: str
    size_bytes: int
    sha256: str
    parse_ok: bool
    error: str | None = None
    message_id: str | None = None
    subject: str | None = None
    date_raw: str | None = None
    date_iso: str | None = None
    from_: str | None = None
    to: list[str] = field(default_factory=list)
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    attachments_count: int = 0
    attachments_total_bytes: int = 0
    has_html: bool = False
    has_text: bool = False
    body_text_preview: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "path": self.path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "parse_ok": self.parse_ok,
            "error": self.error,
            "message_id": self.message_id,
            "subject": self.subject,
            "date_raw": self.date_raw,
            "date_iso": self.date_iso,
            "from": self.from_,
            "to": self.to,
            "cc": self.cc,
            "bcc": self.bcc,
            "attachments_count": self.attachments_count,
            "attachments_total_bytes": self.attachments_total_bytes,
            "has_html": self.has_html,
            "has_text": self.has_text,
            "body_text_preview": self.body_text_preview,
        }
        return d


def _file_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize_path(p: Path) -> str:
    """Return a forward-slash path string for deterministic output."""
    return str(PurePosixPath(p))


_STRIP_HTML_RE = re.compile(r"<[^>]+>")


def _strip_html(html: str) -> str:
    """Minimal tag stripping — not a full HTML parser."""
    return _STRIP_HTML_RE.sub("", html)


def _extract_addresses(msg: EmailMessage, header: str) -> list[str]:
    raw = msg.get_all(header, [])
    pairs = email.utils.getaddresses(raw)
    results: list[str] = []
    for display_name, addr in pairs:
        if display_name and addr:
            results.append(f"{display_name} <{addr}>")
        elif addr:
            results.append(addr)
        elif display_name:
            results.append(display_name)
    return results


def _get_payload_bytes(part: EmailMessage) -> bytes | None:
    """Return decoded payload as bytes, or None."""
    payload = part.get_payload(decode=True)
    if isinstance(payload, bytes):
        return payload
    return None


def _decode_payload(part: EmailMessage) -> str | None:
    """Decode a MIME part's payload to str, or return None."""
    raw = _get_payload_bytes(part)
    if raw is None:
        return None
    charset = part.get_content_charset() or "utf-8"
    try:
        return raw.decode(charset, errors="replace")
    except (LookupError, UnicodeDecodeError):
        return raw.decode("utf-8", errors="replace")


def _parse_date_iso(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        dt = email.utils.parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        return None


def _is_attachment(part: EmailMessage) -> bool:
    cd = part.get_content_disposition()
    if cd == "attachment":
        return True
    if part.get_filename():
        return True
    return False


def scan_eml(
    file_path: Path,
    *,
    include_body: bool = False,
    max_body_chars: int = 2000,
) -> ScanRecord:
    """Parse a single .eml file and return a ScanRecord."""
    posix_path = _normalize_path(file_path)
    try:
        raw = file_path.read_bytes()
    except OSError as exc:
        return ScanRecord(
            path=posix_path,
            size_bytes=0,
            sha256="",
            parse_ok=False,
            error=f"read error: {exc}",
        )

    size = len(raw)
    sha = _file_hash(raw)

    try:
        msg: EmailMessage = email.message_from_bytes(  # type: ignore[assignment]
            raw, policy=email.policy.default
        )
    except Exception as exc:
        return ScanRecord(
            path=posix_path,
            size_bytes=size,
            sha256=sha,
            parse_ok=False,
            error=f"parse error: {exc}",
        )

    try:
        record = _extract_metadata(msg, posix_path, size, sha, include_body, max_body_chars)
    except Exception as exc:
        return ScanRecord(
            path=posix_path,
            size_bytes=size,
            sha256=sha,
            parse_ok=False,
            error=f"extraction error: {exc}",
        )

    return record


def _extract_metadata(
    msg: EmailMessage,
    posix_path: str,
    size: int,
    sha: str,
    include_body: bool,
    max_body_chars: int,
) -> ScanRecord:
    date_raw = msg.get("Date")
    date_iso = _parse_date_iso(date_raw)

    from_addrs = _extract_addresses(msg, "From")
    from_str = from_addrs[0] if from_addrs else None

    att_count = 0
    att_bytes = 0
    has_html = False
    has_text = False
    text_body: str | None = None
    html_body: str | None = None

    for part in msg.walk():
        ct = part.get_content_type()

        if _is_attachment(part):
            att_count += 1
            raw_payload = _get_payload_bytes(part)
            if raw_payload is not None:
                att_bytes += len(raw_payload)
            continue

        if ct == "text/plain" and not has_text:
            has_text = True
            if include_body and text_body is None:
                text_body = _decode_payload(part)
        elif ct == "text/html":
            has_html = True
            if include_body and text_body is None and html_body is None:
                html_body = _decode_payload(part)

    body_preview: str | None = None
    if include_body:
        raw_text = text_body if text_body else (_strip_html(html_body) if html_body else None)
        if raw_text:
            body_preview = raw_text[:max_body_chars]

    return ScanRecord(
        path=posix_path,
        size_bytes=size,
        sha256=sha,
        parse_ok=True,
        message_id=msg.get("Message-ID"),
        subject=msg.get("Subject"),
        date_raw=date_raw,
        date_iso=date_iso,
        from_=from_str,
        to=_extract_addresses(msg, "To"),
        cc=_extract_addresses(msg, "Cc"),
        bcc=_extract_addresses(msg, "Bcc"),
        attachments_count=att_count,
        attachments_total_bytes=att_bytes,
        has_html=has_html,
        has_text=has_text,
        body_text_preview=body_preview,
    )


def scan_path(
    target: Path,
    *,
    include_body: bool = False,
    max_body_chars: int = 2000,
) -> list[ScanRecord]:
    """Scan a file or directory for .eml files and return records."""
    if target.is_file():
        return [scan_eml(target, include_body=include_body, max_body_chars=max_body_chars)]

    if target.is_dir():
        records: list[ScanRecord] = []
        for child in sorted(target.rglob("*")):
            if child.is_file() and child.suffix.lower() == ".eml":
                records.append(
                    scan_eml(child, include_body=include_body, max_body_chars=max_body_chars)
                )
        return records

    return [
        ScanRecord(
            path=_normalize_path(target),
            size_bytes=0,
            sha256="",
            parse_ok=False,
            error=f"path not found: {target}",
        )
    ]
