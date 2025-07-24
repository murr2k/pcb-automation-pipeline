# PCB Automation Pipeline Guide

## Overview

The PCB Automation Pipeline streamlines the entire PCB design process from concept to manufacturing. It automates:

1. Schematic generation from high-level specifications
2. PCB layout creation with component placement
3. Design rule checking and validation
4. Manufacturing file generation
5. Order submission to JLCPCB

## Pipeline Architecture

```
Design Specification (YAML)
         ↓
Schematic Generator
         ↓
    Schematic
         ↓
PCB Layout Engine
         ↓
   PCB Layout
         ↓
Design Validator
         ↓
  Gerber Export
         ↓
 JLCPCB Order
```

## Creating a Design Specification

Design specifications are written in YAML format. Here's the structure:

```yaml
name: Project Name
description: Project description

# Board specifications
board:
  size: [width, height]  # mm
  layers: 2              # Number of copper layers
  thickness: 1.6         # mm

# Component list
components:
  - type: resistor
    reference: R1
    value: "10k"
    package: "0603"
    
# Connections (nets)
connections:
  - net: "VCC"
    connect:
      - "R1.1"
      - "C1.1"

# Manufacturing options
manufacturing:
  vendor: "jlcpcb"
  quantity: 10
```

## Component Types

Supported component types:

- **Passive Components**: resistor, capacitor, inductor
- **Semiconductors**: diode, led, transistor
- **Connectors**: Various pin headers and connectors
- **ICs**: Integrated circuits (specify footprint)

## Using the Pipeline

### 1. Basic Usage

```python
from pcb_pipeline import PCBPipeline

# Initialize pipeline
pipeline = PCBPipeline()

# Load design
design = pipeline.load_specification("my_board.yaml")

# Generate schematic
schematic = pipeline.generate_schematic(design)

# Create layout
layout = pipeline.create_layout(schematic)

# Validate
if pipeline.validate_design(layout):
    # Export files
    pipeline.export_gerbers(layout, "output/")
```

### 2. Custom Configuration

```python
from pcb_pipeline import PCBPipeline, PipelineConfig

# Create custom configuration
config = PipelineConfig()
config.set('auto_place', True)
config.set('placement_strategy', 'optimize')
config.set('strict_drc', True)

# Use configuration
pipeline = PCBPipeline(config)
```

### 3. Component Library

```python
# Access component library
lib_mgr = pipeline.library_mgr

# Search for components
results = lib_mgr.search_components("resistor", filters={"package": "0603"})

# Add custom component
lib_mgr.add_custom_component("my_ic", {
    "type": "ic",
    "footprint": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "pins": 8
})
```

## Design Rules

Configure design rules in the specification or configuration file:

- **Trace Width**: Minimum trace width (default: 0.25mm)
- **Clearance**: Minimum clearance between objects (default: 0.2mm)
- **Via Size**: Via diameter and drill size
- **Courtyard**: Component courtyard overlap checking

## Component Placement Strategies

### Grid Placement
Components are arranged in a regular grid pattern. Best for simple boards.

```yaml
placement_strategy: grid
placement_grid: 5.0  # mm
```

### Cluster Placement
Groups related components together. Good for functional blocks.

```yaml
placement_strategy: cluster
```

### Optimized Placement
Uses algorithms to minimize trace length and crossings.

```yaml
placement_strategy: optimize
```

## Manufacturing Options

### JLCPCB Integration

The pipeline supports direct integration with JLCPCB:

```python
# Get quote
order_data = pipeline.jlcpcb.prepare_order(layout, quantity=10)
quote = pipeline.jlcpcb.get_quote(order_data)

# Submit order (requires API access)
order_id = pipeline.submit_order(layout, quantity=10)
```

### Supported Options

- **Surface Finish**: HASL, Lead-free HASL, ENIG, OSP
- **Solder Mask Colors**: Green, Red, Blue, Black, White, Yellow
- **Board Thickness**: 0.6mm to 2.0mm
- **Copper Weight**: 1oz, 2oz

## Advanced Features

### Custom Validators

Add custom validation rules:

```python
def custom_validator(layout):
    # Check custom rules
    errors = []
    for comp in layout.components.values():
        if comp['type'] == 'ic' and comp['position'][0] < 10:
            errors.append("ICs must be at least 10mm from board edge")
    return errors

# Add to pipeline
pipeline.validator.add_custom_check(custom_validator)
```

### Batch Processing

Process multiple designs:

```python
designs = ['board1.yaml', 'board2.yaml', 'board3.yaml']

for design_file in designs:
    design = pipeline.load_specification(design_file)
    schematic = pipeline.generate_schematic(design)
    layout = pipeline.create_layout(schematic)
    
    if pipeline.validate_design(layout):
        pipeline.export_gerbers(layout, f"output/{design['name']}/")
```

## Best Practices

1. **Start Simple**: Begin with basic designs and gradually add complexity
2. **Use Version Control**: Track your design specifications in Git
3. **Validate Early**: Run validation after each major step
4. **Component Libraries**: Build a library of commonly used components
5. **Design Rules**: Set appropriate rules for your manufacturer
6. **Documentation**: Document custom components and special requirements

## Troubleshooting

### Common Issues

1. **Component Not Found**
   - Check component type spelling
   - Verify package/footprint availability
   - Add custom component if needed

2. **Placement Failures**
   - Reduce board size constraints
   - Use smaller packages
   - Adjust placement grid

3. **DRC Violations**
   - Review design rules
   - Check manufacturer capabilities
   - Adjust trace width/clearance

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Examples

See the `examples/` directory for complete examples:
- `simple_led_board/`: Basic LED circuit
- More examples coming soon!

## Next Steps

- Explore the [API Reference](API.md) for detailed documentation
- Contribute to the project on GitHub
- Share your designs with the community