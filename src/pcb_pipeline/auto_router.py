import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import json

from .config import PipelineConfig
from .pcb_layout import PCBLayout

logger = logging.getLogger(__name__)


class AutoRouter:
    """Advanced auto-routing system with multiple backends."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.routing_backend = config.get('routing_backend', 'freerouting')
        self.routing_quality = config.get('routing_quality', 'medium')  # fast, medium, high
        
    def route_board(self, layout: PCBLayout) -> PCBLayout:
        """Route the PCB using configured backend.
        
        Args:
            layout: PCB layout with placed components
            
        Returns:
            Layout with routed traces
        """
        logger.info(f"Starting auto-routing with {self.routing_backend} backend")
        
        if self.routing_backend == 'freerouting':
            return self._route_with_freerouting(layout)
        elif self.routing_backend == 'kicad_builtin':
            return self._route_with_kicad(layout)
        elif self.routing_backend == 'grid_based':
            return self._route_grid_based(layout)
        else:
            logger.warning(f"Unknown routing backend: {self.routing_backend}")
            return self._route_grid_based(layout)
    
    def _route_with_freerouting(self, layout: PCBLayout) -> PCBLayout:
        """Route using FreeRouting external tool."""
        logger.info("Routing with FreeRouting")
        
        # Check if FreeRouting is available
        if not self._check_freerouting_available():
            logger.warning("FreeRouting not available, falling back to grid routing")
            return self._route_grid_based(layout)
        
        try:
            # Create temporary files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Export design to FreeRouting format
                dsn_file = temp_path / "design.dsn"
                self._export_dsn(layout, dsn_file)
                
                # Run FreeRouting
                ses_file = temp_path / "design.ses"
                self._run_freerouting(dsn_file, ses_file)
                
                # Import routing results
                if ses_file.exists():
                    self._import_routing_results(layout, ses_file)
                    logger.info("FreeRouting completed successfully")
                else:
                    logger.warning("FreeRouting failed, using fallback")
                    return self._route_grid_based(layout)
                    
        except Exception as e:
            logger.error(f"FreeRouting failed: {e}")
            return self._route_grid_based(layout)
        
        return layout
    
    def _route_with_kicad(self, layout: PCBLayout) -> PCBLayout:
        """Route using KiCad's built-in auto-router."""
        logger.info("Routing with KiCad built-in router")
        
        # KiCad's Python API routing capabilities are limited
        # This would interface with KiCad's interactive router
        # For now, fall back to grid-based routing
        
        return self._route_grid_based(layout)
    
    def _route_grid_based(self, layout: PCBLayout) -> PCBLayout:
        """Simple grid-based routing algorithm."""
        logger.info("Using grid-based routing")
        
        # Extract unrouted nets
        unrouted_nets = self._extract_unrouted_nets(layout)
        
        # Route each net
        for net_name, connections in unrouted_nets.items():
            self._route_net_grid(layout, net_name, connections)
        
        logger.info(f"Grid routing completed - routed {len(unrouted_nets)} nets")
        return layout
    
    def _extract_unrouted_nets(self, layout: PCBLayout) -> Dict[str, List[Tuple[str, str]]]:
        """Extract nets that need routing."""
        # This would analyze the netlist and find unconnected pins
        # For demo purposes, create some sample nets
        
        unrouted_nets = {}
        
        # Analyze components for common nets
        components = layout.components
        
        # Find VCC connections
        vcc_pins = []
        gnd_pins = []
        
        for ref, comp in components.items():
            # Simple heuristic - first pin often power, second often ground
            if comp.get('type') in ['resistor', 'capacitor', 'led']:
                # Assume pin 1 goes to signal/power, pin 2 to ground for some components
                if ref.startswith('R') or ref.startswith('C'):
                    vcc_pins.append((ref, '1'))
                    gnd_pins.append((ref, '2'))
        
        if vcc_pins:
            unrouted_nets['VCC'] = vcc_pins
        if gnd_pins:
            unrouted_nets['GND'] = gnd_pins
            
        return unrouted_nets
    
    def _route_net_grid(self, layout: PCBLayout, net_name: str, 
                       connections: List[Tuple[str, str]]) -> None:
        """Route a single net using grid-based algorithm."""
        if len(connections) < 2:
            return
        
        # Get component positions
        positions = []
        for comp_ref, pin in connections:
            if comp_ref in layout.components:
                comp_pos = layout.components[comp_ref]['position']
                # Offset for pin position (simplified)
                pin_pos = (comp_pos[0] + 1, comp_pos[1])
                positions.append((comp_ref, pin, pin_pos))
        
        if len(positions) < 2:
            return
        
        # Create minimum spanning tree for net
        traces = self._create_mst_routing(positions)
        
        # Add traces to layout
        for trace in traces:
            layout.traces.append({
                'net': net_name,
                'start': trace['start'],
                'end': trace['end'],
                'width': self.config.get('default_trace_width', 0.25),
                'layer': 'F.Cu'
            })
    
    def _create_mst_routing(self, positions: List[Tuple[str, str, Tuple[float, float]]]) -> List[Dict]:
        """Create minimum spanning tree for routing."""
        if len(positions) < 2:
            return []
        
        traces = []
        connected = [positions[0]]
        unconnected = positions[1:]
        
        while unconnected:
            # Find closest unconnected point to any connected point
            min_dist = float('inf')
            best_connection = None
            
            for conn_ref, conn_pin, conn_pos in connected:
                for unconn_ref, unconn_pin, unconn_pos in unconnected:
                    dist = self._calculate_distance(conn_pos, unconn_pos)
                    if dist < min_dist:
                        min_dist = dist
                        best_connection = (
                            (conn_ref, conn_pin, conn_pos),
                            (unconn_ref, unconn_pin, unconn_pos)
                        )
            
            if best_connection:
                conn_point, unconn_point = best_connection
                traces.append({
                    'start': conn_point[2],
                    'end': unconn_point[2],
                    'start_ref': conn_point[0],
                    'end_ref': unconn_point[0]
                })
                
                connected.append(unconn_point)
                unconnected.remove(unconn_point)
        
        return traces
    
    def _calculate_distance(self, pos1: Tuple[float, float], 
                          pos2: Tuple[float, float]) -> float:
        """Calculate Manhattan distance between two points."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def _check_freerouting_available(self) -> bool:
        """Check if FreeRouting is available."""
        try:
            # Check for FreeRouting JAR file
            freerouting_jar = self.config.get('freerouting_jar_path')
            if freerouting_jar and Path(freerouting_jar).exists():
                return True
            
            # Check for system-installed FreeRouting
            result = subprocess.run(['java', '-version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                # Java is available, check for FreeRouting
                # This would be more sophisticated in practice
                return False  # For now, assume not available
            
        except FileNotFoundError:
            pass
        
        return False
    
    def _export_dsn(self, layout: PCBLayout, dsn_file: Path) -> None:
        """Export layout to Specctra DSN format for FreeRouting."""
        # This would generate a proper DSN file
        # For now, create a placeholder
        
        dsn_content = f'''(pcb {layout.name}
  (parser
    (string_quote ")
    (space_in_quoted_tokens on)
    (host_cad KiCad)
    (host_version 8.0.0)
  )
  
  (resolution um 10)
  (unit um)
  
  (structure
    (layer F.Cu
      (type signal)
      (property
        (index 0)
      )
    )
    (layer B.Cu
      (type signal)
      (property
        (index 1)
      )
    )
  )
  
  (placement
'''
        
        # Add component placements
        for ref, comp in layout.components.items():
            x, y = comp['position']
            dsn_content += f'    (component {ref} (place {ref} {x*1000:.0f} {y*1000:.0f} front 0))\n'
        
        dsn_content += '''  )
  
  (library
    (image default
      (pin default default (at 0 0))
    )
  )
  
  (network
'''
        
        # Add nets (simplified)
        for trace in layout.traces:
            net_name = trace.get('net', 'unnamed')
            dsn_content += f'    (net {net_name})\n'
        
        dsn_content += '''  )
)'''
        
        with open(dsn_file, 'w') as f:
            f.write(dsn_content)
    
    def _run_freerouting(self, dsn_file: Path, ses_file: Path) -> None:
        """Run FreeRouting on the DSN file."""
        freerouting_jar = self.config.get('freerouting_jar_path', 'freerouting.jar')
        
        cmd = [
            'java', '-jar', freerouting_jar,
            '-de', str(dsn_file),
            '-do', str(ses_file),
            '-mp', '20'  # Max passes
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise RuntimeError(f"FreeRouting failed: {result.stderr}")
    
    def _import_routing_results(self, layout: PCBLayout, ses_file: Path) -> None:
        """Import routing results from SES file."""
        # This would parse the SES file and update the layout
        # For now, just log that we would import results
        
        logger.info(f"Would import routing results from {ses_file}")
        
        # In a real implementation, this would:
        # 1. Parse the SES file format
        # 2. Extract wire segments and vias
        # 3. Update layout.traces and layout.vias
    
    def optimize_routing(self, layout: PCBLayout) -> PCBLayout:
        """Optimize existing routing."""
        logger.info("Optimizing routing")
        
        # Simple optimization strategies
        self._minimize_via_count(layout)
        self._optimize_trace_lengths(layout)
        self._balance_copper_distribution(layout)
        
        return layout
    
    def _minimize_via_count(self, layout: PCBLayout) -> None:
        """Minimize number of vias in routing."""
        # Analyze traces and remove unnecessary layer changes
        pass
    
    def _optimize_trace_lengths(self, layout: PCBLayout) -> None:
        """Optimize trace lengths and shapes."""
        # Implement trace length matching for critical signals
        pass
    
    def _balance_copper_distribution(self, layout: PCBLayout) -> None:
        """Balance copper distribution across layers."""
        # Add copper pours or adjust routing to balance layers
        pass