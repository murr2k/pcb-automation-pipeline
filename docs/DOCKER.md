# 🐳 Docker Integration Guide

This guide covers how to use the PCB Automation Pipeline with Docker, including the official KiCad Docker image.

## 📋 Prerequisites

- Docker Desktop or Docker Engine installed
- Docker Compose (usually included with Docker Desktop)
- X11 server (for GUI applications, optional)
- At least 4GB of free disk space

## 🚀 Quick Start

### 1. Build the Docker Image

```bash
# Build the image
docker-compose build pcb-pipeline

# Or use the helper script
./scripts/docker_run.sh --build
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env to add your API keys (optional)
nano .env
```

### 3. Run the Pipeline

```bash
# Process a design
./scripts/docker_run.sh -d examples/simple_led_board/spec.yaml

# Or use docker-compose directly
docker-compose run --rm pcb-pipeline
```

## 🏗️ Architecture

The Docker setup includes three services:

### 1. **pcb-pipeline** - Main Processing Service
- Based on `kicad/kicad:nightly-full-trixie`
- Includes full KiCad installation with Python bindings
- Processes PCB designs from YAML specifications
- Generates manufacturing files

### 2. **pcb-web-api** - REST API Service
- FastAPI web interface
- Accessible at http://localhost:8000
- Async job processing
- File upload/download support

### 3. **pcb-notebook** - Jupyter Development
- Interactive Python environment
- Pre-configured with KiCad libraries
- Accessible at http://localhost:8888

## 📦 Docker Image Details

The PCB Pipeline Docker image is based on the official KiCad nightly image:

```dockerfile
FROM kicad/kicad:nightly-full-trixie
```

**Image Features:**
- ✅ Full KiCad installation (latest nightly build)
- ✅ Python 3.11+ with KiCad bindings
- ✅ All PCB Pipeline dependencies
- ✅ FreeRouting support (when JAR provided)
- ✅ Manufacturing file generation tools

**Image Size:** ~2.5GB (includes full KiCad)

## 🔧 Usage Examples

### Basic Pipeline Run

```bash
# Run with default example
docker-compose run --rm pcb-pipeline

# Process specific design
docker-compose run --rm pcb-pipeline \
  python3 scripts/run_pipeline.py \
  --design /workspace/designs/my_board.yaml \
  --output /output
```

### Web API Server

```bash
# Start the API server
docker-compose up pcb-web-api

# Or use the helper script
./scripts/docker_run.sh -a web-api

# Access at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Interactive Development

```bash
# Start Jupyter notebook
docker-compose up pcb-notebook

# Or use the helper script
./scripts/docker_run.sh -a notebook

# Open browser to http://localhost:8888
```

### Shell Access

```bash
# Open interactive shell in container
docker-compose run --rm pcb-pipeline bash

# Or use the helper script
./scripts/docker_run.sh -a shell

# Test KiCad Python bindings
python3 -c "import pcbnew; print(pcbnew.Version())"
```

## 📁 Volume Mounts

The Docker setup uses several volume mounts:

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./designs` | `/workspace/designs` | Input design specifications |
| `./output` | `/output` | Generated files output |
| `./examples` | `/workspace/examples` | Example projects |
| `./configs` | `/app/configs` | Configuration files |
| `./libraries` | `/workspace/libraries` | Component libraries |

## ⚙️ Configuration

### Environment Variables

Key environment variables for Docker:

```bash
# Pipeline Configuration
PCB_OUTPUT_DIR=/output          # Output directory in container
PCB_LOG_LEVEL=INFO             # Logging level
PCB_USE_DOCKER=true            # Enable Docker-specific features

# API Keys (optional)
PCB_JLCPCB_API_KEY=xxx         # JLCPCB API access
PCB_MACROFAB_API_KEY=xxx       # MacroFab API access
PCB_OCTOPART_API_KEY=xxx       # Component data API

# Display (for GUI tools)
DISPLAY=:0                      # X11 display
QT_X11_NO_MITSHM=1            # Qt compatibility
```

### Docker Compose Override

Create `docker-compose.override.yml` for local customizations:

```yaml
version: '3.8'

services:
  pcb-pipeline:
    # Mount additional directories
    volumes:
      - /path/to/kicad/libraries:/usr/share/kicad/library:ro
      - /path/to/freerouting.jar:/app/tools/freerouting.jar:ro
    
    # Additional environment
    environment:
      - PCB_FREEROUTING_JAR=/app/tools/freerouting.jar
      - KICAD_SYMBOL_DIR=/usr/share/kicad/library
```

## 🖥️ GUI Support (Advanced)

To run KiCad GUI tools from Docker:

### Linux

```bash
# Allow X11 connections
xhost +local:docker

# Run with display
docker-compose run --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  pcb-pipeline \
  pcview /output/board.kicad_pcb
```

### macOS

```bash
# Install XQuartz
brew install --cask xquartz

# Start XQuartz and allow connections
open -a XQuartz
# In XQuartz: Preferences → Security → Allow connections from network clients

# Get display
export DISPLAY=host.docker.internal:0

# Run with display
docker-compose run --rm pcb-pipeline pcview /output/board.kicad_pcb
```

### Windows

```bash
# Install VcXsrv or similar X server
# Start with "Disable access control" option

# Set display
export DISPLAY=host.docker.internal:0

# Run with display
docker-compose run --rm pcb-pipeline pcview /output/board.kicad_pcb
```

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
name: PCB Pipeline Docker

on: [push, pull_request]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Build Docker image
      run: docker-compose build pcb-pipeline
    
    - name: Run tests in Docker
      run: |
        docker-compose run --rm pcb-pipeline \
          pytest tests/ -v
    
    - name: Generate example PCB
      run: |
        docker-compose run --rm pcb-pipeline \
          python3 scripts/run_pipeline.py \
          --design /workspace/examples/simple_led_board/spec.yaml \
          --output /output
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: pcb-output
        path: output/
```

### Building Multi-Architecture Images

```bash
# Setup buildx
docker buildx create --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t yourusername/pcb-pipeline:latest \
  --push .
```

## 🐛 Troubleshooting

### Common Issues

#### 1. KiCad Python Import Error

```bash
# Error: ImportError: No module named pcbnew

# Solution: Check Python path
docker-compose run --rm pcb-pipeline \
  python3 -c "import sys; print(sys.path)"

# Should include: /usr/lib/kicad/lib/python3/dist-packages
```

#### 2. Permission Denied on Output

```bash
# Error: Permission denied: '/output/gerbers'

# Solution: Fix permissions
sudo chown -R $USER:$USER ./output
```

#### 3. Container Can't Find Design File

```bash
# Error: FileNotFoundError: design.yaml

# Solution: Use absolute paths or check mounts
docker-compose run --rm pcb-pipeline \
  ls -la /workspace/designs/
```

#### 4. GUI Application Won't Start

```bash
# Error: cannot connect to X server

# Solution: Check display settings
echo $DISPLAY
xhost +local:docker  # Linux only
```

### Debugging

```bash
# Run with debug logging
docker-compose run --rm \
  -e PCB_LOG_LEVEL=DEBUG \
  pcb-pipeline

# Check container logs
docker-compose logs pcb-pipeline

# Inspect running container
docker exec -it pcb-automation bash
```

## 🚀 Advanced Usage

### Custom KiCad Build

Create custom Dockerfile for specific KiCad version:

```dockerfile
# Use specific KiCad version
FROM kicad/kicad:7.0.10-jammy

# Your customizations...
```

### Production Deployment

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  pcb-web-api:
    image: pcb-automation-pipeline:latest
    restart: unless-stopped
    ports:
      - "80:8000"
    environment:
      - PCB_LOG_LEVEL=WARNING
      - WEB_CONCURRENCY=4
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

### Monitoring

```yaml
# Add to docker-compose.yml
  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
```

## 📚 Additional Resources

- [Official KiCad Docker Images](https://hub.docker.com/r/kicad/kicad)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PCB Pipeline API Documentation](API.md)
- [Main README](../README.md)

## 🤝 Contributing

When contributing Docker-related changes:

1. Test with multiple KiCad versions
2. Ensure images build on multiple platforms
3. Update documentation for any new features
4. Keep image size minimal

---

**Ready to automate your PCB design workflow with Docker?** 🚀

```bash
./scripts/docker_run.sh --build
./scripts/docker_run.sh -d examples/simple_led_board/spec.yaml
```