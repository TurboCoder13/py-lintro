# ascii-resizer

Resize and standardize ASCII art to consistent dimensions.

## Features

- **Braille art support**: Properly decodes Braille Unicode characters to pixels,
  resizes, and re-encodes
- **Aspect ratio preservation**: By default, scales content to fit while maintaining
  proportions
- **Multiple resize methods**: Nearest neighbor, bilinear, bicubic, and Lanczos
  interpolation
- **Multi-section files**: Handle files with multiple ASCII art pieces separated by
  blank lines
- **Auto-detection**: Automatically detects Braille art

## Installation

```bash
uv pip install -e .
```

## Usage

Run commands with `uv run ascii-resizer` or activate the virtual environment first.

### Resize ASCII art

```bash
# Resize all sections to default 65x30 and write to file
uv run ascii-resizer resize input.txt output.txt

# Modify file in place
uv run ascii-resizer resize input.txt --in-place

# Output to stdout
uv run ascii-resizer resize input.txt
```

### View file information

```bash
uv run ascii-resizer info input.txt
```

Example output:

```text
File: input.txt
Sections: 3
  Section 1: 40x20 chars (braille)
  Section 2: 55x25 chars (braille)
  Section 3: 30x15 chars (braille)
```

### Display sections

```bash
# Show all sections
uv run ascii-resizer show input.txt

# Show specific section
uv run ascii-resizer show input.txt -n 3
```

## How it works

For Braille art (U+2800-U+28FF):

1. **Decode**: Each Braille character represents a 2×4 pixel grid. The tool decodes the
   entire art to a bitmap.
2. **Resize**: Uses PIL/Pillow's image resizing with the selected interpolation method.
3. **Re-encode**: Converts the resized bitmap back to Braille characters.

This approach gives reliable, predictable results because it treats ASCII art as what it
really is: a rasterized image.

### Aspect ratio preservation

By default, content is scaled to fit within the target dimensions while maintaining its
original proportions. The resized content is then centered on the canvas. Use
`--stretch` to fill the entire target area (may distort the image).

## CLI Reference

### `resize`

Resize ASCII art to target dimensions.

| Option            | Default   | Description                                      |
| ----------------- | --------- | ------------------------------------------------ |
| `-w, --width`     | `65`      | Target width in characters                       |
| `-h, --height`    | `30`      | Target height in lines                           |
| `-m, --method`    | `nearest` | Interpolation: `nearest`, `bilinear`, `bicubic`, |
|                   |           | `lanczos`                                        |
| `-t, --threshold` | `128`     | Binarization threshold (0-255)                   |
| `-i, --in-place`  |           | Modify input file in place                       |
| `--stretch`       |           | Stretch to fill (don't preserve aspect ratio)    |

### `info`

Show file information including section count and dimensions.

### `show`

Display ASCII art sections.

| Option          | Description                           |
| --------------- | ------------------------------------- |
| `-n, --section` | Section number to display (1-indexed) |

## Resize methods

| Method     | Description                                        |
| ---------- | -------------------------------------------------- |
| `nearest`  | Best for pixel art, preserves hard edges (default) |
| `bilinear` | Smooth interpolation, good for general use         |
| `bicubic`  | Smoother than bilinear, may introduce artifacts    |
| `lanczos`  | Highest quality, best for downscaling              |

## Dependencies

- Python >= 3.11
- click >= 8.0
- numpy >= 1.24
- pillow >= 10.0
