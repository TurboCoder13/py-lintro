"""Sample pytest test file with intentional failures for testing."""

import pytest


def test_simple_failure():
    """Test that intentionally fails."""
    assert 1 == 2, "This test should fail"


def test_division_by_zero():
    """Test that causes a division by zero error."""
    result = 1 / 0
    assert result > 0


def test_attribute_error():
    """Test that causes an AttributeError."""
    obj = None
    obj.some_attribute  # This will raise AttributeError


def test_key_error():
    """Test that causes a KeyError."""
    my_dict = {"key1": "value1"}
    my_dict["nonexistent_key"]  # This will raise KeyError


def test_type_error():
    """Test that causes a TypeError."""


def test_index_error():
    """Test that causes an IndexError."""
    my_list = [1, 2, 3]
    my_list[10]  # This will raise IndexError


def test_value_error():
    """Test that causes a ValueError."""
    int("not_a_number")  # This will raise ValueError


def test_runtime_error():
    """Test that causes a RuntimeError."""
    raise RuntimeError("This is a runtime error")


def test_custom_exception():
    """Test that causes a custom exception."""

    class CustomException(Exception):
        pass

    raise CustomException("This is a custom exception")


def test_multiple_assertions():
    """Test with multiple failing assertions."""
    assert 1 == 2, "First assertion fails"
    assert 3 == 4, "Second assertion fails"
    assert 5 == 6, "Third assertion fails"


def test_nested_failure():
    """Test with nested function calls that fail."""

    def inner_function():
        raise AssertionError("Inner function fails")

    def outer_function():
        inner_function()

    outer_function()


@pytest.fixture
def failing_fixture():
    """Fixture that fails."""
    raise AssertionError("Fixture fails")
    return "value"


def test_fixture_failure():
    """Test that fails due to fixture issues."""
    # This test will fail during fixture setup
    pass


def test_with_failing_fixture(failing_fixture):
    """Test that uses the failing fixture."""
    assert failing_fixture == "value"


@pytest.mark.parametrize(
    "value,expected",
    [
        (1, 1),  # This will pass
        (2, 3),  # This will fail
        (3, 4),  # This will fail
        (4, 4),  # This will pass
    ],
)
def test_parametrized(value, expected):
    """Test with parametrized values, some failing."""
    assert value == expected


def test_parametrized_failure():
    """Test with parametrized values, some failing."""
    # This test is replaced by test_parametrized above
    pass


def test_skip_test():
    """Test that gets skipped."""
    pytest.skip("This test is skipped")


def test_xfail_test():
    """Test that is expected to fail."""
    pytest.xfail("This test is expected to fail")
    raise AssertionError()  # This will fail but is expected


def test_timeout():
    """Test that might timeout."""
    import time

    time.sleep(10)  # This might cause timeout
    assert True
