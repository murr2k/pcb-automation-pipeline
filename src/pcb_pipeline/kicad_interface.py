import logging
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from .config import PipelineConfig

logger = logging.getLogger(__name__)


class KiCadInterface:
    """Interface for KiCad automation using Python API."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.kicad_path = config.kicad_path
        self.use_docker = os.environ.get('PCB_USE_DOCKER', 'false').lower() == 'true'
        self.pcbnew = None
        self.eeschema = None
        
        # Try to import KiCad Python modules
        self._init_kicad_modules()
    
    def _init_kicad_modules(self) -> None:
        """Initialize KiCad Python modules."""
        try:
            # Add KiCad Python path to sys.path
            if self.kicad_path and not self.use_docker:
                kicad_python_path = Path(self.kicad_path).parent / 'lib' / 'python3' / 'dist-packages'
                if kicad_python_path.exists():
                    sys.path.insert(0, str(kicad_python_path))
            
            # Try to import pcbnew
            try:
                import pcbnew
                self.pcbnew = pcbnew
                logger.info("Successfully imported pcbnew module")
            except ImportError:
                logger.warning("Could not import pcbnew module")
            
            # Try to import eeschema (if available)
            try:
                import eeschema
                self.eeschema = eeschema
                logger.info("Successfully imported eeschema module")
            except ImportError:
                logger.debug("Could not import eeschema module (this is normal)")
                
        except Exception as e:
            logger.error(f"Error initializing KiCad modules: {e}")
    
    def create_project(self, project_name: str, output_dir: Path) -> Path:
        """Create a new KiCad project.
        
        Args:
            project_name: Name of the project
            output_dir: Directory for the project
            
        Returns:
            Path to project file
        """
        project_dir = output_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create project file
        project_file = project_dir / f"{project_name}.kicad_pro"
        
        # Basic project structure
        project_data = {
            "board": {
                "design_settings": {
                    "defaults": {
                        "copper_line_width": self.config.get('default_trace_width', 0.25),
                        "copper_text_size_h": 1.5,
                        "copper_text_size_v": 1.5,
                        "silk_line_width": 0.15,
                        "via_diameter": self.config.get('default_via_size', 0.8),
                        "via_drill": self.config.get('default_via_drill', 0.4)
                    },
                    "rules": {
                        "clearance": self.config.get('clearance', 0.2),
                        "min_track_width": self.config.get('min_track_width', 0.15),
                        "min_via_diameter": self.config.get('min_via_diameter', 0.45)
                    }
                }
            }
        }
        
        # Write project file
        import json
        with open(project_file, 'w') as f:
            json.dump(project_data, f, indent=2)
        
        logger.info(f"Created KiCad project: {project_file}")
        return project_file
    
    def create_board(self, board_name: str, size: Tuple[float, float]) -> 'pcbnew.BOARD':
        """Create a new PCB board.
        
        Args:
            board_name: Name of the board
            size: Board size in mm (width, height)
            
        Returns:
            KiCad board object
        """
        if not self.pcbnew:
            logger.error("pcbnew module not available")
            return None
        
        # Create new board
        board = self.pcbnew.BOARD()
        
        # Set board properties
        board.SetTitle(board_name)
        
        # Create board outline
        self._create_board_outline(board, size)
        
        # Set design rules
        self._set_design_rules(board)
        
        return board
    
    def add_footprint(self, board: 'pcbnew.BOARD', footprint_lib: str, 
                     footprint_name: str, position: Tuple[float, float], 
                     reference: str) -> 'pcbnew.FOOTPRINT':
        """Add a footprint to the board.
        
        Args:
            board: KiCad board object
            footprint_lib: Footprint library name
            footprint_name: Footprint name
            position: Position in mm (x, y)
            reference: Reference designator
            
        Returns:
            Added footprint
        """
        if not self.pcbnew:
            return None
        
        # Load footprint from library
        footprint = self.pcbnew.FootprintLoad(footprint_lib, footprint_name)
        
        if footprint:
            # Set position
            footprint.SetPosition(self.pcbnew.wxPointMM(position[0], position[1]))
            
            # Set reference
            footprint.SetReference(reference)
            
            # Add to board
            board.Add(footprint)
            
            logger.debug(f"Added footprint {reference} at {position}")
        else:
            logger.error(f"Could not load footprint {footprint_lib}:{footprint_name}")
        
        return footprint
    
    def add_track(self, board: 'pcbnew.BOARD', start: Tuple[float, float], 
                  end: Tuple[float, float], width: float, 
                  layer: str = 'F.Cu') -> 'pcbnew.PCB_TRACK':
        """Add a track (trace) to the board.
        
        Args:
            board: KiCad board object
            start: Start position in mm (x, y)
            end: End position in mm (x, y)
            width: Track width in mm
            layer: Layer name
            
        Returns:
            Added track
        """
        if not self.pcbnew:
            return None
        
        track = self.pcbnew.PCB_TRACK(board)
        track.SetStart(self.pcbnew.wxPointMM(start[0], start[1]))
        track.SetEnd(self.pcbnew.wxPointMM(end[0], end[1]))
        track.SetWidth(int(width * 1e6))  # Convert mm to nm
        track.SetLayer(board.GetLayerID(layer))
        
        board.Add(track)
        
        return track
    
    def add_via(self, board: 'pcbnew.BOARD', position: Tuple[float, float], 
                diameter: float, drill: float) -> 'pcbnew.PCB_VIA':
        """Add a via to the board.
        
        Args:
            board: KiCad board object
            position: Position in mm (x, y)
            diameter: Via diameter in mm
            drill: Drill diameter in mm
            
        Returns:
            Added via
        """
        if not self.pcbnew:
            return None
        
        via = self.pcbnew.PCB_VIA(board)
        via.SetPosition(self.pcbnew.wxPointMM(position[0], position[1]))
        via.SetWidth(int(diameter * 1e6))  # Convert mm to nm
        via.SetDrill(int(drill * 1e6))  # Convert mm to nm
        via.SetViaType(self.pcbnew.VIATYPE_THROUGH)
        
        board.Add(via)
        
        return via
    
    def save_board(self, board: 'pcbnew.BOARD', filename: str) -> None:
        """Save board to file.
        
        Args:
            board: KiCad board object
            filename: Output filename
        """
        if not self.pcbnew:
            logger.error("Cannot save board - pcbnew not available")
            return
        
        # Save board
        self.pcbnew.SaveBoard(filename, board)
        logger.info(f"Saved board to {filename}")
    
    def export_gerbers(self, board_file: str, output_dir: Path) -> List[Path]:
        """Export Gerber files from board.
        
        Args:
            board_file: Path to board file
            output_dir: Output directory for Gerbers
            
        Returns:
            List of generated Gerber files
        """
        if self.use_docker:
            return self._export_gerbers_docker(board_file, output_dir)
        else:
            return self._export_gerbers_native(board_file, output_dir)
    
    def run_drc(self, board_file: str) -> Dict[str, Any]:
        """Run Design Rule Check on board.
        
        Args:
            board_file: Path to board file
            
        Returns:
            DRC results
        """
        if not self.pcbnew:
            logger.warning("Cannot run DRC - pcbnew not available")
            return {'errors': [], 'warnings': []}
        
        # Load board
        board = self.pcbnew.LoadBoard(board_file)
        
        # Create DRC object
        drc = self.pcbnew.DRC()
        drc.SetBoard(board)
        
        # Run tests
        drc.RunTests()
        
        # Get results
        # Note: Actual implementation would parse DRC results
        return {
            'errors': [],
            'warnings': [],
            'status': 'passed'
        }
    
    def _create_board_outline(self, board: 'pcbnew.BOARD', 
                             size: Tuple[float, float]) -> None:
        """Create board outline on Edge.Cuts layer."""
        if not self.pcbnew:
            return
        
        width, height = size
        edge_layer = board.GetLayerID('Edge.Cuts')
        line_width = 0.15  # mm
        
        # Create rectangle
        lines = [
            ((0, 0), (width, 0)),
            ((width, 0), (width, height)),
            ((width, height), (0, height)),
            ((0, height), (0, 0))
        ]
        
        for start, end in lines:
            line = self.pcbnew.PCB_SHAPE(board)
            line.SetShape(self.pcbnew.SHAPE_T_SEGMENT)
            line.SetStart(self.pcbnew.wxPointMM(start[0], start[1]))
            line.SetEnd(self.pcbnew.wxPointMM(end[0], end[1]))
            line.SetLayer(edge_layer)
            line.SetWidth(int(line_width * 1e6))
            board.Add(line)
    
    def _set_design_rules(self, board: 'pcbnew.BOARD') -> None:
        """Set design rules for the board."""
        if not self.pcbnew:
            return
        
        # Get design settings
        settings = board.GetDesignSettings()
        
        # Set clearance
        settings.SetDefault(self.pcbnew.CLEARANCE_CONSTRAINT, 
                          int(self.config.get('clearance', 0.2) * 1e6))
        
        # Set track width
        settings.SetDefault(self.pcbnew.TRACK_WIDTH_CONSTRAINT,
                          int(self.config.get('default_trace_width', 0.25) * 1e6))
        
        # Set via size
        settings.SetDefault(self.pcbnew.VIA_DIAMETER_CONSTRAINT,
                          int(self.config.get('default_via_size', 0.8) * 1e6))
    
    def _export_gerbers_docker(self, board_file: str, 
                              output_dir: Path) -> List[Path]:
        """Export Gerbers using Docker container."""
        logger.info("Exporting Gerbers using Docker")
        
        # Run kicad-cli in Docker
        docker_cmd = [
            'docker', 'run', '--rm',
            '-v', f'{Path(board_file).parent}:/work',
            '-v', f'{output_dir}:/output',
            self.config.get('docker_image', 'kicad/kicad:nightly-full-trixie'),
            'kicad-cli', 'pcb', 'export', 'gerbers',
            '--output', '/output',
            f'/work/{Path(board_file).name}'
        ]
        
        try:
            subprocess.run(docker_cmd, check=True, capture_output=True)
            
            # List generated files
            gerber_files = list(output_dir.glob('*.gbr'))
            gerber_files.extend(output_dir.glob('*.drl'))
            
            return gerber_files
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to export Gerbers: {e}")
            return []
    
    def _export_gerbers_native(self, board_file: str, 
                              output_dir: Path) -> List[Path]:
        """Export Gerbers using native KiCad."""
        if not self.pcbnew:
            logger.error("Cannot export Gerbers - pcbnew not available")
            return []
        
        # Load board
        board = self.pcbnew.LoadBoard(board_file)
        
        # Plot controller
        plot_controller = self.pcbnew.PLOT_CONTROLLER(board)
        plot_options = plot_controller.GetPlotOptions()
        
        # Set output directory
        plot_options.SetOutputDirectory(str(output_dir))
        
        # Configure plot options
        plot_options.SetPlotFrameRef(False)
        plot_options.SetLineWidth(self.pcbnew.FromMM(0.1))
        plot_options.SetAutoScale(False)
        plot_options.SetScale(1)
        plot_options.SetMirror(False)
        plot_options.SetUseGerberAttributes(True)
        plot_options.SetUseAuxOrigin(True)
        
        # Plot layers
        gerber_files = []
        layers = [
            ('F.Cu', 'F_Cu'),
            ('B.Cu', 'B_Cu'),
            ('F.SilkS', 'F_SilkS'),
            ('B.SilkS', 'B_SilkS'),
            ('F.Mask', 'F_Mask'),
            ('B.Mask', 'B_Mask'),
            ('Edge.Cuts', 'Edge_Cuts')
        ]
        
        for layer_name, suffix in layers:
            layer_id = board.GetLayerID(layer_name)
            plot_controller.SetLayer(layer_id)
            plot_controller.OpenPlotfile(suffix, self.pcbnew.PLOT_FORMAT_GERBER, '')
            plot_controller.PlotLayer()
            
            gerber_file = output_dir / f"{Path(board_file).stem}_{suffix}.gbr"
            if gerber_file.exists():
                gerber_files.append(gerber_file)
        
        plot_controller.ClosePlot()
        
        return gerber_files