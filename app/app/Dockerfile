FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Set environment variables (non-sensitive only)
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Run the bot - token will be passed via Railway variables
CMD ["python", "-m", "app.main"]
