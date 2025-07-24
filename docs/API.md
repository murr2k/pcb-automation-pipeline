# PCB Pipeline API Reference

## Core Classes

### PCBPipeline

Main pipeline orchestrator class.

```python
class PCBPipeline:
    def __init__(self, config: Optional[PipelineConfig] = None)
```

#### Methods

##### load_specification(spec_path: str) -> Dict[str, Any]
Load design specification from YAML/JSON file.

##### generate_schematic(design_spec: Dict[str, Any]) -> Schematic
Generate KiCad schematic from design specification.

##### create_layout(schematic: Schematic) -> PCBLayout
Create PCB layout from schematic.

##### validate_design(pcb_layout: PCBLayout) -> bool
Run design rule checks on PCB layout.

##### export_gerbers(pcb_layout: PCBLayout, output_dir: str) -> Path
Export Gerber files for manufacturing.

##### submit_order(pcb_layout: PCBLayout, **kwargs) -> str
Submit order to JLCPCB (requires API access).

---

### PipelineConfig

Configuration management for the pipeline.

```python
class PipelineConfig:
    def __init__(self, config_file: Optional[str] = None)
```

#### Methods

##### get(key: str, default: Any = None) -> Any
Get configuration value.

##### set(key: str, value: Any) -> None
Set configuration value.

##### save(output_file: str) -> None
Save configuration to file.

---

### SchematicGenerator

Generates KiCad schematics from specifications.

```python
class SchematicGenerator:
    def __init__(self, config: PipelineConfig)
```

#### Methods

##### generate(design_spec: Dict[str, Any]) -> Schematic
Generate schematic from design specification.

---

### Schematic

Represents a KiCad schematic.

```python
class Schematic:
    def __init__(self, name: str)
```

#### Properties
- `name`: Schematic name
- `components`: Dictionary of components
- `nets`: Dictionary of electrical nets

#### Methods

##### add_component(component: Component) -> None
Add component to schematic.

##### add_net(net: Net) -> None
Add electrical net to schematic.

##### extract_netlist() -> Dict[str, Any]
Extract netlist from schematic.

---

### Component

Represents a schematic component.

```python
class Component:
    def __init__(self, ref: str, comp_type: str, value: str, **kwargs)
```

#### Properties
- `reference`: Reference designator (e.g., "R1")
- `type`: Component type
- `value`: Component value
- `footprint`: PCB footprint
- `lcsc_part`: LCSC part number
- `position`: Position coordinates
- `rotation`: Rotation angle

---

### Net

Represents an electrical net.

```python
class Net:
    def __init__(self, name: str)
```

#### Methods

##### add_connection(component_ref: str, pin: str) -> None
Add connection to net.

---

### PCBLayout

Represents a PCB layout.

```python
class PCBLayout:
    def __init__(self, name: str, config: PipelineConfig)
```

#### Properties
- `name`: Layout name
- `board_size`: Board dimensions (width, height) in mm
- `components`: Component placements
- `traces`: Routed traces
- `vias`: Via locations

#### Methods

##### export_gerbers(output_dir: Path) -> List[Path]
Export Gerber files.

##### export_drill_files(output_dir: Path) -> List[Path]
Export drill files.

##### export_pick_and_place(output_dir: Path) -> Path
Export pick and place file.

##### export_bom(output_dir: Path) -> Path
Export bill of materials.

---

### PCBLayoutEngine

Engine for creating PCB layouts.

```python
class PCBLayoutEngine:
    def __init__(self, config: PipelineConfig)
```

#### Methods

##### create_layout(netlist: Dict[str, Any]) -> PCBLayout
Create PCB layout from netlist.

##### auto_place_components(layout: PCBLayout) -> PCBLayout
Automatically place components.

##### auto_route(layout: PCBLayout) -> PCBLayout
Automatically route traces (not implemented).

---

### DesignValidator

Validates PCB designs.

```python
class DesignValidator:
    def __init__(self, config: PipelineConfig)
```

#### Methods

##### run_drc(layout: PCBLayout) -> bool
Run Design Rule Check.

##### run_erc(layout: PCBLayout) -> bool
Run Electrical Rule Check.

##### check_manufacturing_constraints(layout: PCBLayout) -> bool
Check manufacturing constraints.

---

### JLCPCBInterface

Interface for JLCPCB API.

```python
class JLCPCBInterface:
    def __init__(self, config: PipelineConfig)
```

#### Methods

##### prepare_order(pcb_layout: PCBLayout, **kwargs) -> Dict[str, Any]
Prepare order data for submission.

##### submit_order(order_data: Dict[str, Any]) -> str
Submit order to JLCPCB.

##### get_quote(order_data: Dict[str, Any]) -> Dict[str, Any]
Get price quote for PCB order.

##### check_order_status(order_id: str) -> Dict[str, Any]
Check order status.

---

### ComponentLibraryManager

Manages component libraries.

```python
class ComponentLibraryManager:
    def __init__(self, config: PipelineConfig)
```

#### Methods

##### get_component(comp_type: str, value: str, package: Optional[str] = None) -> Dict[str, Any]
Get component information.

##### find_lcsc_part(comp_type: str, value: str, package: Optional[str] = None) -> Optional[str]
Find LCSC part number.

##### is_basic_part(lcsc_part: str) -> bool
Check if part is JLCPCB basic part.

##### add_custom_component(name: str, component_data: Dict[str, Any]) -> None
Add custom component to library.

##### search_components(query: str, filters: Optional[Dict] = None) -> List[Dict]
Search for components in library.

---

## Design Specification Format

### Structure

```yaml
name: string                    # Project name
description: string             # Project description
version: string                 # Version number

board:
  size: [width, height]        # Board dimensions in mm
  layers: integer              # Number of copper layers
  thickness: float             # Board thickness in mm

components:
  - type: string               # Component type
    reference: string          # Reference designator (optional)
    value: string              # Component value
    package: string            # Package type (optional)
    footprint: string          # Specific footprint (optional)
    lcsc_part: string          # LCSC part number (optional)
    properties:                # Additional properties
      key: value

connections:
  - net: string                # Net name
    connect:                   # List of connections
      - "REF.PIN"              # Component.Pin format
      
power:
  vcc: ["REF.PIN", ...]        # VCC connections
  gnd: ["REF.PIN", ...]        # GND connections
  
design_rules:
  trace_width: float           # Default trace width in mm
  clearance: float             # Minimum clearance in mm
  via_size: float              # Via diameter in mm
  via_drill: float             # Via drill size in mm
  
manufacturing:
  vendor: string               # Manufacturer name
  quantity: integer            # Order quantity
  surface_finish: string       # Surface finish type
  solder_mask_color: string    # Solder mask color
  silkscreen_color: string     # Silkscreen color
```

---

## Configuration Options

Key configuration parameters:

```yaml
# General
project_name: string
output_dir: string

# KiCad
kicad_path: string
use_docker: boolean
docker_image: string

# Design
default_trace_width: float
default_via_size: float
clearance: float
copper_layers: integer

# Layout
auto_place: boolean
placement_strategy: string
placement_grid: float

# Manufacturing
manufacturer: string
surface_finish: string
solder_mask_color: string

# JLCPCB
jlcpcb_api_key: string
jlcpcb_api_secret: string
assembly_service: boolean

# Validation
strict_drc: boolean
min_track_width: float
min_via_diameter: float
```

---

## Examples

### Basic Usage

```python
from pcb_pipeline import PCBPipeline

pipeline = PCBPipeline()
design = pipeline.load_specification("board.yaml")
schematic = pipeline.generate_schematic(design)
layout = pipeline.create_layout(schematic)
pipeline.export_gerbers(layout, "output/")
```

### Custom Configuration

```python
from pcb_pipeline import PCBPipeline, PipelineConfig

config = PipelineConfig()
config.set('copper_layers', 4)
config.set('min_track_width', 0.1)

pipeline = PCBPipeline(config)
```

### Error Handling

```python
try:
    layout = pipeline.create_layout(schematic)
    if not pipeline.validate_design(layout):
        print("Validation failed!")
        # Handle errors
except Exception as e:
    print(f"Pipeline error: {e}")
```