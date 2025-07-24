# Use the official KiCad nightly image with full features
FROM kicad/kicad:nightly-full-trixie

# Install Python dependencies and utilities
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    wget \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python packages
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Install the package in development mode
RUN pip3 install -e .

# Create directories for input/output
RUN mkdir -p /workspace /output

# Set environment variables
ENV PYTHONPATH=/usr/lib/kicad/lib/python3/dist-packages:$PYTHONPATH
ENV KICAD_PATH=/usr/share/kicad
ENV PCB_USE_DOCKER=true

# Default command
CMD ["python3", "scripts/run_in_docker.py"]