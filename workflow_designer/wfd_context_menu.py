"""
Context menu system for the workflow designer.
Provides right-click functionality for adding new entities to the scene.
"""

from typing import Callable, Optional, Tuple, TYPE_CHECKING
from PySide6.QtWidgets import QMenu, QWidget
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
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent_widget = parent
        self._current_position: Optional[Tuple[float, float]] = None
        
    def show_context_menu(self, position: QPoint, scene_position: Tuple[float, float], scene: 'WFScene') -> None:
        """
        Show context menu at the specified position.
        
        Args:
            position: Widget position for menu display
            scene_position: Scene coordinates for entity placement
            scene: Current workflow scene
        """
        self._current_position = scene_position
        
        menu = QMenu(self.parent_widget)
        
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
        
        # Add info action showing coordinates
        info_action = QAction(f"Position: ({scene_position[0]:.0f}, {scene_position[1]:.0f})", menu)
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
        from PySide6.QtWidgets import QInputDialog
        
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