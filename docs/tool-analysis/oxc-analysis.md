# Oxc Tools Analysis (oxlint + oxfmt)

## Overview

The Oxc (Oxidation Compiler) project provides extremely fast JavaScript/TypeScript tooling
written in Rust. Lintro integrates two Oxc tools:

- **oxlint**: Linter (50-100x faster than ESLint, 655+ built-in rules)
- **oxfmt**: Formatter (30x faster than Prettier)

This analysis compares Lintro's wrapper implementations with the core tools.

---

## Oxlint (Linter)

### Core Capabilities

- **Linting**: 655+ rules covering ESLint, TypeScript, React, JSX-a11y, Unicorn, and more
- **Performance**: Extremely fast execution (50-100x faster than ESLint)
- **Auto-fixing**: Many rules support automatic fixes via `--fix`
- **JSON output**: Machine-readable output with `--format json`
- **Configuration**: `.oxlintrc.json` or command-line options
- **TypeScript**: Native TypeScript support without additional configuration

### Lintro Implementation

**Preserved Features:**

- Linting via `oxlint --format json`
- Auto-fixing via `oxlint --fix`
- Configuration file support (`.oxlintrc.json`)
- File patterns: `*.js`, `*.ts`, `*.jsx`, `*.tsx`, `*.vue`, `*.svelte`, `*.astro`

**Configuration Options:**

- `exclude_patterns`: List of patterns to exclude
- `quiet`: Suppress warnings, only report errors
- `timeout`: Configurable execution timeout
- `verbose_fix_output`: Include raw output in fix results
- `config`: Path to Oxlint config file (--config)
- `tsconfig`: Path to tsconfig.json for TypeScript support (--tsconfig)
- `allow`: Rules to allow/turn off (--allow)
- `deny`: Rules to deny/report as errors (--deny)
- `warn`: Rules to warn on (--warn)

**Limited/Missing Features:**

- No plugin enabling flags (`--react-perf-plugin`, `--nextjs-plugin`)
- No watch mode (`--watch`)
- No cache control

### Usage Comparison

```bash
# Core oxlint
oxlint src/
oxlint --deny no-debugger --allow no-console src/
oxlint --fix src/
```

```python
# Lintro wrapper
oxlint_plugin = get_plugin("oxlint")
result = oxlint_plugin.check(["src/"])
result = oxlint_plugin.fix(["src/"])
oxlint_plugin.set_options(quiet=True, exclude_patterns=["node_modules"])
```

### Rule Categories

| Category                | Description                   |
| ----------------------- | ----------------------------- |
| **ESLint**              | Core JavaScript linting rules |
| **typescript-eslint**   | TypeScript-specific rules     |
| **eslint-plugin-react** | React best practices          |
| **jsx-a11y**            | Accessibility rules for JSX   |
| **unicorn**             | Various helpful rules         |
| **import**              | Import/export validation      |

---

## Oxfmt (Formatter)

### Oxfmt Core Capabilities

- **Formatting**: JS, TS, JSX, TSX, JSON, CSS, SCSS, HTML, Markdown, YAML, TOML, GraphQL
- **Performance**: Approximately 30x faster than Prettier
- **Check mode**: Verify formatting via `--check --list-different`
- **Write mode**: Format in place via `--write`
- **Prettier compatibility**: Aims for Prettier-compatible output

### Oxfmt Lintro Implementation

**Preserved Features:**

- Check mode via `oxfmt --check --list-different`
- Fix mode via `oxfmt --write`
- Configuration file support (`.oxfmtrc.json`, `.oxfmtrc.jsonc`)
- Extensive file patterns for all supported types

**Configuration Options:**

- `timeout`: Configurable execution timeout
- `verbose_fix_output`: Include raw output in fix results
- `config`: Path to oxfmt config file (--config)
- `ignore_path`: Path to ignore file (--ignore-path)
- `print_width`: Line width (--print-width)
- `tab_width`: Tab width (--tab-width)
- `use_tabs`: Use tabs instead of spaces (--use-tabs / --no-use-tabs)
- `semi`: Add semicolons (--semi / --no-semi)
- `single_quote`: Use single quotes (--single-quote / --no-single-quote)

**Limited/Missing Features:**

- No stdin/stdout piping support
- No explicit parser selection

### Oxfmt Usage Comparison

```bash
# Core oxfmt
oxfmt --check src/
oxfmt --write src/
```

```python
# Lintro wrapper
oxfmt_plugin = get_plugin("oxfmt")
result = oxfmt_plugin.check(["src/"])
result = oxfmt_plugin.fix(["src/"])
```

### Supported File Types

| Category       | Extensions                    |
| -------------- | ----------------------------- |
| **JavaScript** | `.js`, `.mjs`, `.cjs`, `.jsx` |
| **TypeScript** | `.ts`, `.mts`, `.cts`, `.tsx` |
| **JSON**       | `.json`, `.jsonc`             |
| **CSS**        | `.css`, `.scss`, `.less`      |
| **HTML**       | `.html`, `.vue`               |
| **Markdown**   | `.md`, `.mdx`                 |
| **Config**     | `.yaml`, `.yml`, `.toml`      |
| **GraphQL**    | `.graphql`                    |

---

## Configuration

### Oxlint Configuration

Example `.oxlintrc.json`:

```json
{
  "rules": {
    "no-debugger": "error",
    "no-console": "warn",
    "eqeqeq": "error"
  },
  "plugins": ["react", "unicorn"],
  "ignorePatterns": ["dist/**", "node_modules/**"]
}
```

### Oxfmt Configuration

Example `.oxfmtrc.json`:

```json
{
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5"
}
```

---

## Recommendations

### When to Use Core Tools Directly

- Need maximum configuration flexibility
- Require specific plugins or formatting options
- Want watch mode for development
- Need stdin/stdout piping

### When to Use Lintro Wrapper

- Part of multi-tool linting/formatting pipeline
- Need consistent issue reporting across tools
- Want Python object integration
- Require standardized error handling and timeout protection

---

## Migration Guide

### From ESLint to Oxlint

1. Install: `npm install -g oxlint` or `bun add -g oxlint`
2. Run oxlint alongside ESLint to compare results
3. Create `.oxlintrc.json` for custom rule configuration
4. Update CI/CD (keep ESLint as fallback initially)
5. Remove ESLint once confident

**Rule Mapping** (most rules have identical names):

| ESLint Rule      | Oxlint Rule      |
| ---------------- | ---------------- |
| `no-debugger`    | `no-debugger`    |
| `no-console`     | `no-console`     |
| `eqeqeq`         | `eqeqeq`         |
| `no-unused-vars` | `no-unused-vars` |

### From Prettier to Oxfmt

1. Install: `npm install -g oxfmt` or `bun add -g oxfmt`
2. Run oxfmt alongside Prettier to compare output
3. Create `.oxfmtrc.json` matching your `.prettierrc`
4. Update CI/CD and editor configurations

**Configuration Mapping**:

| Prettier Option  | Oxfmt Option     |
| ---------------- | ---------------- |
| `printWidth`     | `printWidth`     |
| `tabWidth`       | `tabWidth`       |
| `useTabs`        | `useTabs`        |
| `semi`           | `semi`           |
| `singleQuote`    | `singleQuote`    |
| `trailingComma`  | `trailingComma`  |
| `bracketSpacing` | `bracketSpacing` |

### From Biome to Oxc

1. Install both oxlint and oxfmt
2. Replace `biome lint` with `oxlint`
3. Replace `biome format` with `oxfmt --write`
4. Replace `biome check` with `oxfmt --check`
5. Update configuration files

| Biome Command          | Oxc Equivalent                   |
| ---------------------- | -------------------------------- |
| `biome lint`           | `oxlint`                         |
| `biome format`         | `oxfmt --write`                  |
| `biome format --check` | `oxfmt --check --list-different` |
| `biome ci`             | `oxlint && oxfmt --check`        |

---

## Out of Scope for Lintro

The Oxc project includes additional components that are not integrated into Lintro:

| Component       | Purpose             | Reason for Exclusion             |
| --------------- | ------------------- | -------------------------------- |
| **Parser**      | AST parsing library | Internal library, not a CLI tool |
| **Transformer** | Code transpilation  | Build tool, not lint/format      |
| **Resolver**    | Module resolution   | Internal library, not a CLI tool |
| **Minifier**    | Code minification   | Build tool, not lint/format      |

These components are intended for use by other tools and build systems, not for direct
invocation in a linting/formatting workflow.

---

## Limitations and Workarounds

### Oxlint Limitations

| Limitation               | Workaround                            |
| ------------------------ | ------------------------------------- |
| No plugin enabling flags | Configure plugins in `.oxlintrc.json` |
| No watch mode via Lintro | Use `oxlint --watch` directly         |
| No cache control         | Use native oxlint cache options       |

### Oxfmt Limitations

| Limitation                  | Workaround                      |
| --------------------------- | ------------------------------- |
| No stdin support via Lintro | Use `oxfmt` directly for piping |
| No explicit parser override | Use appropriate file extensions |

---

## Future Enhancement Opportunities

### Oxlint Enhancements

1. Plugin enable/disable flags at runtime (`--react-perf-plugin`, etc.)
2. Watch mode integration
3. Cache control options

### Oxfmt Enhancements

1. Stdin/stdout support for piping
2. Diff output mode
3. Explicit parser selection
