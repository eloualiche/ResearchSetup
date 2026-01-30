# ResearchSetup - Claude Code Instructions

## Project Overview

This project provides tools for creating symbolic links from source data directories to research projects using declarative Nickel templates.

## Code Formatting

### Python

Use `ruff` for linting and formatting:

```bash
# Check for issues
uv run ruff check src/python/ install.py

# Auto-fix issues
uv run ruff check --fix src/python/ install.py

# Format code
uv run ruff format src/python/ install.py
```

Ruff configuration (defaults are fine):
- Line length: 88
- Python target: 3.11+

### Nickel

No official formatter yet. Follow these conventions:
- Use 2-space indentation
- Use `# ===...` for section headers
- Use `# ---` for subsection separators
- Place `in` on its own line after `let` bindings
- Use trailing commas in records and arrays

## File Structure

```
src/python/link_json.py    # Self-contained linker script
src/nickel/link_contracts.ncl  # Type contracts
install.py                 # Installer script
examples/                  # Example configurations
```

## Testing

Test the installer locally:

```bash
# Create temp directory and install
mkdir -p /tmp/test-project
uv run install.py /tmp/test-project --dest _tools

# Verify files were created
ls -la /tmp/test-project/_tools/
```

Test the linker:

```bash
# Export a template and run dry-run
cd /tmp/test-project
nickel export --format json _tools/templates/links.ncl > links.json
uv run _tools/link_json.py links.json --dry-run
```

## Dependencies

Python scripts use inline PEP 723 metadata for uv:
- `rich` - Terminal output formatting
- `tomli` - TOML parsing
- `httpx` - HTTP client (installer only)
