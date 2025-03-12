# Lintro

A comprehensive CLI tool that unifies various code formatting, linting, and quality assurance tools under a single command-line interface.

## Features

- Run multiple linting and formatting tools with a single command
- Standardized configuration and output formatting
- Consistent error handling
- Extensible architecture for adding new tools

## Supported Tools

- Black (code formatting)
- isort (import sorting)
- flake8 (linting)

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
lintro check --tools flake8 [PATH]
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

## Configuration

### Tool Configuration

Lintro uses the configuration files of the underlying tools. For example, it will respect:

- `pyproject.toml` (for Black and isort)
- `.flake8` (for Flake8)

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
    ├── flake8.py       # Flake8 integration
    └── isort.py        # isort integration
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
from lintro.tools import Tool

class MyTool(Tool):
    name = "mytool"
    description = "Description of my tool"
    can_fix = True  # or False if it can only check

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

## License

MIT 

