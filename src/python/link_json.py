# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich>=13.0.0",
#     "tomli>=2.0.0",
# ]
# ///
"""
link_json.py - Create symbolic links from a configuration file.

Reads a JSON or TOML configuration (exported from a Nickel template) and
creates symbolic links from target paths to source paths.

Usage:
    uv run link_json.py links.toml
    uv run link_json.py links.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tomli
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from rich.console import Console

console = Console()


# =============================================================================
# Data Types
# =============================================================================


@dataclass
class LinkEntry:
    """A single link entry from the configuration."""

    name: str
    link_type: str  # "file", "files", or "directory"
    description: str
    source_dir: Path
    target_dir: Path
    source_files: list[str] | None = None  # For 'file' and 'files' types
    target_files: list[str] | None = None

    @classmethod
    def from_dict(cls, name: str, data: dict, cwd: Path) -> LinkEntry | None:
        """Parse a link entry from configuration dict."""
        metadata = data.get("metadata", {})
        source = data.get("source", {})
        target = data.get("target", {})

        link_type = metadata.get("type", "")
        if link_type not in ("file", "files", "directory"):
            return None

        src_task = source.get("task", "")
        tgt_task = target.get("task", str(cwd))

        entry = cls(
            name=name,
            link_type=link_type,
            description=metadata.get("description", ""),
            source_dir=Path(src_task) / source.get("directory", ""),
            target_dir=Path(tgt_task) / target.get("directory", ""),
        )

        if link_type == "file":
            src_file = source.get("file", "")
            entry.source_files = [src_file]
            entry.target_files = [target.get("file", src_file)]
        elif link_type == "files":
            entry.source_files = source.get("file", [])
            entry.target_files = target.get("file", entry.source_files)

        return entry

    def source_exists(self) -> bool:
        """Check if all source paths exist."""
        if self.link_type == "directory":
            return self.source_dir.exists()
        elif self.source_files:
            return all((self.source_dir / f).exists() for f in self.source_files)
        return False

    def iter_paths(self) -> Iterator[tuple[Path, Path]]:
        """Iterate over (source, target) path pairs."""
        if self.link_type == "directory":
            yield self.source_dir, self.target_dir
        elif self.source_files and self.target_files:
            for src_file, tgt_file in zip(self.source_files, self.target_files):
                yield self.source_dir / src_file, self.target_dir / tgt_file


# =============================================================================
# Core Functions
# =============================================================================


def load_config(file_path: Path) -> dict:
    """Load configuration from JSON or TOML file."""
    ext = file_path.suffix.lower()
    content = file_path.read_text()

    if ext == ".json":
        return json.loads(content)
    elif ext == ".toml":
        return tomli.loads(content)
    else:
        console.print(f"[red]Error:[/] Unsupported format: {ext}")
        console.print("Supported formats: .json, .toml")
        sys.exit(1)


def create_symlink(source: Path, target: Path, is_directory: bool = False) -> bool:
    """Create a symbolic link. Returns True on success."""
    # Validate source
    if is_directory and not source.is_dir():
        console.print(f"  [red]Error:[/] Source is not a directory: {source}")
        return False
    if not is_directory and not source.is_file():
        console.print(f"  [red]Error:[/] Source is not a file: {source}")
        return False

    # Remove existing target
    if target.is_symlink():
        target.unlink()
    elif target.exists():
        if is_directory:
            shutil.rmtree(target)
        else:
            target.unlink()

    # Create symlink
    try:
        target.symlink_to(source, target_is_directory=is_directory)
        return True
    except OSError as e:
        console.print(f"  [red]Error:[/] Failed to create symlink: {e}")
        return False


def shorten_path(path: Path, max_parts: int = 4) -> str:
    """Shorten a path for display by keeping only the last N parts."""
    parts = path.parts
    if len(parts) <= max_parts:
        return str(path)
    return ".../" + "/".join(parts[-max_parts:])


def process_entry(
    entry: LinkEntry, dry_run: bool = False, verbose: bool = False
) -> bool:
    """Process a single link entry. Returns True if all links succeeded."""
    # Header
    type_label = {"files": "(multiple)", "directory": "(dir)"}.get(entry.link_type, "")
    console.print(f"[bold]{entry.name}[/] [dim]{type_label}[/]")

    if entry.description:
        console.print(f"  [italic dim]{entry.description}[/]")

    success = True
    paths = list(entry.iter_paths())

    for idx, (src, tgt) in enumerate(paths):
        # Only show first 5 for multi-file links
        if idx < 5:
            console.print(f"  [dim]src:[/] [green]{shorten_path(src)}[/]")
            console.print(f"  [dim]tgt:[/] [blue]{shorten_path(tgt)}[/]")
        elif idx == 5 and len(paths) > 5:
            console.print(f"  [dim]... and {len(paths) - 5} more[/]")

        if dry_run:
            continue

        # Create parent directory if needed
        tgt.parent.mkdir(parents=True, exist_ok=True)

        # Create the symlink
        is_dir = entry.link_type == "directory"
        if not create_symlink(src, tgt, is_directory=is_dir):
            success = False

    if dry_run:
        console.print("  [dim](dry-run)[/]")

    console.print()
    return success


# =============================================================================
# Main
# =============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create symbolic links from a JSON/TOML configuration file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run link_json.py links.toml              # Create links from TOML config
  uv run link_json.py links.json --dry-run    # Preview without creating
  uv run link_json.py links.toml -v           # Verbose output

The configuration file is typically exported from a Nickel template:
  nickel export --format toml links_template.ncl > links.toml
""",
    )
    parser.add_argument(
        "config_file",
        type=Path,
        help="Path to the configuration file (.json or .toml)",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Preview links without creating them",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show additional details",
    )
    args = parser.parse_args()

    config_path = Path(args.config_file)
    if not config_path.exists():
        console.print(f"[red]Error:[/] File not found: {config_path}")
        return 1

    console.print(f"\n[bold]Processing[/] {config_path.name}\n")

    if args.dry_run:
        console.print("[italic]Dry run - no changes will be made[/]\n")

    # Load and parse configuration
    data = load_config(config_path)
    cwd = Path.cwd()

    # Parse entries
    entries: list[LinkEntry] = []
    missing: list[str] = []

    for name, value in data.items():
        if not isinstance(value, dict):
            continue

        entry = LinkEntry.from_dict(name, value, cwd)
        if entry is None:
            continue

        if entry.source_exists():
            entries.append(entry)
        else:
            missing.append(f"{name}: {entry.source_dir}")

    console.print(f"Found {len(entries)} valid entries\n")

    # Process entries
    all_success = True
    for entry in entries:
        if not process_entry(entry, dry_run=args.dry_run, verbose=args.verbose):
            all_success = False

    # Report missing sources
    if missing:
        console.print("[yellow]Skipped (source not found):[/]")
        for m in missing:
            console.print(f"  [dim]{m}[/]")
        console.print()

    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
