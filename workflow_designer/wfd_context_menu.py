"""
Context menu system for the workflow designer.
Provides right-click functionality for adding new entities to the scene.
"""

from typing import Callable, Optional, Tuple, TYPE_CHECKING
from PySide6.QtWidgets import QMenu, QWidget, QInputDialog
from PySide6.QtCore import QPoint, Signal, QObject
from PySide6.QtGui import QAction

if TYPE_CHECKING:
    from workflow_designer.wfd_scene import WFScene

from workflow_designer.wfd_logger import logger


class ContextMenuHandler(QObject):
    """Handles context menu creation and actions for the drawing widget"""
    
    # Signals for menu actions
    add_status_requested = Signal(tuple, str)  # position, title
    add_workflow_requested = Signal(tuple)     # position
    connect_to_target_requested = Signal(object)  # target entity/status line
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent_widget = parent
        self._current_position: Optional[Tuple[float, float]] = None
        self._current_target = None  # Entity or status line that was right-clicked
        
    def show_context_menu(self, position: QPoint, scene_position: Tuple[float, float], scene: 'WFScene') -> None:
        """
        Show context menu at the specified position.
        
        Args:
            position: Widget position for menu display
            scene_position: Scene coordinates for entity placement
            scene: Current workflow scene
        """
        self._current_position = scene_position
        
        # Determine what was right-clicked (entity or status line)
        self._current_target = self._identify_right_click_target(scene_position, scene)
        
        # Get current selection state
        selected_items = scene.selection_manager.get_selected_items() if scene.selection_manager else set()
        has_selection = len(selected_items) > 0
        
        menu = QMenu(self.parent_widget)
        
        # Connection options (only show if items are selected and target is different)
        if has_selection and self._current_target and self._current_target not in selected_items:
            connect_action = QAction("Connect to Here", menu)
            target_description = self._get_target_description(self._current_target)
            connect_action.setToolTip(f"Create connection(s) from selected items to {target_description}")
            connect_action.triggered.connect(self._handle_connect_to_target)
            menu.addAction(connect_action)
            menu.addSeparator()
        
        # Standard creation actions (only show on empty space)
        if not self._current_target:
            # Add "Add New Status" action
            add_status_action = QAction("Add New Status", menu)
            add_status_action.setToolTip("Add a new status at this position")
            add_status_action.triggered.connect(self._handle_add_status)
            menu.addAction(add_status_action)
            
            # Add "Add Existing Workflow" action
            add_workflow_action = QAction("Add Existing Workflow", menu)
            add_workflow_action.setToolTip("Add an existing workflow at this position")
            add_workflow_action.triggered.connect(self._handle_add_workflow)
            menu.addAction(add_workflow_action)
            
            # Add separator
            menu.addSeparator()
        
        # Add info action showing coordinates and selection state
        info_text = f"Position: ({scene_position[0]:.0f}, {scene_position[1]:.0f})"
        if has_selection:
            info_text += f" | Selected: {len(selected_items)} item(s)"
        if self._current_target:
            info_text += f" | Target: {self._get_target_description(self._current_target)}"
        
        info_action = QAction(info_text, menu)
        info_action.setEnabled(False)
        menu.addAction(info_action)
        
        # Show the menu
        menu.exec(position)
        
    def _handle_add_status(self):
        """Handle add status action"""
        if self._current_position is None:
            logger.warning("No position available for add status action")
            return
            
        # Emit signal with position and default title
        self.add_status_requested.emit(self._current_position, "New Status")
        logger.debug(f"Add status requested at position {self._current_position}")
        
    def _handle_add_workflow(self):
        """Handle add workflow action"""
        if self._current_position is None:
            logger.warning("No position available for add workflow action")
            return
            
        # Emit signal with position
        self.add_workflow_requested.emit(self._current_position)
        logger.debug(f"Add workflow requested at position {self._current_position}")
    
    def _handle_connect_to_target(self):
        """Handle connect to target action"""
        if self._current_target is None:
            logger.warning("No target available for connection")
            return
            
        # Emit signal with target entity/status line
        self.connect_to_target_requested.emit(self._current_target)
        logger.debug(f"Connect to target requested: {self._get_target_description(self._current_target)}")
    
    def _identify_right_click_target(self, scene_position: Tuple[float, float], scene: 'WFScene') -> Optional[object]:
        """
        Identify what entity or status line was right-clicked at the given position.
        
        Args:
            scene_position: Scene coordinates of right-click
            scene: Current workflow scene
            
        Returns:
            Entity, WorkflowStatusLine, or None if empty space
        """
        from PySide6.QtCore import QPointF
        
        # Check workflows first (including status lines within workflows)
        for workflow in scene.workflows:
            if not workflow.shape or not workflow.shape.graphicsItem:
                continue
                
            # Get workflow bounds
            workflow_bounds = workflow.shape.graphicsItem.sceneBoundingRect()
            scene_point = QPointF(scene_position[0], scene_position[1])
            
            if workflow_bounds.contains(scene_point):
                # Convert scene position to workflow local position
                local_pos = workflow.shape.graphicsItem.mapFromScene(scene_point)
                
                # Check if click is on a specific status line
                clicked_status_line = workflow._find_status_line_at_position(local_pos)
                if clicked_status_line:
                    return clicked_status_line
                else:
                    # Click is on workflow background
                    return workflow
        
        # Check standalone statuses
        for status in scene.statuses:
            if not status.shape or not status.shape.graphicsItem:
                continue
                
            status_bounds = status.shape.graphicsItem.sceneBoundingRect()
            scene_point = QPointF(scene_position[0], scene_position[1])
            
            if status_bounds.contains(scene_point):
                return status
        
        # Nothing found - empty space
        return None
    
    def _get_target_description(self, target: object) -> str:
        """Get a human-readable description of the target for UI display"""
        if hasattr(target, 'status_title'):  # WorkflowStatusLine
            return f"status line '{target.status_title}'"
        elif hasattr(target, 'title'):  # WFEntity (status or workflow)
            entity_type = "workflow" if hasattr(target, 'statuses') else "status"
            return f"{entity_type} '{target.title}'"
        else:
            return "unknown target"


class SimpleStatusInputDialog:
    """Simple dialog to get status title from user"""
    
    @staticmethod
    def get_status_title(parent: Optional[QWidget] = None, default_title: str = "New Status") -> Optional[str]:
        """
        Get status title from user input.
        
        Args:
            parent: Parent widget
            default_title: Default title text
            
        Returns:
            User-entered title or None if cancelled
        """
        
        title, ok = QInputDialog.getText(
            parent,
            "New Status",
            "Enter status title:",
            text=default_title
        )
        
        if ok and title.strip():
            return title.strip()
        return None


def create_context_menu_handler(parent: QWidget) -> ContextMenuHandler:
    """
    Factory function to create a context menu handler.
    
    Args:
        parent: Parent widget for the menu handler
        
    Returns:
        Configured context menu handler
    """
    handler = ContextMenuHandler(parent)
    logger.debug("Created context menu handler")
    return handler


def setup_context_menu_for_widget(
    widget: QWidget, 
    scene_getter: Callable[[], Optional['WFScene']],
    position_mapper: Callable[[QPoint], Tuple[float, float]]
) -> ContextMenuHandler:
    """
    Set up context menu functionality for a widget.
    
    Args:
        widget: Widget to add context menu to
        scene_getter: Function to get current scene
        position_mapper: Function to map widget coordinates to scene coordinates
        
    Returns:
        Context menu handler for further customization
    """
    handler = create_context_menu_handler(widget)
    
    def handle_context_menu(position: QPoint):
        scene = scene_getter()
        if scene is None:
            logger.warning("No scene available for context menu")
            return
            
        scene_position = position_mapper(position)
        global_position = widget.mapToGlobal(position)
        handler.show_context_menu(global_position, scene_position, scene)
    
    # Override the widget's context menu event
    original_context_menu_event = getattr(widget, 'contextMenuEvent', None)
    
    def context_menu_event(event):
        handle_context_menu(event.pos())
        event.accept()
    
    widget.contextMenuEvent = context_menu_event
    logger.debug(f"Set up context menu for widget {widget.__class__.__name__}")
    
    return handler
