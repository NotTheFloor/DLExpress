import random

from PySide6.QtWidgets import QFrame, QGraphicsView, QVBoxLayout, QGraphicsScene, QRubberBand, QMessageBox
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
from .wfd_deletion_manager import DeletionManager
from workflow_designer.wfd_context_menu import setup_context_menu_for_widget, SimpleStatusInputDialog
from workflow_designer.wfd_workflow_selector import select_workflow_for_scene

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
    
    def keyPressEvent(self, event):
        """Handle keyboard events, particularly Delete key for object deletion and undo/redo"""
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            self._handleDeleteKey()
        elif event.key() == Qt.Key_Z and event.modifiers() & Qt.ControlModifier:
            self._handleUndoKey()
        elif event.key() == Qt.Key_Y and event.modifiers() & Qt.ControlModifier:
            self._handleRedoKey()
        else:
            # Call parent handler for other keys
            super().keyPressEvent(event)
    
    def _handleDeleteKey(self):
        """Handle Delete key press - delete selected items"""
        
        logger.debug(f"Delete key pressed - scene has {len(self.scene().items())} items")

        if not self._wf_scene or not hasattr(self._wf_scene, 'selection_manager'):
            logger.warning("No scene or selection manager available for deletion")
            return
        
        selection_manager = self._wf_scene.selection_manager
        selected_items = selection_manager.get_selected_items()
        
        if not selected_items:
            logger.debug("No items selected for deletion")
            return
        
        # Debug logging to understand what's selected
        logger.debug(f"Selected {len(selected_items)} items for deletion:")
        for i, item in enumerate(selected_items):
            item_type = type(item).__name__
            has_entity_type = hasattr(item, 'entityType')
            has_src_entity = hasattr(item, 'srcEntity')
            logger.debug(f"  {i}: {item_type} (entityType={has_entity_type}, srcEntity={has_src_entity})")
        
        # Create deletion manager with Qt scene reference for graphics cleanup
        qt_scene = self.scene() if hasattr(self, 'scene') and self.scene() else None
        deletion_manager = DeletionManager(self._wf_scene, qt_scene)
        
        # Check if deletion is possible
        if not deletion_manager.canDelete(list(selected_items)):
            logger.warning("Selected items cannot be deleted")
            return
        
        # For entities, show impact information
        entities = [item for item in selected_items if hasattr(item, 'entityType')]
        if entities:
            impact = deletion_manager.getImpactedItems(entities)
            logger.info(f"Delete impact: {impact['entities']} entities + {impact['cascaded_lines']} connected lines = {impact['total_items']} total items")

        # Temporary hard delete
        deletion_manager.deleteSelected(selection_manager)

        logger.debug(f"After deletion - scene has {len(self.scene().items())} items")

        self.parent().refresh_rendering_settings()

        ## UNDO ISSUES : Following code is removed for now
        # Perform the deletion using undo/redo command pattern
        """try:
            from .wfd_undo_system import CommandFactory
            
            # Create undoable delete command using factory
            delete_command = CommandFactory.createDeleteCommand(
                scene=self._wf_scene, 
                items_to_delete=list(selected_items),
                qt_graphics_scene=qt_scene
            )
            
            # Execute command through undo stack (this will call redo() automatically)
            self._wf_scene.undo_stack.push(delete_command)
            
            logger.info(f"Undoable deletion executed: {delete_command.text()}")
            
            # Refresh rendering settings after deletion (scene complexity may have changed)
            if hasattr(self.parent(), 'refresh_rendering_settings'):
                self.parent().refresh_rendering_settings()
                
        except Exception as e:
            logger.error(f"Error during undoable deletion: {e}")
        """

    def _handleUndoKey(self):
        """Handle Ctrl+Z key press - undo last command"""
        logger.warning("Undo currently removed")
        return

        if not self._wf_scene or not hasattr(self._wf_scene, 'undo_stack'):
            logger.warning("No scene or undo stack available for undo")
            return
        
        undo_stack = self._wf_scene.undo_stack
        if undo_stack.canUndo():
            command_text = undo_stack.undoText()
            undo_stack.undo()
            logger.info(f"Undid: {command_text}")
        else:
            logger.debug("Nothing to undo")
    
    def _handleRedoKey(self):
        """Handle Ctrl+Y key press - redo last undone command"""
        logger.warning("Redo is currently disabled")
        return
        
        if not self._wf_scene or not hasattr(self._wf_scene, 'undo_stack'):
            logger.warning("No scene or undo stack available for redo")
            return
        
        undo_stack = self._wf_scene.undo_stack
        if undo_stack.canRedo():
            command_text = undo_stack.redoText()
            undo_stack.redo()
            logger.info(f"Redid: {command_text}")
        else:
            logger.debug("Nothing to redo")
    
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
        
        # Set up context menu functionality
        self._setup_context_menu()
    
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
    
    def get_undo_redo_status(self) -> dict:
        """Get current undo/redo availability and command text"""
        if not self.currentWorkflow or self.currentWorkflow not in self.sceneManagerDict:
            return {'can_undo': False, 'can_redo': False, 'undo_text': '', 'redo_text': ''}
        
        wf_scene = self.sceneManagerDict[self.currentWorkflow]
        if not hasattr(wf_scene, 'undo_stack'):
            return {'can_undo': False, 'can_redo': False, 'undo_text': '', 'redo_text': ''}
        
        undo_stack = wf_scene.undo_stack
        return {
            'can_undo': undo_stack.canUndo(),
            'can_redo': undo_stack.canRedo(),
            'undo_text': undo_stack.undoText() if undo_stack.canUndo() else '',
            'redo_text': undo_stack.redoText() if undo_stack.canRedo() else ''
        }


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
    
    def _setup_context_menu(self):
        """Set up context menu functionality for the graphics view"""
        
        def get_current_scene():
            """Get the current WFScene"""
            if self.currentWorkflow and self.currentWorkflow in self.sceneManagerDict:
                return self.sceneManagerDict[self.currentWorkflow]
            return None
        
        def map_position_to_scene(widget_pos):
            """Map widget position to scene coordinates"""
            try:
                scene_pos = self.view.mapToScene(widget_pos)
                x, y = scene_pos.x(), scene_pos.y()
                
                # Validate that coordinates are valid numbers
                if x is None or y is None or not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                    logger.error(f"Invalid scene coordinates: x={x}, y={y} from widget_pos={widget_pos}")
                    return (100.0, 100.0)  # Fallback position
                
                return (float(x), float(y))
            except Exception as e:
                logger.error(f"Error mapping widget position to scene: {e}")
                return (100.0, 100.0)  # Fallback position
        
        # Set up context menu handler
        self.context_menu_handler = setup_context_menu_for_widget(
            self.view,
            get_current_scene,
            map_position_to_scene
        )
        
        # Connect context menu signals to our handlers
        self.context_menu_handler.add_status_requested.connect(self._handle_add_status_request)
        self.context_menu_handler.add_workflow_requested.connect(self._handle_add_workflow_request)
        self.context_menu_handler.connect_to_target_requested.connect(self._handle_connect_to_target_request)
        
        logger.debug("Context menu functionality set up for drawing widget")
    
    def _handle_add_status_request(self, position, default_title):
        """Handle request to add a new status"""
        
        # Get status title from user
        title = SimpleStatusInputDialog.get_status_title(self, default_title)
        if not title:
            return  # User cancelled
        
        # Get current scene
        wf_scene = self._get_current_wf_scene()
        if not wf_scene:
            logger.error("No current WFScene available for adding status")
            return
        
        try:
            # Add the status to the scene
            new_status = wf_scene.add_new_status_visual(position, title)
            
            # Refresh the graphics scene to show the new status
            self._refresh_graphics_scene(wf_scene)
            
            logger.info(f"Added new status '{title}' at position {position}")
            
        except Exception as e:
            logger.error(f"Failed to add new status: {e}")
            self._show_error_message("Add Status Error", f"Failed to add new status: {str(e)}")
    
    def _handle_add_workflow_request(self, position):
        """Handle request to add an existing workflow"""
        
        # Get current scene
        wf_scene = self._get_current_wf_scene()
        if not wf_scene:
            logger.error("No current WFScene available for adding workflow")
            return
        
        # Show workflow selection dialog
        selected_workflow = select_workflow_for_scene(
            wf_scene.sceneManager,
            self.currentWorkflow,
            self
        )
        
        if not selected_workflow:
            return  # User cancelled
        
        try:
            # Add the workflow to the scene
            new_workflow = wf_scene.add_existing_workflow_visual(
                position, 
                selected_workflow['WorkflowKey']
            )
            
            # Refresh the graphics scene to show the new workflow
            self._refresh_graphics_scene(wf_scene)
            
            logger.info(f"Added workflow '{selected_workflow['Title']}' at position {position}")
            
        except Exception as e:
            logger.error(f"Failed to add existing workflow: {e}")
            self._show_error_message("Add Workflow Error", f"Failed to add workflow: {str(e)}")
    
    def _handle_connect_to_target_request(self, target):
        """Handle request to create connections to a target"""
        # Get current scene
        wf_scene = self._get_current_wf_scene()
        if not wf_scene:
            logger.error("No current WFScene available for creating connections")
            return
        
        # Get selected items
        selected_items = list(wf_scene.selection_manager.get_selected_items()) if wf_scene.selection_manager else []
        if not selected_items:
            logger.warning("No items selected for connection creation")
            self._show_error_message("Connection Error", "No items are selected to connect from")
            return
        
        try:
            # Create the connections
            created_connections = wf_scene.create_connections_visual(selected_items, target)
            
            if created_connections:
                # Refresh the graphics scene to show the new connections
                self._refresh_graphics_scene(wf_scene)
                
                # Get target description for user feedback
                from workflow_designer.wfd_context_menu import ContextMenuHandler
                context_handler = ContextMenuHandler()
                target_desc = context_handler._get_target_description(target)
                
                logger.info(f"Created {len(created_connections)} connection(s) to {target_desc}")
                
                # Optionally clear selection after connecting
                wf_scene.selection_manager.deselect_all()
            else:
                logger.warning("No connections were created")
                self._show_error_message("Connection Error", "Unable to create connections")
            
        except Exception as e:
            logger.error(f"Failed to create connections: {e}")
            self._show_error_message("Connection Error", f"Failed to create connections: {str(e)}")
    
    def _get_current_wf_scene(self):
        """Get the current WFScene object"""
        if self.currentWorkflow and self.currentWorkflow in self.sceneManagerDict:
            return self.sceneManagerDict[self.currentWorkflow]
        return None
    
    def _refresh_graphics_scene(self, wf_scene):
        """Refresh the Qt graphics scene to reflect changes in WFScene"""
        if not self.currentWorkflow or self.currentWorkflow not in self.sceneDict:
            logger.warning("Cannot refresh graphics scene: no current workflow or scene")
            return
        
        qt_scene = self.sceneDict[self.currentWorkflow]
        
        # Get current Qt scene items for comparison
        current_qt_items = set(qt_scene.items())
        
        # Add any new entities that aren't in the Qt scene yet
        entities_added = 0
        
        # Check status entities
        for status in wf_scene.statuses:
            if status.shape and status.shape.graphicsItem:
                if status.shape.graphicsItem not in current_qt_items:
                    qt_scene.addItem(status.shape.graphicsItem)
                    entities_added += 1
                    logger.debug(f"Added status '{status.title}' graphics item to Qt scene")
        
        # Check workflow entities  
        for workflow in wf_scene.workflows:
            if workflow.shape and workflow.shape.graphicsItem:
                if workflow.shape.graphicsItem not in current_qt_items:
                    qt_scene.addItem(workflow.shape.graphicsItem)
                    entities_added += 1
                    logger.debug(f"Added workflow '{workflow.title}' graphics item to Qt scene")
        
        # Check line entities (for future line additions)
        for line in wf_scene.lines:
            if hasattr(line, 'lineSegments'):
                for item in line.lineSegments:
                    # Handle both wrapped objects and raw Qt items
                    graphics_item = getattr(item, 'graphicsItem', item)
                    if graphics_item not in current_qt_items:
                        qt_scene.addItem(graphics_item)
                        entities_added += 1
        
        if entities_added > 0:
            logger.info(f"Added {entities_added} new graphics items to Qt scene")
            # Force view to update
            if hasattr(self.view, 'viewport'):
                self.view.viewport().update()
        else:
            logger.debug("No new entities to add to Qt scene")
    
    def _show_error_message(self, title, message):
        """Show an error message to the user"""
        
        msg_box = QMessageBox(QMessageBox.Critical, title, message, parent=self)
        msg_box.exec()
