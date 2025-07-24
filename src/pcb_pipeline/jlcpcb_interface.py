import logging
import requests
import json
import zipfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .config import PipelineConfig
from .pcb_layout import PCBLayout

logger = logging.getLogger(__name__)


class JLCPCBInterface:
    """Interface for JLCPCB API and order management."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.api_key = config.jlcpcb_api_key
        self.api_secret = config.get('jlcpcb_api_secret')
        self.api_url = config.get('jlcpcb_api_url', 'https://api.jlcpcb.com/v1')
        self.session = requests.Session()
        
        if self.api_key and self.api_secret:
            self._authenticate()
    
    def _authenticate(self) -> None:
        """Authenticate with JLCPCB API."""
        # Note: Actual authentication would depend on JLCPCB's API implementation
        # This is a placeholder for the authentication process
        logger.info("Authenticating with JLCPCB API")
        
        # Set authentication headers
        self.session.headers.update({
            'API-Key': self.api_key,
            'API-Secret': self.api_secret,
            'Content-Type': 'application/json'
        })
    
    def prepare_order(self, pcb_layout: PCBLayout, **kwargs) -> Dict[str, Any]:
        """Prepare order data for submission.
        
        Args:
            pcb_layout: PCB layout to order
            **kwargs: Additional order parameters
            
        Returns:
            Order data dictionary
        """
        logger.info("Preparing JLCPCB order")
        
        # Get board specifications
        board_width, board_height = pcb_layout.board_size
        
        order_data = {
            'project_name': pcb_layout.name,
            'board_type': 'single',  # or 'panel'
            'board_layers': self.config.get('copper_layers', 2),
            'board_width': board_width,
            'board_height': board_height,
            'board_thickness': self.config.get('board_thickness', 1.6),
            'quantity': kwargs.get('quantity', 5),
            
            # Manufacturing options
            'surface_finish': self.config.get('surface_finish', 'HASL'),
            'solder_mask_color': self.config.get('solder_mask_color', 'green'),
            'silkscreen_color': self.config.get('silkscreen_color', 'white'),
            'copper_weight': kwargs.get('copper_weight', 1),  # oz
            
            # Special options
            'gold_fingers': kwargs.get('gold_fingers', False),
            'castellated_holes': kwargs.get('castellated_holes', False),
            'remove_order_number': kwargs.get('remove_order_number', 'yes'),
            
            # Assembly options
            'assembly_service': self.config.get('assembly_service', False),
            'assembly_side': kwargs.get('assembly_side', 'top'),
            'tooling_holes': kwargs.get('tooling_holes', 'added'),
        }
        
        # Add assembly data if enabled
        if order_data['assembly_service']:
            order_data['assembly'] = self._prepare_assembly_data(pcb_layout)
        
        return order_data
    
    def submit_order(self, order_data: Dict[str, Any]) -> str:
        """Submit order to JLCPCB.
        
        Args:
            order_data: Prepared order data
            
        Returns:
            Order ID
        """
        if not self.api_key or not self.api_secret:
            logger.error("JLCPCB API credentials not configured")
            return self._simulate_order_submission(order_data)
        
        logger.info("Submitting order to JLCPCB")
        
        try:
            # Upload Gerber files
            gerber_url = self._upload_gerbers(order_data['project_name'])
            order_data['gerber_file_url'] = gerber_url
            
            # Submit order
            response = self.session.post(
                f"{self.api_url}/orders",
                json=order_data
            )
            response.raise_for_status()
            
            result = response.json()
            order_id = result.get('order_id')
            
            logger.info(f"Order submitted successfully. Order ID: {order_id}")
            return order_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to submit order: {e}")
            raise
    
    def get_quote(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get price quote for PCB order.
        
        Args:
            order_data: Order specifications
            
        Returns:
            Quote information including price and lead time
        """
        if not self.api_key:
            return self._simulate_quote(order_data)
        
        logger.info("Getting quote from JLCPCB")
        
        try:
            response = self.session.post(
                f"{self.api_url}/quote",
                json=order_data
            )
            response.raise_for_status()
            
            quote = response.json()
            return {
                'price': quote.get('total_price'),
                'currency': quote.get('currency', 'USD'),
                'lead_time': quote.get('lead_time_days'),
                'shipping_options': quote.get('shipping_options', [])
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get quote: {e}")
            return self._simulate_quote(order_data)
    
    def check_order_status(self, order_id: str) -> Dict[str, Any]:
        """Check order status.
        
        Args:
            order_id: JLCPCB order ID
            
        Returns:
            Order status information
        """
        if not self.api_key:
            return {'status': 'simulated', 'order_id': order_id}
        
        try:
            response = self.session.get(
                f"{self.api_url}/orders/{order_id}"
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check order status: {e}")
            raise
    
    def get_component_info(self, lcsc_part: str) -> Dict[str, Any]:
        """Get component information from LCSC/JLCPCB.
        
        Args:
            lcsc_part: LCSC part number
            
        Returns:
            Component information including price and availability
        """
        # This would query the JLCPCB parts API
        # For now, return simulated data
        return {
            'part_number': lcsc_part,
            'description': 'Component description',
            'manufacturer': 'Manufacturer',
            'stock': 1000,
            'price': 0.10,
            'category': 'basic'  # basic, extended
        }
    
    def _upload_gerbers(self, project_name: str) -> str:
        """Upload Gerber files to JLCPCB.
        
        Args:
            project_name: Project name
            
        Returns:
            URL of uploaded Gerber files
        """
        # Create zip file with Gerbers
        gerber_dir = self.config.output_dir / 'gerbers'
        zip_path = gerber_dir / f"{project_name}_gerbers.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for gerber_file in gerber_dir.glob('*.gbr'):
                zf.write(gerber_file, gerber_file.name)
            for drill_file in gerber_dir.glob('*.drl'):
                zf.write(drill_file, drill_file.name)
        
        # Upload zip file
        # This would use JLCPCB's file upload API
        # For now, return a placeholder URL
        return f"https://api.jlcpcb.com/files/{project_name}_gerbers.zip"
    
    def _prepare_assembly_data(self, pcb_layout: PCBLayout) -> Dict[str, Any]:
        """Prepare assembly data for PCBA service.
        
        Args:
            pcb_layout: PCB layout with component information
            
        Returns:
            Assembly data dictionary
        """
        components = []
        
        for ref, comp in pcb_layout.components.items():
            if comp.get('lcsc_part'):
                components.append({
                    'reference': ref,
                    'lcsc_part': comp['lcsc_part'],
                    'position': comp['position'],
                    'rotation': comp['rotation'],
                    'layer': comp['layer']
                })
        
        return {
            'components': components,
            'component_count': len(components),
            'unique_parts': len(set(c['lcsc_part'] for c in components)),
            'bom_file': 'bom.csv',
            'pnp_file': 'pick_and_place.csv'
        }
    
    def _simulate_order_submission(self, order_data: Dict[str, Any]) -> str:
        """Simulate order submission when API is not available.
        
        Args:
            order_data: Order data
            
        Returns:
            Simulated order ID
        """
        logger.warning("JLCPCB API not configured. Simulating order submission.")
        
        # Generate simulated order ID
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        order_id = f"SIM-{timestamp}"
        
        # Save order data for reference
        order_file = self.config.output_dir / f"order_{order_id}.json"
        order_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(order_file, 'w') as f:
            json.dump({
                'order_id': order_id,
                'timestamp': timestamp,
                'order_data': order_data,
                'status': 'simulated'
            }, f, indent=2)
        
        logger.info(f"Simulated order created: {order_id}")
        logger.info(f"Order details saved to: {order_file}")
        
        return order_id
    
    def _simulate_quote(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate price quote when API is not available.
        
        Args:
            order_data: Order specifications
            
        Returns:
            Simulated quote
        """
        # Simple price calculation
        area = order_data['board_width'] * order_data['board_height'] / 100  # cm²
        base_price = 5.0  # Base price
        area_price = area * 0.1  # Price per cm²
        layer_multiplier = 1 + (order_data['board_layers'] - 2) * 0.5
        quantity = order_data['quantity']
        
        unit_price = (base_price + area_price) * layer_multiplier
        total_price = unit_price * quantity
        
        return {
            'price': round(total_price, 2),
            'currency': 'USD',
            'lead_time': 5 if quantity <= 10 else 7,
            'shipping_options': [
                {'method': 'Standard', 'cost': 10, 'days': 15},
                {'method': 'Express', 'cost': 30, 'days': 7}
            ]
        }