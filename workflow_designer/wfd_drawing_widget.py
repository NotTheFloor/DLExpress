import random

from PySide6.QtWidgets import QFrame, QGraphicsView, QVBoxLayout, QGraphicsScene, QRubberBand
from PySide6.QtGui import QPainter, QPen, QColor, QFontMetrics, QSurfaceFormat
from PySide6.QtCore import QPoint, QRect, Qt, QRectF

try:
    from PySide6.QtOpenGLWidgets import QOpenGLWidget
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False

from .wfd_utilities import drawArrow
from .wfd_logger import logger
from .wfd_rendering_config import RenderingOptimizer, default_config

_DEF_DW_SZ_X = 1400
_DEF_DW_SZ_Y = 900
_TITLE_OFFS_X = 5
_TITLE_OFFS_Y = 12

class CustomGraphicsView(QGraphicsView):
    """Custom QGraphicsView that handles empty space clicks for deselection and box selection"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._wf_scene = None  # Reference to WFScene for selection manager access
        
        # Enable anti-aliasing for smooth lines and shapes
        self.setRenderHints(QPainter.RenderHint.Antialiasing | 
                           QPainter.RenderHint.SmoothPixmapTransform |
                           QPainter.RenderHint.TextAntialiasing)
        
        # Rubber band selection
        self._rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self._rubber_band_origin = QPoint()
        self._rubber_band_active = False
        self._rubber_band_enabled = False  # Only enable when clicking empty space
    
    def set_wf_scene(self, wf_scene):
        """Set the workflow scene reference for selection handling"""
        self._wf_scene = wf_scene
    
    def enable_opengl_antialiasing(self, samples=4):
        """
        Enable OpenGL viewport with multisampling anti-aliasing.
        
        Args:
            samples (int): Number of MSAA samples (4, 8, 16). Higher = better quality but slower.
        
        Returns:
            bool: True if OpenGL was successfully enabled, False otherwise
        """
        if not OPENGL_AVAILABLE:
            logger.warning("OpenGL widgets not available - falling back to standard rendering")
            return False
            
        try:
            # Create OpenGL widget with MSAA format
            opengl_widget = QOpenGLWidget()
            
            # Configure surface format for anti-aliasing
            surface_format = QSurfaceFormat()
            surface_format.setSamples(samples)  # MSAA samples
            surface_format.setDepthBufferSize(24)
            surface_format.setStencilBufferSize(8)
            opengl_widget.setFormat(surface_format)
            
            # Set as viewport
            self.setViewport(opengl_widget)
            
            logger.info(f"OpenGL viewport enabled with {samples}x MSAA")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable OpenGL viewport: {e}")
            return False
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Check if click is on empty space
            item = self.itemAt(event.pos())
            
            if item is None:
                # Click on empty space - enable rubber band selection
                self._rubber_band_origin = event.pos()
                self._rubber_band_active = False  # Will be activated on drag
                self._rubber_band_enabled = True  # Enable rubber band mode
                logger.debug(f"Empty space click: rubber band enabled at {self._rubber_band_origin}")
                
                # Detect modifier keys
                modifiers = event.modifiers()
                has_modifier = bool(modifiers & (Qt.ControlModifier | Qt.MetaModifier))
                
                if not has_modifier and self._wf_scene and hasattr(self._wf_scene, 'selection_manager'):
                    # No modifier - deselect all immediately
                    self._wf_scene.selection_manager.deselect_all()
            else:
                # Disable rubber band completely when clicking on items
                self._rubber_band_enabled = False
                self._rubber_band_active = False
                self._rubber_band.hide()
                logger.debug(f"Item clicked: rubber band disabled")
        
        # Call parent handler to maintain normal functionality
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self._rubber_band_enabled:
            # Only do rubber band logic if we clicked on empty space initially
            if not self._rubber_band_active:
                # Calculate distance moved
                distance = (event.pos() - self._rubber_band_origin).manhattanLength()
                if distance >= 3:  # Start rubber band after 3 pixels of movement
                    self._rubber_band_active = True
                    rubber_rect = QRect(self._rubber_band_origin, event.pos()).normalized()
                    self._rubber_band.setGeometry(rubber_rect)
                    self._rubber_band.show()
                    logger.debug(f"Rubber band selection started")
            else:
                # Update rubber band size
                rubber_rect = QRect(self._rubber_band_origin, event.pos()).normalized()
                self._rubber_band.setGeometry(rubber_rect)
        
        # Call parent handler
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._rubber_band_active:            
            # Get selection rectangle in widget coordinates
            widget_rect = self._rubber_band.geometry()
            
            # Convert view coordinates to scene coordinates
            top_left_scene = self.mapToScene(widget_rect.topLeft())
            bottom_right_scene = self.mapToScene(widget_rect.bottomRight())
            scene_rect = QRectF(top_left_scene, bottom_right_scene)
            
            logger.debug(f"Box selection completed: scene_rect={scene_rect}")
            
            # Finish rubber band selection
            self._rubber_band.hide()
            self._rubber_band_active = False
            self._rubber_band_enabled = False  # Reset for next operation
            
            # Find items within the selection rectangle
            self._select_items_in_rect(scene_rect)
        
        # Call parent handler
        super().mouseReleaseEvent(event)
        
    def _select_items_in_rect(self, scene_rect: QRectF):
        """Find and select all selectable items within the given scene rectangle"""
        if not self._wf_scene or not hasattr(self._wf_scene, 'selection_manager'):
            logger.warning("No scene or selection manager available for box selection")
            return
            
        # Find entities (statuses and workflows) within the rectangle
        entities_to_select = set()
        lines_to_select = set()
        
        # Check workflow entities
        for workflow in self._wf_scene.workflows:
            if self._is_entity_in_rect(workflow, scene_rect):
                entities_to_select.add(workflow)
                
        # Check status entities  
        for status in self._wf_scene.statuses:
            if self._is_entity_in_rect(status, scene_rect):
                entities_to_select.add(status)
                
        # Check line groups
        for line in self._wf_scene.lines:
            if self._is_line_in_rect(line, scene_rect):
                lines_to_select.add(line)
        
        logger.debug(f"Box selection found: {len(entities_to_select)} entities, {len(lines_to_select)} lines")
        
        # Apply type-based selection rules
        all_items = entities_to_select | lines_to_select
        if all_items:
            self._wf_scene.selection_manager.add_items_to_selection(all_items)
        else:
            logger.debug("No items found in selection rectangle")
            
    def _is_entity_in_rect(self, entity, scene_rect: QRectF) -> bool:
        """Check if an entity's shape is within the selection rectangle"""
        if not entity.shape or not entity.shape.graphicsItem:
            return False
            
        # Get entity bounds in scene coordinates
        item_rect = entity.shape.graphicsItem.sceneBoundingRect()
        return scene_rect.intersects(item_rect)
        
    def _is_line_in_rect(self, line_group, scene_rect: QRectF) -> bool:
        """Check if any part of a line group is within the selection rectangle"""
        # Check if any of the line segments intersect with the selection rectangle
        for line_item in line_group.lineSegments:
            if hasattr(line_item, 'sceneBoundingRect'):
                item_rect = line_item.sceneBoundingRect()
                if scene_rect.intersects(item_rect):
                    return True
        return False


class DrawingWidget(QFrame):
    def __init__(self, sceneDict: dict, sceneManagerDict: dict = None, initial_workflow_key: str = None, enable_opengl=True, parent=None):
        super().__init__(parent)

        self.sceneDict: dict = sceneDict  # Qt graphics scenes
        self.sceneManagerDict: dict = sceneManagerDict or {}  # WFScene objects
        self.rendering_optimizer = RenderingOptimizer(default_config)
        
        # Use provided initial workflow key, or fall back to first available key
        if initial_workflow_key and initial_workflow_key in sceneDict:
            self.currentWorkflow = initial_workflow_key
        else:
            # Fallback to first available workflow
            self.currentWorkflow = next(iter(sceneDict.keys())) if sceneDict else None

        self.setMinimumSize(_DEF_DW_SZ_X, _DEF_DW_SZ_Y)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.view = CustomGraphicsView()
        layout.addWidget(self.view)
        
        # Configure rendering based on scene complexity
        self._configure_rendering_quality()

        # Set initial scene if we have workflows
        if self.currentWorkflow:
            self.view.setScene(self.sceneDict[self.currentWorkflow])
            
            # Set the WFScene reference if available
            if self.currentWorkflow in self.sceneManagerDict:
                self.view.set_wf_scene(self.sceneManagerDict[self.currentWorkflow])
    
    def _get_current_scene_item_count(self) -> int:
        """Get the number of items in the current scene for performance optimization"""
        if not self.currentWorkflow or self.currentWorkflow not in self.sceneDict:
            return 0
            
        scene = self.sceneDict[self.currentWorkflow]
        return len(scene.items()) if scene else 0
    
    def _configure_rendering_quality(self):
        """Configure rendering quality based on scene complexity and user preferences"""
        item_count = self._get_current_scene_item_count()
        settings = self.rendering_optimizer.get_optimized_settings(item_count)
        
        # Apply OpenGL settings if enabled
        opengl_enabled = False
        if settings['enable_opengl'] and OPENGL_AVAILABLE:
            opengl_enabled = self.view.enable_opengl_antialiasing(samples=settings['msaa_samples'])
        
        # Log rendering configuration
        perf_info = self.rendering_optimizer.get_performance_info(item_count)
        if opengl_enabled:
            logger.info(f"Rendering configured: {perf_info}")
        else:
            logger.info(f"Rendering configured: Basic anti-aliasing (OpenGL {'disabled' if not settings['enable_opengl'] else 'unavailable'})")
        
        # Show performance warning if needed
        if settings['show_performance_warning']:
            logger.warning(f"Large workflow ({item_count} items) - using reduced quality settings for better performance")
    
    def refresh_rendering_settings(self):
        """Refresh rendering settings - useful after scene changes or preference updates"""
        self._configure_rendering_quality()


    def change_workflow(self, wfTitle):
        self.currentWorkflow = wfTitle
        #self.update()
        self.view.setScene(self.sceneDict[self.currentWorkflow])
        
        # Update WFScene reference when switching workflows
        if self.currentWorkflow in self.sceneManagerDict:
            self.view.set_wf_scene(self.sceneManagerDict[self.currentWorkflow])
            
        # Reconfigure rendering for the new workflow's complexity
        self.refresh_rendering_settings()

    def unused(self):
        painter = QPainter(self)
        pen = QPen(QColor(0, 0, 0), 2)
        painter.setPen(pen)

        fontMetric = QFontMetrics(painter.font())

        currentScene = self.sceneDict[self.currentWorkflow]

        for key, workflow in currentScene["workflows"].items():
            painter.drawRect(QRect(workflow.nodeRect.left, workflow.nodeRect.top, workflow.nodeRect.width, workflow.nodeRect.height))
            painter.drawText(
                    QPoint(workflow.nodeRect.left + _TITLE_OFFS_X, workflow.nodeRect.top + _TITLE_OFFS_Y), 
                    workflow.nodeAttribs["LayoutNode"]["Tooltip"]
                )

            offset = 1
            for wfStatus in currentScene["workflowStatuses"][key]:
                painter.drawText(
                        QPoint(workflow.nodeRect.left + _TITLE_OFFS_X + 5, workflow.nodeRect.top + 12 + (offset * 15)), 
                        wfStatus.Title
                    )
                offset += 1

        for key, status in currentScene["statuses"].items():
            painter.drawEllipse(QPoint(status.nodeRect.cx, status.nodeRect.cy), status.nodeRect.rx, status.nodeRect.ry)
            text = status.nodeProps['Text']
            textWidth = fontMetric.horizontalAdvance(text)
            textHeight = fontMetric.height()
            painter.drawText(
                    QPoint(status.nodeRect.cx - textWidth // 2, status.nodeRect.cy + textHeight // 4), # 4 to account for Qt baseline
                    text
                )
            

        for i in range(1, len(currentScene["linkPoints"])):
            # If new segment, skip to break line
            if currentScene["linkPoints"][i][2]:
                pen = QPen(QColor(random.randint(0,255), random.randint(0,255), 0), 2)
                continue
            
            painter.setPen(pen)
            # This is gross
            if i+1 == len(currentScene["linkPoints"]) or currentScene["linkPoints"][i+1][2]:
                drawArrow(painter, currentScene["linkPoints"][i-1], currentScene["linkPoints"][i])
            else:
                painter.drawLine(
                        currentScene["linkPoints"][i-1][0], 
                        currentScene["linkPoints"][i-1][1], 
                        currentScene["linkPoints"][i][0], 
                        currentScene["linkPoints"][i][1]
                        )
