# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "rich>=13.0.0",
#     "httpx>=0.27.0",
# ]
# ///
"""
ResearchSetup Installer

Installs the ResearchSetup linking tools into your project.

Usage:
    # Download from release and run
    curl -fsSL https://github.com/eloualiche/ResearchSetup/releases/latest/download/install.py | uv run --script -

    # Install to a specific project
    curl -fsSL .../install.py | uv run --script - /path/to/project

    # Custom tools location
    curl -fsSL .../install.py | uv run --script - /path/to/project --dest utils

    # If running locally
    uv run install.py /path/to/project
"""

import argparse
import shutil
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

console = Console()

# Repository info
REPO_RAW_URL = "https://raw.githubusercontent.com/eloualiche/ResearchSetup/main"


def detect_source_dir() -> Path | None:
    """Check if we're running from the ResearchSetup source directory."""
    try:
        script_dir = Path(__file__).resolve().parent
        if (script_dir / "src/python/link_json.py").exists():
            return script_dir
    except NameError:
        # __file__ not defined when piped to interpreter
        pass
    return None


def copy_local_file(source_dir: Path, src_path: str, dest_path: Path) -> bool:
    """Copy a file from local source."""
    src = source_dir / src_path
    if not src.exists():
        console.print(f"  [red]x[/] {src_path} not found")
        return False

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest_path)
    console.print(f"  [green]ok[/] {dest_path.name}")
    return True


def download_file(src_path: str, dest_path: Path) -> bool:
    """Download a file from the repository."""
    import httpx

    url = f"{REPO_RAW_URL}/{src_path}"
    try:
        response = httpx.get(url, follow_redirects=True)
        response.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(response.content)
        console.print(f"  [green]ok[/] {dest_path.name}")
        return True
    except httpx.HTTPError as e:
        console.print(f"  [red]x[/] Failed to download {src_path}: {e}")
        return False


def create_template(tools_path: Path) -> None:
    """Create the starter template."""
    template_content = """\
# =============================================================================
# links_template.ncl - Define your data links here
# =============================================================================
# Usage:
#   nickel export --format json _tools/nickel/links_template.ncl > links.json
#   uv run _tools/scripts/link_json.py links.json
# =============================================================================

let
    link_contracts = (import "link_contracts.ncl")
in
let
    Link = link_contracts.link,
    serialize_records = link_contracts.serialize_records
in

{
  # Environment - override local_task at evaluation time if needed
  env | not_exported = {
    local_task | String | default = ".",
  },

  # -------------------------------------------------------------------------
  # Define your links below
  # -------------------------------------------------------------------------

  # Example: Link a single file
  # MyDataFile | Link = 'file {
  #     metadata = { description = "Description of this data file." },
  #     source = {
  #       file = "data.csv",
  #       directory = "/path/to/source/data"
  #     },
  #     target = {
  #       directory = "%{env.local_task}/input/data"
  #     }
  # },

  # Example: Link a directory
  # MyDataDir | Link = 'dir {
  #     metadata = { description = "Raw data directory." },
  #     source = { directory = "/path/to/source/raw_data" },
  #     target = { directory = "%{env.local_task}/input/raw" }
  # },

}
|> serialize_records
"""

    template_path = tools_path / "nickel/links_template.ncl"
    if template_path.exists():
        console.print("  [yellow]skip[/] links_template.ncl (already exists)")
    else:
        template_path.write_text(template_content)
        console.print("  [green]ok[/] links_template.ncl")


def main():
    parser = argparse.ArgumentParser(
        description="""
Install ResearchSetup linking tools into a project directory.

This script downloads and installs:
  - scripts/link_json.py: The main linker script
  - nickel/link_contracts.ncl: Type contracts for link definitions
  - nickel/links_template.ncl: Starter template for defining your links
""".strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Install to current directory with tools in _tools/
  uv run install.py

  # Install to a specific project
  uv run install.py /path/to/my/project

  # Put tools in a custom subdirectory
  uv run install.py /path/to/project --dest utils

  # Pipe from curl (for remote installation)
  curl -fsSL https://github.com/.../install.py | uv run --script - /path/to/project

After installation:
  1. Edit <dest>/nickel/links_template.ncl to define your links
  2. Run: nickel export <dest>/nickel/links_template.ncl > links.json
  3. Run: uv run <dest>/scripts/link_json.py links.json
""",
    )
    parser.add_argument(
        "target_dir",
        nargs="?",
        default=".",
        metavar="PROJECT_DIR",
        help="Project directory to install into (default: current directory)",
    )
    parser.add_argument(
        "--dest",
        default="_tools",
        metavar="DIR",
        help="Subdirectory for tools inside the project (default: _tools)",
    )
    parser.add_argument(
        "--remote",
        action="store_true",
        help="Force download from GitHub even when running from local repo",
    )
    args = parser.parse_args()

    target_dir = Path(args.target_dir).resolve()
    tools_dir = args.dest.strip("/")  # Normalize

    if not target_dir.exists():
        console.print(f"[red]Error:[/] Target directory does not exist: {target_dir}")
        sys.exit(1)

    tools_path = target_dir / tools_dir if tools_dir != "." else target_dir

    console.print(
        Panel.fit(
            f"[bold blue]ResearchSetup Installer[/]\n\n"
            f"Project:  [green]{target_dir}[/]\n"
            f"Tools in: [green]{tools_dir}/[/]"
            if tools_dir != "."
            else f"Project: [green]{target_dir}[/]",
            border_style="blue",
        )
    )

    # Detect source mode
    source_dir = detect_source_dir() if not args.remote else None

    def install_file(src: str, dest: Path) -> bool:
        if source_dir:
            return copy_local_file(source_dir, src, dest)
        return download_file(src, dest)

    if source_dir:
        console.print(f"\n[dim]Source: {source_dir}[/]")
    else:
        console.print(f"\n[dim]Source: {REPO_RAW_URL}[/]")

    # Create directories
    console.print("\n[blue]Installing...[/]")
    (tools_path / "scripts").mkdir(parents=True, exist_ok=True)
    (tools_path / "nickel").mkdir(parents=True, exist_ok=True)

    # Install core files
    success = True

    # Main linker script
    if not install_file("src/python/link_json.py", tools_path / "scripts/link_json.py"):
        success = False

    # Nickel contracts
    if not install_file(
        "src/nickel/link_contracts.ncl", tools_path / "nickel/link_contracts.ncl"
    ):
        success = False

    # Create starter template
    create_template(tools_path)

    # Summary
    if success:
        console.print("\n[bold green]Done![/]\n")
        console.print("Next steps:")
        console.print(
            f"  1. Edit [blue]{tools_dir}/nickel/links_template.ncl[/] to define your links"
        )
        console.print(
            f"  2. Export: [blue]nickel export {tools_dir}/nickel/links_template.ncl > links.json[/]"
        )
        console.print(
            f"  3. Link:   [blue]uv run {tools_dir}/scripts/link_json.py links.json[/]"
        )
    else:
        console.print("\n[bold red]Installation completed with errors.[/]")
        sys.exit(1)


if __name__ == "__main__":
    main()
