#!/usr/bin/env python3
"""Render Homebrew formula from template.

Usage:
    python3 render_formula.py \\
        --tarball-url "https://..." \\
        --tarball-sha "abc123" \\
        --poet-resources poet_output.txt \\
        --darglint-resource darglint.txt \\
        --pydantic-resource pydantic.txt \\
        --output Formula/lintro.rb
"""

import argparse
import sys
from pathlib import Path


def read_file_content(path: str) -> str:
    """Read content from file or stdin if path is '-'."""
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
        "--darglint-resource",
        required=True,
        help="Path to darglint resource stanza file",
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

    # Read resources
    poet_resources = read_file_content(args.poet_resources)
    darglint_resource = read_file_content(args.darglint_resource)
    pydantic_resource = read_file_content(args.pydantic_resource)

    # Render template
    rendered = template.replace("{{TARBALL_URL}}", args.tarball_url)
    rendered = rendered.replace("{{TARBALL_SHA}}", args.tarball_sha)
    rendered = rendered.replace("{{POET_RESOURCES}}", poet_resources)
    rendered = rendered.replace("{{DARGLINT_RESOURCE}}", darglint_resource)
    rendered = rendered.replace("{{PYDANTIC_CORE_RESOURCE}}", pydantic_resource)

    # Output
    if args.output:
        Path(args.output).write_text(rendered)
        print(f"Formula written to {args.output}", file=sys.stderr)
    else:
        print(rendered)


if __name__ == "__main__":
    main()
