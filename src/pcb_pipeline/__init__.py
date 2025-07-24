"""PCB Automation Pipeline

A comprehensive solution for automating PCB design from schematic to manufacturing.
"""

__version__ = "0.1.0"
__author__ = "PCB Automation Team"

from .pipeline import PCBPipeline
from .config import PipelineConfig

__all__ = ["PCBPipeline", "PipelineConfig"]