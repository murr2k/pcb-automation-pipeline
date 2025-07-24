#!/usr/bin/env python3
"""
Demonstration of MacroFab API integration with PCB Automation Pipeline.

This example shows how to:
1. Get a quote from MacroFab
2. Submit an order
3. Track order status
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pcb_pipeline import PCBPipeline, PipelineConfig
from pcb_pipeline.fab_interface import FabricationManager


def main():
    """Demonstrate MacroFab integration."""
    
    # Configure pipeline with MacroFab API key
    config = PipelineConfig()
    config.set('macrofab_api_key', 'k2TlSRhDC41lKLdP5QxeTDP3v4AcnCO')
    config.set('manufacturer', 'macrofab')
    
    # Initialize pipeline
    pipeline = PCBPipeline(config)
    fab_manager = FabricationManager(config)
    
    # Load example design
    spec_file = 'examples/simple_led_board/spec.yaml'
    design_spec = pipeline.load_specification(spec_file)
    print(f"Loaded design: {design_spec['name']}")
    
    # Generate PCB
    print("\nGenerating PCB design...")
    schematic = pipeline.generate_schematic(design_spec)
    pcb_layout = pipeline.create_layout(schematic)
    
    # Get MacroFab capabilities
    print("\n=== MacroFab Capabilities ===")
    macrofab = fab_manager.get_interface('macrofab')
    capabilities = macrofab.get_capabilities()
    
    print(f"Location: {capabilities['location']}")
    print(f"Max board size: {capabilities['max_board_size'][0]}x{capabilities['max_board_size'][1]}mm")
    print(f"Max layers: {capabilities['max_layers']}")
    print(f"Min trace width: {capabilities['min_trace_width']}mm")
    print(f"Lead times: {capabilities['lead_time_days']}")
    print(f"Services: Assembly={capabilities['assembly_service']}, "
          f"Inventory={capabilities['inventory_service']}, "
          f"Fulfillment={capabilities['fulfillment_service']}")
    
    # Get quote
    print("\n=== Getting Quote from MacroFab ===")
    order_data = macrofab.prepare_order(pcb_layout, quantity=10)
    quote = macrofab.get_quote(order_data)
    
    print(f"PCB Price: ${quote['pcb_price']} {quote['currency']}")
    print(f"Total Price: ${quote['price']} {quote['currency']}")
    print(f"Lead Time: {quote['lead_time']} days")
    
    print("\nShipping Options:")
    for option in quote['shipping_options']:
        print(f"  - {option['method']}: ${option['cost']} ({option['days']} days)")
    
    # Compare with other manufacturers
    print("\n=== Manufacturer Comparison ===")
    quotes = fab_manager.get_all_quotes(pcb_layout, quantity=10)
    
    print(f"{'Manufacturer':<15} {'Price':<10} {'Lead Time':<10} {'Status'}")
    print("-" * 45)
    for mfg, mfg_quote in quotes.items():
        if 'error' not in mfg_quote:
            price = f"${mfg_quote['price']}"
            lead_time = f"{mfg_quote['lead_time']} days"
            status = "✓ Available"
        else:
            price = "N/A"
            lead_time = "N/A"
            status = "✗ " + str(mfg_quote['error'])[:20]
        
        print(f"{mfg:<15} {price:<10} {lead_time:<10} {status}")
    
    # Demonstrate order submission (commented out to prevent actual orders)
    print("\n=== Order Submission (Simulated) ===")
    print("To submit an actual order, uncomment the following code:")
    print("""
    # Export manufacturing files
    output_dir = pipeline.export_gerbers(pcb_layout, "output/macrofab_order")
    
    # Add file paths to order data
    order_data['file_paths'] = {
        'gerbers': output_dir / 'gerbers.zip',
        'placement': output_dir / 'pick_and_place.csv',
        'bom': output_dir / 'bom.csv'
    }
    
    # Submit order
    order_id = macrofab.submit_order(order_data)
    print(f"Order submitted! ID: {order_id}")
    
    # Check status
    status = macrofab.check_order_status(order_id)
    print(f"Order status: {status['status']}")
    print(f"Stage: {status['stage']}")
    print(f"Progress: {status['progress']}%")
    """)
    
    print("\n✅ MacroFab integration demo complete!")


if __name__ == "__main__":
    main()