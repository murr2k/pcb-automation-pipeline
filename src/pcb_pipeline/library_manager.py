import logging
import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

from .config import PipelineConfig

logger = logging.getLogger(__name__)


class ComponentLibraryManager:
    """Manages component libraries and footprint mappings."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.library_path = Path(config.get('library_path', 'templates/component_libraries'))
        self.library_path.mkdir(parents=True, exist_ok=True)
        
        # Component databases
        self.components = {}  # Main component database
        self.footprint_map = {}  # Component to footprint mapping
        self.lcsc_map = {}  # Component to LCSC part mapping
        self.jlc_basic_parts = set()  # JLCPCB basic parts
        
        # Load libraries
        self._load_libraries()
    
    def _load_libraries(self) -> None:
        """Load component libraries from files."""
        # Load standard components
        self._load_standard_components()
        
        # Load custom libraries
        for lib_file in self.library_path.glob('*.json'):
            self._load_library_file(lib_file)
        
        # Load LCSC mapping
        lcsc_file = self.library_path / 'lcsc_parts.csv'
        if lcsc_file.exists():
            self._load_lcsc_mapping(lcsc_file)
        
        # Load JLC basic parts
        jlc_file = self.library_path / 'jlc_basic_parts.txt'
        if jlc_file.exists():
            self._load_jlc_basic_parts(jlc_file)
    
    def _load_standard_components(self) -> None:
        """Load standard component definitions."""
        # Basic passive components
        self.components.update({
            # Resistors
            'resistor': {
                'type': 'resistor',
                'symbol': 'Device:R',
                'default_footprints': {
                    '0402': 'Resistor_SMD:R_0402_1005Metric',
                    '0603': 'Resistor_SMD:R_0603_1608Metric',
                    '0805': 'Resistor_SMD:R_0805_2012Metric',
                    '1206': 'Resistor_SMD:R_1206_3216Metric',
                    'THT': 'Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal'
                },
                'parameters': ['resistance', 'tolerance', 'power'],
                'pins': 2
            },
            
            # Capacitors
            'capacitor': {
                'type': 'capacitor',
                'symbol': 'Device:C',
                'default_footprints': {
                    '0402': 'Capacitor_SMD:C_0402_1005Metric',
                    '0603': 'Capacitor_SMD:C_0603_1608Metric',
                    '0805': 'Capacitor_SMD:C_0805_2012Metric',
                    '1206': 'Capacitor_SMD:C_1206_3216Metric',
                    'THT': 'Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm'
                },
                'parameters': ['capacitance', 'voltage', 'tolerance', 'dielectric'],
                'pins': 2
            },
            
            # Inductors
            'inductor': {
                'type': 'inductor',
                'symbol': 'Device:L',
                'default_footprints': {
                    '0603': 'Inductor_SMD:L_0603_1608Metric',
                    '0805': 'Inductor_SMD:L_0805_2012Metric',
                    '1210': 'Inductor_SMD:L_1210_3225Metric',
                },
                'parameters': ['inductance', 'current', 'tolerance'],
                'pins': 2
            },
            
            # LEDs
            'led': {
                'type': 'led',
                'symbol': 'Device:LED',
                'default_footprints': {
                    '0603': 'LED_SMD:LED_0603_1608Metric',
                    '0805': 'LED_SMD:LED_0805_2012Metric',
                    '1206': 'LED_SMD:LED_1206_3216Metric',
                    'THT_3mm': 'LED_THT:LED_D3.0mm',
                    'THT_5mm': 'LED_THT:LED_D5.0mm'
                },
                'parameters': ['color', 'voltage_forward', 'current'],
                'pins': 2
            },
            
            # Diodes
            'diode': {
                'type': 'diode',
                'symbol': 'Device:D',
                'default_footprints': {
                    'SOD-123': 'Diode_SMD:D_SOD-123',
                    'SOD-323': 'Diode_SMD:D_SOD-323',
                    'SMA': 'Diode_SMD:D_SMA',
                    'DO-41': 'Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal'
                },
                'parameters': ['voltage_reverse', 'current_forward'],
                'pins': 2
            },
            
            # Transistors
            'transistor_npn': {
                'type': 'transistor',
                'symbol': 'Device:Q_NPN_BCE',
                'default_footprints': {
                    'SOT-23': 'Package_TO_SOT_SMD:SOT-23',
                    'SOT-223': 'Package_TO_SOT_SMD:SOT-223-3_TabPin2',
                    'TO-92': 'Package_TO_SOT_THT:TO-92_Inline'
                },
                'parameters': ['model', 'voltage_ce', 'current_collector'],
                'pins': 3
            },
            
            # Connectors
            'connector_2pin': {
                'type': 'connector',
                'symbol': 'Connector:Conn_01x02_Pin',
                'default_footprints': {
                    '2.54mm': 'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical',
                    '2.00mm': 'Connector_PinHeader_2.00mm:PinHeader_1x02_P2.00mm_Vertical',
                    'JST_XH': 'Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical'
                },
                'parameters': ['pitch', 'current_rating'],
                'pins': 2
            }
        })
    
    def _load_library_file(self, lib_file: Path) -> None:
        """Load a component library from JSON file."""
        try:
            with open(lib_file, 'r') as f:
                library_data = json.load(f)
            
            # Merge with existing components
            self.components.update(library_data.get('components', {}))
            self.footprint_map.update(library_data.get('footprint_map', {}))
            
            logger.info(f"Loaded library: {lib_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to load library {lib_file}: {e}")
    
    def _load_lcsc_mapping(self, lcsc_file: Path) -> None:
        """Load LCSC part number mappings."""
        try:
            with open(lcsc_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = f"{row['type']}_{row['value']}"
                    self.lcsc_map[key] = row['lcsc_part']
            
            logger.info(f"Loaded {len(self.lcsc_map)} LCSC mappings")
            
        except Exception as e:
            logger.error(f"Failed to load LCSC mapping: {e}")
    
    def _load_jlc_basic_parts(self, jlc_file: Path) -> None:
        """Load JLCPCB basic parts list."""
        try:
            with open(jlc_file, 'r') as f:
                self.jlc_basic_parts = set(line.strip() for line in f)
            
            logger.info(f"Loaded {len(self.jlc_basic_parts)} JLC basic parts")
            
        except Exception as e:
            logger.error(f"Failed to load JLC basic parts: {e}")
    
    def get_component(self, comp_type: str, value: str, 
                     package: Optional[str] = None) -> Dict[str, Any]:
        """Get component information.
        
        Args:
            comp_type: Component type (e.g., 'resistor', 'capacitor')
            value: Component value (e.g., '10k', '100nF')
            package: Package type (e.g., '0603', 'SOT-23')
            
        Returns:
            Component information dictionary
        """
        # Normalize type
        comp_type_lower = comp_type.lower()
        
        # Get base component
        if comp_type_lower in self.components:
            component = self.components[comp_type_lower].copy()
        else:
            # Try to find by partial match
            for key, comp in self.components.items():
                if comp_type_lower in key or key in comp_type_lower:
                    component = comp.copy()
                    break
            else:
                logger.warning(f"Unknown component type: {comp_type}")
                return self._get_default_component(comp_type)
        
        # Add value
        component['value'] = value
        
        # Select footprint
        if package and package in component.get('default_footprints', {}):
            component['footprint'] = component['default_footprints'][package]
        else:
            # Use first available footprint
            footprints = component.get('default_footprints', {})
            if footprints:
                component['footprint'] = list(footprints.values())[0]
        
        # Find LCSC part if available
        component['lcsc_part'] = self.find_lcsc_part(comp_type, value, package)
        
        return component
    
    def find_lcsc_part(self, comp_type: str, value: str, 
                      package: Optional[str] = None) -> Optional[str]:
        """Find LCSC part number for component.
        
        Args:
            comp_type: Component type
            value: Component value
            package: Package type
            
        Returns:
            LCSC part number or None
        """
        # Try exact match
        key = f"{comp_type.lower()}_{value}"
        if key in self.lcsc_map:
            return self.lcsc_map[key]
        
        # Try with package
        if package:
            key_with_package = f"{comp_type.lower()}_{value}_{package}"
            if key_with_package in self.lcsc_map:
                return self.lcsc_map[key_with_package]
        
        # Try to find similar
        # This would implement fuzzy matching in a real system
        
        return None
    
    def is_basic_part(self, lcsc_part: str) -> bool:
        """Check if LCSC part is a JLCPCB basic part.
        
        Args:
            lcsc_part: LCSC part number
            
        Returns:
            True if basic part
        """
        return lcsc_part in self.jlc_basic_parts
    
    def add_custom_component(self, name: str, component_data: Dict[str, Any]) -> None:
        """Add a custom component to the library.
        
        Args:
            name: Component name
            component_data: Component information
        """
        self.components[name] = component_data
        logger.info(f"Added custom component: {name}")
    
    def save_library(self, filename: str) -> None:
        """Save current library to file.
        
        Args:
            filename: Output filename
        """
        output_file = self.library_path / filename
        
        library_data = {
            'components': self.components,
            'footprint_map': self.footprint_map,
            'metadata': {
                'version': '1.0',
                'component_count': len(self.components),
                'lcsc_part_count': len(self.lcsc_map)
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(library_data, f, indent=2)
        
        logger.info(f"Saved library to {output_file}")
    
    def search_components(self, query: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Search for components in library.
        
        Args:
            query: Search query
            filters: Optional filters (type, package, etc.)
            
        Returns:
            List of matching components
        """
        results = []
        query_lower = query.lower()
        
        for name, component in self.components.items():
            # Check name match
            if query_lower in name.lower():
                match = True
            # Check type match
            elif query_lower in component.get('type', '').lower():
                match = True
            # Check description match
            elif query_lower in component.get('description', '').lower():
                match = True
            else:
                match = False
            
            # Apply filters
            if match and filters:
                for key, value in filters.items():
                    if component.get(key) != value:
                        match = False
                        break
            
            if match:
                results.append({
                    'name': name,
                    **component
                })
        
        return results
    
    def _get_default_component(self, comp_type: str) -> Dict[str, Any]:
        """Get default component structure."""
        return {
            'type': comp_type,
            'symbol': f'Device:{comp_type}',
            'footprint': '',
            'pins': 2,
            'parameters': [],
            'value': ''
        }
    
    def import_csv_library(self, csv_file: Path) -> int:
        """Import components from CSV file.
        
        Args:
            csv_file: Path to CSV file
            
        Returns:
            Number of components imported
        """
        imported = 0
        
        try:
            with open(csv_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Extract component data from CSV
                    comp_type = row.get('Type', '').lower()
                    value = row.get('Value', '')
                    footprint = row.get('Footprint', '')
                    lcsc_part = row.get('LCSC', '')
                    
                    if comp_type and value:
                        key = f"{comp_type}_{value}"
                        
                        # Add to appropriate maps
                        if footprint:
                            self.footprint_map[key] = footprint
                        if lcsc_part:
                            self.lcsc_map[key] = lcsc_part
                        
                        imported += 1
            
            logger.info(f"Imported {imported} components from {csv_file}")
            
        except Exception as e:
            logger.error(f"Failed to import CSV library: {e}")
        
        return imported