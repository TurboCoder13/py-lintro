"""CLI to normalize ASCII art files to a standard size.

Usage (via uv):
    uv run python -m lintro.utils.ascii_normalize_cli --width 80 --height 20

By default processes all .txt files under lintro/ascii-art.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from lintro.utils.formatting import normalize_ascii_file_sections


def _ascii_art_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "ascii-art"


def _write_sections(
    file_path: Path,
    sections: list[list[str]],
) -> None:
    # Join sections with a single blank line between them
    lines: list[str] = []
    for idx, sec in enumerate(sections):
        lines.extend(sec)
        if idx != len(sections) - 1:
            lines.append("")
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    """Normalize ASCII art files based on width/height and alignment.

    Returns:
        int: Zero on success, non-zero when the base directory is missing.
    """
    parser = argparse.ArgumentParser(description="Normalize ASCII art files.")
    parser.add_argument("files", nargs="*", help="Specific ASCII art files to process")
    parser.add_argument("--width", type=int, default=80)
    parser.add_argument("--height", type=int, default=20)
    parser.add_argument(
        "--align",
        choices=["left", "center", "right"],
        default="center",
    )
    parser.add_argument(
        "--valign",
        choices=["top", "middle", "bottom"],
        default="middle",
    )
    args = parser.parse_args()

    base_dir = _ascii_art_dir()
    if not base_dir.exists():
        print(f"ASCII art directory not found: {base_dir}")
        return 1

    targets: list[Path]
    if args.files:
        targets = [base_dir / f for f in args.files]
    else:
        targets = sorted(base_dir.glob("*.txt"))

    updated = 0
    for fp in targets:
        sections = normalize_ascii_file_sections(
            file_path=fp,
            width=args.width,
            height=args.height,
            align=args.align,
            valign=args.valign,
        )
        if not sections:
            print(f"Skipping (no sections or unreadable): {fp.name}")
            continue
        _write_sections(
            arg1=fp,
            arg2=sections,
        )
        updated += 1
        print(f"Normalized: {fp.name} -> {args.width}x{args.height}")

    print(f"Done. Updated {updated} file(s).")
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via CLI in practice
    raise SystemExit(main())
