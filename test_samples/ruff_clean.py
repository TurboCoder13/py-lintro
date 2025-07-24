"""Clean Python file for Ruff integration tests."""

def hello(name: str = "World") -> None:
    """Say hello to someone.
    
    Args:
        name: The name to greet.
    """
    print(f"Hello, {name}!")


if __name__ == "__main__":
    hello() 