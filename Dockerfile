# Use official Alpine Linux as base (lightweight and supports OpenTofu)
FROM alpine:latest

# Set working directory
WORKDIR /app

# Copy the application files and scripts
COPY terradex.py ./
COPY entrypoint.sh ./
COPY requirements.txt ./

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Install OpenTofu (from OpenTofu documentation for Alpine: https://opentofu.org/docs/intro/install/alpine/)
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories
RUN apk update && apk add --no-cache opentofu

# Install Python, pip, and virtualenv (required for Textual)
RUN apk add --no-cache python3 py3-pip py3-virtualenv

# Create and activate a virtual environment, then install Textual
RUN python3 -m virtualenv /app/venv
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Ensure the container runs in a terminal for Textual
ENV TERM=xterm-256color
ENV PATH="/app/venv/bin:$PATH"

# Set the entrypoint to handle OpenTofu initialization and run the app
CMD ["sh", "/app/entrypoint.sh"]
