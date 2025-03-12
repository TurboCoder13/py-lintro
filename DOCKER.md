# Lintro Docker Usage

This document explains how to use Lintro with Docker, which allows you to run Lintro without installing all the dependencies directly on your system.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, for using the docker-compose.yml file)

## Quick Start

The easiest way to use Lintro with Docker is to use the provided shell script:

```bash
# Make the script executable (first time only)
chmod +x lintro-docker.sh

# Run lintro commands
./lintro-docker.sh check --table-format
./lintro-docker.sh fmt --tools black,isort
./lintro-docker.sh list-tools
```

The script will automatically build the Docker image if it doesn't exist and run Lintro with your specified arguments.

## Manual Docker Usage

If you prefer to use Docker commands directly:

```bash
# Build the Docker image
docker build -t lintro:latest .

# Run lintro with Docker
docker run --rm -v "$(pwd):/code" lintro:latest check --table-format
docker run --rm -v "$(pwd):/code" lintro:latest fmt --tools black,isort
```

## Using Docker Compose

You can also use Docker Compose:

```bash
# Build the image
docker-compose build

# Run lintro with Docker Compose
docker-compose run --rm lintro check --table-format
docker-compose run --rm lintro fmt --tools black,isort
```

## Output to File

To save the output to a file, you can use the `--output` option:

```bash
./lintro-docker.sh check --table-format --group-by code --output result.txt
```

## Common Use Cases

### Check Code Quality

```bash
./lintro-docker.sh check --table-format --group-by code
```

### Format Code

```bash
./lintro-docker.sh fmt --tools black,isort
```

### List Available Tools

```bash
./lintro-docker.sh list-tools
```

### Check Specific Files or Directories

```bash
./lintro-docker.sh check path/to/file.py path/to/directory
```

### Use Specific Tools Only

```bash
./lintro-docker.sh check --tools black,flake8,pylint
```

## Troubleshooting

### Permission Issues

If you encounter permission issues with the output files, you may need to adjust the user in the Docker container:

```bash
docker run --rm -v "$(pwd):/code" --user "$(id -u):$(id -g)" lintro:latest check
```

### Volume Mounting Issues

If you're having trouble with volume mounting, ensure you're using the absolute path:

```bash
docker run --rm -v "$(pwd):/code" lintro:latest check
```

## Building Custom Images

You can modify the Dockerfile to include additional tools or configurations. After making changes, rebuild the image:

```bash
docker build -t lintro:custom .
docker run --rm -v "$(pwd):/code" lintro:custom check
``` 