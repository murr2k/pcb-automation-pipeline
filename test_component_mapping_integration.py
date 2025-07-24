#!/usr/bin/env python3
"""
Integration test for component mapping in the PCB pipeline
"""

import sys
sys.path.insert(0, 'src')

from pcb_pipeline.pipeline import PCBPipeline
from pcb_pipeline.config import PipelineConfig
from pcb_pipeline.component_mapper import ComponentMapper, ComponentSpec
import yaml
import tempfile
import os


def create_test_spec_with_mapping():
    """Create a test specification that requires component mapping"""
    return {
        'name': 'Component Mapping Test Board',
        'description': 'Test board to verify component mapping works',
        'board': {
            'size': [50, 30],
            'layers': 2
        },
        'components': [
            # These will need to be mapped to physical parts
            {
                'name': 'R1',
                'type': 'resistor',
                'value': '10k',
                'package': '0603'
            },
            {
                'name': 'R2',
                'type': 'resistor',
                'value': '4.7k',
                'package': '0603'
            },
            {
                'name': 'C1',
                'type': 'capacitor',
                'value': '100nF',
                'voltage': '50V',
                'package': '0603'
            },
            {
                'name': 'C2',
                'type': 'capacitor',
                'value': '10uF',
                'voltage': '16V',
                'package': '0805'
            },
            {
                'name': 'LED1',
                'type': 'led',
                'value': 'red',
                'package': '0603'
            },
            {
                'name': 'U1',
                'type': 'ic',
                'value': 'NE555',
                'package': 'SOIC-8'
            },
            {
                'name': 'J1',
                'type': 'connector',
                'value': 'USB-C'
            },
            {
                'name': 'Y1',
                'type': 'crystal',
                'value': '16MHz'
            }
        ],
        'connections': [
            {'from': 'R1.1', 'to': 'VCC'},
            {'from': 'R1.2', 'to': 'U1.7'},
            {'from': 'R2.1', 'to': 'U1.7'},
            {'from': 'R2.2', 'to': 'C1.1'},
            {'from': 'C1.2', 'to': 'GND'},
            {'from': 'LED1.cathode', 'to': 'GND'},
            {'from': 'LED1.anode', 'to': 'U1.3'},
            {'from': 'U1.1', 'to': 'GND'},
            {'from': 'U1.8', 'to': 'VCC'},
            {'from': 'C2.1', 'to': 'VCC'},
            {'from': 'C2.2', 'to': 'GND'}
        ],
        'power': {
            'vcc': ['VCC'],
            'gnd': ['GND']
        }
    }


def test_component_mapping_integration():
    """Test that component mapping works within the pipeline"""
    print("PCB Pipeline Component Mapping Integration Test")
    print("=" * 60)
    
    # Create pipeline with component mapping enabled
    config = PipelineConfig()
    config.set('use_component_mapping', True)
    
    # Initialize component mapper
    mapper_config = {
        'cache_dir': 'cache/components',
        'octopart_api_key': config.get('octopart_api_key'),
        'lcsc_api_key': config.get('lcsc_api_key')
    }
    mapper = ComponentMapper(mapper_config)
    
    # Create test specification
    spec = create_test_spec_with_mapping()
    
    print("\n1. Mapping Components:")
    print("-" * 40)
    
    # Map each component
    mapped_components = []
    for comp in spec['components']:
        comp_spec = ComponentSpec(
            type=comp['type'],
            value=comp.get('value'),
            package=comp.get('package'),
            voltage=comp.get('voltage')
        )
        
        result = mapper.map_component(comp_spec)
        
        # Add mapped info to component
        comp['lcsc_part'] = result.primary.supplier_pn
        comp['manufacturer'] = result.primary.manufacturer
        comp['mapped_package'] = result.primary.package
        comp['mapping_confidence'] = result.confidence
        
        mapped_components.append({
            'name': comp['name'],
            'type': comp['type'],
            'value': comp.get('value', 'N/A'),
            'lcsc': result.primary.supplier_pn,
            'confidence': f"{result.confidence:.0%}"
        })
        
        print(f"  {comp['name']}: {comp['type']} {comp.get('value', '')} -> LCSC: {result.primary.supplier_pn} ({result.confidence:.0%})")
    
    print("\n2. Component Mapping Summary:")
    print("-" * 40)
    
    # Summary statistics
    total_components = len(spec['components'])
    high_confidence = sum(1 for c in spec['components'] if c.get('mapping_confidence', 0) > 0.8)
    mapped = sum(1 for c in spec['components'] if c.get('lcsc_part') != 'N/A')
    
    print(f"  Total components: {total_components}")
    print(f"  Successfully mapped: {mapped} ({mapped/total_components:.0%})")
    print(f"  High confidence (>80%): {high_confidence}")
    
    # Show mapped BOM
    print("\n3. Mapped Bill of Materials:")
    print("-" * 40)
    print(f"{'Ref':<6} {'Type':<12} {'Value':<10} {'LCSC Part':<12} {'Confidence'}")
    print("-" * 60)
    for comp in mapped_components:
        print(f"{comp['name']:<6} {comp['type']:<12} {comp['value']:<10} {comp['lcsc']:<12} {comp['confidence']}")
    
    # Save mapped specification
    print("\n4. Saving Mapped Specification:")
    print("-" * 40)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(spec, f, default_flow_style=False)
        spec_file = f.name
    
    print(f"  Saved to: {spec_file}")
    
    # Generate component library info
    print("\n5. Component Library Info:")
    print("-" * 40)
    
    library_info = []
    for comp in spec['components']:
        if comp.get('lcsc_part') and comp['lcsc_part'] != 'N/A':
            library_info.append({
                'Reference': comp['name'],
                'Value': comp.get('value', comp['type']),
                'LCSC': comp['lcsc_part'],
                'Package': comp.get('mapped_package', comp.get('package', 'Unknown')),
                'Manufacturer': comp.get('manufacturer', 'Unknown')
            })
    
    for info in library_info[:5]:  # Show first 5
        print(f"  {info['Reference']}: {info['Value']} - LCSC: {info['LCSC']} ({info['Package']})")
    
    # Clean up
    os.unlink(spec_file)
    
    print("\n" + "=" * 60)
    print("✅ Component mapping integration test completed successfully!")


if __name__ == "__main__":
    test_component_mapping_integration()