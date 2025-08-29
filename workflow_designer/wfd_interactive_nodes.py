import math
import uuid
from typing import List, Tuple, Optional, TYPE_CHECKING
from dataclasses import dataclass
import time
import traceback

from PySide6.QtCore import QObject, Signal, Qt, QPointF
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsItem, QApplication

if TYPE_CHECKING:
    from workflow_designer.wfd_utilities import MultiSegmentArrow

from .wfd_logger import logger

@dataclass
class InteractiveWaypoint:
    """Represents a waypoint in a line that can be moved by the user"""
    position: Tuple[float, float]
    is_user_created: bool = False  # False if from XML, True if created by user
    node_id: str = ""
    
    def __post_init__(self):
        if not self.node_id:
            self.node_id = str(uuid.uuid4())
    
    @property
    def x(self) -> float:
        return self.position[0]
    
    @property 
    def y(self) -> float:
        return self.position[1]
    
    def move_to(self, new_position: Tuple[float, float]):
        """Update waypoint position"""
        # Validate position to prevent (0,0) coordinate bugs
        if new_position and len(new_position) == 2:
            x, y = new_position
            # Only update if coordinates are reasonable (not NaN or extreme values)
            if not (math.isnan(x) or math.isnan(y) or abs(x) > 100000 or abs(y) > 100000):
                self.position = new_position
            else:
                logger.warning(f"Warning: Invalid waypoint position rejected: {new_position}")
        else:
            logger.warning(f"Warning: Invalid position format rejected: {new_position}")
    
    def distance_to(self, point: Tuple[float, float]) -> float:
        """Calculate distance to another point"""
        dx = self.x - point[0]
        dy = self.y - point[1]
        return math.sqrt(dx * dx + dy * dy)


class WaypointNode(QGraphicsEllipseItem):
    """Visual representation of a movable waypoint"""
    
    def __init__(self, waypoint: InteractiveWaypoint, node_manager: 'LineNodeManager', parent=None):
        # Create 6px radius circle centered at waypoint
        super().__init__(-6, -6, 12, 12, parent)
        
        self.waypoint = waypoint
        self.node_manager = node_manager
        self.is_dragging = False
        self.drag_start_pos = None
        
        # DEBUG: Enhanced tracking for round 2
        self.creation_timestamp = None
        self.move_count = 0
        self.drag_session_count = 0
        self.last_known_scene_pos = None
        self.last_known_item_pos = None
        
        # Set position with validation
        x, y = waypoint.x, waypoint.y
        if math.isnan(x) or math.isnan(y):
            logger.warning(f"Warning: WaypointNode has NaN coordinates: ({x}, {y}) for waypoint {waypoint.node_id}")
            # Use a fallback position
            x, y = 50, 50
            waypoint.move_to((x, y))
        elif (x == 0 and y == 0):
            logger.warning(f"Warning: WaypointNode created at origin (0,0) for waypoint {waypoint.node_id}")
            # This might be legitimate, but worth noting
        
        self.setPos(x, y)
        
        # DEBUG: Log coordinate system state at creation
        self.creation_timestamp = time.time()
        self.last_known_scene_pos = self.scenePos()
        self.last_known_item_pos = self.pos()
        #self._log_coordinate_state("CREATION")
        
        # Visual properties
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Default appearance
        self._normal_pen = QPen(QColor("#666666"), 1)
        self._normal_brush = QBrush(QColor("#CCCCCC"))
        self._hover_pen = QPen(QColor("#333333"), 2)
        self._hover_brush = QBrush(QColor("#FFFFFF"))
        self._drag_pen = QPen(QColor("#FF8C00"), 2)
        self._drag_brush = QBrush(QColor("#FF8C00"))
        
        self.setPen(self._normal_pen)
        self.setBrush(self._normal_brush)
        
        # Enable hover events
        self.setAcceptHoverEvents(True)
    
    def hoverEnterEvent(self, event):
        if not self.is_dragging:
            self.setPen(self._hover_pen)
            self.setBrush(self._hover_brush)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        if not self.is_dragging:
            self.setPen(self._normal_pen)
            self.setBrush(self._normal_brush)
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = self.pos()
            self.setPen(self._drag_pen)
            self.setBrush(self._drag_brush)
            
            # Track drag sessions and reset move count
            self.drag_session_count += 1
            self.move_count = 0
            
            # DEBUG: Log coordinate state at press  
            time_since_creation = time.time() - self.creation_timestamp if self.creation_timestamp else 0
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.move_count += 1
            
            # COORDINATE FIX: Use event.scenePos() instead of self.pos() to avoid Qt coordinate corruption
            scene_pos = event.scenePos()
            
            # Update both Qt graphics position and waypoint data
            self.setPos(scene_pos.x(), scene_pos.y())
            position_tuple = (scene_pos.x(), scene_pos.y())
            self.waypoint.move_to(position_tuple)
            
            # Notify manager to update line geometry
            self.node_manager.on_waypoint_moved(self.waypoint)
        
        # Do NOT call super().mouseMoveEvent(event) to prevent Qt's default ItemIsMovable behavior
    
    def mouseReleaseEvent(self, event):

        if event.button() == Qt.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.setPen(self._hover_pen)
            self.setBrush(self._hover_brush)
            
            self.node_manager.on_waypoint_drag_finished(self.waypoint)
            
        super().mouseReleaseEvent(event)
    
    def update_position(self, new_pos: Tuple[float, float]):
        """Update visual position to match waypoint position"""
        self.setPos(new_pos[0], new_pos[1])
        self.waypoint.position = new_pos
        
    def set_selection_color(self, color: QColor):
        """Update colors based on current theme"""
        self._drag_pen = QPen(color, 2)
        self._drag_brush = QBrush(color)
    
    def _log_coordinate_state(self, event_name: str, event=None):
        """Enhanced coordinate system debugging for round 2"""
        
        # Current coordinates
        item_pos = self.pos()
        print(f"CURRENT self.pos():           ({item_pos.x():.2f}, {item_pos.y():.2f})")
        
        try:
            scene_pos = self.scenePos()
            print(f"CURRENT self.scenePos():      ({scene_pos.x():.2f}, {scene_pos.y():.2f})")
        except Exception as e:
            print(f"CURRENT self.scenePos():      ERROR: {e}")
        
        # Compare with last known positions
        if self.last_known_item_pos:
            last_item = self.last_known_item_pos
            print(f"LAST self.pos():              ({last_item.x():.2f}, {last_item.y():.2f})")
            item_delta = (item_pos.x() - last_item.x(), item_pos.y() - last_item.y())
            print(f"ITEM POSITION DELTA:          ({item_delta[0]:.2f}, {item_delta[1]:.2f})")
        
        if self.last_known_scene_pos:
            last_scene = self.last_known_scene_pos
            print(f"LAST self.scenePos():         ({last_scene.x():.2f}, {last_scene.y():.2f})")
            try:
                scene_pos = self.scenePos()
                scene_delta = (scene_pos.x() - last_scene.x(), scene_pos.y() - last_scene.y())
                print(f"SCENE POSITION DELTA:         ({scene_delta[0]:.2f}, {scene_delta[1]:.2f})")
            except:
                print(f"SCENE POSITION DELTA:         ERROR calculating")
        
        # Waypoint data  
        print(f"waypoint.position:            ({self.waypoint.x:.2f}, {self.waypoint.y:.2f})")
        
        # Event coordinates (if available)
        if event:
            try:
                event_pos = event.pos()
                print(f"event.pos():                  ({event_pos.x():.2f}, {event_pos.y():.2f})")
            except Exception as e:
                print(f"event.pos():                  ERROR: {e}")
            
            try:
                event_scene_pos = event.scenePos()
                print(f"event.scenePos():             ({event_scene_pos.x():.2f}, {event_scene_pos.y():.2f})")
            except Exception as e:
                print(f"event.scenePos():             ERROR: {e}")
        
        # Item flags and state
        print(f"ItemIsMovable:                {bool(self.flags() & QGraphicsItem.ItemIsMovable)}")
        print(f"ItemIsSelectable:             {bool(self.flags() & QGraphicsItem.ItemIsSelectable)}")
        print(f"ItemSendsGeometryChanges:     {bool(self.flags() & QGraphicsItem.ItemSendsGeometryChanges)}")
        
        # Parent and scene info
        parent = self.parentItem()
        print(f"Parent item:                  {type(parent).__name__ if parent else 'None'}")
        scene = self.scene()
        print(f"Scene:                        {type(scene).__name__ if scene else 'None'}")
        
        # Update last known positions
        self.last_known_item_pos = self.pos()
        try:
            self.last_known_scene_pos = self.scenePos()
        except:
            pass
        
        print(f"================================================\n")


class MidpointNode(QGraphicsRectItem):
    """Visual representation of a segment midpoint (creates new waypoint when dragged)"""
    
    def __init__(self, midpoint: Tuple[float, float], segment_index: int, node_manager: 'LineNodeManager', parent=None):
        # Create 8x8px square centered at midpoint
        super().__init__(-4, -4, 8, 8, parent)
        
        self.midpoint = midpoint
        self.segment_index = segment_index
        self.node_manager = node_manager
        self.is_dragging = False
        self.has_been_dragged = False
        self.ghost_waypoint = None  # For ghost dragging
        self.original_position = midpoint  # Store original position
        
        # Set position
        self.setPos(midpoint[0], midpoint[1])
        
        # Visual properties
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Default appearance (more transparent than waypoint nodes)
        self._normal_pen = QPen(QColor("#888888"), 1)
        self._normal_brush = QBrush(QColor("#CCCCCC80"))  # 50% alpha
        self._hover_pen = QPen(QColor("#444444"), 1)  
        self._hover_brush = QBrush(QColor("#FFFFFF80"))   # 50% alpha
        self._drag_pen = QPen(QColor("#FF8C00"), 2)
        self._drag_brush = QBrush(QColor("#FF8C00"))
        
        self.setPen(self._normal_pen)
        self.setBrush(self._normal_brush)
        
        # Enable hover events
        self.setAcceptHoverEvents(True)
    
    def hoverEnterEvent(self, event):
        if not self.is_dragging:
            self.setPen(self._hover_pen)
            self.setBrush(self._hover_brush)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        if not self.is_dragging:
            self.setPen(self._normal_pen)
            self.setBrush(self._normal_brush)
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.setPen(self._drag_pen)
            self.setBrush(self._drag_brush)
            
            # Create a ghost waypoint for tracking drag position
            # Use scenePos() for consistency with coordinate fix
            current_pos = self.scenePos()
            self.ghost_waypoint = InteractiveWaypoint((current_pos.x(), current_pos.y()), is_user_created=True)
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.is_dragging:

            self.has_been_dragged = True
            
            # COORDINATE FIX: Use event.scenePos() instead of self.pos() to avoid Qt coordinate corruption
            scene_pos = event.scenePos()
            
            # Update both Qt graphics position and ghost waypoint position
            self.setPos(scene_pos.x(), scene_pos.y())
            if self.ghost_waypoint:
                self.ghost_waypoint.move_to((scene_pos.x(), scene_pos.y()))
            
            # Update line geometry preview with ghost waypoint
            self.node_manager.update_line_preview_with_ghost(self.segment_index, self.ghost_waypoint)
        
        # Do NOT call super().mouseMoveEvent(event) to prevent Qt's default ItemIsMovable behavior
    
    def mouseReleaseEvent(self, event):

        self.node_manager._scene = self.scene()
        if event.button() == Qt.LeftButton and self.is_dragging:
            self.is_dragging = False
            
            if self.has_been_dragged and self.ghost_waypoint:
                # Commit the ghost waypoint as a real waypoint
                final_pos = self.ghost_waypoint.position
                
                # Split the segment at the final position
                self.node_manager.split_segment_at_midpoint(self.segment_index, final_pos)
                # Note: This will destroy this MidpointNode and create new nodes including the waypoint
            else:
                # Not dragged, just restore appearance
                self.setPen(self._hover_pen)
                self.setBrush(self._hover_brush)
                
            # Clean up ghost waypoint
            self.ghost_waypoint = None

        super().mouseReleaseEvent(event)

    def set_selection_color(self, color: QColor):
        """Update colors based on current theme"""
        self._drag_pen = QPen(color, 2)
        self._drag_brush = QBrush(color)


class LineNodeManager(QObject):
    """Manages interactive nodes for a line (waypoints and midpoints)"""
    
    waypoint_moved = Signal(InteractiveWaypoint)
    waypoint_added = Signal(InteractiveWaypoint, int)  # waypoint, segment_index
    waypoint_removed = Signal(InteractiveWaypoint)
    geometry_update_requested = Signal()
    
    def __init__(self, arrow: "MultiSegmentArrow", selection_color: QColor, parent=None, scene=None):
        super().__init__(parent)
        
        self._scene = scene
        self.arrow = arrow
        self.selection_color = selection_color
        self.waypoint_nodes: List[WaypointNode] = []
        self.midpoint_nodes: List[MidpointNode] = []
        self.is_visible = False
        
        # Merge detection settings
        self.merge_angle_threshold = 5.0  # degrees
        self.merge_distance_threshold = 10.0  # pixels
        
    def scene(self):
        return self._scene

    def create_nodes(self, waypoints: List[InteractiveWaypoint]):
        """Create all waypoint and midpoint nodes"""
        # Validate waypoints before creating nodes
        self._validate_waypoints(waypoints)
        
        self.clear_nodes()
        
        # Create waypoint nodes
        for waypoint in waypoints:
            # Additional validation per waypoint
            if self._is_valid_waypoint(waypoint):
                node = WaypointNode(waypoint, self)
                node.set_selection_color(self.selection_color)
                self.waypoint_nodes.append(node)
            else:
                logger.warning(f"Warning: Skipping invalid waypoint {waypoint.node_id} at ({waypoint.x}, {waypoint.y})")
        
        # Create midpoint nodes between segments
        self._create_midpoint_nodes(waypoints)
        
        # Add nodes to scene if one exists (check if we can find a scene from existing items)
        self._add_nodes_to_scene()
        
        # Final validation
        self._validate_created_nodes()
        
        self.is_visible = True
    
    def _add_nodes_to_scene(self):
        """Add nodes to scene if a scene can be found from arrow graphics items"""
        if not (self.waypoint_nodes or self.midpoint_nodes):
            return
        
        # Try to find a scene from the arrow's graphics items
        scene = None
        
        # Check if arrow has line items with scene
        if hasattr(self.arrow, 'lineItems') and self.arrow.lineItems:
            scene = self.arrow.lineItems[0].scene()
        elif hasattr(self.arrow, 'lineItem'):
            scene = self.arrow.lineItem.scene()
            
        if scene:
            for node in self.waypoint_nodes + self.midpoint_nodes:
                if node not in scene.items():
                    scene.addItem(node)
    
    def _create_midpoint_nodes(self, waypoints: List[InteractiveWaypoint]):
        """Create midpoint nodes for each segment"""
        # Get the full path including entity edge points
        path_points = self.arrow.get_current_path_points()
        
        # Validate path points before creating midpoint nodes
        if not path_points or len(path_points) < 2:
            logger.warning(f"Warning: Invalid path points for midpoint creation: {path_points}")
            return
        
        # Create midpoint nodes for each segment (even with 0 waypoints, we have 1 segment)
        for i in range(len(path_points) - 1):
            start_point = path_points[i]
            end_point = path_points[i + 1]
            
            # Validate individual points
            if not (start_point and end_point and 
                    len(start_point) == 2 and len(end_point) == 2):
                logger.warning(f"Warning: Invalid segment points {i}: start={start_point}, end={end_point}")
                continue
                
            # Calculate midpoint
            midpoint = (
                (start_point[0] + end_point[0]) / 2,
                (start_point[1] + end_point[1]) / 2
            )
            
            # Validate calculated midpoint
            if math.isnan(midpoint[0]) or math.isnan(midpoint[1]) or (midpoint[0] == 0 and midpoint[1] == 0):
                logger.warning(f"Warning: Suspicious midpoint calculated for segment {i}: {midpoint} from {start_point} to {end_point}")
                # Use a safe fallback position slightly offset from start point
                midpoint = (start_point[0] + 1, start_point[1] + 1)
            
            # Create midpoint node
            node = MidpointNode(midpoint, i, self)
            node.set_selection_color(self.selection_color)
            self.midpoint_nodes.append(node)
    
    def show_nodes(self):
        """Make all nodes visible"""
        for node in self.waypoint_nodes + self.midpoint_nodes:
            node.setVisible(True)
        self.is_visible = True
    
    def hide_nodes(self):
        """Hide all nodes"""
        for node in self.waypoint_nodes + self.midpoint_nodes:
            node.setVisible(False)
        self.is_visible = False
    
    def clear_nodes(self):
        """Remove all nodes from scene and clear lists"""
        for node in self.waypoint_nodes + self.midpoint_nodes:
            if node.scene():
                node.scene().removeItem(node)
        
        self.waypoint_nodes.clear()
        self.midpoint_nodes.clear()
        self.is_visible = False
    
    def get_graphics_items(self) -> List[QGraphicsItem]:
        """Get all node graphics items for adding to scene"""
        return self.waypoint_nodes + self.midpoint_nodes
    
    def update_midpoint_positions(self):
        """Update midpoint node positions based on current line geometry"""
        if not self.is_visible:
            return
            
        path_points = self.arrow.get_current_path_points()
        
        # Update existing midpoint nodes
        for i, node in enumerate(self.midpoint_nodes):
            if i < len(path_points) - 1:
                start_point = path_points[i]
                end_point = path_points[i + 1]
                
                midpoint = (
                    (start_point[0] + end_point[0]) / 2,
                    (start_point[1] + end_point[1]) / 2
                )
                
                node.setPos(midpoint[0], midpoint[1])
                node.midpoint = midpoint
    
    def on_waypoint_moved(self, waypoint: InteractiveWaypoint):
        """Handle waypoint movement during drag"""
        self.waypoint_moved.emit(waypoint)
        self.geometry_update_requested.emit()
        # Update midpoint positions in real-time
        self.update_midpoint_positions()
    
    def on_waypoint_drag_finished(self, waypoint: InteractiveWaypoint):
        """Handle end of waypoint drag - create undo command and check for merges"""
        # Create undo command for waypoint movement
        self._create_waypoint_move_command(waypoint)
        
        self.check_for_merges()
        self.geometry_update_requested.emit()
        
    def _create_waypoint_move_command(self, moved_waypoint: InteractiveWaypoint):
        """Create and execute a LineManipulationCommand for waypoint movement"""
        try:
            # Get the scene through the arrow's parent line group
            line_group = getattr(self.arrow, '_parent_line_group', None)
            if not line_group or not hasattr(line_group, 'srcEntity'):
                print("Warning: Could not get line group for undo command")
                return
                
            scene = self.scene()
            if not scene:
                print("Warning: Could not find scene for undo command")
                return
                
            # We need to store the old state before movement, but since this is called after movement,
            # we'll implement a more comprehensive tracking system later
            # For now, just ensure the waypoint state is applied
            current_waypoints = list(self.arrow.interactive_waypoints)
            
            # Create the command with current state (this is a simplified version)
            # UNDO ISSUES
            """
            from workflow_designer.wfd_undo_system import CommandFactory
            command = CommandFactory.createLineManipulationCommand(
                scene, line_group, "move_waypoint", current_waypoints, current_waypoints
            )
            
            # Note: For proper implementation, we need to track the before/after states
            # This will be enhanced in the next phase
            print(f"Created waypoint move command for {moved_waypoint.node_id}")
            """
        except Exception as e:
            logger.error(f"Error creating waypoint move command: {e}")
            traceback.print_exc()

    
    def split_segment_at_midpoint(self, segment_index: int, position: Tuple[float, float]):
        """Split a segment by creating new waypoint at midpoint using undo system"""

        self._fallback_split_segment(segment_index, position)
        return

        # UNDO ISSUES

        try:
            # Get the scene and line group for undo command
            line_group = getattr(self.arrow, '_parent_line_group', None)
            if not line_group:
                print("Warning: Could not get line group for segment split")
                self._fallback_split_segment(segment_index, position)
                return
                
            scene = self.scene() #self._get_scene_from_line_group(line_group)
            if not scene:
                print("Warning: Could not find scene for segment split")
                self._fallback_split_segment(segment_index, position)
                return
                
            # Capture current waypoint state before split
            old_waypoints = list(self.arrow.interactive_waypoints)
            
            # Create and execute the split command
            from workflow_designer.wfd_undo_system import CommandFactory
            split_command = CommandFactory.createSegmentSplitCommand(
                scene, line_group, segment_index, position, old_waypoints
            )
            
            # Execute the command through the undo stack
            if hasattr(scene, 'undo_stack'):
                scene.undo_stack.push(split_command)
                print(f"Executed segment split command via undo stack")
            else:
                # Fallback to direct execution
                split_command.redo()
                print(f"Executed segment split command directly")
                
            # Recreate nodes to reflect the new waypoint structure
            self._recreate_nodes_after_split()
            
        except Exception as e:
            print(f"Error in segment split: {e}")
            import traceback
            traceback.print_exc()
            # Fall back to old method
            self._fallback_split_segment(segment_index, position)
            
    def _get_scene_from_line_group(self, line_group):
        """Helper to get scene reference from line group"""
        if hasattr(line_group.srcEntity, '_selection_manager'):
            selection_manager = line_group.srcEntity._selection_manager
            # Try to find the scene that contains this selection manager
            for attr_name in dir(selection_manager):
                if attr_name.startswith('_'):
                    continue
                try:
                    attr = getattr(selection_manager, attr_name)
                    if hasattr(attr, 'lines') and line_group in attr.lines:
                        return attr
                except:
                    continue
        return None
        
    def _recreate_nodes_after_split(self):
        """Recreate nodes after a split operation"""
        try:
            # Get current waypoints from arrow
            current_waypoints = self.arrow.get_interactive_waypoints()
            
            # Recreate all nodes with new waypoint structure
            self.create_nodes(current_waypoints)
            
            logger.debug(f"Recreated nodes after split: {len(current_waypoints)} waypoints")
            
        except Exception as e:
            logger.error(f"Error recreating nodes after split: {e}")
            
    def _fallback_split_segment(self, segment_index: int, position: Tuple[float, float]):
        """Fallback segment split method (original implementation)"""
        # Store current node positions before recreation to prevent (0,0) issues
        current_node_positions = {}
        current_midpoint_positions = {}
        
        # Save positions of existing waypoint nodes
        for node in self.waypoint_nodes:
            if node.waypoint and node.waypoint.node_id:
                current_node_positions[node.waypoint.node_id] = (node.pos().x(), node.pos().y())
        
        # Save positions of existing midpoint nodes (except the one being converted)
        for i, node in enumerate(self.midpoint_nodes):
            if i != segment_index:  # Don't save the midpoint that's being converted to waypoint
                current_midpoint_positions[i] = (node.pos().x(), node.pos().y())
        
        # Create new waypoint
        new_waypoint = InteractiveWaypoint(position, is_user_created=True)
        
        # Notify arrow to add waypoint
        self.waypoint_added.emit(new_waypoint, segment_index)
        
        # Important: Ensure geometry is updated before recreating nodes
        self.arrow.updateGeometry()
        
        # Brief pause to ensure all geometry updates are complete
        # This prevents timing issues with coordinate calculations
        QApplication.processEvents()  # Process any pending updates
        
        # Recreate all nodes with new waypoint
        waypoints = self.arrow.get_interactive_waypoints()
        self.create_nodes(waypoints)
        # Note: create_nodes() already calls _add_nodes_to_scene() internally
        
        # Restore positions for nodes that weren't removed
        logger.debug(f"Split complete: restoring {len(current_node_positions)} waypoint positions and {len(current_midpoint_positions)} midpoint positions")
        self._restore_node_positions(current_node_positions)
        
        # Restore positions for remaining midpoint nodes with adjusted indices
        self._restore_midpoint_positions(current_midpoint_positions, segment_index)
        
        return new_waypoint
    
    def update_line_preview_with_ghost(self, segment_index: int, ghost_waypoint: InteractiveWaypoint):
        """Update line geometry preview during ghost dragging"""
        if not ghost_waypoint:
            return
            
        # Create a temporary waypoint list with the ghost waypoint inserted
        original_waypoints = self.arrow.get_interactive_waypoints().copy()
        temp_waypoints = original_waypoints.copy()
        
        # DEBUG: Log ghost dragging operation
        logger.debug(f"Ghost dragging: segment_index={segment_index}, "
                    f"original_waypoints={len(original_waypoints)}, "
                    f"ghost_pos=({ghost_waypoint.x:.1f},{ghost_waypoint.y:.1f})")
        
        # Convert segment_index (from path points) to waypoint insertion index
        # Path structure: [startPoint, waypoint0, waypoint1, ..., waypointN, endPoint]
        # Segment 0: startPoint → waypoint0 (insert before waypoint0, index=0)
        # Segment 1: waypoint0 → waypoint1 (insert before waypoint1, index=1)  
        # Segment N: waypointN → endPoint (insert after waypointN, index=N+1)
        
        if segment_index == 0:
            # Splitting first segment (start → first waypoint or start → end)
            temp_waypoints.insert(0, ghost_waypoint)
            logger.debug(f"  Inserting ghost at index 0 (first segment)")
        elif segment_index >= len(temp_waypoints) + 1:
            # Splitting last segment (last waypoint → end)
            temp_waypoints.append(ghost_waypoint)
            logger.debug(f"  Appending ghost (last segment)")
        else:
            # Splitting middle segment (waypoint[i-1] → waypoint[i])
            temp_waypoints.insert(segment_index, ghost_waypoint)
            logger.debug(f"  Inserting ghost at index {segment_index} (middle segment)")
        
        logger.debug(f"  Result: temp_waypoints={len(temp_waypoints)} (was {len(original_waypoints)})")
        
        # Update line geometry with temporary waypoint list (preview only)
        self.arrow.update_geometry_with_temp_waypoints(temp_waypoints)
    
    def check_for_merges(self):
        """Check if any three consecutive points form a straight line and merge if so"""
        waypoints = self.arrow.get_interactive_waypoints()
        if len(waypoints) < 1:
            return
            
        path_points = self.arrow.get_current_path_points()
        if len(path_points) < 3:
            return
        
        # First check for complete line straightness (more aggressive merging)
        if self._is_entire_line_straight(path_points):
            # If the entire line is straight, remove ALL waypoints (including XML ones)
            self._remove_all_waypoints(waypoints)
            return
            
        # Otherwise, check each triplet of consecutive points (standard merging)
        points_to_remove = []
        
        for i in range(1, len(path_points) - 1):
            prev_point = path_points[i - 1]
            current_point = path_points[i]
            next_point = path_points[i + 1]
            
            if self._should_merge_points(prev_point, current_point, next_point):
                # Find corresponding waypoint to remove using improved matching
                waypoint_to_remove = self._find_waypoint_by_position(waypoints, current_point)
                if waypoint_to_remove:
                    # Allow merging of both user-created AND XML waypoints when they're straightened
                    # This enables XML-loaded lines to be simplified when manually straightened
                    points_to_remove.append(waypoint_to_remove)
                    logger.debug(f"Merging waypoint {waypoint_to_remove.node_id[:8]}... (user_created: {waypoint_to_remove.is_user_created})")
        
        # Remove waypoints and recreate nodes
        for waypoint in points_to_remove:
            self.waypoint_removed.emit(waypoint)
        
        if points_to_remove:
            # Store current node positions before recreation to prevent (0,0) issues
            current_node_positions = {}
            for node in self.waypoint_nodes:
                if node.waypoint and node.waypoint.node_id:
                    current_node_positions[node.waypoint.node_id] = (node.pos().x(), node.pos().y())
            
            # Recreate nodes after removal
            remaining_waypoints = self.arrow.get_interactive_waypoints()
            logger.debug(f"Recreating nodes after merge check: {len(remaining_waypoints)} waypoints")
            for i, wp in enumerate(remaining_waypoints):
                logger.debug(f"  Waypoint {i}: {wp.node_id} at ({wp.x:.1f}, {wp.y:.1f})")
            
            self.create_nodes(remaining_waypoints)
            
            # Restore positions for nodes that weren't removed
            self._restore_node_positions(current_node_positions)
    
    def _restore_node_positions(self, saved_positions: dict):
        """Restore node positions from saved positions to prevent (0,0) corruption"""
        logger.debug(f"_restore_node_positions: {len(saved_positions)} saved positions, {len(self.waypoint_nodes)} current nodes")
        for node in self.waypoint_nodes:
            if node.waypoint and node.waypoint.node_id in saved_positions:
                saved_pos = saved_positions[node.waypoint.node_id]
                current_pos = (node.pos().x(), node.pos().y())
                logger.debug(f"  Node {node.waypoint.node_id}: current=({current_pos[0]:.1f}, {current_pos[1]:.1f}), saved={saved_pos}")
                
                # Validate the saved position before applying
                if saved_pos and len(saved_pos) == 2:
                    x, y = saved_pos
                    if not (math.isnan(x) or math.isnan(y) or (x == 0 and y == 0)):
                        node.setPos(x, y)
                        node.waypoint.move_to(saved_pos)
                        logger.debug(f"    Restored position for waypoint {node.waypoint.node_id}: {saved_pos}")
                        
                        # DEBUG: Log coordinate state after restoration
                        #node._log_coordinate_state("POSITION_RESTORED")
                    else:
                        logger.warning(f"    Warning: Invalid saved position for waypoint {node.waypoint.node_id}: {saved_pos}")
                else:
                    logger.warning(f"    Warning: Invalid saved position format for waypoint {node.waypoint.node_id}: {saved_pos}")
            else:
                current_pos = (node.pos().x(), node.pos().y())
                logger.debug(f"  Node {node.waypoint.node_id}: current=({current_pos[0]:.1f}, {current_pos[1]:.1f}), no saved position")
    
    def _restore_midpoint_positions(self, saved_midpoint_positions: dict, split_segment_index: int):
        """Restore midpoint node positions after segment splitting with index adjustment"""
        for old_index, saved_pos in saved_midpoint_positions.items():
            # Calculate new index after segment split
            # When we split segment at index N, all segments at index >= N shift by +1
            if old_index < split_segment_index:
                new_index = old_index  # Segments before split point don't change index
            else:
                new_index = old_index + 1  # Segments after split point shift by +1
            
            # Apply saved position if the new index is valid
            if new_index < len(self.midpoint_nodes):
                node = self.midpoint_nodes[new_index]
                if saved_pos and len(saved_pos) == 2:
                    x, y = saved_pos
                    if not (math.isnan(x) or math.isnan(y) or (x == 0 and y == 0)):
                        node.setPos(x, y)
                        node.midpoint = saved_pos
                        logger.debug(f"Restored midpoint {old_index}→{new_index} position: {saved_pos}")
                    else:
                        logger.warning(f"Warning: Invalid saved midpoint position {old_index}→{new_index}: {saved_pos}")
    
    def _find_waypoint_by_position(self, waypoints: List[InteractiveWaypoint], target_position: Tuple[float, float]) -> Optional[InteractiveWaypoint]:
        """Find waypoint that matches the target position with improved tolerance and validation"""
        if not target_position or len(target_position) != 2:
            return None
            
        target_x, target_y = target_position
        best_match = None
        min_distance = float('inf')
        
        for waypoint in waypoints:
            try:
                # Calculate distance to waypoint
                distance = waypoint.distance_to(target_position)
                
                # Use a reasonable tolerance (5 pixels) and find the closest match
                if distance < 5.0 and distance < min_distance:
                    min_distance = distance
                    best_match = waypoint
                    
            except Exception as e:
                logger.warning(f"Warning: Error calculating distance for waypoint {waypoint.node_id}: {e}")
                continue
        
        return best_match
    
    def _is_entire_line_straight(self, path_points: List[Tuple[float, float]]) -> bool:
        """Check if the entire line path is straight enough to remove all waypoints"""
        if len(path_points) < 3:
            return False
            
        # Check if all intermediate points lie on the line from start to end
        start_point = path_points[0]
        end_point = path_points[-1]
        
        # Use a more lenient threshold for complete line merging
        distance_threshold = 15.0  # pixels
        
        for i in range(1, len(path_points) - 1):
            intermediate_point = path_points[i]
            distance = self._point_to_line_distance(intermediate_point, start_point, end_point)
            
            if distance >= distance_threshold:
                return False  # Found a point that's too far from the straight line
                
        # All intermediate points are close enough to the straight line
        return True
    
    def _remove_all_waypoints(self, waypoints: List[InteractiveWaypoint]):
        """Remove all waypoints to create a direct line (used when entire line is straight)"""
        logger.debug(f"Removing all {len(waypoints)} waypoints - line is completely straight")
        
        # Store current positions before removal for debugging
        for waypoint in waypoints:
            logger.debug(f"  Removing waypoint {waypoint.node_id} at ({waypoint.x}, {waypoint.y}), is_user_created: {waypoint.is_user_created}")
        
        # Remove all waypoints (including XML ones)
        for waypoint in waypoints:
            self.waypoint_removed.emit(waypoint)
        
        # Recreate nodes with empty waypoint list (direct line)
        self.create_nodes([])
    
    def _validate_waypoints(self, waypoints: List[InteractiveWaypoint]):
        """Validate waypoint list for common issues"""
        logger.debug(f"Validating {len(waypoints)} waypoints...")
        
        for i, waypoint in enumerate(waypoints):
            if not self._is_valid_waypoint(waypoint):
                logger.warning(f"  Issue with waypoint {i}: {waypoint.node_id} at ({waypoint.x}, {waypoint.y})")
    
    def _is_valid_waypoint(self, waypoint: InteractiveWaypoint) -> bool:
        """Check if a waypoint has valid coordinates and data"""
        if not waypoint:
            return False
            
        try:
            x, y = waypoint.x, waypoint.y
            
            # Check for invalid coordinates
            if math.isnan(x) or math.isnan(y):
                return False
                
            # Check for extreme values
            if abs(x) > 100000 or abs(y) > 100000:
                return False
                
            # Check for missing node ID
            if not waypoint.node_id:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating waypoint: {e}")
            return False
    
    def _validate_created_nodes(self):
        """Validate that created nodes have reasonable positions"""
        suspicious_nodes = []
        
        for node in self.waypoint_nodes:
            pos = node.pos()
            if math.isnan(pos.x()) or math.isnan(pos.y()) or (pos.x() == 0 and pos.y() == 0):
                suspicious_nodes.append(node)
                
        if suspicious_nodes:
            logger.warning(f"Warning: Found {len(suspicious_nodes)} nodes with suspicious positions:")
            for node in suspicious_nodes:
                pos = node.pos()
                logger.warning(f"  Node {node.waypoint.node_id} at ({pos.x()}, {pos.y()})")
    
    def _should_merge_points(self, p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float]) -> bool:
        """Determine if three points are straight enough to merge"""
        # Method 1: Angle-based detection
        angle_straight = self._calculate_angle_straightness(p1, p2, p3)
        
        # Method 2: Distance-based detection  
        distance_straight = self._calculate_distance_straightness(p1, p2, p3)
        
        return angle_straight or distance_straight
    
    def _calculate_angle_straightness(self, p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float]) -> bool:
        """Check straightness using angle between vectors"""
        # Calculate vectors
        v1 = (p2[0] - p1[0], p2[1] - p1[1])
        v2 = (p3[0] - p2[0], p3[1] - p2[1])
        
        # Calculate magnitudes
        mag1 = math.sqrt(v1[0] * v1[0] + v1[1] * v1[1])
        mag2 = math.sqrt(v2[0] * v2[0] + v2[1] * v2[1])
        
        if mag1 == 0 or mag2 == 0:
            return True  # Zero-length vectors, merge
        
        # Calculate dot product and angle
        dot_product = v1[0] * v2[0] + v1[1] * v2[1]
        cos_angle = dot_product / (mag1 * mag2)
        
        # Clamp to valid range for acos
        cos_angle = max(-1.0, min(1.0, cos_angle))
        
        angle_radians = math.acos(cos_angle)
        angle_degrees = math.degrees(angle_radians)
        
        # For a straight line, vectors should point in same direction (0° angle)
        # or we can check if the angle is very small (close to 0°)
        return angle_degrees < self.merge_angle_threshold
    
    def _calculate_distance_straightness(self, p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float]) -> bool:
        """Check straightness using distance from point to line"""
        # Calculate distance from p2 to line p1-p3
        distance = self._point_to_line_distance(p2, p1, p3)
        return distance < self.merge_distance_threshold
    
    def _point_to_line_distance(self, point: Tuple[float, float], line_start: Tuple[float, float], line_end: Tuple[float, float]) -> float:
        """Calculate perpendicular distance from point to line"""
        px, py = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        # Line length squared
        line_length_sq = (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1)
        
        if line_length_sq == 0:
            # Line is actually a point
            return math.sqrt((px - x1) * (px - x1) + (py - y1) * (py - y1))
        
        # Calculate the projection parameter
        t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq
        t = max(0, min(1, t))  # Clamp to line segment
        
        # Find the projection point
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        
        # Calculate distance
        return math.sqrt((px - proj_x) * (px - proj_x) + (py - proj_y) * (py - proj_y))
    
    def update_selection_color(self, color: QColor):
        """Update all node colors when theme changes"""
        self.selection_color = color
        for node in self.waypoint_nodes + self.midpoint_nodes:
            node.set_selection_color(color)
