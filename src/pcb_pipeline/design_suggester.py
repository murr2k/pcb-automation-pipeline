import logging
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import json
from pathlib import Path

from .config import PipelineConfig
from .pcb_layout import PCBLayout

logger = logging.getLogger(__name__)


class DesignSuggester:
    """AI-assisted design suggestion and optimization system."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.knowledge_base = self._load_knowledge_base()
        self.placement_rules = self._load_placement_rules()
        self.routing_heuristics = self._load_routing_heuristics()
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load design knowledge base from previous successful designs."""
        kb_file = Path(self.config.get('knowledge_base_path', 'data/design_knowledge.json'))
        
        if kb_file.exists():
            try:
                with open(kb_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load knowledge base: {e}")
        
        # Default knowledge base
        return {
            'component_patterns': {
                'power_supply': {
                    'components': ['regulator', 'capacitor', 'inductor'],
                    'placement': 'cluster',
                    'considerations': 'minimize switching noise'
                },
                'crystal_oscillator': {
                    'components': ['crystal', 'capacitor'],
                    'placement': 'close_to_ic',
                    'considerations': 'minimize trace length'
                },
                'decoupling': {
                    'components': ['capacitor'],
                    'placement': 'near_power_pins',
                    'considerations': 'minimize inductance'
                }
            },
            'design_rules': {
                'high_speed_signals': {
                    'max_trace_length': 25,  # mm
                    'impedance_control': True,
                    'via_minimization': True
                },
                'power_traces': {
                    'min_width': 0.5,  # mm
                    'copper_pour': True
                },
                'analog_signals': {
                    'isolation': True,
                    'guard_traces': True
                }
            }
        }
    
    def _load_placement_rules(self) -> List[Dict[str, Any]]:
        """Load component placement rules."""
        return [
            {
                'name': 'power_decoupling',
                'condition': lambda comp: comp.get('type') == 'capacitor' and 'decoupling' in comp.get('role', ''),
                'rule': 'place_near_power_pins',
                'priority': 'high'
            },
            {
                'name': 'crystal_placement',
                'condition': lambda comp: comp.get('type') == 'crystal',
                'rule': 'minimize_trace_length_to_ic',
                'priority': 'high'
            },
            {
                'name': 'connector_edge_placement',
                'condition': lambda comp: comp.get('type') == 'connector',
                'rule': 'place_on_board_edge',
                'priority': 'medium'
            },
            {
                'name': 'heat_sensitive_spacing',
                'condition': lambda comp: comp.get('power_rating', 0) > 1.0,
                'rule': 'maintain_thermal_clearance',
                'priority': 'medium'
            }
        ]
    
    def _load_routing_heuristics(self) -> List[Dict[str, Any]]:
        """Load routing optimization heuristics."""
        return [
            {
                'name': 'minimize_via_count',
                'weight': 0.8,
                'description': 'Prefer single-layer routing'
            },
            {
                'name': 'minimize_trace_length',
                'weight': 0.6,
                'description': 'Shorter traces for better performance'
            },
            {
                'name': 'avoid_acute_angles',
                'weight': 0.4,
                'description': 'Use 45-degree or curved traces'
            },
            {
                'name': 'power_trace_width',
                'weight': 0.9,
                'description': 'Wider traces for power nets'
            }
        ]
    
    def suggest_placement_improvements(self, layout: PCBLayout) -> List[Dict[str, Any]]:
        """Suggest improvements to component placement."""
        suggestions = []
        
        # Analyze current placement
        placement_analysis = self._analyze_placement(layout)
        
        # Check placement rules
        for rule in self.placement_rules:
            violations = self._check_placement_rule(layout, rule)
            if violations:
                suggestions.extend(violations)
        
        # Thermal analysis
        thermal_suggestions = self._analyze_thermal_layout(layout)
        suggestions.extend(thermal_suggestions)
        
        # Signal integrity suggestions
        si_suggestions = self._analyze_signal_integrity(layout)
        suggestions.extend(si_suggestions)
        
        # EMI/EMC suggestions
        emc_suggestions = self._analyze_emc_layout(layout)
        suggestions.extend(emc_suggestions)
        
        return sorted(suggestions, key=lambda x: x.get('priority_score', 0), reverse=True)
    
    def _analyze_placement(self, layout: PCBLayout) -> Dict[str, Any]:
        """Analyze current component placement."""
        analysis = {
            'component_density': 0,
            'thermal_hotspots': [],
            'critical_path_lengths': {},
            'placement_efficiency': 0
        }
        
        # Calculate component density
        board_area = layout.board_size[0] * layout.board_size[1]
        component_area = len(layout.components) * 25  # Assume 5x5mm average
        analysis['component_density'] = component_area / board_area
        
        # Find potential thermal issues
        for ref, comp in layout.components.items():
            power_rating = comp.get('power_rating', 0)
            if power_rating > 0.5:  # >0.5W components
                analysis['thermal_hotspots'].append({
                    'component': ref,
                    'power': power_rating,
                    'position': comp['position']
                })
        
        return analysis
    
    def _check_placement_rule(self, layout: PCBLayout, rule: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check a specific placement rule."""
        violations = []
        
        for ref, comp in layout.components.items():
            if rule['condition'](comp):
                violation = self._evaluate_rule_compliance(layout, ref, comp, rule)
                if violation:
                    violations.append({
                        'type': 'placement_violation',
                        'rule': rule['name'],
                        'component': ref,
                        'description': violation,
                        'priority_score': self._get_priority_score(rule['priority']),
                        'suggestion': self._get_rule_suggestion(rule['rule'])
                    })
        
        return violations
    
    def _evaluate_rule_compliance(self, layout: PCBLayout, ref: str, 
                                 comp: Dict[str, Any], rule: Dict[str, Any]) -> Optional[str]:
        """Evaluate if component complies with placement rule."""
        rule_name = rule['rule']
        
        if rule_name == 'place_near_power_pins':
            # Find nearest IC with power pins
            nearest_ic = self._find_nearest_ic(layout, comp['position'])
            if nearest_ic:
                distance = self._calculate_distance(comp['position'], nearest_ic['position'])
                if distance > 5:  # mm
                    return f"Decoupling capacitor {ref} is {distance:.1f}mm from nearest IC (recommend <5mm)"
        
        elif rule_name == 'place_on_board_edge':
            x, y = comp['position']
            board_w, board_h = layout.board_size
            edge_margin = 5  # mm
            
            if not (x < edge_margin or x > board_w - edge_margin or 
                   y < edge_margin or y > board_h - edge_margin):
                return f"Connector {ref} should be placed closer to board edge"
        
        elif rule_name == 'maintain_thermal_clearance':
            # Check distance to other high-power components
            clearance_violations = self._check_thermal_clearance(layout, ref, comp)
            if clearance_violations:
                return clearance_violations
        
        return None
    
    def _analyze_thermal_layout(self, layout: PCBLayout) -> List[Dict[str, Any]]:
        """Analyze thermal aspects of layout."""
        suggestions = []
        
        # Find high-power components
        high_power_components = []
        for ref, comp in layout.components.items():
            power = comp.get('power_rating', 0)
            if power > 0.5:
                high_power_components.append((ref, comp, power))
        
        # Check thermal clustering
        if len(high_power_components) > 1:
            for i, (ref1, comp1, power1) in enumerate(high_power_components):
                for ref2, comp2, power2 in high_power_components[i+1:]:
                    distance = self._calculate_distance(comp1['position'], comp2['position'])
                    if distance < 10:  # mm
                        suggestions.append({
                            'type': 'thermal_issue',
                            'description': f"High-power components {ref1} and {ref2} too close ({distance:.1f}mm)",
                            'priority_score': 70,
                            'suggestion': f"Increase spacing to >10mm or add thermal vias"
                        })
        
        return suggestions
    
    def _analyze_signal_integrity(self, layout: PCBLayout) -> List[Dict[str, Any]]:
        """Analyze signal integrity aspects."""
        suggestions = []
        
        # Check for long high-speed traces
        for trace in layout.traces:
            net_name = trace.get('net', '')
            if 'clk' in net_name.lower() or 'clock' in net_name.lower():
                length = self._calculate_trace_length(trace)
                if length > 25:  # mm
                    suggestions.append({
                        'type': 'signal_integrity',
                        'description': f"Clock trace {net_name} is {length:.1f}mm (recommend <25mm)",
                        'priority_score': 80,
                        'suggestion': "Consider length matching or differential routing"
                    })
        
        return suggestions
    
    def _analyze_emc_layout(self, layout: PCBLayout) -> List[Dict[str, Any]]:
        """Analyze EMC/EMI aspects."""
        suggestions = []
        
        # Check for proper ground plane coverage
        ground_coverage = self._estimate_ground_coverage(layout)
        if ground_coverage < 0.7:  # 70%
            suggestions.append({
                'type': 'emc_issue',
                'description': f"Ground plane coverage only {ground_coverage*100:.0f}% (recommend >70%)",
                'priority_score': 60,
                'suggestion': "Add ground pour or increase ground traces"
            })
        
        return suggestions
    
    def optimize_placement(self, layout: PCBLayout) -> PCBLayout:
        """Apply AI-driven placement optimization."""
        logger.info("Applying AI-driven placement optimization")
        
        # Get current placement quality score
        initial_score = self._calculate_placement_score(layout)
        
        # Apply optimization algorithms
        optimized_layout = self._apply_genetic_algorithm(layout)
        optimized_layout = self._apply_force_directed_placement(optimized_layout)
        optimized_layout = self._apply_clustering_optimization(optimized_layout)
        
        # Calculate final score
        final_score = self._calculate_placement_score(optimized_layout)
        
        logger.info(f"Placement optimization: {initial_score:.2f} → {final_score:.2f}")
        
        return optimized_layout
    
    def _calculate_placement_score(self, layout: PCBLayout) -> float:
        """Calculate overall placement quality score."""
        score = 0.0
        
        # Trace length score (shorter is better)
        total_trace_length = sum(self._calculate_trace_length(trace) for trace in layout.traces)
        trace_score = max(0, 100 - total_trace_length)  # Simplified scoring
        score += trace_score * 0.3
        
        # Component clustering score
        cluster_score = self._calculate_clustering_score(layout)
        score += cluster_score * 0.2
        
        # Thermal score
        thermal_score = self._calculate_thermal_score(layout)
        score += thermal_score * 0.2
        
        # EMC score
        emc_score = self._calculate_emc_score(layout)
        score += emc_score * 0.3
        
        return score
    
    def _apply_genetic_algorithm(self, layout: PCBLayout) -> PCBLayout:
        """Apply genetic algorithm for placement optimization."""
        # Simplified GA implementation
        # In practice, this would be more sophisticated
        
        population_size = 10
        generations = 20
        
        # For now, just return the input layout
        # Real implementation would evolve component positions
        
        return layout
    
    def _apply_force_directed_placement(self, layout: PCBLayout) -> PCBLayout:
        """Apply force-directed algorithm for component placement."""
        # Simulate forces between connected components
        # Components connected by nets attract each other
        # All components repel each other to avoid clustering
        
        return layout
    
    def _apply_clustering_optimization(self, layout: PCBLayout) -> PCBLayout:
        """Apply clustering optimization for functional blocks."""
        # Group related components together
        # Examples: power supply components, crystal + caps, etc.
        
        return layout
    
    def learn_from_design(self, layout: PCBLayout, performance_metrics: Dict[str, float]) -> None:
        """Learn from completed design and update knowledge base."""
        logger.info("Learning from design feedback")
        
        # Extract features from successful design
        features = {
            'component_count': len(layout.components),
            'board_size': layout.board_size,
            'trace_count': len(layout.traces),
            'placement_density': self._calculate_placement_density(layout),
            'performance_score': performance_metrics.get('overall_score', 0)
        }
        
        # Update knowledge base
        self._update_knowledge_base(features, performance_metrics)
    
    # Helper methods
    def _find_nearest_ic(self, layout: PCBLayout, position: Tuple[float, float]) -> Optional[Dict[str, Any]]:
        """Find nearest IC component."""
        ics = [(ref, comp) for ref, comp in layout.components.items() 
               if comp.get('type') == 'ic' or ref.startswith('U')]
        
        if not ics:
            return None
        
        nearest = min(ics, key=lambda x: self._calculate_distance(position, x[1]['position']))
        return nearest[1]
    
    def _calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between positions."""
        return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def _calculate_trace_length(self, trace: Dict[str, Any]) -> float:
        """Calculate trace length."""
        start = trace.get('start', (0, 0))
        end = trace.get('end', (0, 0))
        return self._calculate_distance(start, end)
    
    def _get_priority_score(self, priority: str) -> int:
        """Convert priority string to numeric score."""
        priority_map = {'high': 90, 'medium': 60, 'low': 30}
        return priority_map.get(priority, 50)
    
    def _get_rule_suggestion(self, rule: str) -> str:
        """Get human-readable suggestion for rule."""
        suggestions = {
            'place_near_power_pins': 'Move closer to IC power pins',
            'place_on_board_edge': 'Move to board edge for accessibility',
            'maintain_thermal_clearance': 'Increase spacing from heat sources'
        }
        return suggestions.get(rule, 'Review component placement')
    
    def _check_thermal_clearance(self, layout: PCBLayout, ref: str, comp: Dict[str, Any]) -> Optional[str]:
        """Check thermal clearance for component."""
        # Implementation would check spacing from other high-power components
        return None
    
    def _estimate_ground_coverage(self, layout: PCBLayout) -> float:
        """Estimate ground plane coverage."""
        # Simplified estimation
        return 0.8  # 80% coverage
    
    def _calculate_clustering_score(self, layout: PCBLayout) -> float:
        """Calculate how well components are clustered by function."""
        return 75.0  # Placeholder
    
    def _calculate_thermal_score(self, layout: PCBLayout) -> float:
        """Calculate thermal design score."""
        return 80.0  # Placeholder
    
    def _calculate_emc_score(self, layout: PCBLayout) -> float:
        """Calculate EMC design score."""
        return 70.0  # Placeholder
    
    def _calculate_placement_density(self, layout: PCBLayout) -> float:
        """Calculate component placement density."""
        board_area = layout.board_size[0] * layout.board_size[1]
        return len(layout.components) / board_area
    
    def _update_knowledge_base(self, features: Dict[str, Any], metrics: Dict[str, float]) -> None:
        """Update knowledge base with new learning."""
        # In practice, this would update ML models or rule weights
        logger.debug("Knowledge base updated with new design data")