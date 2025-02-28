#!/bin/bash

# Check if a volume with Terraform code is mounted at /app/terraform
if [ ! -d "/app/terraform" ]; then
    echo "Error: No Terraform code directory mounted at /app/terraform. Use '-v /path/to/terraform/code:/app/terraform:ro' to mount read-only Terraform code."
    exit 1
fi

# Change to the Terraform code directory
cd /app/terraform

# Check if .terraform directory and .terraform.lock.hcl exist (indicating tofu init has been run)
if [ ! -d ".terraform" ] || [ ! -f ".terraform.lock.hcl" ]; then
    echo "Error: .terraform directory or .terraform.lock.hcl file not found. Please run 'tofu init' in your Terraform code directory before running the container."
    exit 1
fi

# Generate schema.json using OpenTofu in a temporary location
echo "Generating schema.json..."
tofu providers schema -json > /tmp/schema.json

# Check if schema.json was created successfully in the temporary location
if [ ! -f "/tmp/schema.json" ]; then
    echo "Error: Failed to generate schema.json."
    exit 1
fi

# Change to the temporary directory and run the Textual app with the generated schema
cd /tmp
echo "Running Terradex..."
python3 /app/terradex.py

# Clean up schema.json after execution (optional, comment out if you want to keep it)
rm -f /tmp/schema.json
