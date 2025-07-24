import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .config import PipelineConfig
from .schematic_generator import SchematicGenerator
from .pcb_layout import PCBLayoutEngine
from .design_validator import DesignValidator
from .jlcpcb_interface import JLCPCBInterface
from .library_manager import ComponentLibraryManager

logger = logging.getLogger(__name__)


class PCBPipeline:
    """Main PCB automation pipeline orchestrator."""
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize the PCB pipeline.
        
        Args:
            config: Pipeline configuration. If None, uses default config.
        """
        self.config = config or PipelineConfig()
        
        self.schematic_gen = SchematicGenerator(self.config)
        self.layout_engine = PCBLayoutEngine(self.config)
        self.validator = DesignValidator(self.config)
        self.jlcpcb = JLCPCBInterface(self.config)
        self.library_mgr = ComponentLibraryManager(self.config)
        
        logger.info("PCB Pipeline initialized")
    
    def load_specification(self, spec_path: str) -> Dict[str, Any]:
        """Load design specification from file.
        
        Args:
            spec_path: Path to specification file (YAML/JSON)
            
        Returns:
            Design specification dictionary
        """
        spec_file = Path(spec_path)
        if not spec_file.exists():
            raise FileNotFoundError(f"Specification file not found: {spec_path}")
        
        import yaml
        with open(spec_file, 'r') as f:
            spec = yaml.safe_load(f)
        
        logger.info(f"Loaded specification from {spec_path}")
        return spec
    
    def generate_schematic(self, design_spec: Dict[str, Any]) -> 'Schematic':
        """Generate KiCad schematic from design specification.
        
        Args:
            design_spec: Design specification dictionary
            
        Returns:
            Generated schematic object
        """
        logger.info("Generating schematic...")
        
        # Validate specification
        self._validate_spec(design_spec)
        
        # Generate schematic
        schematic = self.schematic_gen.generate(design_spec)
        
        logger.info("Schematic generation complete")
        return schematic
    
    def create_layout(self, schematic: 'Schematic') -> 'PCBLayout':
        """Create PCB layout from schematic.
        
        Args:
            schematic: Generated schematic
            
        Returns:
            PCB layout object
        """
        logger.info("Creating PCB layout...")
        
        # Extract netlist from schematic
        netlist = schematic.extract_netlist()
        
        # Create layout
        layout = self.layout_engine.create_layout(netlist)
        
        # Auto-place components
        layout = self.layout_engine.auto_place_components(layout)
        
        # Auto-route if enabled
        if self.config.auto_route:
            layout = self.layout_engine.auto_route(layout)
        
        logger.info("PCB layout complete")
        return layout
    
    def validate_design(self, pcb_layout: 'PCBLayout') -> bool:
        """Run design rule checks on PCB layout.
        
        Args:
            pcb_layout: PCB layout to validate
            
        Returns:
            True if validation passes, False otherwise
        """
        logger.info("Running design validation...")
        
        # Run DRC
        drc_result = self.validator.run_drc(pcb_layout)
        
        # Run electrical rules check
        erc_result = self.validator.run_erc(pcb_layout)
        
        # Check manufacturing constraints
        mfg_result = self.validator.check_manufacturing_constraints(pcb_layout)
        
        success = drc_result and erc_result and mfg_result
        
        if success:
            logger.info("Design validation passed")
        else:
            logger.error("Design validation failed")
        
        return success
    
    def export_gerbers(self, pcb_layout: 'PCBLayout', output_dir: str) -> Path:
        """Export Gerber files for manufacturing.
        
        Args:
            pcb_layout: PCB layout to export
            output_dir: Directory for output files
            
        Returns:
            Path to output directory
        """
        logger.info(f"Exporting Gerbers to {output_dir}...")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export Gerbers
        gerber_files = pcb_layout.export_gerbers(output_path)
        
        # Export drill files
        drill_files = pcb_layout.export_drill_files(output_path)
        
        # Export pick and place
        pnp_file = pcb_layout.export_pick_and_place(output_path)
        
        # Export BOM
        bom_file = pcb_layout.export_bom(output_path)
        
        logger.info(f"Export complete. Files in {output_path}")
        return output_path
    
    def submit_order(self, pcb_layout: 'PCBLayout', **kwargs) -> str:
        """Submit order to JLCPCB.
        
        Args:
            pcb_layout: PCB layout to order
            **kwargs: Additional order parameters
            
        Returns:
            Order ID
        """
        logger.info("Submitting order to JLCPCB...")
        
        # Prepare order data
        order_data = self.jlcpcb.prepare_order(pcb_layout, **kwargs)
        
        # Submit order
        order_id = self.jlcpcb.submit_order(order_data)
        
        logger.info(f"Order submitted. ID: {order_id}")
        return order_id
    
    def _validate_spec(self, spec: Dict[str, Any]) -> None:
        """Validate design specification."""
        required_fields = ['name', 'components', 'connections']
        
        for field in required_fields:
            if field not in spec:
                raise ValueError(f"Missing required field in specification: {field}")
        
        # Validate components
        for comp in spec['components']:
            if 'type' not in comp or 'value' not in comp:
                raise ValueError(f"Invalid component specification: {comp}")