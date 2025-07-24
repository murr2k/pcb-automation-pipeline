#!/usr/bin/env python3
"""Example script to run the PCB automation pipeline."""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pcb_pipeline import PCBPipeline, PipelineConfig


def main():
    """Run the PCB automation pipeline example."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create pipeline configuration
    config = PipelineConfig()
    config.set('output_dir', 'output/simple_led_board')
    config.set('auto_place', True)
    config.set('auto_route', False)  # Routing not implemented yet
    
    # Initialize pipeline
    pipeline = PCBPipeline(config)
    
    try:
        # Load design specification
        spec_file = 'examples/simple_led_board/spec.yaml'
        design_spec = pipeline.load_specification(spec_file)
        print(f"Loaded design: {design_spec['name']}")
        
        # Generate schematic
        print("\n1. Generating schematic...")
        schematic = pipeline.generate_schematic(design_spec)
        print(f"   Created {len(schematic.components)} components")
        print(f"   Created {len(schematic.nets)} nets")
        
        # Create PCB layout
        print("\n2. Creating PCB layout...")
        pcb_layout = pipeline.create_layout(schematic)
        print(f"   Board size: {pcb_layout.board_size[0]}x{pcb_layout.board_size[1]}mm")
        
        # Validate design
        print("\n3. Validating design...")
        if pipeline.validate_design(pcb_layout):
            print("   Design validation passed!")
        else:
            print("   Design validation failed!")
            print("   Check the validation report for details")
        
        # Export manufacturing files
        print("\n4. Exporting manufacturing files...")
        output_path = pipeline.export_gerbers(pcb_layout, config.output_dir)
        print(f"   Files exported to: {output_path}")
        
        # Generate quote (simulated)
        print("\n5. Getting JLCPCB quote...")
        order_data = pipeline.jlcpcb.prepare_order(pcb_layout, quantity=10)
        quote = pipeline.jlcpcb.get_quote(order_data)
        print(f"   Price: ${quote['price']} {quote['currency']}")
        print(f"   Lead time: {quote['lead_time']} days")
        
        # Optional: Submit order (commented out by default)
        # print("\n6. Submitting order...")
        # order_id = pipeline.submit_order(pcb_layout, quantity=10)
        # print(f"   Order submitted! ID: {order_id}")
        
        print("\n✅ Pipeline completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())