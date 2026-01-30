# ResearchSetup

Create symbolic links from source data directories to your research project using declarative Nickel templates.

## Overview

Instead of copying data or manually creating symlinks, define your links in a Nickel config file and run one command.

```
Nickel template (.ncl)  →  TOML/JSON  →  Python creates symlinks
```

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** - Python package runner
- **[Nickel](https://nickel-lang.org/)** - Configuration language

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Nickel (macOS)
brew install nickel

# Or with cargo
cargo install nickel-lang-cli
```

## Install

```bash
curl -fsSL https://github.com/eloualiche/ResearchSetup/releases/latest/download/install.py | uv run --script -
```

With options:
```bash
# Install to specific project
curl -fsSL .../install.py | uv run --script - /path/to/project

# Custom tools directory (default: _tools)
curl -fsSL .../install.py | uv run --script - /path/to/project --dest utils
```

### What gets installed

```
your-project/
└── _tools/
    ├── scripts/
    │   └── link_json.py           # Main linker script
    └── nickel/
        ├── link_contracts.ncl     # Type contracts
        └── links_template.ncl     # Your config (edit this)
```

## Usage

### 1. Define your links

Edit `_tools/nickel/links_template.ncl`:

```nickel
{
  # Link a directory
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

### 2. Export and create symlinks

```bash
# Export template to TOML
nickel export --format toml _tools/nickel/links_template.ncl > links.toml

# Create symlinks
uv run _tools/scripts/link_json.py links.toml

# Or preview first
uv run _tools/scripts/link_json.py links.toml --dry-run
```

## Link Types

### Directory (`'dir`)

```nickel
MyDir | Link = 'dir {
    metadata = { description = "..." },
    source = { directory = "/path/to/data" },
    target = { directory = "%{env.local_task}/input/data" }
}
```

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

## Snakemake Integration

```python
rule link_data:
    input:
        script = "_tools/scripts/link_json.py",
        template = "_tools/nickel/links_template.ncl"
    output:
        toml = "tmp/links.toml"
    shell:
        """
        nickel export --format toml {input.template} > {output.toml}
        uv run {input.script} {output.toml}
        """
```

### With dependency tracking

```python
rule link_data:
    input:
        template = "_tools/nickel/links_template.ncl"
    output:
        flag = touch("tmp/.links_created")
    shell:
        """
        nickel export --format toml {input.template} > tmp/links.toml
        uv run _tools/scripts/link_json.py tmp/links.toml
        """

rule analyze:
    input:
        links = "tmp/.links_created",
        data = "input/raw/data.csv"  # symlink created above
    output:
        "output/results.csv"
    # ...
```

## CLI Reference

### install.py

```
usage: install.py [-h] [--dest DIR] [--remote] [PROJECT_DIR]

positional arguments:
  PROJECT_DIR   Project directory (default: current directory)

options:
  --dest DIR    Tools subdirectory (default: _tools)
  --remote      Force download from GitHub
```

### link_json.py

```
usage: link_json.py [-h] [-d] [-v] CONFIG_FILE

positional arguments:
  CONFIG_FILE   Path to .json or .toml configuration

options:
  -d, --dry-run   Preview without creating links
  -v, --verbose   Show additional details
```

## Repository Structure

```
ResearchSetup/
├── install.py                 # Installer
├── src/
│   ├── python/
│   │   └── link_json.py       # Linker script
│   └── nickel/
│       └── link_contracts.ncl # Type contracts
└── examples/
    └── census_of_governments.ncl
```
