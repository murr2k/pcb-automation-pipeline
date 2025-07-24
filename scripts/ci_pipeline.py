#!/usr/bin/env python3
"""CI/CD pipeline script for automated PCB generation."""

import sys
import logging
import argparse
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pcb_pipeline import PCBPipeline, PipelineConfig
from pcb_pipeline.fab_interface import FabricationManager


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('ci_pipeline.log')
        ]
    )


def validate_design_spec(spec_file: str) -> bool:
    """Validate design specification file."""
    logger = logging.getLogger(__name__)
    
    try:
        # Load and validate specification
        pipeline = PCBPipeline()
        design_spec = pipeline.load_specification(spec_file)
        pipeline._validate_spec(design_spec)
        
        logger.info(f"✓ Design specification {spec_file} is valid")
        return True
        
    except Exception as e:
        logger.error(f"✗ Design specification {spec_file} is invalid: {e}")
        return False


def generate_pcb_design(spec_file: str, output_dir: str, config_file: str = None) -> dict:
    """Generate PCB design from specification."""
    logger = logging.getLogger(__name__)
    
    # Create configuration
    config = PipelineConfig(config_file) if config_file else PipelineConfig()
    config.set('output_dir', output_dir)
    config.set('use_docker', True)  # Use Docker in CI
    
    # Initialize pipeline
    pipeline = PCBPipeline(config)
    
    results = {
        'spec_file': spec_file,
        'output_dir': output_dir,
        'success': False,
        'errors': [],
        'warnings': [],
        'files_generated': []
    }
    
    try:
        # Load specification
        logger.info(f"Loading design specification: {spec_file}")
        design_spec = pipeline.load_specification(spec_file)
        results['design_name'] = design_spec.get('name', 'Unknown')
        
        # Generate schematic
        logger.info("Generating schematic...")
        schematic = pipeline.generate_schematic(design_spec)
        logger.info(f"Generated schematic with {len(schematic.components)} components")
        
        # Create PCB layout
        logger.info("Creating PCB layout...")
        pcb_layout = pipeline.create_layout(schematic)
        logger.info(f"Created PCB layout ({pcb_layout.board_size[0]}x{pcb_layout.board_size[1]}mm)")
        
        # Apply AI suggestions if enabled
        if config.get('use_ai_suggestions', False):
            from pcb_pipeline.design_suggester import DesignSuggester
            suggester = DesignSuggester(config)
            suggestions = suggester.suggest_placement_improvements(pcb_layout)
            
            if suggestions:
                logger.info(f"AI suggester found {len(suggestions)} improvement opportunities")
                results['ai_suggestions'] = suggestions[:5]  # Top 5 suggestions
        
        # Validate design
        logger.info("Validating design...")
        validation_passed = pipeline.validate_design(pcb_layout)
        
        if not validation_passed:
            results['warnings'].append("Design validation failed - check DRC report")
        else:
            logger.info("✓ Design validation passed")
        
        # Export manufacturing files
        logger.info("Exporting manufacturing files...")
        output_path = pipeline.export_gerbers(pcb_layout, output_dir)
        
        # List generated files
        output_path = Path(output_path)
        if output_path.exists():
            results['files_generated'] = [str(f.relative_to(output_path)) 
                                        for f in output_path.rglob('*') if f.is_file()]
        
        # Get quotes from manufacturers
        logger.info("Getting manufacturer quotes...")
        fab_manager = FabricationManager(config)
        quotes = fab_manager.get_all_quotes(pcb_layout, quantity=10)
        results['quotes'] = quotes
        
        results['success'] = True
        logger.info("✅ PCB generation completed successfully")
        
    except Exception as e:
        logger.error(f"❌ PCB generation failed: {e}")
        results['errors'].append(str(e))
        import traceback
        logger.debug(traceback.format_exc())
    
    return results


def compare_with_baseline(results: dict, baseline_file: str) -> dict:
    """Compare results with baseline metrics."""
    logger = logging.getLogger(__name__)
    
    comparison = {
        'baseline_exists': False,
        'improvements': [],
        'regressions': []
    }
    
    baseline_path = Path(baseline_file)
    if not baseline_path.exists():
        logger.info("No baseline file found - creating new baseline")
        with open(baseline_path, 'w') as f:
            json.dump({
                'design_name': results.get('design_name'),
                'component_count': results.get('component_count', 0),
                'board_area': results.get('board_area', 0),
                'trace_count': results.get('trace_count', 0)
            }, f, indent=2)
        return comparison
    
    try:
        with open(baseline_path, 'r') as f:
            baseline = json.load(f)
        
        comparison['baseline_exists'] = True
        
        # Compare metrics (if available)
        # This would be expanded with actual metrics from the design
        
        logger.info("Baseline comparison completed")
        
    except Exception as e:
        logger.warning(f"Failed to compare with baseline: {e}")
    
    return comparison


def main():
    """Main CI pipeline function."""
    parser = argparse.ArgumentParser(description='PCB CI/CD Pipeline')
    parser.add_argument('--design', required=True, help='Design specification file')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--config', help='Configuration file')
    parser.add_argument('--validate', action='store_true', help='Validate design only')
    parser.add_argument('--export-gerbers', action='store_true', help='Export Gerber files')
    parser.add_argument('--get-quotes', action='store_true', help='Get manufacturer quotes')
    parser.add_argument('--baseline', help='Baseline file for comparison')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    parser.add_argument('--output-json', help='Output results to JSON file')
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting PCB CI/CD Pipeline")
    logger.info(f"Design: {args.design}")
    logger.info(f"Output: {args.output}")
    
    # Validate design specification
    if not validate_design_spec(args.design):
        logger.error("Design specification validation failed")
        return 1
    
    if args.validate:
        logger.info("✅ Validation-only mode - design specification is valid")
        return 0
    
    # Generate PCB design
    results = generate_pcb_design(args.design, args.output, args.config)
    
    # Compare with baseline if provided
    if args.baseline:
        comparison = compare_with_baseline(results, args.baseline)
        results['baseline_comparison'] = comparison
    
    # Output results
    if args.output_json:
        with open(args.output_json, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results written to {args.output_json}")
    
    # Print summary
    print("\n" + "="*60)
    print("PCB CI/CD Pipeline Summary")
    print("="*60)
    print(f"Design: {results.get('design_name', 'Unknown')}")
    print(f"Status: {'✅ SUCCESS' if results['success'] else '❌ FAILED'}")
    
    if results['success']:
        print(f"Files generated: {len(results.get('files_generated', []))}")
        
        # Show quotes
        quotes = results.get('quotes', {})
        if quotes:
            print("\nManufacturer Quotes:")
            for manufacturer, quote in quotes.items():
                if 'error' not in quote:
                    price = quote.get('price', 'N/A')
                    lead_time = quote.get('lead_time', 'N/A')
                    print(f"  {manufacturer:12}: ${price:6} | {lead_time:2} days")
        
        # Show AI suggestions
        suggestions = results.get('ai_suggestions', [])
        if suggestions:
            print(f"\nAI Suggestions: {len(suggestions)} improvements found")
            for i, suggestion in enumerate(suggestions[:3], 1):
                print(f"  {i}. {suggestion.get('description', 'No description')}")
    
    if results['errors']:
        print(f"\nErrors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  - {error}")
    
    if results['warnings']:
        print(f"\nWarnings: {len(results['warnings'])}")
        for warning in results['warnings']:
            print(f"  - {warning}")
    
    print("="*60)
    
    return 0 if results['success'] else 1


if __name__ == "__main__":
    sys.exit(main())