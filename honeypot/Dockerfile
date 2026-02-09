FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install paramiko

# Copy all files
COPY . /app

# Expose the honeypot port
EXPOSE 22

# Ensure logs directory exists
RUN mkdir -p /app/logs

# Run the honeypot
CMD ["python3", "honeypot.py"]
