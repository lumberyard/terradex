# Terradex

Terradex is a Textual-based Terminal User Interface (TUI) for exploring Terraform provider schemas, allowing users to navigate and search provider schemas generated from Terraform code.

## Prerequisites

- **Python 3.11+** installed on your system (for local testing) or Docker (recommended for deployment).
- **Textual 2.1.0**, installed via `pip` or Docker.
- **Terraform** (or OpenTofu as an alternative) installed locally to generate the schema file.

## Installation

### Using Docker (Recommended)

1. Clone this repository:

```bash
git clone https://github.com/yourusername/terradex.git
cd terradex
```

2. Build the Docker image:

```bash
docker build -t terradex .
```

### Local Development

1. Install Python 3.11+ and Textual:

```bash
pip install textual==2.1.0
```

2. Ensure the `schema.json` file is in the current directory or specify its path.

### Usage

#### Preparing the Schema File

Before running Terradex, you need to generate the `schema.json` file from your Terraform code. Follow these steps:

1. Create a directory with your Terraform code and ensure it includes a `main.tf` or similar file with a `required_providers` block, e.g.:

```terraform
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

2. Initialize the Terraform providers:

```bash
terraform init
```

3. Generate the schema file:

```bash
terraform providers schema -json > schema.json
```

4. Ensure `schema.json` is accessible in the directory you’ll mount into the Docker container or use locally.

### Running with Docker

Mount the `schema.json` file as a read-only volume and run the container with an interactive terminal session for Textual compatibility:

```bash
docker run -v $(pwd)/schema.json:/app/schema.json:ro -it terradex
```

Alternatively, you can override the schema file location using an environment variable:

```bash
docker run -e SCHEMA_FILE=/app/custom_schema.json -v $(pwd)/schema.json:/app/custom_schema.json:ro -it terradex
```

### Running Locally

Run the script with the schema file path (optional, defaults to `schema.json` or `SCHEMA_FILE` environment variable):

```bash
python terradex.py /path/to/schema.json
```

Or set the environment variable:

```bash
export SCHEMA_FILE=/path/to/schema.json
python terradex.py
```
