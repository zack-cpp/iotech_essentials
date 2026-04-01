# Use a slim Python image to keep the footprint tiny
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /app/logs

# Copy all python scripts and frontend into the container
COPY *.py .
COPY static/ static/
