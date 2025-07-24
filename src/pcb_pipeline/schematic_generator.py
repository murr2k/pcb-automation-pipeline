import logging
from typing import Dict, Any, List, Tuple
from pathlib import Path
import uuid

from .config import PipelineConfig
from .kicad_interface import KiCadInterface

logger = logging.getLogger(__name__)


class Component:
    """Represents a schematic component."""
    
    def __init__(self, ref: str, comp_type: str, value: str, **kwargs):
        self.reference = ref
        self.type = comp_type
        self.value = value
        self.footprint = kwargs.get('footprint', '')
        self.lcsc_part = kwargs.get('lcsc_part', '')
        self.position = kwargs.get('position', (0, 0))
        self.rotation = kwargs.get('rotation', 0)
        self.properties = kwargs
        self.pins = {}
        self.uuid = str(uuid.uuid4())


class Net:
    """Represents an electrical net."""
    
    def __init__(self, name: str):
        self.name = name
        self.connections = []  # List of (component_ref, pin) tuples
        self.uuid = str(uuid.uuid4())
    
    def add_connection(self, component_ref: str, pin: str):
        self.connections.append((component_ref, pin))


class Schematic:
    """Represents a KiCad schematic."""
    
    def __init__(self, name: str):
        self.name = name
        self.components = {}  # Dict[reference, Component]
        self.nets = {}  # Dict[net_name, Net]
        self.sheet_size = 'A4'
        self.uuid = str(uuid.uuid4())
    
    def add_component(self, component: Component):
        self.components[component.reference] = component
    
    def add_net(self, net: Net):
        self.nets[net.name] = net
    
    def extract_netlist(self) -> Dict[str, Any]:
        """Extract netlist from schematic."""
        netlist = {
            'name': self.name,
            'components': {},
            'nets': {}
        }
        
        for ref, comp in self.components.items():
            netlist['components'][ref] = {
                'type': comp.type,
                'value': comp.value,
                'footprint': comp.footprint,
                'lcsc_part': comp.lcsc_part,
                'position': comp.position
            }
        
        for net_name, net in self.nets.items():
            netlist['nets'][net_name] = net.connections
        
        return netlist


class SchematicGenerator:
    """Generates KiCad schematics from high-level descriptions."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.kicad = KiCadInterface(config)
        self._component_library = self._load_component_library()
    
    def generate(self, design_spec: Dict[str, Any]) -> Schematic:
        """Generate schematic from design specification.
        
        Args:
            design_spec: Design specification dictionary
            
        Returns:
            Generated schematic object
        """
        logger.info(f"Generating schematic for {design_spec['name']}")
        
        # Create schematic
        schematic = Schematic(design_spec['name'])
        
        # Add components
        components_map = self._create_components(design_spec['components'])
        for comp in components_map.values():
            schematic.add_component(comp)
        
        # Create nets from connections
        nets = self._create_nets(design_spec['connections'], components_map)
        for net in nets.values():
            schematic.add_net(net)
        
        # Add power nets if specified
        if 'power' in design_spec:
            power_nets = self._create_power_nets(design_spec['power'], components_map)
            for net in power_nets.values():
                schematic.add_net(net)
        
        # Auto-arrange components
        self._arrange_components(schematic)
        
        # Generate KiCad schematic file
        if self.config.get('generate_files', True):
            self._generate_kicad_file(schematic)
        
        return schematic
    
    def _create_components(self, components_spec: List[Dict]) -> Dict[str, Component]:
        """Create components from specification."""
        components = {}
        
        for idx, comp_spec in enumerate(components_spec):
            # Generate reference if not provided
            ref = comp_spec.get('reference')
            if not ref:
                prefix = self._get_reference_prefix(comp_spec['type'])
                ref = f"{prefix}{idx + 1}"
            
            # Look up component in library
            lib_comp = self._lookup_component(comp_spec['type'], comp_spec['value'])
            
            # Create component
            component = Component(
                ref=ref,
                comp_type=comp_spec['type'],
                value=comp_spec['value'],
                footprint=lib_comp.get('footprint', ''),
                lcsc_part=lib_comp.get('lcsc_part', ''),
                **comp_spec.get('properties', {})
            )
            
            components[ref] = component
        
        return components
    
    def _create_nets(self, connections_spec: List[Dict], 
                     components: Dict[str, Component]) -> Dict[str, Net]:
        """Create nets from connection specification."""
        nets = {}
        
        for conn_spec in connections_spec:
            net_name = conn_spec.get('net', f"Net_{len(nets) + 1}")
            
            if net_name not in nets:
                nets[net_name] = Net(net_name)
            
            # Add all connections to the net
            for connection in conn_spec['connect']:
                if isinstance(connection, str):
                    # Simple format: "R1.1"
                    comp_ref, pin = connection.split('.')
                else:
                    # Dict format: {"component": "R1", "pin": "1"}
                    comp_ref = connection['component']
                    pin = connection['pin']
                
                if comp_ref in components:
                    nets[net_name].add_connection(comp_ref, pin)
                else:
                    logger.warning(f"Component {comp_ref} not found for net {net_name}")
        
        return nets
    
    def _create_power_nets(self, power_spec: Dict, 
                          components: Dict[str, Component]) -> Dict[str, Net]:
        """Create power and ground nets."""
        power_nets = {}
        
        # Create VCC net
        if 'vcc' in power_spec:
            vcc_net = Net('VCC')
            for conn in power_spec['vcc']:
                comp_ref, pin = conn.split('.')
                if comp_ref in components:
                    vcc_net.add_connection(comp_ref, pin)
            power_nets['VCC'] = vcc_net
        
        # Create GND net
        if 'gnd' in power_spec:
            gnd_net = Net('GND')
            for conn in power_spec['gnd']:
                comp_ref, pin = conn.split('.')
                if comp_ref in components:
                    gnd_net.add_connection(comp_ref, pin)
            power_nets['GND'] = gnd_net
        
        # Create other power nets
        for net_name, connections in power_spec.items():
            if net_name not in ['vcc', 'gnd']:
                net = Net(net_name.upper())
                for conn in connections:
                    comp_ref, pin = conn.split('.')
                    if comp_ref in components:
                        net.add_connection(comp_ref, pin)
                power_nets[net_name.upper()] = net
        
        return power_nets
    
    def _arrange_components(self, schematic: Schematic) -> None:
        """Auto-arrange components on schematic."""
        # Simple grid-based arrangement
        grid_size = 25.4  # mm (1 inch in schematic units)
        cols = 5
        
        for idx, (ref, comp) in enumerate(schematic.components.items()):
            row = idx // cols
            col = idx % cols
            comp.position = (col * grid_size * 2, row * grid_size * 2)
    
    def _generate_kicad_file(self, schematic: Schematic) -> None:
        """Generate KiCad schematic file."""
        output_path = self.config.output_dir / f"{schematic.name}.kicad_sch"
        logger.info(f"Generating KiCad schematic file: {output_path}")
        
        # This would use KiCad's file format
        # For now, we'll create a placeholder
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In a real implementation, this would generate proper KiCad format
        with open(output_path, 'w') as f:
            f.write(f"# KiCad Schematic for {schematic.name}\n")
            f.write("# Generated by PCB Automation Pipeline\n")
    
    def _load_component_library(self) -> Dict[str, Dict]:
        """Load component library."""
        # In a real implementation, this would load from files
        return {
            'resistor': {
                'symbol': 'Device:R',
                'footprint': 'Resistor_SMD:R_0603_1608Metric',
                'pins': 2
            },
            'capacitor': {
                'symbol': 'Device:C',
                'footprint': 'Capacitor_SMD:C_0603_1608Metric',
                'pins': 2
            },
            'led': {
                'symbol': 'Device:LED',
                'footprint': 'LED_SMD:LED_0603_1608Metric',
                'pins': 2
            },
            'connector': {
                'symbol': 'Connector:Conn_01x02_Pin',
                'footprint': 'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',
                'pins': 2
            }
        }
    
    def _lookup_component(self, comp_type: str, value: str) -> Dict[str, Any]:
        """Look up component in library."""
        # Normalize component type
        comp_type_lower = comp_type.lower()
        
        # Find in library
        if comp_type_lower in self._component_library:
            return self._component_library[comp_type_lower]
        
        # Default fallback
        logger.warning(f"Component type {comp_type} not found in library")
        return {
            'symbol': f'Device:{comp_type}',
            'footprint': '',
            'pins': 2
        }
    
    def _get_reference_prefix(self, comp_type: str) -> str:
        """Get reference designator prefix for component type."""
        prefixes = {
            'resistor': 'R',
            'capacitor': 'C',
            'inductor': 'L',
            'diode': 'D',
            'led': 'D',
            'transistor': 'Q',
            'ic': 'U',
            'connector': 'J',
            'switch': 'SW',
            'crystal': 'Y',
            'fuse': 'F',
        }
        
        return prefixes.get(comp_type.lower(), 'U')