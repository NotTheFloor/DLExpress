import math
import uuid
from typing import List, Tuple, Optional, TYPE_CHECKING
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, Qt, QPointF
from PySide6.QtGui import QPen, QBrush, QColor
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsItem

if TYPE_CHECKING:
    from workflow_designer.wfd_utilities import MultiSegmentArrow

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
        self.position = new_position
    
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
        
        # Set position
        self.setPos(waypoint.x, waypoint.y)
        
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
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            # Update waypoint position
            new_pos = self.pos()
            self.waypoint.move_to((new_pos.x(), new_pos.y()))
            # Notify manager to update line geometry
            self.node_manager.on_waypoint_moved(self.waypoint)
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.setPen(self._hover_pen)
            self.setBrush(self._hover_brush)
            # Final update and check for merges
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
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.is_dragging and not self.has_been_dragged:
            # Only split segment on first move, not continuously during drag
            self.has_been_dragged = True
            new_pos = self.pos()
            self.node_manager.split_segment_at_midpoint(self.segment_index, (new_pos.x(), new_pos.y()))
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_dragging:
            self.is_dragging = False
            # Split has already happened on first move if dragged
            # If not dragged, just restore appearance
            if not self.has_been_dragged:
                self.setPen(self._hover_pen)
                self.setBrush(self._hover_brush)
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
    
    def __init__(self, arrow: "MultiSegmentArrow", selection_color: QColor, parent=None):
        super().__init__(parent)
        
        self.arrow = arrow
        self.selection_color = selection_color
        self.waypoint_nodes: List[WaypointNode] = []
        self.midpoint_nodes: List[MidpointNode] = []
        self.is_visible = False
        
        # Merge detection settings
        self.merge_angle_threshold = 5.0  # degrees
        self.merge_distance_threshold = 10.0  # pixels
        
    def create_nodes(self, waypoints: List[InteractiveWaypoint]):
        """Create all waypoint and midpoint nodes"""
        self.clear_nodes()
        
        # Create waypoint nodes
        for waypoint in waypoints:
            node = WaypointNode(waypoint, self)
            node.set_selection_color(self.selection_color)
            self.waypoint_nodes.append(node)
        
        # Create midpoint nodes between segments
        self._create_midpoint_nodes(waypoints)
        
        # Add nodes to scene if one exists (check if we can find a scene from existing items)
        self._add_nodes_to_scene()
        
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
        
        # Create midpoint nodes for each segment (even with 0 waypoints, we have 1 segment)
        for i in range(len(path_points) - 1):
            start_point = path_points[i]
            end_point = path_points[i + 1]
            
            # Calculate midpoint
            midpoint = (
                (start_point[0] + end_point[0]) / 2,
                (start_point[1] + end_point[1]) / 2
            )
            
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
        """Handle end of waypoint drag - check for merges"""
        self.check_for_merges()
        self.geometry_update_requested.emit()
    
    def split_segment_at_midpoint(self, segment_index: int, position: Tuple[float, float]):
        """Split a segment by creating new waypoint at midpoint"""
        # Create new waypoint
        new_waypoint = InteractiveWaypoint(position, is_user_created=True)
        
        # Notify arrow to add waypoint
        self.waypoint_added.emit(new_waypoint, segment_index)
        
        # Recreate all nodes with new waypoint
        waypoints = self.arrow.get_interactive_waypoints()
        self.create_nodes(waypoints)
        # Note: create_nodes() already calls _add_nodes_to_scene() internally
    
    def check_for_merges(self):
        """Check if any three consecutive points form a straight line and merge if so"""
        waypoints = self.arrow.get_interactive_waypoints()
        if len(waypoints) < 2:
            return
            
        path_points = self.arrow.get_current_path_points()
        if len(path_points) < 3:
            return
            
        # Check each triplet of consecutive points
        points_to_remove = []
        
        for i in range(1, len(path_points) - 1):
            prev_point = path_points[i - 1]
            current_point = path_points[i]
            next_point = path_points[i + 1]
            
            if self._should_merge_points(prev_point, current_point, next_point):
                # Find corresponding waypoint to remove
                for waypoint in waypoints:
                    if abs(waypoint.x - current_point[0]) < 1.0 and abs(waypoint.y - current_point[1]) < 1.0:
                        if waypoint.is_user_created:  # Only remove user-created waypoints
                            points_to_remove.append(waypoint)
                        break
        
        # Remove waypoints and recreate nodes
        for waypoint in points_to_remove:
            self.waypoint_removed.emit(waypoint)
        
        if points_to_remove:
            # Recreate nodes after removal
            remaining_waypoints = self.arrow.get_interactive_waypoints()
            self.create_nodes(remaining_waypoints)
    
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