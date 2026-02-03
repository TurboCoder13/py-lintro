# TSC (TypeScript Compiler) Tool Analysis

## Overview

TSC is the TypeScript compiler that performs static type checking on TypeScript files.
This analysis compares Lintro's wrapper with core tsc behavior.

## Core Tool Capabilities

- Static type checking with full TypeScript type system
- Config discovery: `tsconfig.json` with `extends` chain support
- Build modes: `--build` for composite projects, `--watch` for development
- Output: JavaScript emission, declaration files, sourcemaps
- Flags: `--strict`, `--noEmit`, `--skipLibCheck`, `--project`, `--target`, `--module`,
  `--moduleResolution`, `--paths`, `--baseUrl`, and 100+ compiler options
- Incremental compilation with `--incremental` and `--tsBuildInfoFile`
- Project references for monorepo support

## Lintro Implementation Analysis

### ✅ Preserved Features

- ✅ Invokes tsc with `--noEmit --pretty false` for type checking without output
- ✅ Respects native `tsconfig.json` compiler options (auto-discovered or via
  `--project`)
- ✅ **File targeting works even with tsconfig.json** (see below)
- ✅ Supports `--strict` mode toggle
- ✅ Supports `--skipLibCheck` for faster checks (enabled by default)
- ✅ File discovery for `*.ts`, `*.tsx`, `*.mts`, `*.cts`
- ✅ Intelligent command fallback: direct `tsc` -> `bunx tsc` -> `npx tsc`
- ✅ Parses tsc output into structured `ToolResult` with file/line/column/code

### File Targeting Behavior

**The Problem:** Native tsc ignores CLI file arguments when `tsconfig.json` exists,
instead checking all files defined in the config's `include`/`files` patterns.

**Lintro's Solution:** By default, lintro respects your file selection even when
`tsconfig.json` exists. This is achieved by creating a temporary tsconfig that:

1. Extends your project's `tsconfig.json` (preserving all compiler options)
2. Overrides `include` to target only the files you specified

```bash
# Check only specific files (default behavior - lintro respects file targeting)
lintro check src/utils.ts src/helpers.ts --tools tsc
# → Creates temp config extending tsconfig.json but only checking these 2 files

# Check all files defined in tsconfig.json (native behavior)
lintro check . --tools tsc --tool-options "tsc:use_project_files=True"
# → Uses tsconfig.json as-is, checks all files in include/files patterns
```

This gives you the best of both worlds:

- **Default:** Lintro-style file targeting with tsconfig.json compiler options
- **Opt-in:** Native tsconfig.json file selection when needed

### ⚠️ Limited / Missing

**Build & Watch Modes:**

- ❌ No `--watch` mode (continuous compilation)
- ❌ No `--build` mode (composite project building)
- ❌ No `--incremental` caching (each run is fresh)

**Output Generation:**

- ❌ No JavaScript emission (always uses `--noEmit`)
- ❌ No declaration file generation (`--declaration`, `--declarationMap`)
- ❌ No sourcemap generation (`--sourceMap`, `--inlineSourceMap`)
- ❌ No output directory control (`--outDir`, `--outFile`)

**Compiler Options (config-file-only):**

- ⚠️ `target`, `module`, `moduleResolution` - must be set in tsconfig.json
- ⚠️ `paths`, `baseUrl`, `rootDir`, `rootDirs` - must be set in tsconfig.json
- ⚠️ `lib`, `types`, `typeRoots` - must be set in tsconfig.json
- ⚠️ `esModuleInterop`, `allowSyntheticDefaultImports` - must be set in tsconfig.json
- ⚠️ `jsx`, `jsxFactory`, `jsxFragmentFactory` - must be set in tsconfig.json
- ⚠️ `experimentalDecorators`, `emitDecoratorMetadata` - must be set in tsconfig.json
- ⚠️ All other `compilerOptions` not exposed via `--tool-options`

**Advanced Features:**

- ❌ No project references support
- ❌ No plugins configuration
- ❌ No `--generateTrace` performance profiling
- ❌ No custom diagnostic formatting
- ❌ No `--listFiles`, `--listEmittedFiles` introspection

### 🚀 Enhancements

- ✅ Safe timeout handling (default 60s) with structured timeout result
- ✅ Auto config discovery prioritizes `tsconfig.json` in working directory
- ✅ **Smart file targeting** via temp tsconfig (preserves compiler options)
- ✅ Normalized `ToolResult` with parsed issues from `tsc_parser`
- ✅ Priority 82, tool type `LINTER | TYPE_CHECKER`, same as mypy
- ✅ Windows path normalization in parser output
- ✅ Graceful handling when tsc is not installed with helpful install hints
- ✅ **Dependency error categorization** - separates missing module errors from type
  errors
- ✅ **Auto-install support** - optionally install Node.js deps before running tsc

## Dependency Error Handling

Lintro intelligently categorizes tsc errors to distinguish between actual type errors
and errors caused by missing dependencies (e.g., when `node_modules` is not installed).

### Error Categories

**Dependency errors** (TS2307, TS2688, TS7016):

- `TS2307`: Cannot find module 'X' or its corresponding type declarations
- `TS2688`: Cannot find type definition file for 'X'
- `TS7016`: Could not find a declaration file for module 'X'

**Type errors** (all other codes):

- Actual TypeScript type checking issues in your code

### Output Example

When dependency errors are detected, Lintro shows them separately with actionable
guidance:

```text
Results: tsc
├── Type errors: 3
│   └── src/utils.ts:15 - Type 'string' not assignable to 'number'
│   └── ...
└── Missing dependencies: 4
    └── vite/client, react, @types/node, ...

    Suggestions:
    - Run 'bun install' or 'npm install'
    - Use '--auto-install' flag
```

### Auto-Install Dependencies

Use the `--auto-install` flag to automatically install Node.js dependencies before
running tsc:

```bash
# Auto-install deps then run tsc
lintro check src/ --tools tsc --auto-install

# Enable globally in config
# .lintro-config.yaml
execution:
  auto_install_deps: true
```

**Package manager preference:**

1. `bun install --frozen-lockfile` (falls back to `bun install`)
2. `npm ci` (falls back to `npm install`)

**Note:** In Docker, dependencies are auto-installed by default when the container
starts

## Usage Comparison

```bash
# Core tsc - type check only (checks all files in tsconfig.json)
tsc --noEmit

# Core tsc - with specific config
tsc --project tsconfig.app.json --noEmit

# Lintro wrapper - check specific files (respects file targeting)
lintro check src/utils.ts --tools tsc

# Lintro wrapper - check directory (finds all .ts/.tsx files)
lintro check src/ --tools tsc

# Lintro wrapper - use tsconfig.json file selection (native behavior)
lintro check . --tools tsc --tool-options "tsc:use_project_files=True"

# Lintro wrapper - enable strict mode override
lintro check src/ --tools tsc --tool-options "tsc:strict=True"

# Lintro wrapper - use specific config file
lintro check src/ --tools tsc --tool-options "tsc:project=tsconfig.build.json"
```

## Configuration Strategy

- **File targeting preserved:** Lintro respects your file selection by default
- **Compiler options inherited:** All settings from `tsconfig.json` are preserved
- **No config injection:** Lintro cannot modify tsconfig.json settings; tool is "Native
  only"
- **Tool options available:**
  - `tsc:project` (string) - path to tsconfig.json file
  - `tsc:strict` (bool) - enable `--strict` flag
  - `tsc:skip_lib_check` (bool) - enable `--skipLibCheck` (default: true)
  - `tsc:use_project_files` (bool) - use tsconfig.json's include/files patterns instead
    of lintro's file targeting (default: false)
  - `tsc:timeout` (int) - execution timeout in seconds (default: 60)
- **Config display:** `lintro config -v` shows parsed tsconfig.json compilerOptions

## Priority and Conflicts

- **Priority:** 82 (runs after formatters/linters, before tests)
- **Tool Type:** LINTER | TYPE_CHECKER
- **Conflicts:** None
- **Complements:** oxlint, oxfmt, prettier (formatting/linting)

## Recommendations

- **Use Lintro** when you want quick type checking integrated into a multi-tool workflow
  with normalized output and timeout safety.
- **Use core tsc directly** when you need:
  - Watch mode for development (`tsc --watch`)
  - Build mode for composite projects (`tsc --build`)
  - Incremental compilation for large projects
  - JavaScript/declaration file output
  - Fine-grained compiler option control beyond tsconfig.json
  - Project references in monorepos
