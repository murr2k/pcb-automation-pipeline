#!/usr/bin/env python3
"""
Test the symbolic-to-physical component mapping layer
"""

import sys
sys.path.insert(0, 'src')

from pcb_pipeline.component_mapper import ComponentMapper, ComponentSpec
from pcb_pipeline.config import PipelineConfig


def test_component_mapping():
    """Test various component mappings"""
    
    # Initialize mapper
    config = {
        'cache_dir': 'cache/components',
        'octopart_api_key': None,
        'digikey_api_key': None,
        'lcsc_api_key': None
    }
    mapper = ComponentMapper(config)
    
    # Test cases
    test_components = [
        # Resistors
        ComponentSpec(type="resistor", value="10k", package="0603"),
        ComponentSpec(type="resistor", value="1k", tolerance="1%"),
        ComponentSpec(type="resistor", value="4.7k", package="0805"),
        
        # Capacitors
        ComponentSpec(type="capacitor", value="100nF", voltage="50V"),
        ComponentSpec(type="capacitor", value="10uF", voltage="16V"),
        ComponentSpec(type="capacitor", value="22pF", package="0603"),
        
        # LEDs
        ComponentSpec(type="led", value="red", package="0603"),
        ComponentSpec(type="led", value="blue"),
        
        # ICs
        ComponentSpec(type="ic", value="555"),
        ComponentSpec(type="ic", value="ESP32-WROOM-32"),
        ComponentSpec(type="ic", value="STM32F103C8T6"),
        
        # Connectors
        ComponentSpec(type="connector", value="USB-C"),
        ComponentSpec(type="connector", value="Pin_Header_2x20"),
        
        # Crystal
        ComponentSpec(type="crystal", value="16MHz"),
        
        # Unknown component
        ComponentSpec(type="unknown", value="special_part"),
    ]
    
    print("PCB Component Mapper Test")
    print("=" * 80)
    
    for spec in test_components:
        print(f"\nMapping: {spec.type} - {spec.value or 'N/A'}")
        print("-" * 40)
        
        result = mapper.map_component(spec)
        
        print(f"Result: {result.primary.supplier_pn} ({result.primary.supplier})")
        print(f"  MPN: {result.primary.mpn}")
        print(f"  Description: {result.primary.description}")
        print(f"  Package: {result.primary.package}")
        print(f"  Confidence: {result.confidence:.1%}")
        
        if result.primary.price:
            print(f"  Price: ${result.primary.price:.3f}")
        if result.primary.stock:
            print(f"  Stock: {result.primary.stock} units")
        
        if result.warnings:
            print(f"  Warnings: {', '.join(result.warnings)}")
        
        if result.alternatives:
            print(f"  Alternatives: {len(result.alternatives)} found")
            for i, alt in enumerate(result.alternatives[:3]):
                print(f"    {i+1}. {alt.supplier_pn} - {alt.description}")
    
    print("\n" + "=" * 80)
    print("Component Mapper Statistics:")
    print(f"  Components mapped: {len(test_components)}")
    print(f"  Database entries: {sum(len(v.get('common_values', {})) + len(v.get('common_parts', {})) for v in mapper.database.values())}")
    print(f"  Component types: {len(mapper.database)}")
    

def test_value_normalization():
    """Test component value normalization"""
    config = {'cache_dir': 'cache/components'}
    mapper = ComponentMapper(config)
    
    print("\nValue Normalization Test:")
    print("=" * 40)
    
    test_values = [
        ("resistor", "10k"),
        ("resistor", "10K"),
        ("resistor", "10k ohm"),
        ("resistor", "10kΩ"),
        ("resistor", "4.7k"),
        ("resistor", "4k7"),
        ("resistor", "4R7"),
        ("capacitor", "100nF"),
        ("capacitor", "100nf"),
        ("capacitor", "0.1uF"),
        ("capacitor", "0.1µF"),
    ]
    
    for comp_type, value in test_values:
        normalized = mapper._normalize_value(value)
        print(f"  '{value}' -> '{normalized}'")


def test_package_compatibility():
    """Test package compatibility checking"""
    config = {'cache_dir': 'cache/components'}
    mapper = ComponentMapper(config)
    
    print("\nPackage Compatibility Test:")
    print("=" * 40)
    
    test_packages = [
        ("0603", "1608"),  # Metric equivalent
        ("0805", "2012"),  # Metric equivalent
        ("SOIC-8", "SO-8"),  # Naming variation
        ("SOT-23", "SOT23"),  # With/without hyphen
        ("0603", "0805"),  # Different sizes - not compatible
    ]
    
    for pkg1, pkg2 in test_packages:
        compatible = mapper._packages_compatible(pkg1, pkg2)
        print(f"  '{pkg1}' <-> '{pkg2}': {'✓ Compatible' if compatible else '✗ Not compatible'}")


if __name__ == "__main__":
    test_component_mapping()
    test_value_normalization()
    test_package_compatibility()