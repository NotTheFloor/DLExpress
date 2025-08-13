"""
Rendering configuration and performance optimization for workflow designer.

This module provides settings for anti-aliasing, OpenGL acceleration, and 
performance optimization based on scene complexity.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class AntiAliasingLevel(Enum):
    """Anti-aliasing quality levels"""
    DISABLED = 0
    BASIC = 1       # QPainter antialiasing only
    ENHANCED = 2    # QPainter + OpenGL viewport
    MAXIMUM = 3     # Global MSAA + OpenGL viewport


class PerformanceMode(Enum):
    """Performance optimization modes"""
    QUALITY = "quality"         # Maximum quality, performance secondary
    BALANCED = "balanced"       # Balance quality vs performance  
    PERFORMANCE = "performance" # Maximum performance, quality secondary
    AUTO = "auto"              # Automatic based on scene complexity


@dataclass
class RenderingConfig:
    """Configuration settings for rendering quality and performance"""
    
    # Anti-aliasing settings
    antialiasing_level: AntiAliasingLevel = AntiAliasingLevel.ENHANCED
    msaa_samples: int = 4  # 2, 4, 8, 16 - higher = better quality but slower
    
    # Performance settings
    performance_mode: PerformanceMode = PerformanceMode.AUTO
    max_items_for_full_quality: int = 1000  # Disable AA above this item count
    
    # OpenGL settings
    enable_opengl: bool = True
    opengl_fallback: bool = True  # Fall back to standard rendering if OpenGL fails
    
    # Debug settings
    show_performance_info: bool = False
    log_rendering_stats: bool = False


class RenderingOptimizer:
    """
    Optimizes rendering settings based on scene complexity and user preferences.
    """
    
    def __init__(self, config: RenderingConfig = None):
        self.config = config or RenderingConfig()
        
    def get_optimized_settings(self, scene_item_count: int) -> dict:
        """
        Get optimized rendering settings based on scene complexity.
        
        Args:
            scene_item_count: Number of items in the current scene
            
        Returns:
            dict: Optimized settings for the scene
        """
        settings = {
            'enable_basic_aa': True,
            'enable_opengl': self.config.enable_opengl,
            'msaa_samples': self.config.msaa_samples,
            'show_performance_warning': False
        }
        
        # Auto-adjust based on performance mode and scene complexity
        if self.config.performance_mode == PerformanceMode.AUTO:
            if scene_item_count > self.config.max_items_for_full_quality:
                # Large scene - reduce quality for performance
                settings['enable_basic_aa'] = True  # Keep basic AA
                settings['enable_opengl'] = False   # Disable OpenGL for large scenes
                settings['msaa_samples'] = 2        # Reduce MSAA samples
                settings['show_performance_warning'] = True
                
        elif self.config.performance_mode == PerformanceMode.PERFORMANCE:
            # Performance priority - minimal anti-aliasing
            settings['enable_basic_aa'] = True
            settings['enable_opengl'] = False
            settings['msaa_samples'] = 2
            
        elif self.config.performance_mode == PerformanceMode.QUALITY:
            # Quality priority - maximum settings regardless of performance
            settings['enable_basic_aa'] = True
            settings['enable_opengl'] = True
            settings['msaa_samples'] = self.config.msaa_samples
            
        # Apply anti-aliasing level overrides
        if self.config.antialiasing_level == AntiAliasingLevel.DISABLED:
            settings['enable_basic_aa'] = False
            settings['enable_opengl'] = False
            
        elif self.config.antialiasing_level == AntiAliasingLevel.BASIC:
            settings['enable_opengl'] = False
            
        return settings
    
    def get_performance_info(self, scene_item_count: int) -> str:
        """Get human-readable performance information"""
        settings = self.get_optimized_settings(scene_item_count)
        
        info_parts = []
        
        if settings['enable_basic_aa']:
            info_parts.append("Basic AA")
        
        if settings['enable_opengl']:
            samples = settings['msaa_samples']
            info_parts.append(f"OpenGL {samples}x MSAA")
            
        if settings['show_performance_warning']:
            info_parts.append(f"(Large scene: {scene_item_count} items)")
            
        return " + ".join(info_parts) if info_parts else "No anti-aliasing"


# Default global configuration instance
default_config = RenderingConfig()