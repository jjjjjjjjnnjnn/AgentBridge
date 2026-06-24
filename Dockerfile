FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
COPY relayos/ relayos/
RUN pip install --no-cache-dir .[server]

# Default port
EXPOSE 8080

# Start the dashboard
CMD ["relayos", "serve", "--host", "0.0.0.0", "--port", "8080"]
