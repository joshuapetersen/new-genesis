FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y curl wget unzip

# Install Circle Developer CLI for Agent integration
RUN curl -sSL https://raw.githubusercontent.com/circlefin/circle-cli/main/install.sh | bash

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Surrogate logic
COPY cloud_main.py .

# Expose standard cloud port
EXPOSE 8080

# Run the Surrogate
CMD ["python", "cloud_main.py"]
