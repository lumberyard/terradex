# Use official Python 3.11 slim image as base (lightweight and up-to-date)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy the application files and scripts
COPY terradex.py ./
COPY entrypoint.sh ./
COPY requirements.txt ./

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Install Textual from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Ensure the container runs in a terminal for Textual
ENV COLORTERM=truecolor

# Set the default schema file location as an environment variable
ENV SCHEMA_FILE=/app/schema.json

# Set the entrypoint to run the app
ENTRYPOINT ["/app/entrypoint.sh"]
