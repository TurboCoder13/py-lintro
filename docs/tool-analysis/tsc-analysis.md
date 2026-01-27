# TSC (TypeScript Compiler) Tool Analysis

## Overview

TSC is the TypeScript compiler that performs static type checking on TypeScript files. This
analysis compares Lintro's wrapper with core tsc behavior.

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

### Preserved Features

- Invokes tsc with `--noEmit --pretty false` for type checking without output
- Respects native `tsconfig.json` configuration (auto-discovered or via `--project`)
- Supports `--strict` mode toggle
- Supports `--skipLibCheck` for faster checks (enabled by default)
- File discovery for `*.ts`, `*.tsx`, `*.mts`, `*.cts`
- Intelligent command fallback: direct `tsc` -> `bunx tsc` -> `npx tsc`
- Parses tsc output into structured `ToolResult` with file/line/column/code

### Limited / Missing

**Build & Watch Modes:**

- No `--watch` mode (continuous compilation)
- No `--build` mode (composite project building)
- No `--incremental` caching (each run is fresh)

**Output Generation:**

- No JavaScript emission (always uses `--noEmit`)
- No declaration file generation (`--declaration`, `--declarationMap`)
- No sourcemap generation (`--sourceMap`, `--inlineSourceMap`)
- No output directory control (`--outDir`, `--outFile`)

**Compiler Options (config-file-only):**

- `target`, `module`, `moduleResolution` - must be set in tsconfig.json
- `paths`, `baseUrl`, `rootDir`, `rootDirs` - must be set in tsconfig.json
- `lib`, `types`, `typeRoots` - must be set in tsconfig.json
- `esModuleInterop`, `allowSyntheticDefaultImports` - must be set in tsconfig.json
- `jsx`, `jsxFactory`, `jsxFragmentFactory` - must be set in tsconfig.json
- `experimentalDecorators`, `emitDecoratorMetadata` - must be set in tsconfig.json
- All other `compilerOptions` not exposed via `--tool-options`

**Advanced Features:**

- No project references support
- No plugins configuration
- No `--generateTrace` performance profiling
- No custom diagnostic formatting
- No `--listFiles`, `--listEmittedFiles` introspection

### Enhancements

- Safe timeout handling (default 60s) with structured timeout result
- Auto config discovery prioritizes `tsconfig.json` in working directory
- Normalized `ToolResult` with parsed issues from `tsc_parser`
- Priority 82, tool type `LINTER | TYPE_CHECKER`, same as mypy
- Windows path normalization in parser output
- Graceful handling when tsc is not installed with helpful install hints

## Usage Comparison

```bash
# Core tsc - type check only
tsc --noEmit

# Core tsc - with specific config
tsc --project tsconfig.app.json --noEmit

# Lintro wrapper - uses tsconfig.json automatically
lintro check src/ --tools tsc

# Lintro wrapper - enable strict mode override
lintro check src/ --tools tsc --tool-options "tsc:strict=True"

# Lintro wrapper - use specific config
lintro check src/ --tools tsc --tool-options "tsc:project=tsconfig.build.json"
```

## Configuration Strategy

- **Native config preferred:** If `tsconfig.json` exists, tsc uses it automatically
- **No config injection:** Lintro cannot modify tsconfig.json settings; tool is "Native only"
- **Tool options available:**
  - `tsc:project` (string) - path to tsconfig.json file
  - `tsc:strict` (bool) - enable `--strict` flag
  - `tsc:skip_lib_check` (bool) - enable `--skipLibCheck` (default: true)
  - `tsc:timeout` (int) - execution timeout in seconds (default: 60)
- **Config display:** `lintro config -v` shows parsed tsconfig.json compilerOptions

## Priority and Conflicts

- **Priority:** 82 (runs after formatters/linters, before tests)
- **Tool Type:** LINTER | TYPE_CHECKER
- **Conflicts:** None
- **Complements:** biome, prettier (formatting), eslint (linting)

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
