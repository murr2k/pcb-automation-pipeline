import os
from pathlib import Path
from typing import Optional, Dict, Any
import yaml


class PipelineConfig:
    """Configuration management for PCB automation pipeline."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_file: Path to configuration file. If None, uses defaults.
        """
        self._config = self._get_defaults()
        
        if config_file:
            self._load_from_file(config_file)
        
        # Override with environment variables if present
        self._load_from_env()
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            # General settings
            'project_name': 'PCB_Project',
            'output_dir': 'output',
            'temp_dir': '/tmp/pcb_pipeline',
            
            # KiCad settings
            'kicad_path': '/usr/local/bin/kicad',
            'kicad_version': '8.0',
            'use_docker': True,
            'docker_image': 'kicad/kicad:latest',
            
            # Design settings
            'default_trace_width': 0.25,  # mm
            'default_via_size': 0.8,  # mm
            'default_via_drill': 0.4,  # mm
            'clearance': 0.2,  # mm
            'board_thickness': 1.6,  # mm
            'copper_layers': 2,
            
            # Layout settings
            'auto_place': True,
            'auto_route': False,
            'placement_grid': 0.5,  # mm
            'routing_grid': 0.25,  # mm
            
            # Component library
            'library_path': 'templates/component_libraries',
            'use_jlc_libraries': True,
            'preferred_parts_only': False,
            
            # Manufacturing settings
            'manufacturer': 'jlcpcb',
            'surface_finish': 'HASL',
            'solder_mask_color': 'green',
            'silkscreen_color': 'white',
            'min_hole_size': 0.3,  # mm
            
            # JLCPCB settings
            'jlcpcb_api_key': None,
            'jlcpcb_api_secret': None,
            'jlcpcb_api_url': 'https://api.jlcpcb.com/v1',
            'assembly_service': False,
            
            # Validation settings
            'strict_drc': True,
            'check_courtyard': True,
            'check_unconnected': True,
            'min_track_width': 0.15,  # mm
            'min_via_diameter': 0.45,  # mm
            'min_hole_to_hole': 0.5,  # mm
            
            # Logging
            'log_level': 'INFO',
            'log_file': 'pcb_pipeline.log',
        }
    
    def _load_from_file(self, config_file: str) -> None:
        """Load configuration from file."""
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        with open(config_path, 'r') as f:
            if config_path.suffix in ['.yaml', '.yml']:
                file_config = yaml.safe_load(f)
            else:
                import json
                file_config = json.load(f)
        
        # Update config with file values
        self._config.update(file_config)
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_mapping = {
            'PCB_KICAD_PATH': 'kicad_path',
            'PCB_OUTPUT_DIR': 'output_dir',
            'PCB_JLCPCB_API_KEY': 'jlcpcb_api_key',
            'PCB_JLCPCB_API_SECRET': 'jlcpcb_api_secret',
            'PCB_LOG_LEVEL': 'log_level',
        }
        
        for env_var, config_key in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                self._config[config_key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
    
    def save(self, output_file: str) -> None:
        """Save current configuration to file.
        
        Args:
            output_file: Path to save configuration
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)
    
    # Convenience properties
    @property
    def kicad_path(self) -> str:
        return self._config['kicad_path']
    
    @property
    def output_dir(self) -> Path:
        return Path(self._config['output_dir'])
    
    @property
    def auto_place(self) -> bool:
        return self._config['auto_place']
    
    @property
    def auto_route(self) -> bool:
        return self._config['auto_route']
    
    @property
    def jlcpcb_api_key(self) -> Optional[str]:
        return self._config.get('jlcpcb_api_key')
    
    @property
    def use_docker(self) -> bool:
        return self._config['use_docker']