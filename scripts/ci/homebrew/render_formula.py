#!/usr/bin/env python3
r"""Render Homebrew formula from template.

Usage:
    python3 render_formula.py \
        --tarball-url "https://..." \
        --tarball-sha "abc123" \
        --poet-resources poet_output.txt \
        --pydoclint-resource pydoclint.txt \
        --pydantic-resource pydantic.txt \
        --output Formula/lintro.rb
"""

import argparse
import sys
from pathlib import Path


def read_file_content(path: str) -> str:
    """Read content from file or stdin if path is '-'.

    Args:
        path: File path or '-' for stdin.

    Returns:
        File content as a string.
    """
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Render Homebrew formula from template",
    )
    parser.add_argument(
        "--template",
        default=str(
            Path(__file__).parent / "templates" / "lintro.rb.template",
        ),
        help="Path to template file",
    )
    parser.add_argument(
        "--tarball-url",
        required=True,
        help="Source tarball URL",
    )
    parser.add_argument(
        "--tarball-sha",
        required=True,
        help="Source tarball SHA256",
    )
    parser.add_argument(
        "--poet-resources",
        required=True,
        help="Path to poet resources file (or - for stdin)",
    )
    parser.add_argument(
        "--pydoclint-resource",
        required=True,
        help="Path to pydoclint resource stanza file",
    )
    parser.add_argument(
        "--pydantic-resource",
        required=True,
        help="Path to pydantic_core resource stanza file",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file (default: stdout)",
    )
    args = parser.parse_args()

    # Read template
    template = Path(args.template).read_text()

    # Validate all placeholders exist in template
    placeholders = [
        "{{TARBALL_URL}}",
        "{{TARBALL_SHA}}",
        "{{POET_RESOURCES}}",
        "{{PYDOCLINT_RESOURCE}}",
        "{{PYDANTIC_CORE_RESOURCE}}",
    ]
    for placeholder in placeholders:
        if placeholder not in template:
            print(
                f"Warning: Placeholder {placeholder} not found in template",
                file=sys.stderr,
            )

    # Read resources (strip trailing whitespace to avoid extra blank lines)
    poet_resources = read_file_content(args.poet_resources).rstrip()
    pydoclint_resource = read_file_content(args.pydoclint_resource).rstrip()
    pydantic_resource = read_file_content(args.pydantic_resource).rstrip()

    # Render template
    rendered = template.replace("{{TARBALL_URL}}", args.tarball_url)
    rendered = rendered.replace("{{TARBALL_SHA}}", args.tarball_sha)
    rendered = rendered.replace("{{POET_RESOURCES}}", poet_resources)
    rendered = rendered.replace("{{PYDOCLINT_RESOURCE}}", pydoclint_resource)
    rendered = rendered.replace("{{PYDANTIC_CORE_RESOURCE}}", pydantic_resource)

    # Output
    if args.output:
        Path(args.output).write_text(rendered)
        print(f"Formula written to {args.output}", file=sys.stderr)
    else:
        print(rendered)


if __name__ == "__main__":
    main()
