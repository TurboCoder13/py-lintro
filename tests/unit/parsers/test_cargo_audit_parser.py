"""Unit tests for cargo-audit parser."""

from __future__ import annotations

import pytest
from assertpy import assert_that

from lintro.parsers.cargo_audit.cargo_audit_parser import parse_cargo_audit_output


@pytest.mark.parametrize(
    ("output", "expected_count"),
    [
        pytest.param(None, 0, id="none_input"),
        pytest.param("", 0, id="empty_string"),
        pytest.param("   \n\n  ", 0, id="whitespace_only"),
    ],
)
def test_parse_cargo_audit_output_empty_cases(
    output: str | None,
    expected_count: int,
) -> None:
    """Parser returns empty list for empty/None input.

    Args:
        output: The input to parse.
        expected_count: Expected number of issues.
    """
    result = parse_cargo_audit_output(output)
    assert_that(result).is_length(expected_count)


def test_parse_cargo_audit_output_no_vulnerabilities() -> None:
    """Parser returns empty list when no vulnerabilities found."""
    output = """{
        "vulnerabilities": {
            "count": 0,
            "list": []
        }
    }"""
    result = parse_cargo_audit_output(output)

    assert_that(result).is_length(0)


def test_parse_cargo_audit_output_single_vulnerability() -> None:
    """Parser extracts single vulnerability correctly."""
    output = """{
        "vulnerabilities": {
            "count": 1,
            "list": [
                {
                    "advisory": {
                        "id": "RUSTSEC-2021-0124",
                        "title": "Data race in crossbeam-deque",
                        "description": "A data race can occur in crossbeam-deque.",
                        "severity": "HIGH",
                        "url": "https://rustsec.org/advisories/RUSTSEC-2021-0124"
                    },
                    "package": {
                        "name": "crossbeam-deque",
                        "version": "0.7.3"
                    }
                }
            ]
        }
    }"""
    result = parse_cargo_audit_output(output)

    assert_that(result).is_length(1)
    assert_that(result[0].advisory_id).is_equal_to("RUSTSEC-2021-0124")
    assert_that(result[0].package_name).is_equal_to("crossbeam-deque")
    assert_that(result[0].package_version).is_equal_to("0.7.3")
    assert_that(result[0].severity).is_equal_to("HIGH")
    assert_that(result[0].file).is_equal_to("Cargo.lock")


def test_parse_cargo_audit_output_multiple_vulnerabilities() -> None:
    """Parser handles multiple vulnerabilities."""
    output = """{
        "vulnerabilities": {
            "count": 2,
            "list": [
                {
                    "advisory": {
                        "id": "RUSTSEC-2021-0001",
                        "title": "First vulnerability",
                        "severity": "MEDIUM"
                    },
                    "package": {
                        "name": "crate-a",
                        "version": "1.0.0"
                    }
                },
                {
                    "advisory": {
                        "id": "RUSTSEC-2022-0002",
                        "title": "Second vulnerability",
                        "severity": "CRITICAL"
                    },
                    "package": {
                        "name": "crate-b",
                        "version": "2.0.0"
                    }
                }
            ]
        }
    }"""
    result = parse_cargo_audit_output(output)

    assert_that(result).is_length(2)
    assert_that(result[0].advisory_id).is_equal_to("RUSTSEC-2021-0001")
    assert_that(result[0].severity).is_equal_to("MEDIUM")
    assert_that(result[1].advisory_id).is_equal_to("RUSTSEC-2022-0002")
    assert_that(result[1].severity).is_equal_to("CRITICAL")


def test_parse_cargo_audit_output_normalizes_severity() -> None:
    """Parser normalizes severity levels."""
    output = """{
        "vulnerabilities": {
            "count": 1,
            "list": [
                {
                    "advisory": {
                        "id": "RUSTSEC-2021-0001",
                        "title": "Test",
                        "severity": "moderate"
                    },
                    "package": {
                        "name": "test",
                        "version": "1.0.0"
                    }
                }
            ]
        }
    }"""
    result = parse_cargo_audit_output(output)

    assert_that(result).is_length(1)
    assert_that(result[0].severity).is_equal_to("MEDIUM")


def test_parse_cargo_audit_output_none_severity() -> None:
    """Parser handles RustSec 'none' severity level."""
    output = """{
        "vulnerabilities": {
            "count": 1,
            "list": [
                {
                    "advisory": {
                        "id": "RUSTSEC-2021-0001",
                        "title": "Informational advisory",
                        "severity": "none"
                    },
                    "package": {
                        "name": "test",
                        "version": "1.0.0"
                    }
                }
            ]
        }
    }"""
    result = parse_cargo_audit_output(output)

    assert_that(result).is_length(1)
    assert_that(result[0].severity).is_equal_to("LOW")


def test_parse_cargo_audit_output_invalid_json() -> None:
    """Parser handles invalid JSON gracefully."""
    output = "{invalid json}"
    result = parse_cargo_audit_output(output)

    assert_that(result).is_length(0)


def test_parse_cargo_audit_output_missing_advisory() -> None:
    """Parser handles missing advisory data gracefully."""
    output = """{
        "vulnerabilities": {
            "count": 1,
            "list": [
                {
                    "package": {
                        "name": "test",
                        "version": "1.0.0"
                    }
                }
            ]
        }
    }"""
    result = parse_cargo_audit_output(output)

    # Should skip entries without advisory data
    assert_that(result).is_length(0)


def test_parse_cargo_audit_output_json_with_extra_text() -> None:
    """Parser extracts JSON from output with extra text."""
    output = """Fetching advisory database...
Loading Cargo.lock...
{
    "vulnerabilities": {
        "count": 1,
        "list": [
            {
                "advisory": {
                    "id": "RUSTSEC-2021-0001",
                    "title": "Test"
                },
                "package": {
                    "name": "test",
                    "version": "1.0.0"
                }
            }
        ]
    }
}
Done."""
    result = parse_cargo_audit_output(output)

    assert_that(result).is_length(1)
    assert_that(result[0].advisory_id).is_equal_to("RUSTSEC-2021-0001")
