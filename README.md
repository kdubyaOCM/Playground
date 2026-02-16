# Outlook Utility Toolbox

Cross-platform CLI for archiving and processing email data.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Usage

### scan

Scan `.eml` files and extract structured metadata.

```bash
# Scan a directory (recursive), output JSONL (one JSON object per line):
outlook-toolbox scan ./inbox/

# Scan a single file, output as a JSON array:
outlook-toolbox scan message.eml --format json

# Include a body text preview (up to 2000 chars by default):
outlook-toolbox scan ./inbox/ --include-body --max-body-chars 500
```

`.eml` is implemented first. `.msg` / `.pst` support is planned.

### Other commands

```bash
outlook-toolbox dedupe        # stub – not implemented yet
outlook-toolbox export-pdf    # stub – not implemented yet
```

## Development

```bash
ruff check .
pytest -q
mypy outlook_toolbox
```

## License

Apache-2.0 – see [LICENSE](LICENSE).
