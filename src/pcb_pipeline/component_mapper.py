"""
Symbolic-to-Physical Component Mapping Layer

This module provides intelligent mapping between high-level component descriptions
and actual manufacturer part numbers, supporting multiple suppliers and automatic
substitution based on availability and specifications.
"""

import logging
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
import requests
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class ComponentSpec:
    """High-level component specification"""
    type: str  # resistor, capacitor, ic, etc.
    value: Optional[str] = None  # 10k, 100nF, etc.
    tolerance: Optional[str] = None  # 5%, 1%, etc.
    power: Optional[str] = None  # 0.25W, 1W, etc.
    voltage: Optional[str] = None  # 50V, 16V, etc.
    package: Optional[str] = None  # 0603, SOIC-8, etc.
    temperature: Optional[str] = None  # -40C to 85C, etc.
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PhysicalComponent:
    """Physical component with manufacturer part number"""
    mpn: str  # Manufacturer part number
    manufacturer: str
    description: str
    package: str
    supplier: str  # LCSC, Digikey, Mouser, etc.
    supplier_pn: str  # Supplier part number
    price: Optional[float] = None
    stock: Optional[int] = None
    datasheet: Optional[str] = None
    specifications: Dict[str, Any] = field(default_factory=dict)
    

@dataclass
class MappingResult:
    """Result of component mapping"""
    primary: PhysicalComponent  # Best match
    alternatives: List[PhysicalComponent] = field(default_factory=list)
    confidence: float = 1.0  # 0-1 confidence score
    warnings: List[str] = field(default_factory=list)


class ComponentMapper:
    """Maps symbolic component descriptions to physical parts"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache_dir = Path(config.get('cache_dir', 'cache/components'))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load component database
        self.database = self._load_database()
        
        # Supplier APIs
        self.suppliers = {
            'lcsc': LCSCSupplier(config),
            'octopart': OctopartSupplier(config),
            'digikey': DigikeySupplier(config),
        }
        
    def _load_database(self) -> Dict[str, Any]:
        """Load local component database"""
        db_path = Path(__file__).parent / 'data' / 'component_database.json'
        if db_path.exists():
            with open(db_path) as f:
                return json.load(f)
        return self._create_default_database()
    
    def _create_default_database(self) -> Dict[str, Any]:
        """Create default component mapping database"""
        return {
            'resistor': {
                'patterns': [
                    r'(?P<value>\d+\.?\d*[kKmMrR]?)\s*(?P<unit>ohm|Ω)?',
                ],
                'common_values': {
                    '10k': {'lcsc': 'C25804', 'package': '0603', 'tolerance': '1%'},
                    '1k': {'lcsc': 'C21190', 'package': '0603', 'tolerance': '1%'},
                    '100': {'lcsc': 'C22775', 'package': '0603', 'tolerance': '1%'},
                    '4.7k': {'lcsc': 'C23162', 'package': '0603', 'tolerance': '1%'},
                    '100k': {'lcsc': 'C25803', 'package': '0603', 'tolerance': '1%'},
                    '0': {'lcsc': 'C21189', 'package': '0603', 'tolerance': '1%'},  # 0 ohm jumper
                },
                'attributes': ['tolerance', 'power', 'temperature']
            },
            'capacitor': {
                'patterns': [
                    r'(?P<value>\d+\.?\d*)\s*(?P<unit>[pnuμmF]F?)',
                ],
                'common_values': {
                    '100nF': {'lcsc': 'C14663', 'package': '0603', 'voltage': '50V'},
                    '10uF': {'lcsc': 'C19702', 'package': '0603', 'voltage': '16V'},
                    '1uF': {'lcsc': 'C15849', 'package': '0603', 'voltage': '50V'},
                    '22pF': {'lcsc': 'C1653', 'package': '0603', 'voltage': '50V'},
                    '100uF': {'lcsc': 'C16133', 'package': '1206', 'voltage': '16V'},
                },
                'attributes': ['voltage', 'tolerance', 'temperature', 'dielectric']
            },
            'led': {
                'patterns': [
                    r'(?P<color>red|green|blue|yellow|white|orange|rgb)',
                ],
                'common_values': {
                    'red': {'lcsc': 'C2286', 'package': '0603', 'voltage': '2.0V'},
                    'green': {'lcsc': 'C72043', 'package': '0603', 'voltage': '3.2V'},
                    'blue': {'lcsc': 'C72041', 'package': '0603', 'voltage': '3.2V'},
                    'yellow': {'lcsc': 'C72038', 'package': '0603', 'voltage': '2.0V'},
                },
                'attributes': ['color', 'brightness', 'voltage', 'current']
            },
            'ic': {
                'common_parts': {
                    '555': {'lcsc': 'C7593', 'package': 'SOIC-8', 'description': 'Timer IC'},
                    'NE555': {'lcsc': 'C7593', 'package': 'SOIC-8', 'description': 'Timer IC'},
                    'LM358': {'lcsc': 'C7950', 'package': 'SOIC-8', 'description': 'Dual Op-Amp'},
                    'ATmega328P': {'lcsc': 'C14877', 'package': 'TQFP-32', 'description': 'AVR MCU'},
                    'ESP32-WROOM-32': {'lcsc': 'C473893', 'package': 'SMD-38', 'description': 'WiFi/BT Module'},
                    'STM32F103C8T6': {'lcsc': 'C8734', 'package': 'LQFP-48', 'description': 'ARM Cortex-M3'},
                }
            },
            'connector': {
                'common_parts': {
                    'USB-C': {'lcsc': 'C165948', 'package': 'USB-C-16P', 'description': 'USB Type-C Receptacle'},
                    'USB-A': {'lcsc': 'C2345', 'package': 'USB-A-TH', 'description': 'USB Type-A Receptacle'},
                    'RJ45': {'lcsc': 'C86580', 'package': 'RJ45-8P8C', 'description': 'Ethernet Jack'},
                    'JST-XH-2': {'lcsc': 'C158012', 'package': 'JST-XH-2P', 'description': '2-pin JST XH'},
                    'Pin_Header_2x20': {'lcsc': 'C2337', 'package': '2.54mm-2x20P', 'description': 'GPIO Header'},
                }
            },
            'crystal': {
                'patterns': [
                    r'(?P<frequency>\d+\.?\d*)\s*(?P<unit>[kKmM]?Hz)',
                ],
                'common_values': {
                    '16MHz': {'lcsc': 'C16212', 'package': 'HC-49S', 'tolerance': '30ppm'},
                    '8MHz': {'lcsc': 'C16213', 'package': 'HC-49S', 'tolerance': '30ppm'},
                    '32.768kHz': {'lcsc': 'C32346', 'package': '3215', 'tolerance': '20ppm'},
                    '25MHz': {'lcsc': 'C16214', 'package': 'HC-49S', 'tolerance': '30ppm'},
                },
                'attributes': ['frequency', 'tolerance', 'load_capacitance']
            }
        }
    
    def map_component(self, spec: ComponentSpec) -> MappingResult:
        """Map a symbolic component to physical part"""
        logger.info(f"Mapping component: {spec}")
        
        # Check cache first
        cache_key = self._get_cache_key(spec)
        cached = self._get_cached_mapping(cache_key)
        if cached:
            return cached
        
        # Try local database first
        result = self._map_from_database(spec)
        
        # If no good match, search suppliers
        if not result or result.confidence < 0.8:
            supplier_results = self._search_suppliers(spec)
            if supplier_results:
                result = self._select_best_match(spec, supplier_results)
        
        # Cache the result
        if result:
            self._cache_mapping(cache_key, result)
        
        return result or MappingResult(
            primary=PhysicalComponent(
                mpn="UNKNOWN",
                manufacturer="Unknown",
                description=f"No match found for {spec.type}",
                package=spec.package or "Unknown",
                supplier="None",
                supplier_pn="N/A"
            ),
            confidence=0.0,
            warnings=[f"Could not find suitable part for {spec}"]
        )
    
    def _map_from_database(self, spec: ComponentSpec) -> Optional[MappingResult]:
        """Map component using local database"""
        if spec.type not in self.database:
            return None
        
        db_entry = self.database[spec.type]
        
        # Try direct value match
        if 'common_values' in db_entry and spec.value:
            normalized_value = self._normalize_value(spec.value)
            if normalized_value in db_entry['common_values']:
                part_info = db_entry['common_values'][normalized_value]
                return self._create_mapping_result(spec, part_info)
        
        # Try common parts (for ICs)
        if 'common_parts' in db_entry and spec.value:
            if spec.value.upper() in db_entry['common_parts']:
                part_info = db_entry['common_parts'][spec.value.upper()]
                return self._create_mapping_result(spec, part_info)
        
        return None
    
    def _normalize_value(self, value: str) -> str:
        """Normalize component value for matching"""
        # Convert various formats to standard
        value = value.strip().lower()
        
        # Handle resistor values
        value = value.replace('ohm', '').replace('Ω', '').replace('ω', '')
        value = value.replace(' ', '')
        # Convert 4r7 to 4.7k
        if 'r' in value.lower():
            parts = value.lower().split('r')
            if len(parts) == 2 and parts[0].replace('.', '').isdigit() and parts[1].replace('.', '').isdigit():
                value = f"{parts[0]}.{parts[1]}k"
        
        # Handle capacitor values
        value = value.replace('uf', 'uF').replace('μf', 'uF')
        value = value.replace('nf', 'nF').replace('pf', 'pF')
        
        # Handle multipliers
        if value.endswith('k'):
            try:
                num = float(value[:-1])
                value = f"{int(num)}k" if num.is_integer() else f"{num}k"
            except ValueError:
                pass
        
        return value
    
    def _create_mapping_result(self, spec: ComponentSpec, part_info: Dict) -> MappingResult:
        """Create mapping result from database entry"""
        primary = PhysicalComponent(
            mpn=part_info.get('mpn', part_info.get('lcsc', 'Unknown')),
            manufacturer=part_info.get('manufacturer', 'Unknown'),
            description=part_info.get('description', f"{spec.type} {spec.value or ''}"),
            package=part_info.get('package', spec.package or 'Unknown'),
            supplier='LCSC' if 'lcsc' in part_info else 'Unknown',
            supplier_pn=part_info.get('lcsc', 'Unknown'),
            specifications=part_info
        )
        
        return MappingResult(
            primary=primary,
            confidence=0.95,  # High confidence for database matches
            warnings=[]
        )
    
    def _search_suppliers(self, spec: ComponentSpec) -> List[PhysicalComponent]:
        """Search supplier APIs for matching components"""
        results = []
        
        for name, supplier in self.suppliers.items():
            if supplier.is_available():
                try:
                    matches = supplier.search(spec)
                    results.extend(matches)
                except Exception as e:
                    logger.warning(f"Supplier {name} search failed: {e}")
        
        return results
    
    def _select_best_match(self, spec: ComponentSpec, 
                          candidates: List[PhysicalComponent]) -> MappingResult:
        """Select best matching component from candidates"""
        if not candidates:
            return None
        
        # Score each candidate
        scored = []
        for candidate in candidates:
            score = self._score_candidate(spec, candidate)
            scored.append((score, candidate))
        
        # Sort by score
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Select top candidate and alternatives
        best_score, best_match = scored[0]
        alternatives = [c for s, c in scored[1:6] if s > 0.5]  # Top 5 alternatives
        
        return MappingResult(
            primary=best_match,
            alternatives=alternatives,
            confidence=best_score,
            warnings=self._generate_warnings(spec, best_match)
        )
    
    def _score_candidate(self, spec: ComponentSpec, 
                        candidate: PhysicalComponent) -> float:
        """Score how well a candidate matches the specification"""
        score = 0.0
        
        # Package match
        if spec.package and candidate.package:
            if spec.package.lower() == candidate.package.lower():
                score += 0.3
            elif self._packages_compatible(spec.package, candidate.package):
                score += 0.15
        
        # Value match (for passives)
        if spec.value and 'value' in candidate.specifications:
            if self._values_match(spec.value, candidate.specifications['value']):
                score += 0.3
        
        # Stock availability
        if candidate.stock and candidate.stock > 100:
            score += 0.2
        elif candidate.stock and candidate.stock > 0:
            score += 0.1
        
        # Price (prefer cheaper)
        if candidate.price:
            if candidate.price < 0.10:  # Less than 10 cents
                score += 0.1
            elif candidate.price < 1.00:  # Less than $1
                score += 0.05
        
        # Preferred suppliers
        if candidate.supplier in ['LCSC', 'Digikey']:
            score += 0.1
        
        return min(score, 1.0)
    
    def _packages_compatible(self, spec_pkg: str, cand_pkg: str) -> bool:
        """Check if two packages are compatible"""
        # Normalize package names
        spec_pkg = spec_pkg.lower().replace('-', '').replace('_', '')
        cand_pkg = cand_pkg.lower().replace('-', '').replace('_', '')
        
        # Direct match
        if spec_pkg == cand_pkg:
            return True
        
        # Common equivalences
        equivalences = [
            {'0603', '1608', '1608metric'},
            {'0805', '2012', '2012metric'},
            {'1206', '3216', '3216metric'},
            {'soic8', 'so8', 'soic8'},
            {'sot23', 'sot233', 'sot23'},
        ]
        
        for group in equivalences:
            if spec_pkg in group and cand_pkg in group:
                return True
        
        return False
    
    def _values_match(self, spec_value: str, cand_value: str) -> bool:
        """Check if component values match"""
        # Normalize both values
        spec_norm = self._normalize_value(spec_value)
        cand_norm = self._normalize_value(cand_value)
        
        return spec_norm == cand_norm
    
    def _generate_warnings(self, spec: ComponentSpec, 
                          match: PhysicalComponent) -> List[str]:
        """Generate warnings about the match"""
        warnings = []
        
        # Package mismatch
        if spec.package and match.package:
            if not self._packages_compatible(spec.package, match.package):
                warnings.append(f"Package mismatch: requested {spec.package}, "
                              f"matched {match.package}")
        
        # Stock warning
        if match.stock and match.stock < 100:
            warnings.append(f"Low stock: only {match.stock} units available")
        
        # Price warning
        if match.price and match.price > 10:
            warnings.append(f"High price: ${match.price:.2f} per unit")
        
        return warnings
    
    def _get_cache_key(self, spec: ComponentSpec) -> str:
        """Generate cache key for component spec"""
        key_parts = [
            spec.type,
            spec.value or 'none',
            spec.package or 'any',
            spec.tolerance or 'any',
        ]
        return '_'.join(key_parts).lower()
    
    def _get_cached_mapping(self, cache_key: str) -> Optional[MappingResult]:
        """Get cached mapping result"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                # Reconstruct MappingResult from JSON
                return self._mapping_from_json(data)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        return None
    
    def _cache_mapping(self, cache_key: str, result: MappingResult):
        """Cache mapping result"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(self._mapping_to_json(result), f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to cache mapping: {e}")
    
    def _mapping_to_json(self, result: MappingResult) -> Dict:
        """Convert MappingResult to JSON-serializable dict"""
        return {
            'primary': {
                'mpn': result.primary.mpn,
                'manufacturer': result.primary.manufacturer,
                'description': result.primary.description,
                'package': result.primary.package,
                'supplier': result.primary.supplier,
                'supplier_pn': result.primary.supplier_pn,
                'price': result.primary.price,
                'stock': result.primary.stock,
                'datasheet': result.primary.datasheet,
                'specifications': result.primary.specifications,
            },
            'alternatives': [
                {
                    'mpn': alt.mpn,
                    'manufacturer': alt.manufacturer,
                    'description': alt.description,
                    'package': alt.package,
                    'supplier': alt.supplier,
                    'supplier_pn': alt.supplier_pn,
                    'price': alt.price,
                    'stock': alt.stock,
                }
                for alt in result.alternatives
            ],
            'confidence': result.confidence,
            'warnings': result.warnings,
        }
    
    def _mapping_from_json(self, data: Dict) -> MappingResult:
        """Reconstruct MappingResult from JSON data"""
        primary_data = data['primary']
        primary = PhysicalComponent(
            mpn=primary_data['mpn'],
            manufacturer=primary_data['manufacturer'],
            description=primary_data['description'],
            package=primary_data['package'],
            supplier=primary_data['supplier'],
            supplier_pn=primary_data['supplier_pn'],
            price=primary_data.get('price'),
            stock=primary_data.get('stock'),
            datasheet=primary_data.get('datasheet'),
            specifications=primary_data.get('specifications', {}),
        )
        
        alternatives = [
            PhysicalComponent(
                mpn=alt['mpn'],
                manufacturer=alt['manufacturer'],
                description=alt['description'],
                package=alt['package'],
                supplier=alt['supplier'],
                supplier_pn=alt['supplier_pn'],
                price=alt.get('price'),
                stock=alt.get('stock'),
            )
            for alt in data.get('alternatives', [])
        ]
        
        return MappingResult(
            primary=primary,
            alternatives=alternatives,
            confidence=data['confidence'],
            warnings=data.get('warnings', []),
        )


class LCSCSupplier:
    """LCSC component supplier interface"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('lcsc_api_key')
        self.base_url = "https://api.lcsc.com/v1"
    
    def is_available(self) -> bool:
        """Check if LCSC API is available"""
        # LCSC API requires application process
        return bool(self.api_key)
    
    def search(self, spec: ComponentSpec) -> List[PhysicalComponent]:
        """Search LCSC for matching components"""
        # This would implement actual LCSC API search
        # For now, return empty list
        return []


class OctopartSupplier:
    """Octopart component supplier interface"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('octopart_api_key')
        self.base_url = "https://octopart.com/api/v4"
    
    def is_available(self) -> bool:
        """Check if Octopart API is available"""
        return bool(self.api_key)
    
    def search(self, spec: ComponentSpec) -> List[PhysicalComponent]:
        """Search Octopart for matching components"""
        if not self.is_available():
            return []
        
        # Build search query
        query_parts = [spec.type]
        if spec.value:
            query_parts.append(spec.value)
        
        query = ' '.join(query_parts)
        
        # Make API request
        headers = {'apikey': self.api_key}
        params = {
            'q': query,
            'start': 0,
            'limit': 10,
            'include': 'specs,offers'
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            results = []
            data = response.json()
            
            for result in data.get('results', []):
                part = result.get('part', {})
                
                # Get best offer
                best_offer = self._get_best_offer(part.get('offers', []))
                
                if best_offer:
                    component = PhysicalComponent(
                        mpn=part.get('mpn', 'Unknown'),
                        manufacturer=part.get('manufacturer', {}).get('name', 'Unknown'),
                        description=part.get('description', ''),
                        package=self._extract_package(part.get('specs', {})),
                        supplier=best_offer['seller']['name'],
                        supplier_pn=best_offer.get('sku', 'Unknown'),
                        price=best_offer.get('prices', {}).get('USD', [{}])[0].get('price'),
                        stock=best_offer.get('in_stock_quantity', 0),
                        datasheet=part.get('datasheet_url'),
                        specifications=part.get('specs', {})
                    )
                    results.append(component)
            
            return results
            
        except Exception as e:
            logger.error(f"Octopart search failed: {e}")
            return []
    
    def _get_best_offer(self, offers: List[Dict]) -> Optional[Dict]:
        """Select best offer from list"""
        # Filter for in-stock offers
        in_stock = [o for o in offers if o.get('in_stock_quantity', 0) > 0]
        
        if not in_stock:
            return None
        
        # Sort by price (ascending)
        in_stock.sort(key=lambda o: o.get('prices', {}).get('USD', [{'price': float('inf')}])[0].get('price', float('inf')))
        
        return in_stock[0]
    
    def _extract_package(self, specs: Dict) -> str:
        """Extract package info from specs"""
        # Common package spec keys
        package_keys = ['case_package', 'package', 'case', 'package_case']
        
        for key in package_keys:
            if key in specs:
                values = specs[key].get('value', [])
                if values:
                    return values[0]
        
        return 'Unknown'


class DigikeySupplier:
    """Digikey component supplier interface"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('digikey_api_key')
        self.client_id = config.get('digikey_client_id')
    
    def is_available(self) -> bool:
        """Check if Digikey API is available"""
        return bool(self.api_key and self.client_id)
    
    def search(self, spec: ComponentSpec) -> List[PhysicalComponent]:
        """Search Digikey for matching components"""
        # Digikey API implementation would go here
        # Requires OAuth2 authentication
        return []