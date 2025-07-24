# PCB Automation Pipeline Setup Guide

## Prerequisites

- Python 3.8 or higher
- KiCad 8.0 or higher (or Docker)
- Git
- Basic knowledge of PCB design concepts

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/murr2k/pcb-automation-pipeline.git
cd pcb-automation-pipeline
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install the Package

For development:
```bash
pip install -e .
```

For production:
```bash
python setup.py install
```

## KiCad Setup

### Option 1: Native Installation

1. Download and install KiCad from [kicad.org](https://www.kicad.org/)
2. Update the configuration file with your KiCad path:
   ```yaml
   kicad_path: /path/to/kicad
   use_docker: false
   ```

### Option 2: Docker Installation

1. Install Docker from [docker.com](https://www.docker.com/)
2. Pull the KiCad Docker image:
   ```bash
   docker pull kicad/kicad:latest
   ```
3. Ensure configuration uses Docker:
   ```yaml
   use_docker: true
   docker_image: kicad/kicad:latest
   ```

## JLCPCB API Setup (Optional)

To enable automated ordering:

1. Apply for JLCPCB API access at [jlcpcb.com](https://jlcpcb.com/help/article/jlcpcb-online-api-available-now)
2. Once approved, add credentials to configuration:
   ```yaml
   jlcpcb_api_key: YOUR_API_KEY
   jlcpcb_api_secret: YOUR_API_SECRET
   ```

Or use environment variables:
```bash
export PCB_JLCPCB_API_KEY=YOUR_API_KEY
export PCB_JLCPCB_API_SECRET=YOUR_API_SECRET
```

## Configuration

1. Copy the example configuration:
   ```bash
   cp configs/pipeline_config.yaml configs/my_config.yaml
   ```

2. Edit the configuration file to match your setup:
   - Adjust paths and preferences
   - Set design rules
   - Configure manufacturing options

## Verify Installation

Run the test script:
```bash
python scripts/run_pipeline.py
```

This should:
- Load the example LED board specification
- Generate a schematic
- Create PCB layout
- Export manufacturing files
- Display a price quote

## Troubleshooting

### KiCad Python Module Not Found

If you get import errors for `pcbnew`:

1. Ensure KiCad is installed
2. Add KiCad's Python path to your environment:
   ```bash
   export PYTHONPATH=/usr/lib/kicad/lib/python3/dist-packages:$PYTHONPATH
   ```

### Docker Permission Issues

On Linux, add your user to the docker group:
```bash
sudo usermod -aG docker $USER
```

### JLCPCB API Errors

- Verify API credentials are correct
- Check if API access is still active
- The pipeline will work in simulation mode without API access

## Next Steps

- Read the [Pipeline Guide](PIPELINE_GUIDE.md) to understand the workflow
- Check the [API Reference](API.md) for detailed documentation
- Try modifying the example project in `examples/simple_led_board/`