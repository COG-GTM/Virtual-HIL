# Base image with Python and display capabilities
FROM python:3.10-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    libx11-xcb1 libxrender1 libxi6 libxkbcommon-x11-0 \
    libglu1-mesa libgl1-mesa-glx xvfb \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir flask PyQt5 numpy

# Expose Flask dashboard port
EXPOSE 5001

# Start both Flask and PyQt using Xvfb for virtual display
CMD ["sh", "-c", "xvfb-run python main.py"]
