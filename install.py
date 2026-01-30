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
    # Install to current directory with default location (_tools/)
    uv run install.py

    # Install to a specific project
    uv run install.py /path/to/project

    # Custom utilities location
    uv run install.py /path/to/project --dest utils

    # Download and run directly
    curl -fsSL https://raw.githubusercontent.com/USER/ResearchSetup/main/install.py | uv run --script -
"""

import argparse
import shutil
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

console = Console()

# Remote source URL (update with your repo)
REPO_RAW_URL = "https://raw.githubusercontent.com/USER/ResearchSetup/main"


def detect_source_dir() -> Path | None:
    """Check if we're running from the ResearchSetup source directory."""
    script_dir = Path(__file__).resolve().parent
    if (script_dir / "src/python/link_json.py").exists():
        return script_dir
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
    """Download a file from the remote repository."""
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


def create_link_wrapper(target_dir: Path, tools_dir: str) -> None:
    """Create a convenience wrapper script."""
    wrapper_content = f'''# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Convenience wrapper for ResearchSetup.
Exports the Nickel template and runs the linker.

Usage: uv run link.py [--dry-run] [--verbose]
"""

import subprocess
import sys
from pathlib import Path

def main():
    script_dir = Path(__file__).resolve().parent
    config_file = script_dir / "links.json"
    template_file = script_dir / "{tools_dir}/templates/links.ncl"
    linker_script = script_dir / "{tools_dir}/link_json.py"

    # Check for nickel
    try:
        subprocess.run(["nickel", "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("Error: nickel is not installed. Install it with:")
        print("  brew install nickel")
        print("  # or: cargo install nickel-lang-cli")
        sys.exit(1)

    # Export template to JSON
    print("Exporting Nickel template...")
    result = subprocess.run(
        ["nickel", "export", "--format", "json", str(template_file)],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Error exporting template: {{result.stderr}}")
        sys.exit(1)

    config_file.write_text(result.stdout)

    # Run the linker with uv, passing through any arguments
    subprocess.run(["uv", "run", str(linker_script), str(config_file)] + sys.argv[1:])

if __name__ == "__main__":
    main()
'''

    wrapper_path = target_dir / "link.py"
    wrapper_path.write_text(wrapper_content)
    console.print("  [green]ok[/] link.py")


def create_template(target_dir: Path, tools_dir: str) -> None:
    """Create the starter template with correct import path."""
    template_content = f"""# =============================================================================
# links.ncl - Define your data links here
# =============================================================================
# Usage:
#   nickel export --format json {tools_dir}/templates/links.ncl > links.json
#   uv run {tools_dir}/link_json.py links.json
# =============================================================================

let
    link_contracts = (import "../nickel/link_contracts.ncl")
in
let
    Link = link_contracts.link,
    serialize_records = link_contracts.serialize_records
in

{{
  # Environment - override local_task at evaluation time if needed
  env | not_exported = {{
    local_task | String | default = ".",
  }},

  # -------------------------------------------------------------------------
  # Define your links below
  # -------------------------------------------------------------------------

  # Example: Link a single file
  # MyDataFile | Link = 'file {{
  #     metadata = {{ description = "Description of this data file." }},
  #     source = {{
  #       file = "data.csv",
  #       directory = "/path/to/source/data"
  #     }},
  #     target = {{
  #       directory = "%{{env.local_task}}/input/data"
  #     }}
  # }},

  # Example: Link a directory
  # MyDataDir | Link = 'dir {{
  #     metadata = {{ description = "Raw data directory." }},
  #     source = {{ directory = "/path/to/source/raw_data" }},
  #     target = {{ directory = "%{{env.local_task}}/input/raw" }}
  # }},

}}
|> serialize_records
"""

    template_path = target_dir / tools_dir / "templates/links.ncl"
    if template_path.exists():
        console.print("  [yellow]skip[/] templates/links.ncl (already exists)")
    else:
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text(template_content)
        console.print("  [green]ok[/] templates/links.ncl")


def main():
    parser = argparse.ArgumentParser(
        description="Install ResearchSetup into a project directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run install.py                      # Install to current dir, tools in _tools/
  uv run install.py /path/to/project     # Install to specific project
  uv run install.py . --dest utils       # Install tools to utils/
  uv run install.py . --dest .           # Install directly in project root
        """,
    )
    parser.add_argument(
        "target_dir",
        nargs="?",
        default=".",
        help="Target project directory (default: current directory)",
    )
    parser.add_argument(
        "--dest",
        default="_tools",
        help="Subdirectory for tools inside the project (default: _tools)",
    )
    parser.add_argument(
        "--remote",
        action="store_true",
        help="Force download from remote even if local source exists",
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
    (tools_path / "nickel").mkdir(parents=True, exist_ok=True)
    (tools_path / "templates").mkdir(parents=True, exist_ok=True)

    # Install core files
    success = True

    # Main script
    if not install_file("src/python/link_json.py", tools_path / "link_json.py"):
        success = False

    # Nickel contracts
    if not install_file(
        "src/nickel/link_contracts.ncl", tools_path / "nickel/link_contracts.ncl"
    ):
        success = False

    # Create template with correct import path
    create_template(target_dir, tools_dir)

    # Create convenience wrapper
    create_link_wrapper(target_dir, tools_dir)

    # Summary
    if success:
        console.print("\n[bold green]Done![/]\n")
        console.print("Next steps:")
        console.print(
            f"  1. Edit [blue]{tools_dir}/templates/links.ncl[/] to define your links"
        )
        console.print("  2. Run [blue]uv run link.py --dry-run[/] to preview")
        console.print("  3. Run [blue]uv run link.py[/] to create symlinks")
    else:
        console.print("\n[bold red]Installation completed with errors.[/]")
        sys.exit(1)


if __name__ == "__main__":
    main()
