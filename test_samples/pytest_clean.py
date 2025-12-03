"""Sample pytest test file with passing tests for testing."""

import pytest


def test_simple_pass():
    """Test that passes."""
    assert 1 == 1


def test_string_operations():
    """Test string operations."""
    text = "hello world"
    assert text.upper() == "HELLO WORLD"
    assert text.startswith("hello")
    assert text.endswith("world")


def test_list_operations():
    """Test list operations."""
    my_list = [1, 2, 3, 4, 5]
    assert len(my_list) == 5
    assert my_list[0] == 1
    assert my_list[-1] == 5
    assert 3 in my_list


def test_dict_operations():
    """Test dictionary operations."""
    my_dict = {"key1": "value1", "key2": "value2"}
    assert len(my_dict) == 2
    assert "key1" in my_dict
    assert my_dict["key1"] == "value1"
    assert my_dict.get("key2") == "value2"


def test_math_operations():
    """Test mathematical operations."""
    assert 2 + 2 == 4
    assert 10 - 5 == 5
    assert 3 * 4 == 12
    assert 15 / 3 == 5
    assert 2**3 == 8


def test_boolean_operations():
    """Test boolean operations."""
    assert True
    assert not False
    assert True and True
    assert True or False
    assert not (True and False)


def test_exception_handling():
    """Test exception handling."""
    with pytest.raises(ValueError):
        int("not_a_number")

    with pytest.raises(ZeroDivisionError):
        1 / 0

    with pytest.raises(KeyError):
        {}["missing_key"]


@pytest.fixture
def sample_data():
    """Sample data fixture."""
    return {"name": "test", "value": 42}


def test_fixture_usage():
    """Test using fixtures."""
    # This test is replaced by test_with_fixture below
    pass


def test_with_fixture(sample_data):
    """Test that uses the sample_data fixture."""
    assert sample_data["name"] == "test"
    assert sample_data["value"] == 42


@pytest.mark.parametrize(
    "value,expected",
    [
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
    ],
)
def test_parametrized(value, expected):
    """Test with parametrized values."""
    assert value == expected


def test_parametrized_wrapper():
    """Test with parametrized values."""
    # This test is replaced by test_parametrized above
    pass


@pytest.mark.slow
def test_slow_operation():
    """Test marked as slow."""
    assert True


@pytest.mark.integration
def test_integration():
    """Test marked as integration."""
    assert True


@pytest.mark.unit
def test_unit():
    """Test marked as unit."""
    assert True


def test_mark_decorators():
    """Test with mark decorators."""
    # Tests are now at module level above
    pass


async def async_function():
    """Async helper function."""
    return "async result"


def test_async_function():
    """Test async function."""
    # This test is replaced by test_async below
    pass


def test_async():
    """Test that uses async function."""
    import asyncio

    result = asyncio.run(async_function())
    assert result == "async result"


class TestClass:
    """Test class for class-based tests."""

    def test_method_one(self):
        """First test method."""
        assert True

    def test_method_two(self):
        """Second test method."""
        assert 1 + 1 == 2

    def test_method_three(self):
        """Third test method."""
        assert "hello" in "hello world"


def test_class_based():
    """Test class-based test."""
    # TestClass is now at module level above
    pass


# Global variable for setup/teardown tests
test_data = None


def setup_function():
    """Setup function for tests."""
    global test_data
    test_data = [1, 2, 3]


def teardown_function():
    """Teardown function for tests."""
    global test_data
    test_data = None


def test_setup_teardown():
    """Test with setup and teardown."""
    # Setup and teardown functions are now at module level above
    pass


def test_with_setup():
    """Test that uses setup data."""
    assert test_data == [1, 2, 3]
    assert len(test_data) == 3
