#!/bin/bash

# test-docker.sh - Test the lintro Docker setup
#
# This script builds the Docker image and runs a simple test to verify
# that lintro works correctly in the Docker container.

set -e

echo "Building Docker image..."
docker build -t lintro:test .

echo "Testing lintro in Docker..."
docker run --rm lintro:test list-tools

echo "Testing lintro with a sample file..."
echo 'def test_function():
    """This is a test function."""
    print("Hello, world!")
' > test_sample.py

docker run --rm -v "$(pwd):/code" lintro:test check test_sample.py --tools black,flake8,pylint --table-format

echo "Cleaning up..."
rm test_sample.py

echo "Docker test completed successfully!" 