# ResearchSetup

Create symbolic links from source data directories to your research project using declarative Nickel templates.

## Overview

Instead of copying data or manually creating symlinks, define your links in a Nickel config file and run one command.

```
Nickel template (.ncl)  →  JSON  →  Python creates symlinks
```

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** - Python package runner (handles dependencies automatically)
- **[Nickel](https://nickel-lang.org/)** - Configuration language for defining links

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Nickel (macOS)
brew install nickel

# Or with cargo
cargo install nickel-lang-cli
```

## Install

The installer downloads the necessary files into your project. It creates a `_tools/` directory (configurable) containing the linker script and Nickel contracts.

### How the install command works

```bash
curl -fsSL <url> | uv run --script - [arguments]
```

Breaking this down:
- `curl -fsSL <url>` — Downloads the install script from GitHub
- `|` — Pipes the script to the next command
- `uv run --script -` — Runs the piped Python script (`-` means "read from stdin")
- `[arguments]` — Any arguments after `-` are passed to the Python script

### Installation examples

```bash
# Install to CURRENT directory (creates _tools/ here)
curl -fsSL https://github.com/eloualiche/ResearchSetup/releases/latest/download/install.py | uv run --script -

# Install to a SPECIFIC project directory
curl -fsSL https://github.com/eloualiche/ResearchSetup/releases/latest/download/install.py | uv run --script - /path/to/my/project

# Install with CUSTOM tools location (instead of _tools/)
curl -fsSL https://github.com/eloualiche/ResearchSetup/releases/latest/download/install.py | uv run --script - /path/to/project --dest utils

# Install tools directly in project root (no subdirectory)
curl -fsSL https://github.com/eloualiche/ResearchSetup/releases/latest/download/install.py | uv run --script - /path/to/project --dest .
```

The URL `releases/latest/download/install.py` automatically redirects to the most recent release.

### If you have the repo cloned locally

```bash
# The installer detects local source and copies files directly
uv run install.py /path/to/project

# Force download from GitHub even when running locally
uv run install.py /path/to/project --remote
```

### What gets installed

```
your-project/
├── link.py                    # Convenience wrapper (run this)
└── _tools/                    # Tools directory (--dest controls this)
    ├── link_json.py           # Main linker script
    ├── nickel/
    │   └── link_contracts.ncl # Type contracts for links
    └── templates/
        └── links.ncl          # Your link definitions (edit this)
```

## Usage

### 1. Define your links

Edit `_tools/templates/links.ncl` to specify what data to link:

```nickel
{
  # Link an entire directory
  RawData | Link = 'dir {
      metadata = { description = "Raw experiment data." },
      source = { directory = "/data/shared/experiment_2024" },
      target = { directory = "%{env.local_task}/input/raw" }
  },

  # Link a single file
  ConfigFile | Link = 'file {
      metadata = { description = "Analysis config." },
      source = {
        file = "config.yaml",
        directory = "/data/shared/configs"
      },
      target = { directory = "%{env.local_task}/input" }
  },
}
|> serialize_records
```

The `%{env.local_task}` variable expands to the current directory (`.` by default).

### 2. Create the symlinks

```bash
# Preview what will be linked (no changes made)
uv run link.py --dry-run

# Create all symlinks
uv run link.py

# Show verbose output
uv run link.py --verbose
```

### Manual workflow (without wrapper)

```bash
# Step 1: Export Nickel template to JSON
nickel export --format json _tools/templates/links.ncl > links.json

# Step 2: Run the linker
uv run _tools/link_json.py links.json --dry-run
```

## Link Types

### Single file (`'file`)

Creates a symlink for one file. Target filename defaults to source filename.

```nickel
MyFile | Link = 'file {
    metadata = { description = "..." },
    source = {
      file = "data.csv",
      directory = "/path/to/source"
    },
    target = {
      file = "renamed.csv",  # optional, defaults to source filename
      directory = "%{env.local_task}/input"
    }
}
```

### Directory (`'dir`)

Creates a symlink for an entire directory.

```nickel
MyDir | Link = 'dir {
    metadata = { description = "..." },
    source = { directory = "/path/to/data" },
    target = { directory = "%{env.local_task}/input/data" }
}
```

### Multiple files (`'files`)

Creates symlinks for multiple files from the same source directory.

```nickel
Configs | Link = 'files {
    metadata = { description = "..." },
    source = {
      file = ["config1.yaml", "config2.yaml", "config3.yaml"],
      directory = "/path/to/configs"
    },
    target = { directory = "%{env.local_task}/config" }
}
```

## Metadata

Optional fields for documentation and tracking:

```nickel
metadata = {
  description = "Human-readable description",
  generated_by = "task_name",        # Which task creates this data
  used_by = ["task1", "task2"]       # Which tasks consume this data
}
```

## CLI Reference

### install.py

```
usage: install.py [-h] [--dest DEST] [--remote] [target_dir]

Install ResearchSetup linking tools into a project.

positional arguments:
  target_dir    Project directory to install into (default: current directory)

options:
  --dest DEST   Subdirectory for tools (default: _tools)
  --remote      Force download from GitHub even if local source exists
  -h, --help    Show help message
```

### link_json.py

```
usage: link_json.py [-h] [-d] [-v] config_file

Create symbolic links from a JSON/TOML configuration.

positional arguments:
  config_file      Path to the JSON/TOML configuration file

options:
  -d, --dry-run    Preview links without creating them
  -v, --verbose    Show additional details
  -h, --help       Show help message
```

## Repository Structure

```
ResearchSetup/
├── install.py                 # Installer script
├── src/
│   ├── python/
│   │   └── link_json.py       # Self-contained linker
│   └── nickel/
│       └── link_contracts.ncl # Type contracts
└── examples/
    └── census_of_governments.ncl  # Full example
```
