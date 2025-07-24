import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from pcb_pipeline import PCBPipeline, PipelineConfig
from pcb_pipeline.schematic_generator import Schematic, Component, Net


class TestPipeline:
    """Test PCB pipeline functionality."""
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        pipeline = PCBPipeline()
        assert pipeline is not None
        assert pipeline.config is not None
    
    def test_config_loading(self):
        """Test configuration loading."""
        config = PipelineConfig()
        assert config.get('default_trace_width') == 0.25
        assert config.get('copper_layers') == 2
    
    def test_schematic_creation(self):
        """Test schematic creation."""
        schematic = Schematic("TestBoard")
        
        # Add components
        r1 = Component("R1", "resistor", "10k")
        c1 = Component("C1", "capacitor", "100nF")
        
        schematic.add_component(r1)
        schematic.add_component(c1)
        
        assert len(schematic.components) == 2
        assert "R1" in schematic.components
        assert "C1" in schematic.components
    
    def test_net_creation(self):
        """Test net creation."""
        net = Net("VCC")
        net.add_connection("R1", "1")
        net.add_connection("C1", "1")
        
        assert len(net.connections) == 2
        assert ("R1", "1") in net.connections
    
    def test_design_spec_loading(self):
        """Test loading design specification."""
        pipeline = PCBPipeline()
        
        # Create test spec
        test_spec = {
            'name': 'TestBoard',
            'components': [
                {'type': 'resistor', 'value': '10k'},
                {'type': 'capacitor', 'value': '100nF'}
            ],
            'connections': [
                {
                    'net': 'VCC',
                    'connect': ['R1.1', 'C1.1']
                }
            ]
        }
        
        # Test spec validation
        pipeline._validate_spec(test_spec)  # Should not raise
    
    def test_component_library(self):
        """Test component library functionality."""
        config = PipelineConfig()
        from pcb_pipeline.library_manager import ComponentLibraryManager
        
        lib_mgr = ComponentLibraryManager(config)
        
        # Get standard component
        resistor = lib_mgr.get_component('resistor', '10k', '0603')
        assert resistor['type'] == 'resistor'
        assert resistor['value'] == '10k'
        assert '0603' in resistor['footprint']
    
    def test_validation_report(self):
        """Test validation report."""
        from pcb_pipeline.design_validator import ValidationReport
        
        report = ValidationReport()
        report.add_error('drc', 'Test error')
        report.add_warning('drc', 'Test warning')
        
        assert report.has_errors()
        assert len(report.errors) == 1
        assert len(report.warnings) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])