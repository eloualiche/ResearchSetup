# ResearchSetup

Create symbolic links from source data directories to your research project using declarative Nickel templates.

## Overview

Instead of copying data or manually creating symlinks, define your links in a Nickel config file and run one command.

```
Nickel template (.ncl)  →  JSON  →  Python creates symlinks
```

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** - Python package runner
- **[Nickel](https://nickel-lang.org/)** - Configuration language

```bash
# Install Nickel (macOS)
brew install nickel

# Or with cargo
cargo install nickel-lang-cli
```

## Install

```bash
# Download and run directly (installs to current directory)
curl -fsSL https://raw.githubusercontent.com/eloualiche/ResearchSetup/main/install.py | uv run --script -

# Install to specific project
curl -fsSL https://raw.githubusercontent.com/eloualiche/ResearchSetup/main/install.py | uv run --script - /path/to/project

# Custom tools location (default: _tools/)
curl -fsSL https://raw.githubusercontent.com/eloualiche/ResearchSetup/main/install.py | uv run --script - . --dest utils
```

If you have the repo cloned locally:

```bash
uv run install.py /path/to/project
```

## Usage

After installing, your project will have:

```
your-project/
├── link.py                    # Convenience wrapper
└── _tools/                    # (or your --dest location)
    ├── link_json.py           # Main linker script
    ├── nickel/
    │   └── link_contracts.ncl # Type contracts
    └── templates/
        └── links.ncl          # Your link definitions
```

### 1. Define links

Edit `_tools/templates/links.ncl`:

```nickel
{
  RawData | Link = 'dir {
      metadata = { description = "Raw experiment data." },
      source = { directory = "/data/shared/experiment_2024" },
      target = { directory = "%{env.local_task}/input/raw" }
  },

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

### 2. Create symlinks

```bash
uv run link.py              # Create all links
uv run link.py --dry-run    # Preview only
uv run link.py --verbose    # Show details
```

Or manually:

```bash
nickel export --format json _tools/templates/links.ncl > links.json
uv run _tools/link_json.py links.json
```

## Link Types

### Single file (`'file`)

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

```nickel
MyDir | Link = 'dir {
    metadata = { description = "..." },
    source = { directory = "/path/to/data" },
    target = { directory = "%{env.local_task}/input/data" }
}
```

### Multiple files (`'files`)

```nickel
Configs | Link = 'files {
    metadata = { description = "..." },
    source = {
      file = ["config1.yaml", "config2.yaml"],
      directory = "/path/to/configs"
    },
    target = { directory = "%{env.local_task}/config" }
}
```

## Metadata

Optional fields for documentation:

```nickel
metadata = {
  description = "...",
  generated_by = "task1",      # string or array
  used_by = ["task2", "task3"] # string or array
}
```

## Source Files

This repo contains:

```
ResearchSetup/
├── install.py                 # Installer script
├── src/
│   ├── python/
│   │   └── link_json.py       # Self-contained linker
│   └── nickel/
│       └── link_contracts.ncl # Type contracts
└── examples/
    └── census_of_governments.ncl
```
