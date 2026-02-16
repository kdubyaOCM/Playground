# CLAUDE.md

## What this repo is
We are building a cross-platform “Outlook Utility Toolbox” that helps archive and process email data safely.

Primary outcomes
- Ingest email sources (start with EML and MSG. Later add PST/OST and optional Graph export).
- Normalize into a local archive format (files plus JSON metadata).
- Provide utilities: inventory, dedupe, and export (PDF/CSV).

Non-goals (unless explicitly requested)
- Outlook COM automation, VSTO add-ins, or anything requiring Outlook to be installed.
- Cloud auth flows by default.
- GUI. CLI first.

## Operating principles
- Cross-platform first (macOS, Windows, Linux).
- Deterministic output. Same inputs produce the same structure and hashes.
- Privacy by default. No telemetry. No network calls unless a command explicitly requires it.
- Do not introduce real mailbox data into the repo. Fixtures must be synthetic and tiny.

## How Claude should work in this repo
When implementing a change
1) State intended behavior as a short acceptance checklist.
2) Make the smallest viable change set.
3) Add or update tests.
4) Run lint and tests.
5) Update docs if behavior changes.

If something is ambiguous
- Make a conservative assumption.
- Record it in docs/assumptions.md.
- Do not ask questions unless the ambiguity blocks progress.

## Suggested repo layout
- outlook_toolbox/             Python package
- outlook_toolbox/cli/         CLI commands
- outlook_toolbox/core/        core types, hashing, schema, utilities
- outlook_toolbox/parsers/     eml/msg (later pst/ost) adapters
- tests/                       pytest tests
- tests/fixtures/              synthetic EML/MSG only, very small
- docs/                        schema, examples, decisions
- .github/workflows/           CI

## Canonical archive format (MVP)
Output root: archive/

Each message must produce
- A content file (prefer EML). If conversion is not lossless, store the original alongside.
- A JSON metadata file next to it.

Metadata minimum fields
- source_type: eml|msg|pst|ost|graph
- source_path: repository-relative or input-relative. Never absolute.
- message_id (if present)
- subject, from, to, cc, bcc (as available)
- sent_at, received_at (ISO 8601 when possible)
- attachments: filename, size, sha256
- stable_message_hash: deterministic dedupe key

Never store secrets or tokens in metadata.

## Tooling defaults
- Python 3.11+ preferred (3.10+ acceptable if needed)
- pytest for tests
- ruff for lint and formatting
- mypy for types (incremental adoption ok)

Do not add heavy dependencies without justification.
If a dependency is GPL or LGPL, call it out clearly and offer a permissive alternative.

## CLI standards
- Single entrypoint: `outlook-toolbox`
- Every command supports `--help`
- Exit codes: 0 success, 2 usage error, 1 runtime error
- Human-readable output by default. Add `--json` where it helps.

No interactive prompts unless explicitly requested.

## Testing rules
- Every new command or parser must have tests.
- Fixtures must be synthetic and tiny.
- Prefer golden-file tests for archive layout and metadata stability.

## CI rules
CI must run on each PR
- ruff
- pytest
- mypy (can be limited to touched modules if needed)

## Licensing and attribution
- Prefer MIT or Apache-2.0 for this repo.
- If vendoring third-party code, preserve license text and add attribution in docs/third_party.md and LICENSES/ as needed.

## Definition of done
A feature is done when
- It works end-to-end on a minimal fixture.
- It has tests.
- CI passes.
- README/docs reflect usage.
- Output is deterministic.