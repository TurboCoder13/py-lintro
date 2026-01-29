# Troubleshooting

This guide covers common issues and their solutions when using Lintro.

## Common Issues

### "Command not found: lintro"

**Cause**: Lintro is not installed or not in your PATH.

**Solution**: Ensure Lintro is installed correctly:

```bash
pip install lintro
# or with pipx (recommended for CLI tools)
pipx install lintro
# or for development
pip install -e .
```

If using pipx, ensure `~/.local/bin` is in your PATH.

---

### "Tool not found" errors

**Cause**: The underlying tool (e.g., ruff, prettier) is not installed on your system.

**Solution**: Install the required tools or use Docker:

```bash
# Install tools individually
pip install ruff pydoclint
npm install -g prettier
pip install yamllint

# Or use Docker (recommended - includes all tools)
docker run --rm -v $(pwd):/code ghcr.io/lgtm-hq/py-lintro:latest check
```

See [Getting Started](getting-started.md) for complete installation instructions.

---

### Permission errors on Windows

**Cause**: Windows may require elevated privileges for certain operations.

**Solution**: Run as administrator or use WSL:

```bash
# Use WSL for better compatibility
wsl
pip install lintro
```

WSL provides a Linux environment with better tool compatibility.

---

### Docker permission issues

**Cause**: Your user is not in the docker group.

**Solution**: Add your user to the docker group:

```bash
sudo usermod -aG docker $USER
# Log out and back in for changes to take effect
```

---

### Slow performance

**Cause**: Scanning large directories or running all tools unnecessarily.

**Solution**: Use exclude patterns and specific tools:

```bash
# Exclude large directories
lintro check --exclude "node_modules,venv,.git,dist,build"

# Run specific tools only
lintro check --tools ruff,prettier
```

---

### Configuration not being applied

**Cause**: Lintro may not be finding your configuration file.

**Solution**: Check configuration resolution order:

1. CLI arguments (highest priority)
2. `.lintro-config.yaml` in current directory
3. `pyproject.toml` `[tool.lintro]` section
4. Default settings

Verify your config is being loaded:

```bash
lintro check --verbose
```

See [Configuration](configuration.md) for detailed configuration options.

---

### Output format issues

**Cause**: Terminal doesn't support colors or encoding issues.

**Solution**: Adjust output settings:

```bash
# Disable colors
lintro check --no-color

# Use simple output format
lintro check --output-format simple

# Force UTF-8 encoding
export PYTHONIOENCODING=utf-8
lintro check
```

---

### Tool version conflicts

**Cause**: Different versions of tools may produce different results.

**Solution**: Pin tool versions in your project:

```bash
# Check installed versions
lintro list-tools --verbose

# Use Docker for consistent versions
docker run --rm -v $(pwd):/code ghcr.io/lgtm-hq/py-lintro:latest check
```

---

## Getting Help

If your issue isn't covered here:

- **Documentation**: Check the [documentation directory](./) for detailed guides
- **Bug Reports**: Use the
  [bug report template](https://github.com/lgtm-hq/py-lintro/issues/new?template=bug_report.md)
- **Questions**: Use the
  [question template](https://github.com/lgtm-hq/py-lintro/issues/new?template=question.md)
- **Feature Requests**: Use the
  [feature request template](https://github.com/lgtm-hq/py-lintro/issues/new?template=feature_request.md)

## Reporting Bugs

When reporting bugs, please include:

1. Lintro version (`lintro --version`)
2. Python version (`python --version`)
3. Operating system
4. Complete error message
5. Minimal reproduction steps
6. Configuration file (if applicable)
