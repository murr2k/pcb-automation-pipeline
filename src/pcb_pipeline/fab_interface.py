import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path

from .config import PipelineConfig
from .pcb_layout import PCBLayout

logger = logging.getLogger(__name__)


class FabricationInterface(ABC):
    """Abstract base class for PCB fabrication interfaces."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.name = "generic"
    
    @abstractmethod
    def prepare_order(self, pcb_layout: PCBLayout, **kwargs) -> Dict[str, Any]:
        """Prepare order data for submission."""
        pass
    
    @abstractmethod
    def submit_order(self, order_data: Dict[str, Any]) -> str:
        """Submit order to manufacturer."""
        pass
    
    @abstractmethod
    def get_quote(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get price quote."""
        pass
    
    @abstractmethod
    def check_order_status(self, order_id: str) -> Dict[str, Any]:
        """Check order status."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get manufacturer capabilities."""
        pass
    
    def validate_design(self, pcb_layout: PCBLayout) -> List[str]:
        """Validate design against manufacturer capabilities."""
        errors = []
        capabilities = self.get_capabilities()
        
        # Check board size
        board_width, board_height = pcb_layout.board_size
        max_size = capabilities.get('max_board_size', (100, 100))
        if board_width > max_size[0] or board_height > max_size[1]:
            errors.append(f"Board size {board_width}x{board_height}mm exceeds max {max_size}")
        
        # Check layer count
        board_layers = self.config.get('copper_layers', 2)
        max_layers = capabilities.get('max_layers', 10)
        if board_layers > max_layers:
            errors.append(f"Layer count {board_layers} exceeds max {max_layers}")
        
        return errors


class JLCPCBFabInterface(FabricationInterface):
    """JLCPCB fabrication interface."""
    
    def __init__(self, config: PipelineConfig):
        super().__init__(config)
        self.name = "jlcpcb"
        self.api_url = config.get('jlcpcb_api_url', 'https://api.jlcpcb.com/v1')
        
        # Import the existing JLCPCB interface
        from .jlcpcb_interface import JLCPCBInterface
        self.jlc_interface = JLCPCBInterface(config)
    
    def prepare_order(self, pcb_layout: PCBLayout, **kwargs) -> Dict[str, Any]:
        return self.jlc_interface.prepare_order(pcb_layout, **kwargs)
    
    def submit_order(self, order_data: Dict[str, Any]) -> str:
        return self.jlc_interface.submit_order(order_data)
    
    def get_quote(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.jlc_interface.get_quote(order_data)
    
    def check_order_status(self, order_id: str) -> Dict[str, Any]:
        return self.jlc_interface.check_order_status(order_id)
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            'name': 'JLCPCB',
            'max_board_size': (200, 200),  # mm
            'min_board_size': (5, 5),      # mm
            'max_layers': 10,
            'min_trace_width': 0.127,      # mm (5 mil)
            'min_drill_size': 0.3,         # mm
            'surface_finishes': ['HASL', 'Lead-free HASL', 'ENIG', 'OSP'],
            'solder_mask_colors': ['green', 'red', 'blue', 'black', 'white', 'yellow'],
            'assembly_service': True,
            'lead_time_days': 2,
            'countries': ['China', 'Global shipping']
        }


class PCBWayFabInterface(FabricationInterface):
    """PCBWay fabrication interface."""
    
    def __init__(self, config: PipelineConfig):
        super().__init__(config)
        self.name = "pcbway"
        self.api_url = config.get('pcbway_api_url', 'https://api.pcbway.com/v1')
    
    def prepare_order(self, pcb_layout: PCBLayout, **kwargs) -> Dict[str, Any]:
        board_width, board_height = pcb_layout.board_size
        
        return {
            'project_name': pcb_layout.name,
            'board_width': board_width,
            'board_height': board_height,
            'layers': self.config.get('copper_layers', 2),
            'thickness': self.config.get('board_thickness', 1.6),
            'quantity': kwargs.get('quantity', 5),
            'surface_finish': self.config.get('surface_finish', 'HASL'),
            'solder_mask': self.config.get('solder_mask_color', 'green'),
            'silkscreen': self.config.get('silkscreen_color', 'white'),
        }
    
    def submit_order(self, order_data: Dict[str, Any]) -> str:
        # Simulate PCBWay order submission
        logger.info("Simulating PCBWay order submission")
        from datetime import datetime
        order_id = f"PCB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return order_id
    
    def get_quote(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate PCBWay pricing
        area = order_data['board_width'] * order_data['board_height'] / 100
        base_price = 8.0
        area_price = area * 0.15
        layer_multiplier = 1 + (order_data['layers'] - 2) * 0.6
        
        unit_price = (base_price + area_price) * layer_multiplier
        total_price = unit_price * order_data['quantity']
        
        return {
            'price': round(total_price, 2),
            'currency': 'USD',
            'lead_time': 7,
            'shipping_options': [
                {'method': 'Standard', 'cost': 15, 'days': 20},
                {'method': 'Express', 'cost': 45, 'days': 10}
            ]
        }
    
    def check_order_status(self, order_id: str) -> Dict[str, Any]:
        return {
            'order_id': order_id,
            'status': 'in_production',
            'progress': 'fabrication',
            'estimated_completion': '7 days'
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            'name': 'PCBWay',
            'max_board_size': (610, 610),  # mm
            'min_board_size': (5, 5),      # mm
            'max_layers': 32,
            'min_trace_width': 0.075,      # mm (3 mil)
            'min_drill_size': 0.15,        # mm
            'surface_finishes': ['HASL', 'Lead-free HASL', 'ENIG', 'OSP', 'Immersion Silver'],
            'solder_mask_colors': ['green', 'red', 'blue', 'black', 'white', 'yellow', 'purple'],
            'assembly_service': True,
            'lead_time_days': 7,
            'countries': ['China', 'USA', 'Europe']
        }


class OSHParkFabInterface(FabricationInterface):
    """OSH Park fabrication interface."""
    
    def __init__(self, config: PipelineConfig):
        super().__init__(config)
        self.name = "oshpark"
        self.api_url = config.get('oshpark_api_url', 'https://oshpark.com/api/v1')
    
    def prepare_order(self, pcb_layout: PCBLayout, **kwargs) -> Dict[str, Any]:
        board_width, board_height = pcb_layout.board_size
        
        return {
            'project_name': pcb_layout.name,
            'board_width': board_width,
            'board_height': board_height,
            'layers': self.config.get('copper_layers', 2),
            'thickness': 1.6,  # OSH Park standard
            'quantity': 3,  # OSH Park minimum
            'surface_finish': 'ENIG',  # OSH Park standard
            'solder_mask': 'purple',   # OSH Park signature
            'silkscreen': 'white',
        }
    
    def submit_order(self, order_data: Dict[str, Any]) -> str:
        logger.info("Simulating OSH Park order submission")
        from datetime import datetime
        order_id = f"OSH-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return order_id
    
    def get_quote(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        # OSH Park pricing: $5 per square inch for 3 boards
        area_sq_in = (order_data['board_width'] * order_data['board_height']) / 645.16  # mm² to in²
        price_per_sq_in = 5.0
        
        if order_data['layers'] == 4:
            price_per_sq_in = 10.0
        elif order_data['layers'] > 4:
            price_per_sq_in = 15.0
        
        total_price = area_sq_in * price_per_sq_in
        
        return {
            'price': round(max(total_price, 10.0), 2),  # $10 minimum
            'currency': 'USD',
            'lead_time': 12,
            'quantity': 3,  # OSH Park gives 3 boards
            'shipping_options': [
                {'method': 'Standard', 'cost': 0, 'days': 14}  # Free shipping
            ]
        }
    
    def check_order_status(self, order_id: str) -> Dict[str, Any]:
        return {
            'order_id': order_id,
            'status': 'ordered',
            'progress': 'panelization',
            'estimated_completion': '12 days'
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            'name': 'OSH Park',
            'max_board_size': (100, 100),  # mm (4x4 inches)
            'min_board_size': (5, 5),      # mm
            'max_layers': 4,
            'min_trace_width': 0.152,      # mm (6 mil)
            'min_drill_size': 0.2,         # mm
            'surface_finishes': ['ENIG'],
            'solder_mask_colors': ['purple'],
            'assembly_service': False,
            'lead_time_days': 12,
            'countries': ['USA']
        }


class SeeedStudioFabInterface(FabricationInterface):
    """Seeed Studio fabrication interface."""
    
    def __init__(self, config: PipelineConfig):
        super().__init__(config)
        self.name = "seeedstudio"
        self.api_url = config.get('seeed_api_url', 'https://api.seeedstudio.com/v1')
    
    def prepare_order(self, pcb_layout: PCBLayout, **kwargs) -> Dict[str, Any]:
        board_width, board_height = pcb_layout.board_size
        
        return {
            'project_name': pcb_layout.name,
            'board_width': board_width,
            'board_height': board_height,
            'layers': self.config.get('copper_layers', 2),
            'thickness': self.config.get('board_thickness', 1.6),
            'quantity': kwargs.get('quantity', 10),
            'surface_finish': self.config.get('surface_finish', 'HASL'),
            'solder_mask': self.config.get('solder_mask_color', 'green'),
            'silkscreen': self.config.get('silkscreen_color', 'white'),
        }
    
    def submit_order(self, order_data: Dict[str, Any]) -> str:
        logger.info("Simulating Seeed Studio order submission")
        from datetime import datetime
        order_id = f"SEED-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return order_id
    
    def get_quote(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        area = order_data['board_width'] * order_data['board_height'] / 100
        base_price = 4.9
        area_price = area * 0.099
        
        unit_price = base_price + area_price
        total_price = unit_price * order_data['quantity']
        
        return {
            'price': round(total_price, 2),
            'currency': 'USD',
            'lead_time': 3,
            'shipping_options': [
                {'method': 'Standard', 'cost': 12, 'days': 15},
                {'method': 'Express', 'cost': 35, 'days': 8}
            ]
        }
    
    def check_order_status(self, order_id: str) -> Dict[str, Any]:
        return {
            'order_id': order_id,
            'status': 'processing',
            'progress': 'design_review',
            'estimated_completion': '3 days'
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            'name': 'Seeed Studio',
            'max_board_size': (100, 100),  # mm
            'min_board_size': (5, 5),      # mm
            'max_layers': 6,
            'min_trace_width': 0.127,      # mm (5 mil)
            'min_drill_size': 0.2,         # mm
            'surface_finishes': ['HASL', 'Lead-free HASL', 'ENIG'],
            'solder_mask_colors': ['green', 'red', 'blue', 'black', 'white'],
            'assembly_service': True,
            'lead_time_days': 3,
            'countries': ['China', 'Global shipping']
        }


class FabricationManager:
    """Manages multiple fabrication interfaces."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.interfaces = {}
        
        # Register available interfaces
        self.register_interface('jlcpcb', JLCPCBFabInterface)
        self.register_interface('pcbway', PCBWayFabInterface)
        self.register_interface('oshpark', OSHParkFabInterface)
        self.register_interface('seeedstudio', SeeedStudioFabInterface)
        
        # Import and register MacroFab if available
        try:
            from .macrofab_interface import MacroFabInterface
            self.register_interface('macrofab', MacroFabInterface)
        except ImportError:
            pass
    
    def register_interface(self, name: str, interface_class):
        """Register a fabrication interface."""
        self.interfaces[name] = interface_class
    
    def get_interface(self, name: str) -> FabricationInterface:
        """Get fabrication interface by name."""
        if name not in self.interfaces:
            raise ValueError(f"Unknown fabrication interface: {name}")
        
        return self.interfaces[name](self.config)
    
    def get_all_quotes(self, pcb_layout: PCBLayout, **kwargs) -> Dict[str, Dict[str, Any]]:
        """Get quotes from all available manufacturers."""
        quotes = {}
        
        for name in self.interfaces.keys():
            try:
                interface = self.get_interface(name)
                order_data = interface.prepare_order(pcb_layout, **kwargs)
                quote = interface.get_quote(order_data)
                quote['manufacturer'] = name
                quotes[name] = quote
                
            except Exception as e:
                logger.warning(f"Failed to get quote from {name}: {e}")
                quotes[name] = {'error': str(e)}
        
        return quotes
    
    def find_best_option(self, pcb_layout: PCBLayout, criteria: str = 'price', **kwargs) -> Dict[str, Any]:
        """Find best manufacturer based on criteria."""
        quotes = self.get_all_quotes(pcb_layout, **kwargs)
        
        valid_quotes = {k: v for k, v in quotes.items() if 'error' not in v}
        
        if not valid_quotes:
            raise RuntimeError("No valid quotes available")
        
        if criteria == 'price':
            best = min(valid_quotes.items(), key=lambda x: x[1]['price'])
        elif criteria == 'lead_time':
            best = min(valid_quotes.items(), key=lambda x: x[1]['lead_time'])
        else:
            # Default to first available
            best = next(iter(valid_quotes.items()))
        
        return {
            'manufacturer': best[0],
            'quote': best[1],
            'interface': self.get_interface(best[0])
        }
    
    def compare_manufacturers(self, pcb_layout: PCBLayout, **kwargs) -> None:
        """Print comparison of all manufacturers."""
        quotes = self.get_all_quotes(pcb_layout, **kwargs)
        
        print("\n🏭 Manufacturer Comparison")
        print("=" * 60)
        
        for name, quote in quotes.items():
            if 'error' in quote:
                print(f"{name:12}: ERROR - {quote['error']}")
            else:
                price = quote.get('price', 'N/A')
                lead_time = quote.get('lead_time', 'N/A')
                print(f"{name:12}: ${price:6} | {lead_time:2} days | {quote.get('currency', 'USD')}")
        
        print("=" * 60)