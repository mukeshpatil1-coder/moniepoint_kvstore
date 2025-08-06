# Moniepoint KV Store Dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Expose default port
EXPOSE 5000

# Command to run the server
CMD ["python", "server.py", "--port", "5000"]
