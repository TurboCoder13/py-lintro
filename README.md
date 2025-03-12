# Lintro

A comprehensive CLI tool that unifies various code formatting, linting, and quality assurance tools under a single command-line interface.

## Features

- Run multiple linting and formatting tools with a single command
- Standardized configuration and output formatting
- Consistent error handling
- Extensible architecture for adding new tools
- Intelligent conflict resolution between tools
- Configurable tool priorities and execution order

## Supported Tools

- Black (code formatting)
- isort (import sorting)
- flake8 (linting)
- darglint (docstring linting)
- hadolint (Dockerfile linting)
- mypy (static type checking)
- prettier (code formatting for multiple languages)
- pydocstyle (docstring style checking)
- pylint (Python linting)
- semgrep (semantic code pattern matching)
- terraform (Terraform formatting)
- yamllint (YAML linting)

## Installation

### From PyPI (not yet available)

```bash
# Using pip
pip install lintro

# Using uv
uv pip install lintro
```

### From Source

```bash
git clone https://github.com/yourusername/lintro.git
cd lintro
```

#### Using the installation script (recommended)

```bash
# Default installation (uses .venv in the current directory)
./install.sh

# Custom virtual environment location
echo "UV_VENV_PYTHON_PATH=~/.local/share/virtualenvs/lintro" > .env
./install.sh
```

#### Using Makefile

```bash
# Default installation (uses .venv in the current directory)
make setup

# Custom virtual environment location
make UV_VENV_PYTHON_PATH=~/.local/share/virtualenvs/lintro setup
```

#### Manual installation with uv

```bash
# Create and activate a virtual environment (default location)
uv venv
source .venv/bin/activate

# Create and activate a virtual environment (custom location)
mkdir -p ~/.local/share/virtualenvs
uv venv ~/.local/share/virtualenvs/lintro
source ~/.local/share/virtualenvs/lintro/bin/activate

# Install in development mode
uv pip install -e .

# Install development dependencies (optional)
uv pip install -r requirements-dev.txt
```

## Usage

### List available tools

```bash
lintro list-tools
```

### Format code (auto-fix where possible)

```bash
lintro fmt [PATH]
```

### Check code for issues without fixing

```bash
lintro check [PATH]
```

### Run specific tools

```bash
lintro fmt --tools black,isort [PATH]
lintro check --tools flake8,pylint,mypy [PATH]
```

### Exclude specific patterns

By default, Lintro excludes virtual environment directories. You can specify additional patterns to exclude:

```bash
lintro check --exclude "migrations,node_modules,dist" [PATH]
lintro fmt --exclude "migrations,node_modules,dist" [PATH]
```

### Include virtual environment directories

If you want to include virtual environment directories (which are excluded by default):

```bash
lintro check --include-venv [PATH]
lintro fmt --include-venv [PATH]
```

### Export output to a file

You can export the output to a file using the `--output` option:

```bash
lintro check --output report.txt [PATH]
lintro fmt --output changes.txt [PATH]
lintro list-tools --output tools.txt
```

When using the `--output` option, the detailed output will be displayed in both the console and written to the specified file.

### Use table formatting for output

You can use a nicely formatted table for the output using the `--table-format` option:

```bash
lintro check --table-format [PATH]
lintro fmt --table-format [PATH]
```

This option requires the `tabulate` package to be installed. If it's not installed, Lintro will fall back to the standard formatting.

To install tabulate:

```bash
pip install tabulate
```

You can combine the table format with the output file option:

```bash
lintro check --table-format --output report.txt [PATH]
```

### Group issues in the output

When using table formatting, you can choose how to group the issues in the output using the `--group-by` option:

```bash
# Group by file (default for check command)
lintro check --table-format --group-by file [PATH]

# Group by error code
lintro check --table-format --group-by code [PATH]

# No grouping (flat list)
lintro check --table-format --group-by none [PATH]

# Auto-grouping (default for fmt command) - intelligently chooses the best grouping method
lintro check --table-format --group-by auto [PATH]
lintro fmt --table-format --group-by auto [PATH]
```

The auto-grouping option intelligently chooses between file and code grouping based on the output:
- If there are more unique files than error codes (and few error code types), it groups by error code
- Otherwise, it groups by file

Grouping by file is useful when you want to fix issues file by file, while grouping by error code is helpful when you want to fix similar issues across multiple files.

## Tool-Specific Options

Lintro supports various tool-specific options that can be passed directly to the underlying tools:

### darglint

```bash
lintro check --darglint-timeout 20 [PATH]
```

### hadolint

```bash
lintro check --hadolint-timeout 20 [PATH]
```

### mypy

```bash
lintro check --mypy-config mypy.ini [PATH]
lintro check --mypy-python-version 3.9 [PATH]
lintro check --mypy-disallow-untyped-defs [PATH]
lintro check --mypy-disallow-incomplete-defs [PATH]
```

### pydocstyle

```bash
lintro check --pydocstyle-timeout 20 [PATH]
lintro check --pydocstyle-convention numpy [PATH]  # Options: pep257, numpy, google
```

### prettier

```bash
lintro check --prettier-timeout 60 [PATH]
```

### pylint

```bash
lintro check --pylint-rcfile .pylintrc [PATH]
```

### semgrep

```bash
lintro check --semgrep-config p/python [PATH]
```

### terraform

```bash
lintro check --terraform-recursive [PATH]
```

### yamllint

```bash
lintro check --yamllint-config .yamllint [PATH]
lintro check --yamllint-strict [PATH]
```

## Configuration

### Tool Configuration

Lintro uses the configuration files of the underlying tools. For example, it will respect:

- `pyproject.toml` (for Black and isort)
- `.flake8` (for Flake8)
- `.pylintrc` or `pylint.toml` (for Pylint)
- `.mypy.ini` or `mypy.ini` (for MyPy)
- `.pydocstyle` (for pydocstyle)
- `.prettierrc` (for Prettier)
- `.yamllint` (for yamllint)

### Virtual Environment Configuration

You can customize the location of the virtual environment by:

1. Setting the `UV_VENV_PYTHON_PATH` environment variable:
   ```bash
   export UV_VENV_PYTHON_PATH=~/.local/share/virtualenvs/lintro
   ```

2. Creating a `.env` file in the project root:
   ```
   UV_VENV_PYTHON_PATH=~/.local/share/virtualenvs/lintro
   ```

3. Passing the variable to make commands:
   ```bash
   make UV_VENV_PYTHON_PATH=~/.local/share/virtualenvs/lintro setup
   ```

4. Specifying the path directly with uv:
   ```bash
   uv venv ~/.local/share/virtualenvs/lintro
   ```

## Project Structure

```
lintro/
├── __init__.py         # Package initialization
├── cli.py              # Command-line interface
└── tools/              # Tool integrations
    ├── __init__.py     # Tool base class and registry
    ├── black.py        # Black integration
    ├── darglint.py     # Darglint integration
    ├── flake8.py       # Flake8 integration
    ├── hadolint.py     # Hadolint integration
    ├── isort.py        # isort integration
    ├── mypy.py         # MyPy integration
    ├── prettier.py     # Prettier integration
    ├── pydocstyle.py   # Pydocstyle integration
    ├── pylint.py       # Pylint integration
    ├── semgrep.py      # Semgrep integration
    ├── terraform.py    # Terraform integration
    └── yamllint.py     # YAMLLint integration
```

## Development

### Setting up a development environment

```bash
# Using Makefile (recommended)
make setup

# Using uv directly
uv venv ~/.local/share/virtualenvs/lintro
source ~/.local/share/virtualenvs/lintro/bin/activate
uv pip install -e .
uv pip install -r requirements-dev.txt
```

### Running tests

```bash
# Using Makefile
make test

# Using pytest directly
pytest
```

### Linting and formatting

```bash
# Check code style
make lint

# Format code
make format
```

### Cleaning up

```bash
# Remove build artifacts and cache files
make clean
```

## Extending Lintro

### Adding a New Tool

1. Create a new file in the `lintro/tools/` directory (e.g., `lintro/tools/mytool.py`)
2. Implement the `Tool` interface:

```python
from lintro.tools import Tool, ToolConfig

class MyTool(Tool):
    name = "mytool"
    description = "Description of my tool"
    can_fix = True  # or False if it can only check
    
    # Configure tool with conflict information
    config = ToolConfig(
        priority=50,  # Priority level for conflict resolution
        conflicts_with=[],  # List of tools this conflicts with
        file_patterns=["*.ext"],  # File patterns this tool applies to
    )

    def check(self, paths):
        # Implement check logic
        return True, "Success message"

    def fix(self, paths):
        # Implement fix logic
        return True, "Success message"
```

3. Register your tool in `lintro/tools/__init__.py`:

```python
from lintro.tools.mytool import MyTool

# Update AVAILABLE_TOOLS
AVAILABLE_TOOLS = {
    # ... existing tools ...
    "mytool": MyTool(),
}
```

## Tool Conflict Resolution

Lintro includes an intelligent conflict resolution system that prevents tools from contradicting each other. When multiple tools are specified, Lintro:

1. Identifies potential conflicts between tools
2. Resolves conflicts based on tool priorities
3. Executes tools in the optimal order

You can view potential conflicts between tools using:

```bash
lintro list-tools --show-conflicts
```

To ignore conflict resolution and run all specified tools:

```bash
lintro check --ignore-conflicts
lintro fmt --ignore-conflicts
```

## Style Guide

Lintro follows a comprehensive [Style Guide](STYLE_GUIDE.md) that outlines coding standards and best practices for the project. The style guide covers:

- Python code style
- Type hints
- Docstrings
- Function and method definitions
- Imports
- Error handling
- Variable naming
- Project structure
- Commit messages
- Testing
- Documentation
- Tool configuration
- Code review
- Continuous integration

## License

MIT 

