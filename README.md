# Outlook Utility Toolbox

Cross-platform CLI for archiving and processing email data.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Usage

```bash
outlook-toolbox --help
outlook-toolbox scan          # stub – not implemented yet
outlook-toolbox dedupe        # stub – not implemented yet
outlook-toolbox export-pdf    # stub – not implemented yet
```

All subcommands are stubs that print "not implemented yet" and exit 0.

## Development

```bash
ruff check .
pytest -q
```

## License

Apache-2.0 – see [LICENSE](LICENSE).
