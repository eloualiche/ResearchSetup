# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich>=13.0.0",
#     "tomli>=2.0.0",
# ]
# ///
"""
link_json.py - Create symbolic links from a JSON/TOML configuration file.

Usage:
    uv run link_json.py config.json [--dry-run] [--verbose]
"""

import argparse
import json
import shutil
import tomli
from pathlib import Path

from rich.console import Console
from rich.text import Text


# =============================================================================
# Helper Functions
# =============================================================================


def load_config_file(file_path: str) -> dict:
    """Load configuration from JSON or TOML file."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".json":
        return json.loads(path.read_text())
    elif ext == ".toml":
        return tomli.loads(path.read_text())
    else:
        raise ValueError(
            f"Unsupported file extension: {ext}. Only .json and .toml are supported."
        )


def check_path(value: dict) -> bool:
    """Check if the source path exists."""
    source = value.get("source", {})
    src_task = source.get("task", "")
    src_directory = source.get("directory", "")
    src_file = source.get("file")
    link_type = value.get("metadata", {}).get("type")

    if link_type == "file":
        src_path = Path(src_task) / src_directory / src_file
        return src_path.exists()
    elif link_type == "directory":
        src_path = Path(src_task) / src_directory
        return src_path.exists()
    elif link_type == "files":
        src_paths = [Path(src_task) / src_directory / sf for sf in src_file]
        return all(p.exists() for p in src_paths)
    return False


def create_symlink(
    source: Path,
    target: Path,
    console: Console,
    link_type: str = "file",
    verbose: bool = False,
) -> None:
    """Create a symbolic link from target to source."""
    target_is_directory = link_type == "directory"

    if verbose:
        console.print(f"[yellow]source is: {source}[/]")

    if link_type == "directory":
        if not source.is_dir():
            raise Exception("Source declared as directory but is not a directory")
        if target.is_symlink():
            target.unlink()
        elif target.exists():
            shutil.rmtree(target)
    else:
        if not source.is_file():
            raise Exception("Source declared as file but is not a file")
        if target.exists() or target.is_symlink():
            target.unlink()

    try:
        target.symlink_to(source, target_is_directory=target_is_directory)
    except OSError as e:
        console.print(f"[red]Failed to create symlink:[/] {e}")


def remove_common_prefix(path1: Path, path2: Path) -> tuple[Path, Path]:
    """Remove common directory prefix from two paths for cleaner display."""
    p1_parts = Path(path1).parts
    p2_parts = Path(path2).parts

    common_length = 0
    for part1, part2 in zip(p1_parts, p2_parts):
        if part1 == part2:
            common_length += 1
        else:
            break

    p1_suffix = (
        Path(*p1_parts[common_length:]) if common_length < len(p1_parts) else Path(".")
    )
    p2_suffix = (
        Path(*p2_parts[common_length:]) if common_length < len(p2_parts) else Path(".")
    )

    return p1_suffix, p2_suffix


# =============================================================================
# Main
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Create symbolic links from a JSON/TOML configuration file."
    )
    parser.add_argument(
        "conf_file", type=str, help="Path to the JSON/TOML configuration file"
    )
    parser.add_argument(
        "-d", "--dry-run", action="store_true", help="Preview without creating links"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show additional details"
    )
    args = parser.parse_args()

    console = Console(stderr=True)
    current_dir = Path.cwd()

    console.print(
        f"\n[bold blue]Processing[/] [underline]{args.conf_file}[/underline]\n"
    )

    data = load_config_file(args.conf_file)

    if args.dry_run:
        console.print("[italic]Dry run - no links will be created[/]\n")

    # Validate paths and collect missing entries
    file_missing_warning = Text()
    if isinstance(data, dict):
        for key, value in data.items():
            if not check_path(value):
                source = value.get("source", {})
                src_dir = source.get("directory", "")
                src_file = source.get("file", "")
                file_missing_warning.append(
                    Text.from_markup(f"  [dim]{key} ... {src_dir}/{src_file}[/]\n")
                )

        filtered_entries = {k: v for k, v in data.items() if check_path(v)}
        console.print(f"  {len(filtered_entries)} entries to process\n")

    # Process each link entry
    for key, value in filtered_entries.items():
        metadata = value.get("metadata", {})
        description = metadata.get("description", "")
        link_type = metadata.get("type", "")

        source = value.get("source", {})
        src_task = source.get("task", "")
        src_dir = source.get("directory", "")
        src_file = source.get("file")

        target = value.get("target", {})
        tgt_task = target.get("task", current_dir)
        tgt_dir = target.get("directory", "")
        tgt_file = target.get("file")

        # Header
        type_label = {"files": "(multiple files)", "directory": "(directory)"}.get(
            link_type, ""
        )
        console.print(f"[bold]{key}[/] [italic dark_green]{type_label}[/]")
        if description:
            console.print(f"  [italic]{description}[/]")

        # Build paths based on type
        if link_type == "file":
            src_path = Path(src_task) / src_dir / src_file
            tgt_path = Path(tgt_task) / tgt_dir / tgt_file
            target_dirs = [tgt_path.parent]
        elif link_type == "directory":
            src_path = Path(src_task) / src_dir
            tgt_path = Path(tgt_task) / tgt_dir
            target_dirs = [tgt_path]
        elif link_type == "files":
            src_path = [Path(src_task) / src_dir / sf for sf in src_file]
            tgt_path = [Path(tgt_task) / tgt_dir / tf for tf in tgt_file]
            target_dirs = list(set(p.parent for p in tgt_path))

            if len(src_path) != len(tgt_path):
                console.print(
                    "[bold red]ERROR:[/] Source and target file lists must have same length"
                )
                raise Exception("Source and target lists must be equal length")
        else:
            continue

        # Create target directories
        for dir_path in target_dirs:
            if not dir_path.is_dir():
                if args.verbose:
                    console.print(f"  [yellow]Creating directory: {dir_path}[/]")
                if not args.dry_run:
                    dir_path.mkdir(parents=True, exist_ok=True)

        # Create symlinks
        if link_type in ("file", "directory"):
            tgt_short, src_short = remove_common_prefix(tgt_path, src_path)
            console.print(f"  [dim]Target:[/] [blue]{tgt_short}[/]")
            console.print(f"  [dim]Source:[/] [green]{src_short}[/]")
            if args.dry_run:
                console.print("  [dim italic](dry-run)[/]")
            else:
                create_symlink(
                    src_path,
                    tgt_path,
                    console,
                    link_type=link_type,
                    verbose=args.verbose,
                )

        elif link_type == "files":
            for idx, (sf, tf) in enumerate(zip(src_path, tgt_path)):
                tgt_short, src_short = remove_common_prefix(tf, sf)
                if idx < 5:
                    console.print(f"  [dim]Target:[/] [blue]{tgt_short}[/]")
                    console.print(f"  [dim]Source:[/] [green]{src_short}[/]")
                elif idx == 5:
                    console.print(f"  [dim]... and {len(src_path) - 5} more files[/]")
                if not args.dry_run:
                    create_symlink(
                        sf, tf, console, link_type="file", verbose=args.verbose
                    )

            if args.dry_run:
                console.print("  [dim italic](dry-run)[/]")

        console.print("")

    # Show warnings for missing sources
    if file_missing_warning.plain.strip():
        console.print("[yellow]Some source paths not found (skipped):[/]")
        console.print(file_missing_warning)

    console.print("")


if __name__ == "__main__":
    main()
