"""Prettier-specific configuration options."""

from dataclasses import dataclass, field

from .base_tool_options import BaseToolOptions


@dataclass
class PrettierOptions(BaseToolOptions):
    """Prettier-specific configuration options.

    Attributes:
        print_width: Line width
        tab_width: Tab width
        use_tabs: Use tabs instead of spaces
        semi: Add semicolons
        single_quote: Use single quotes
        quote_props: Quote object properties
        jsx_single_quote: Use single quotes in JSX
        trailing_comma: Trailing comma style
        bracket_spacing: Add spaces inside brackets
        bracket_same_line: Put > on the same line as last prop
        arrow_parens: Arrow function parentheses
        end_of_line: End of line character
    """

    print_width: int | None = field(default=None)
    tab_width: int | None = field(default=None)
    use_tabs: bool | None = field(default=None)
    semi: bool | None = field(default=None)
    single_quote: bool | None = field(default=None)
    quote_props: str | None = field(default=None)
    jsx_single_quote: bool | None = field(default=None)
    trailing_comma: str | None = field(default=None)
    bracket_spacing: bool | None = field(default=None)
    bracket_same_line: bool | None = field(default=None)
    arrow_parens: str | None = field(default=None)
    end_of_line: str | None = field(default=None)
