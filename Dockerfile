FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git=1:2.* \
    curl=7.* \
    nodejs=18.* \
    npm=9.* \
    unzip=6.* \
    && rm -rf /var/lib/apt/lists/*

# Install prettier
RUN npm install -g prettier@2.8.8

# Install Terraform
RUN curl -fsSL https://releases.hashicorp.com/terraform/1.5.7/terraform_1.5.7_linux_amd64.zip -o terraform.zip \
    && unzip terraform.zip \
    && mv terraform /usr/local/bin/ \
    && rm terraform.zip

# Install Hadolint
RUN curl -fsSL https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64 -o /usr/local/bin/hadolint \
    && chmod +x /usr/local/bin/hadolint

# Set up working directory
WORKDIR /app

# Create a custom requirements file without hadolint-py
RUN echo "click>=8.0.0\n\
black>=23.0.0\n\
isort>=5.12.0\n\
flake8>=6.0.0\n\
darglint>=1.8.1\n\
pydocstyle>=6.3.0\n\
pylint>=3.0.0\n\
semgrep>=1.100.0\n\
python-terraform>=0.10.1\n\
yamllint>=1.32.0\n\
tabulate>=0.9.0\n\
pytest>=7.0.0\n\
pytest-cov>=4.0.0\n\
pytest-mock>=3.10.0\n\
tox>=4.0.0\n\
mypy>=1.8.0\n\
types-setuptools>=69.0.0\n\
types-tabulate>=0.9.0" > requirements_docker.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_docker.txt

# Copy the lintro package
COPY . .

# Modify pyproject.toml to remove hadolint-py dependency
RUN sed -i '/hadolint-py/d' pyproject.toml

# Install the package
RUN pip install -e .

# Create a volume for the code to be linted
VOLUME ["/code"]

# Set the default working directory to the mounted code
WORKDIR /code

# Create a non-root user to run the container
RUN useradd -m lintro
RUN chown -R lintro:lintro /app /code

# Switch to non-root user
USER lintro

ENTRYPOINT ["lintro"]
CMD ["--help"] 