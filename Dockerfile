FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .[server]

# Copy source
COPY relayos/ relayos/

# Default port
EXPOSE 8080

# Start the dashboard
CMD ["relayos", "serve", "--host", "0.0.0.0", "--port", "8080"]
