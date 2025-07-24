import logging
import requests
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import base64

from .config import PipelineConfig
from .pcb_layout import PCBLayout
from .fab_interface import FabricationInterface

logger = logging.getLogger(__name__)


class MacroFabInterface(FabricationInterface):
    """MacroFab PCB manufacturing interface with full API integration."""
    
    def __init__(self, config: PipelineConfig):
        super().__init__(config)
        self.name = "macrofab"
        self.api_url = "https://api.macrofab.com/api/v3"
        self.api_key = config.get('macrofab_api_key', 'k2TlSRhDC41lKLdP5QxeTDP3v4AcnCO')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def prepare_order(self, pcb_layout: PCBLayout, **kwargs) -> Dict[str, Any]:
        """Prepare order data for MacroFab submission.
        
        Args:
            pcb_layout: PCB layout to order
            **kwargs: Additional order parameters
            
        Returns:
            Order data dictionary formatted for MacroFab API
        """
        logger.info("Preparing MacroFab order")
        
        board_width, board_height = pcb_layout.board_size
        
        # MacroFab-specific order structure
        order_data = {
            "pcb": {
                "name": pcb_layout.name,
                "description": kwargs.get('description', f'PCB for {pcb_layout.name}'),
                "board_length_mm": board_height,
                "board_width_mm": board_width,
                "board_thickness_mm": self.config.get('board_thickness', 1.6),
                "num_layers": self.config.get('copper_layers', 2),
                "surface_finish": self._map_surface_finish(
                    self.config.get('surface_finish', 'HASL')
                ),
                "silkscreen_color": self._map_color(
                    self.config.get('silkscreen_color', 'white')
                ),
                "solder_mask_color": self._map_color(
                    self.config.get('solder_mask_color', 'green')
                ),
                "min_trace_width_mm": self.config.get('min_track_width', 0.15),
                "min_hole_diameter_mm": self.config.get('min_hole_size', 0.3),
                "controlled_impedance": kwargs.get('controlled_impedance', False),
                "stackup": self._generate_stackup(self.config.get('copper_layers', 2))
            },
            "placement": {
                "quantity": kwargs.get('quantity', 10),
                "turn_around_time": kwargs.get('turn_around_time', 'standard'),
                "customer_supplied_parts": kwargs.get('customer_parts', False)
            },
            "files": {
                "gerbers": None,  # Will be populated with uploaded file IDs
                "placement": None,
                "bom": None
            }
        }
        
        # Add assembly options if requested
        if kwargs.get('assembly_service', False):
            order_data['assembly'] = {
                "sides": kwargs.get('assembly_sides', 'top'),
                "conformal_coating": kwargs.get('conformal_coating', False),
                "functional_test": kwargs.get('functional_test', False),
                "notes": kwargs.get('assembly_notes', '')
            }
        
        return order_data
    
    def submit_order(self, order_data: Dict[str, Any]) -> str:
        """Submit order to MacroFab.
        
        Args:
            order_data: Prepared order data
            
        Returns:
            Order ID from MacroFab
        """
        logger.info("Submitting order to MacroFab")
        
        try:
            # First, create the PCB project
            pcb_response = self._create_pcb_project(order_data['pcb'])
            pcb_id = pcb_response['id']
            logger.info(f"Created PCB project: {pcb_id}")
            
            # Upload manufacturing files
            file_ids = self._upload_files(pcb_id, order_data.get('file_paths', {}))
            
            # Create placement (order)
            placement_data = {
                "pcb_id": pcb_id,
                "quantity": order_data['placement']['quantity'],
                "turn_around_time": order_data['placement']['turn_around_time'],
                "file_ids": file_ids,
                "notes": order_data.get('notes', '')
            }
            
            response = self.session.post(
                f"{self.api_url}/placements",
                json=placement_data
            )
            response.raise_for_status()
            
            result = response.json()
            order_id = result['placement_id']
            
            logger.info(f"Order submitted successfully. Order ID: {order_id}")
            return order_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to submit order: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
    
    def get_quote(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get price quote from MacroFab.
        
        Args:
            order_data: Order specifications
            
        Returns:
            Quote information including price and lead time
        """
        logger.info("Getting quote from MacroFab")
        
        try:
            # Create quote request
            quote_request = {
                "pcb": {
                    "board_length_mm": order_data['pcb']['board_length_mm'],
                    "board_width_mm": order_data['pcb']['board_width_mm'],
                    "board_thickness_mm": order_data['pcb']['board_thickness_mm'],
                    "num_layers": order_data['pcb']['num_layers'],
                    "surface_finish": order_data['pcb']['surface_finish']
                },
                "quantity": order_data['placement']['quantity'],
                "turn_around_time": order_data['placement']['turn_around_time'],
                "include_assembly": 'assembly' in order_data
            }
            
            response = self.session.post(
                f"{self.api_url}/quotes",
                json=quote_request
            )
            response.raise_for_status()
            
            quote = response.json()
            
            return {
                'price': quote['total_price_usd'],
                'currency': 'USD',
                'lead_time': quote['lead_time_days'],
                'pcb_price': quote.get('pcb_price_usd', 0),
                'assembly_price': quote.get('assembly_price_usd', 0),
                'shipping_options': self._parse_shipping_options(quote),
                'breakdown': quote
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get quote: {e}")
            # Return simulated quote as fallback
            return self._simulate_quote(order_data)
    
    def check_order_status(self, order_id: str) -> Dict[str, Any]:
        """Check order status from MacroFab.
        
        Args:
            order_id: MacroFab order/placement ID
            
        Returns:
            Order status information
        """
        try:
            response = self.session.get(
                f"{self.api_url}/placements/{order_id}"
            )
            response.raise_for_status()
            
            placement = response.json()
            
            return {
                'order_id': order_id,
                'status': placement['status'],
                'stage': placement.get('current_stage', 'unknown'),
                'progress': placement.get('progress_percentage', 0),
                'estimated_completion': placement.get('estimated_completion_date'),
                'tracking_number': placement.get('tracking_number'),
                'notes': placement.get('notes', [])
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check order status: {e}")
            raise
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get MacroFab manufacturing capabilities."""
        return {
            'name': 'MacroFab',
            'location': 'USA (Houston, TX)',
            'api_available': True,
            'max_board_size': (457, 610),  # mm (18" x 24")
            'min_board_size': (12.7, 12.7),  # mm (0.5" x 0.5")
            'max_layers': 20,
            'min_trace_width': 0.127,  # mm (5 mil)
            'min_drill_size': 0.2,  # mm (8 mil)
            'min_via_diameter': 0.254,  # mm (10 mil)
            'surface_finishes': ['HASL', 'Lead-free HASL', 'ENIG', 'OSP', 'Immersion Silver', 'Immersion Tin'],
            'solder_mask_colors': ['green', 'red', 'blue', 'black', 'white', 'yellow', 'purple'],
            'silkscreen_colors': ['white', 'black', 'yellow'],
            'assembly_service': True,
            'inventory_service': True,
            'fulfillment_service': True,
            'lead_time_days': {
                'standard': 15,
                'expedite': 10,
                'rush': 5
            },
            'certifications': ['ISO 9001:2015', 'IPC-A-610', 'IPC J-STD-001'],
            'countries': ['USA', 'Canada', 'Mexico', 'International shipping']
        }
    
    def _create_pcb_project(self, pcb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a PCB project in MacroFab.
        
        Args:
            pcb_data: PCB specifications
            
        Returns:
            Created PCB project data
        """
        response = self.session.post(
            f"{self.api_url}/pcbs",
            json=pcb_data
        )
        response.raise_for_status()
        return response.json()
    
    def _upload_files(self, pcb_id: str, file_paths: Dict[str, Path]) -> Dict[str, str]:
        """Upload manufacturing files to MacroFab.
        
        Args:
            pcb_id: PCB project ID
            file_paths: Dictionary of file type to file path
            
        Returns:
            Dictionary of file type to uploaded file ID
        """
        file_ids = {}
        
        for file_type, file_path in file_paths.items():
            if not file_path or not Path(file_path).exists():
                continue
            
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Create file upload request
            upload_data = {
                'pcb_id': pcb_id,
                'file_type': file_type,
                'filename': Path(file_path).name,
                'content': base64.b64encode(file_content).decode('utf-8')
            }
            
            response = self.session.post(
                f"{self.api_url}/files",
                json=upload_data
            )
            response.raise_for_status()
            
            file_id = response.json()['file_id']
            file_ids[file_type] = file_id
            logger.info(f"Uploaded {file_type} file: {file_id}")
        
        return file_ids
    
    def _map_surface_finish(self, finish: str) -> str:
        """Map surface finish names to MacroFab format."""
        mapping = {
            'HASL': 'hasl',
            'Lead-free HASL': 'lead_free_hasl',
            'ENIG': 'enig',
            'OSP': 'osp',
            'Immersion Silver': 'immersion_silver',
            'Immersion Tin': 'immersion_tin'
        }
        return mapping.get(finish, 'hasl')
    
    def _map_color(self, color: str) -> str:
        """Map color names to MacroFab format."""
        return color.lower()
    
    def _generate_stackup(self, num_layers: int) -> Dict[str, Any]:
        """Generate stackup configuration for MacroFab."""
        # Simplified stackup - MacroFab will use their standard
        return {
            'num_layers': num_layers,
            'copper_weight_oz': 1,  # 1oz copper standard
            'core_thickness_mm': 1.6 / (num_layers - 1) if num_layers > 2 else 1.6
        }
    
    def _parse_shipping_options(self, quote: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse shipping options from quote."""
        options = []
        
        if 'shipping_options' in quote:
            for option in quote['shipping_options']:
                options.append({
                    'method': option['name'],
                    'cost': option['price_usd'],
                    'days': option['transit_days']
                })
        else:
            # Default options
            options = [
                {'method': 'Standard Ground', 'cost': 15, 'days': 5},
                {'method': '2-Day Air', 'cost': 45, 'days': 2},
                {'method': 'Next Day Air', 'cost': 75, 'days': 1}
            ]
        
        return options
    
    def _simulate_quote(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate quote when API fails."""
        # Calculate simulated pricing
        area = (order_data['pcb']['board_width_mm'] * 
                order_data['pcb']['board_length_mm']) / 100  # cm²
        
        layers = order_data['pcb']['num_layers']
        quantity = order_data['placement']['quantity']
        
        # MacroFab typical pricing model
        setup_fee = 250  # One-time setup
        per_board_base = 15  # Base price per board
        per_layer_cost = 5  # Additional cost per layer pair
        area_cost = area * 0.5  # Cost per cm²
        
        board_cost = per_board_base + (layers - 2) * per_layer_cost + area_cost
        total_pcb_cost = setup_fee + (board_cost * quantity)
        
        # Assembly cost if requested
        assembly_cost = 0
        if 'assembly' in order_data:
            assembly_cost = quantity * 25  # Simplified assembly cost
        
        return {
            'price': round(total_pcb_cost + assembly_cost, 2),
            'currency': 'USD',
            'lead_time': 15,
            'pcb_price': round(total_pcb_cost, 2),
            'assembly_price': round(assembly_cost, 2),
            'shipping_options': [
                {'method': 'Standard Ground', 'cost': 15, 'days': 5},
                {'method': '2-Day Air', 'cost': 45, 'days': 2}
            ]
        }
    
    def get_inventory(self) -> List[Dict[str, Any]]:
        """Get current inventory stored at MacroFab."""
        try:
            response = self.session.get(f"{self.api_url}/inventory")
            response.raise_for_status()
            return response.json()['items']
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get inventory: {e}")
            return []
    
    def create_product(self, product_data: Dict[str, Any]) -> str:
        """Create a product for fulfillment."""
        try:
            response = self.session.post(
                f"{self.api_url}/products",
                json=product_data
            )
            response.raise_for_status()
            return response.json()['product_id']
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create product: {e}")
            raise