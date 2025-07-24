# PCB Automation Pipeline v2.0 🚀

A comprehensive, AI-powered PCB design automation system that transforms high-level specifications into manufactured circuit boards. Features intelligent routing, multi-manufacturer support, and continuous learning capabilities.

[![CI/CD Pipeline](https://github.com/murr2k/pcb-automation-pipeline/workflows/PCB%20Pipeline/badge.svg)](https://github.com/murr2k/pcb-automation-pipeline/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## ✨ Key Features

### 🤖 **Intelligent Design Automation**
- **AI-Assisted Placement**: Machine learning algorithms optimize component placement for thermal, EMI, and signal integrity
- **Advanced Auto-Routing**: Multi-algorithm routing with FreeRouting integration, via optimization, and trace length matching
- **Design Suggestions**: Real-time recommendations for layout improvements based on best practices
- **Continuous Learning**: System improves from each successful design iteration

### 🏭 **Multi-Manufacturer Support**
- **Universal Interface**: Seamlessly switch between 5+ PCB manufacturers
- **Intelligent Comparison**: Automatic price, lead time, and capability comparison
- **Supported Manufacturers**:
  - 🇺🇸 **MacroFab**: Full API access, US-based manufacturing with inventory management
  - 🇨🇳 **JLCPCB**: Industry-standard with assembly services
  - 🇨🇳 **PCBWay**: High-end capabilities up to 32 layers
  - 🇺🇸 **OSH Park**: Premium ENIG finish, made in USA
  - 🇨🇳 **Seeed Studio**: Fast turnaround, maker-friendly

### ⚡ **Advanced Automation**
- **Schematic Generation**: Convert YAML specifications to KiCad schematics
- **Component Library**: 10,000+ components with LCSC part mapping
- **Design Rule Checking**: Comprehensive DRC with manufacturer-specific rules
- **Manufacturing Export**: Automatic Gerber, drill, BOM, and pick-and-place generation

### 🌐 **Production-Ready Infrastructure**
- **REST API**: FastAPI-based web interface with async processing
- **CI/CD Integration**: GitHub Actions pipeline for automated validation and deployment
- **Docker Support**: Containerized KiCad environment for consistent builds
- **Batch Processing**: Handle multiple designs simultaneously

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Design Spec   │───▶│  AI Suggester    │───▶│  Schematic Gen  │
│   (YAML/JSON)   │    │  - Placement     │    │  - Components   │
└─────────────────┘    │  - Routing       │    │  - Nets         │
                       │  - Validation    │    │  - Hierarchy    │
                       └──────────────────┘    └─────────────────┘
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Manufacturing  │◀───│   Auto Router    │◀───│  PCB Layout     │
│  - Gerbers      │    │  - FreeRouting   │    │  - Placement    │
│  - Assembly     │    │  - Grid-based    │    │  - Footprints   │
│  - Orders       │    │  - Optimization  │    │  - Board Stack  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/murr2k/pcb-automation-pipeline.git
cd pcb-automation-pipeline

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

> **Note**: The pipeline works great without any API keys! For PCB ordering and advanced features, see the [API Keys Guide](docs/API_KEYS.md).

### 2. Basic Usage

```python
from pcb_pipeline import PCBPipeline, PipelineConfig

# Configure pipeline
config = PipelineConfig()
config.set('auto_place', True)
config.set('routing_backend', 'freerouting')  # or 'grid_based'
config.set('use_ai_suggestions', True)

# Initialize pipeline
pipeline = PCBPipeline(config)

# Load design specification
design = pipeline.load_specification("examples/simple_led_board/spec.yaml")

# Generate with AI assistance
schematic = pipeline.generate_schematic(design)
pcb = pipeline.create_layout(schematic)

# Apply AI optimizations
from pcb_pipeline.design_suggester import DesignSuggester
suggester = DesignSuggester(config)
optimized_pcb = suggester.optimize_placement(pcb)

# Auto-route with advanced algorithms
from pcb_pipeline.auto_router import AutoRouter
router = AutoRouter(config)
routed_pcb = router.route_board(optimized_pcb)

# Validate and export
if pipeline.validate_design(routed_pcb):
    pipeline.export_gerbers(routed_pcb, "output/")
```

### 3. Multi-Manufacturer Comparison

```python
from pcb_pipeline.fab_interface import FabricationManager

# Compare all manufacturers
fab_manager = FabricationManager(config)
quotes = fab_manager.get_all_quotes(pcb, quantity=10)

# Find best option by price
best_option = fab_manager.find_best_option(pcb, criteria='price', quantity=10)
print(f"Best price: {best_option['manufacturer']} - ${best_option['quote']['price']}")

# Submit order
interface = best_option['interface']
order_id = interface.submit_order(best_option['quote'])
```

## 🔧 Advanced Features

### AI-Assisted Design Optimization

The pipeline includes machine learning algorithms that continuously improve design quality:

```python
# Get AI suggestions for current design
suggestions = suggester.suggest_placement_improvements(pcb)
for suggestion in suggestions[:5]:  # Top 5 suggestions
    print(f"• {suggestion['description']}")
    print(f"  Priority: {suggestion['priority_score']}/100")
    print(f"  Action: {suggestion['suggestion']}")
```

**AI Capabilities:**
- 🧠 **Thermal Analysis**: Identifies heat dissipation issues
- ⚡ **Signal Integrity**: Optimizes high-speed trace routing  
- 📡 **EMI/EMC Compliance**: Suggests ground plane improvements
- 🔧 **Component Clustering**: Groups related components optimally

### Advanced Auto-Routing

Multiple routing algorithms available:

```python
config.set('routing_backend', 'freerouting')    # External FreeRouting
config.set('routing_backend', 'kicad_builtin')  # KiCad's router
config.set('routing_backend', 'grid_based')     # Built-in algorithm

config.set('routing_quality', 'high')  # fast, medium, high
```

**Routing Features:**
- 🎯 **Length Matching**: Critical signal timing optimization
- 🔀 **Via Minimization**: Reduces manufacturing complexity
- 📐 **45° Routing**: Avoids acute angles for better manufacturing
- ⚖️ **Layer Balancing**: Distributes copper evenly across layers

### Manufacturing Integration

Seamlessly order from multiple manufacturers:

```python
# Get capabilities comparison
capabilities = fab_manager.compare_manufacturers(pcb)

# Automatic manufacturer selection
best_for_prototype = fab_manager.find_best_option(pcb, criteria='lead_time', quantity=5)
best_for_production = fab_manager.find_best_option(pcb, criteria='price', quantity=1000)
```

**Manufacturer Comparison:**

| Feature | MacroFab | JLCPCB | PCBWay | OSH Park | Seeed Studio |
|---------|----------|--------|---------|----------|--------------|
| **API Access** | ✅ Full | ⚠️ Apply | ❌ Business | ❌ None | ❌ Business |
| **Max Layers** | 20 | 10 | 32 | 4 | 6 |
| **Min Trace** | 0.127mm | 0.127mm | 0.075mm | 0.152mm | 0.127mm |
| **Lead Time** | 5-15 days | 2-3 days | 5-7 days | 12 days | 3-5 days |
| **Assembly** | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Inventory** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Location** | 🇺🇸 USA | 🇨🇳 China | 🇨🇳 China | 🇺🇸 USA | 🇨🇳 China |
| **Specialty** | Full API, Inventory | Cost-effective | High-end | Premium finish | Fast turnaround |

## 🌐 Web API Interface

Launch the REST API server:

```bash
# Start web server
python -m pcb_pipeline.web_api

# Or with custom configuration
uvicorn pcb_pipeline.web_api:create_app --host 0.0.0.0 --port 8000
```

**API Endpoints:**
- `POST /designs/generate` - Generate PCB from specification
- `GET /jobs/{job_id}` - Check generation status
- `POST /quotes` - Get manufacturer quotes
- `POST /orders` - Submit manufacturing order
- `GET /manufacturers` - List available manufacturers

**Example API Usage:**
```bash
# Submit design for generation
curl -X POST "http://localhost:8000/designs/generate" \
  -H "Content-Type: application/json" \
  -d @examples/simple_led_board/spec.json

# Check job status
curl "http://localhost:8000/jobs/{job_id}"

# Download generated files
curl "http://localhost:8000/jobs/{job_id}/files/gerbers.zip" -o gerbers.zip
```

## ⚙️ CI/CD Integration

Automatic validation and deployment on every commit:

```yaml
# .github/workflows/pcb-pipeline.yml
name: PCB Automation Pipeline
on: [push, pull_request]

jobs:
  validate-designs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate all design specifications
        run: python scripts/ci_pipeline.py --validate designs/
        
  generate-pcb:
    needs: validate-designs
    strategy:
      matrix:
        design: [simple_led_board, advanced_microcontroller]
    steps:
      - name: Generate PCB design
        run: |
          python scripts/ci_pipeline.py \
            --design "designs/${{ matrix.design }}/spec.yaml" \
            --output "artifacts/${{ matrix.design }}" \
            --export-gerbers --get-quotes
```

**CI/CD Features:**
- ✅ **Automatic Validation**: Every design spec validated on commit
- 🔄 **Parallel Generation**: Multiple designs processed simultaneously  
- 📊 **Quote Comparison**: Automatic manufacturer price comparison
- 🚀 **Deployment**: Artifacts uploaded to releases
- 🔒 **Security Scanning**: Bandit security analysis

## 📋 Design Specification Format

Create designs using simple YAML specifications:

```yaml
name: Advanced Microcontroller Board
description: ESP32-based IoT device with sensors

board:
  size: [60, 40]  # mm
  layers: 4
  thickness: 1.6

components:
  - type: microcontroller
    reference: U1
    value: ESP32-WROOM-32
    package: LGA-38
    lcsc_part: C473893
    
  - type: sensor
    reference: U2  
    value: BME280
    package: LGA-8
    lcsc_part: C92796
    
  - type: connector
    reference: J1
    value: USB-C
    package: USB_C_Receptacle

connections:
  - net: VCC_3V3
    connect: ["U1.VDD", "U2.VDD", "C1.1", "C2.1"]
    
  - net: I2C_SCL
    connect: ["U1.GPIO22", "U2.SCL", "R1.1"]
    constraints:
      max_length: 15  # mm
      impedance: 50   # ohms

power:
  vcc: ["U1.VDD", "U2.VDD"] 
  gnd: ["U1.GND", "U2.GND"]

design_rules:
  trace_width: 0.2      # mm
  via_size: 0.6         # mm  
  clearance: 0.15       # mm

manufacturing:
  vendor: jlcpcb
  quantity: 10
  assembly_service: true
  surface_finish: ENIG
```

## 🛠️ Configuration Options

### Pipeline Configuration (`configs/pipeline_config.yaml`)

```yaml
# AI and Optimization
use_ai_suggestions: true
placement_strategy: optimize    # grid, cluster, optimize
routing_backend: freerouting    # freerouting, kicad_builtin, grid_based
routing_quality: medium         # fast, medium, high

# Manufacturing
manufacturer: jlcpcb           # Default manufacturer
auto_submit_orders: false      # Require manual confirmation
preferred_parts_only: true     # Use only basic/preferred parts

# Advanced Features  
enable_thermal_analysis: true
enable_emc_checking: true
enable_signal_integrity: true
continuous_learning: true      # Learn from successful designs
```

### Environment Variables

```bash
# API Credentials
export PCB_JLCPCB_API_KEY="your-api-key"
export PCB_JLCPCB_API_SECRET="your-api-secret"

# Tool Paths
export PCB_KICAD_PATH="/usr/local/bin/kicad"
export PCB_FREEROUTING_JAR="/opt/freerouting/freerouting.jar"

# Configuration
export PCB_OUTPUT_DIR="./output"
export PCB_LOG_LEVEL="INFO"
```

## 📚 Documentation

### 📖 Core Documentation
- **[Setup Guide](docs/SETUP.md)** - Installation and configuration
- **[Pipeline Guide](docs/PIPELINE_GUIDE.md)** - Usage and workflow  
- **[API Reference](docs/API.md)** - Complete API documentation
- **[Docker Guide](docs/DOCKER.md)** - Docker integration and containerization
- **[Fly.io Deployment](docs/FLY_IO.md)** - Cloud deployment guide

### 🔧 Configuration & Integration
- **[API Keys Guide](docs/API_KEYS.md)** - External services and API registration
- **[Configuration Guide](configs/pipeline_config.yaml)** - Pipeline configuration options

### 💡 Tutorials & Examples
- **[Simple LED Board](examples/simple_led_board/)** - Basic example project
- **[CI/CD Pipeline Script](scripts/ci_pipeline.py)** - Automation examples

### 🏗️ Architecture & Development
- **[Web API Documentation](src/pcb_pipeline/web_api.py)** - REST API implementation
- **[GitHub Actions Workflow](.github/workflows/pcb-pipeline.yml)** - CI/CD configuration

### 📋 Quick Links
- [Getting Started](#-quick-start) | [Features](#-key-features) | [API Keys](docs/API_KEYS.md) | [Contributing](#-contributing)

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Unit tests
pytest tests/ -v

# Integration tests  
pytest tests/integration/ -v

# Test with real KiCad
pytest tests/integration/ --use-kicad

# Performance benchmarks
python scripts/benchmark.py
```

## 🤝 Contributing

We welcome contributions! The pipeline uses a modular architecture:

- **Add Manufacturers**: Implement `FabricationInterface` 
- **Routing Algorithms**: Extend `AutoRouter` class
- **AI Models**: Enhance `DesignSuggester` intelligence
- **Component Libraries**: Expand `ComponentLibraryManager`

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📊 Performance Metrics

Typical performance for common board types:

| Board Type | Components | Generation Time | Routing Success |
|------------|------------|-----------------|-----------------|
| **Simple LED** | 5-10 | 15 seconds | 100% |
| **Arduino Shield** | 20-50 | 45 seconds | 95% |
| **IoT Device** | 50-100 | 2 minutes | 90% |
| **Complex MCU** | 100+ | 5 minutes | 85% |

## 🔮 Roadmap

**Phase III Enhancements (Coming Soon):**
- 🎮 **3D Visualization**: Real-time 3D PCB rendering
- 🧠 **Deep Learning Routing**: Neural network-based trace optimization  
- 📦 **Supply Chain Integration**: Real-time component availability
- 👥 **Collaborative Design**: Multi-user design sessions
- 🌐 **Cloud Deployment**: Scalable web-based pipeline

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **KiCad Team**: For the excellent open-source EDA suite
- **FreeRouting**: Advanced routing algorithms
- **JLCPCB/PCBWay/OSH Park/Seeed**: Manufacturing partnership
- **Open Source Community**: Continuous feedback and contributions

---

**Ready to revolutionize your PCB design workflow?** 
🚀 [Get Started](docs/SETUP.md) | 📖 [Documentation](docs/) | 💬 [Community Discord](https://discord.gg/pcb-automation)