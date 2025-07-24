import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

from .config import PipelineConfig
from .pcb_layout import PCBLayout

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Represents a validation error."""
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'drc', 'erc', 'manufacturing'
    message: str
    location: Optional[Tuple[float, float]] = None
    component: Optional[str] = None


class ValidationReport:
    """Validation report containing all errors and warnings."""
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.info: List[ValidationError] = []
    
    def add_error(self, category: str, message: str, **kwargs):
        self.errors.append(ValidationError('error', category, message, **kwargs))
    
    def add_warning(self, category: str, message: str, **kwargs):
        self.warnings.append(ValidationError('warning', category, message, **kwargs))
    
    def add_info(self, category: str, message: str, **kwargs):
        self.info.append(ValidationError('info', category, message, **kwargs))
    
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    def print_summary(self):
        """Print validation summary."""
        print(f"\nValidation Report:")
        print(f"  Errors: {len(self.errors)}")
        print(f"  Warnings: {len(self.warnings)}")
        print(f"  Info: {len(self.info)}")
        
        if self.errors:
            print("\nErrors:")
            for error in self.errors[:10]:  # Show first 10
                print(f"  - [{error.category}] {error.message}")
                if error.component:
                    print(f"    Component: {error.component}")
                if error.location:
                    print(f"    Location: {error.location}")
        
        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings[:10]:  # Show first 10
                print(f"  - [{warning.category}] {warning.message}")


class DesignValidator:
    """Validates PCB designs against various rules."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.report = ValidationReport()
    
    def run_drc(self, layout: PCBLayout) -> bool:
        """Run Design Rule Check on PCB layout.
        
        Args:
            layout: PCB layout to validate
            
        Returns:
            True if DRC passes (no errors), False otherwise
        """
        logger.info("Running Design Rule Check (DRC)")
        self.report = ValidationReport()
        
        # Check clearances
        self._check_clearances(layout)
        
        # Check trace widths
        self._check_trace_widths(layout)
        
        # Check via sizes
        self._check_via_sizes(layout)
        
        # Check component courtyard
        if self.config.get('check_courtyard', True):
            self._check_courtyards(layout)
        
        # Check board outline
        self._check_board_outline(layout)
        
        # Check copper pours
        self._check_copper_zones(layout)
        
        # Print summary
        self.report.print_summary()
        
        return not self.report.has_errors()
    
    def run_erc(self, layout: PCBLayout) -> bool:
        """Run Electrical Rule Check.
        
        Args:
            layout: PCB layout to validate
            
        Returns:
            True if ERC passes (no errors), False otherwise
        """
        logger.info("Running Electrical Rule Check (ERC)")
        
        # Check for unconnected nets
        if self.config.get('check_unconnected', True):
            self._check_unconnected_nets(layout)
        
        # Check power connections
        self._check_power_connections(layout)
        
        # Check for shorts
        self._check_for_shorts(layout)
        
        return not self.report.has_errors()
    
    def check_manufacturing_constraints(self, layout: PCBLayout) -> bool:
        """Check manufacturing constraints.
        
        Args:
            layout: PCB layout to validate
            
        Returns:
            True if all constraints are met, False otherwise
        """
        logger.info("Checking manufacturing constraints")
        
        # Check minimum hole size
        self._check_hole_sizes(layout)
        
        # Check minimum trace/space for manufacturer
        self._check_manufacturer_capabilities(layout)
        
        # Check solder mask requirements
        self._check_solder_mask(layout)
        
        # Check silkscreen
        self._check_silkscreen(layout)
        
        # Check panelization if needed
        if self.config.get('panelize', False):
            self._check_panelization(layout)
        
        return not self.report.has_errors()
    
    def _check_clearances(self, layout: PCBLayout) -> None:
        """Check minimum clearances between objects."""
        min_clearance = self.config.get('clearance', 0.2)  # mm
        
        # Check component-to-component clearance
        components = list(layout.components.items())
        for i, (ref1, comp1) in enumerate(components):
            for j, (ref2, comp2) in enumerate(components[i+1:], i+1):
                distance = self._calculate_distance(
                    comp1['position'], comp2['position']
                )
                
                # Simplified check - in reality would check actual footprint bounds
                if distance < min_clearance * 2:
                    self.report.add_error(
                        'drc',
                        f"Clearance violation between {ref1} and {ref2}",
                        location=comp1['position']
                    )
    
    def _check_trace_widths(self, layout: PCBLayout) -> None:
        """Check minimum trace widths."""
        min_trace_width = self.config.get('min_track_width', 0.15)  # mm
        
        for trace in layout.traces:
            if trace.get('width', 0) < min_trace_width:
                self.report.add_error(
                    'drc',
                    f"Trace width {trace.get('width')}mm below minimum {min_trace_width}mm",
                    location=trace.get('start')
                )
    
    def _check_via_sizes(self, layout: PCBLayout) -> None:
        """Check via sizes."""
        min_via_diameter = self.config.get('min_via_diameter', 0.45)  # mm
        min_via_drill = self.config.get('min_via_drill', 0.2)  # mm
        
        for via in layout.vias:
            if via.get('diameter', 0) < min_via_diameter:
                self.report.add_error(
                    'drc',
                    f"Via diameter {via.get('diameter')}mm below minimum {min_via_diameter}mm",
                    location=via.get('position')
                )
            
            if via.get('drill', 0) < min_via_drill:
                self.report.add_error(
                    'drc',
                    f"Via drill {via.get('drill')}mm below minimum {min_via_drill}mm",
                    location=via.get('position')
                )
    
    def _check_courtyards(self, layout: PCBLayout) -> None:
        """Check component courtyard overlaps."""
        # Simplified check - would need actual courtyard geometry
        for ref, comp in layout.components.items():
            # Check if component is too close to board edge
            x, y = comp['position']
            board_width, board_height = layout.board_size
            margin = 1.0  # mm
            
            if x < margin or x > board_width - margin:
                self.report.add_warning(
                    'drc',
                    f"Component {ref} too close to board edge",
                    component=ref,
                    location=(x, y)
                )
            
            if y < margin or y > board_height - margin:
                self.report.add_warning(
                    'drc',
                    f"Component {ref} too close to board edge",
                    component=ref,
                    location=(x, y)
                )
    
    def _check_board_outline(self, layout: PCBLayout) -> None:
        """Check board outline validity."""
        if not layout.edge_cuts:
            self.report.add_error('drc', "No board outline defined")
            return
        
        # Check if outline is closed
        # Simplified check - would need proper polygon validation
        if len(layout.edge_cuts) < 3:
            self.report.add_error('drc', "Board outline not closed")
    
    def _check_copper_zones(self, layout: PCBLayout) -> None:
        """Check copper pour zones."""
        for zone in layout.zones:
            if zone.get('min_thickness', 0) < 0.15:
                self.report.add_warning(
                    'drc',
                    "Copper zone thickness below recommended minimum",
                    location=zone.get('position')
                )
    
    def _check_unconnected_nets(self, layout: PCBLayout) -> None:
        """Check for unconnected nets."""
        # This would require netlist analysis
        # For now, just a placeholder
        pass
    
    def _check_power_connections(self, layout: PCBLayout) -> None:
        """Check power connections."""
        # Check if all components have proper power connections
        # This would require schematic data
        pass
    
    def _check_for_shorts(self, layout: PCBLayout) -> None:
        """Check for electrical shorts."""
        # This would require trace and pad analysis
        pass
    
    def _check_hole_sizes(self, layout: PCBLayout) -> None:
        """Check minimum hole sizes."""
        min_hole_size = self.config.get('min_hole_size', 0.3)  # mm
        
        # Check component holes
        for ref, comp in layout.components.items():
            # Would need actual footprint data
            pass
        
        # Check vias
        for via in layout.vias:
            if via.get('drill', 0) < min_hole_size:
                self.report.add_error(
                    'manufacturing',
                    f"Hole size {via.get('drill')}mm below minimum {min_hole_size}mm",
                    location=via.get('position')
                )
    
    def _check_manufacturer_capabilities(self, layout: PCBLayout) -> None:
        """Check against manufacturer capabilities."""
        manufacturer = self.config.get('manufacturer', 'jlcpcb')
        
        if manufacturer == 'jlcpcb':
            # JLCPCB standard capabilities
            capabilities = {
                'min_trace_width': 0.127,  # 5 mil
                'min_trace_space': 0.127,  # 5 mil
                'min_via_diameter': 0.45,
                'min_via_drill': 0.2,
                'min_hole_size': 0.3,
            }
            
            # Check against capabilities
            if self.config.get('min_track_width', 0.15) < capabilities['min_trace_width']:
                self.report.add_warning(
                    'manufacturing',
                    f"Design uses traces below JLCPCB standard capability"
                )
    
    def _check_solder_mask(self, layout: PCBLayout) -> None:
        """Check solder mask requirements."""
        # Check solder mask expansion
        # Check solder mask bridges
        pass
    
    def _check_silkscreen(self, layout: PCBLayout) -> None:
        """Check silkscreen requirements."""
        # Check text size
        # Check line width
        # Check overlap with pads
        pass
    
    def _check_panelization(self, layout: PCBLayout) -> None:
        """Check panelization requirements."""
        # Check panel size
        # Check mouse bites or V-grooves
        # Check fiducials
        pass
    
    def _calculate_distance(self, pos1: Tuple[float, float], 
                          pos2: Tuple[float, float]) -> float:
        """Calculate distance between two points."""
        import math
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)