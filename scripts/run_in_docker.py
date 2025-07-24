#!/usr/bin/env python3
"""
Run PCB Pipeline in Docker container with KiCad support.
"""

import argparse
import sys
from pathlib import Path
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pcb_pipeline import PCBPipeline, PipelineConfig
from pcb_pipeline.fab_interface import FabricationManager


def main():
    parser = argparse.ArgumentParser(description='Run PCB Pipeline in Docker')
    parser.add_argument('--design', '-d', type=str, 
                       help='Design specification file (YAML/JSON)')
    parser.add_argument('--output', '-o', type=str, default='/output',
                       help='Output directory')
    parser.add_argument('--quantity', '-q', type=int, default=10,
                       help='Quantity for quotes')
    parser.add_argument('--manufacturer', '-m', type=str, default='jlcpcb',
                       choices=['jlcpcb', 'macrofab', 'pcbway', 'oshpark', 'seeedstudio'],
                       help='Target manufacturer')
    parser.add_argument('--auto-route', action='store_true',
                       help='Enable auto-routing')
    parser.add_argument('--optimize', action='store_true',
                       help='Enable AI optimization')
    parser.add_argument('--compare-quotes', action='store_true',
                       help='Compare quotes from all manufacturers')
    
    args = parser.parse_args()
    
    # Configure pipeline
    config = PipelineConfig()
    config.set('manufacturer', args.manufacturer)
    config.set('use_docker', True)
    config.set('auto_route', args.auto_route)
    config.set('use_ai_suggestions', args.optimize)
    
    # Set environment flag
    os.environ['PCB_USE_DOCKER'] = 'true'
    
    # Initialize pipeline
    pipeline = PCBPipeline(config)
    
    if args.design:
        # Process design file
        print(f"🔧 Processing design: {args.design}")
        
        # Load specification
        design_spec = pipeline.load_specification(args.design)
        print(f"✅ Loaded design: {design_spec['name']}")
        
        # Generate schematic
        print("\n📐 Generating schematic...")
        schematic = pipeline.generate_schematic(design_spec)
        
        # Create PCB layout
        print("🔲 Creating PCB layout...")
        pcb = pipeline.create_layout(schematic)
        
        # Optimize if requested
        if args.optimize:
            print("🤖 Optimizing placement with AI...")
            from pcb_pipeline.design_suggester import DesignSuggester
            suggester = DesignSuggester(config)
            pcb = suggester.optimize_placement(pcb)
        
        # Auto-route if requested
        if args.auto_route:
            print("🔀 Auto-routing board...")
            from pcb_pipeline.auto_router import AutoRouter
            router = AutoRouter(config)
            pcb = router.route_board(pcb)
        
        # Validate design
        print("✔️  Validating design...")
        if pipeline.validate_design(pcb):
            print("✅ Design validation passed!")
        else:
            print("❌ Design validation failed!")
            return 1
        
        # Export manufacturing files
        print(f"\n📦 Exporting to {args.output}...")
        output_dir = Path(args.output)
        pipeline.export_gerbers(pcb, output_dir)
        print(f"✅ Files exported to {output_dir}")
        
        # Get quotes
        if args.compare_quotes:
            print("\n💰 Comparing manufacturer quotes...")
            fab_manager = FabricationManager(config)
            fab_manager.compare_manufacturers(pcb, quantity=args.quantity)
        else:
            print(f"\n💰 Getting quote from {args.manufacturer}...")
            fab_manager = FabricationManager(config)
            interface = fab_manager.get_interface(args.manufacturer)
            order_data = interface.prepare_order(pcb, quantity=args.quantity)
            quote = interface.get_quote(order_data)
            
            print(f"Price: ${quote['price']} {quote['currency']}")
            print(f"Lead time: {quote['lead_time']} days")
    
    else:
        # Demo mode
        print("🚀 PCB Automation Pipeline - Docker Mode")
        print("=" * 50)
        print("\nNo design file specified. Running in demo mode...")
        print("\nExample usage:")
        print("  python run_in_docker.py -d /workspace/designs/my_board.yaml")
        print("  python run_in_docker.py -d examples/simple_led_board/spec.yaml --auto-route")
        print("  python run_in_docker.py -d spec.yaml --compare-quotes")
        
        # Test KiCad availability
        print("\n🔍 Checking KiCad installation...")
        try:
            import pcbnew
            print(f"✅ KiCad version: {pcbnew.GetBuildVersion()}")
        except ImportError:
            print("❌ KiCad Python modules not found")
            print("   Make sure you're running inside the Docker container")
        
        # Show available examples
        examples_dir = Path("/workspace/examples")
        if examples_dir.exists():
            print("\n📁 Available examples:")
            for example in examples_dir.glob("*/spec.yaml"):
                print(f"  - {example.relative_to('/workspace')}")
    
    print("\n✨ Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())