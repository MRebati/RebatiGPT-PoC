FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make the startup script executable and ensure proper line endings
RUN chmod +x start.sh && \
    sed -i 's/\r$//' start.sh

# Expose the port Chainlit runs on
EXPOSE 8000

# Use the startup script as the entrypoint
ENTRYPOINT ["./start.sh"] 