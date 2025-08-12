import math
from typing import Tuple, TYPE_CHECKING, Optional, List

from PySide6.QtCore import QPoint, QPointF, Qt, QObject, Signal
from PySide6.QtGui import QPainter, QPolygon, QPolygonF, QBrush, QPen, QColor
from PySide6.QtWidgets import QGraphicsItem, QGraphicsLineItem, QGraphicsPolygonItem

if TYPE_CHECKING:
    from workflow_designer.wfd_scene import WFEntity
    from workflow_designer.wfd_interactive_nodes import LineNodeManager, InteractiveWaypoint

# Geometric calculation functions for arrow edge intersections
def findCircleEdgeIntersection(centerX: float, centerY: float, radiusX: float, radiusY: float, 
                               lineStartX: float, lineStartY: float, lineEndX: float, lineEndY: float) -> Tuple[float, float]:
    """
    Find where a line from lineStart to lineEnd intersects the edge of an ellipse.
    Returns the intersection point on the ellipse edge closest to lineEnd.
    """
    # Direction vector from line start to end
    dx = lineEndX - lineStartX
    dy = lineEndY - lineStartY
    
    # Normalize direction
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return centerX, centerY
    
    dx /= length
    dy /= length
    
    # For ellipse: (x-cx)²/rx² + (y-cy)²/ry² = 1
    # Parametric line: x = cx + t*dx, y = cy + t*dy
    # Solve for t where line intersects ellipse
    
    # Ellipse equation coefficients
    a = (dx * dx) / (radiusX * radiusX) + (dy * dy) / (radiusY * radiusY)
    b = 2 * dx * (lineStartX - centerX) / (radiusX * radiusX) + 2 * dy * (lineStartY - centerY) / (radiusY * radiusY)
    c = ((lineStartX - centerX) * (lineStartX - centerX)) / (radiusX * radiusX) + ((lineStartY - centerY) * (lineStartY - centerY)) / (radiusY * radiusY) - 1
    
    # Quadratic formula
    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return centerX, centerY  # No intersection, return center
    
    sqrt_discriminant = math.sqrt(discriminant)
    t1 = (-b + sqrt_discriminant) / (2 * a)
    t2 = (-b - sqrt_discriminant) / (2 * a)
    
    # Choose the intersection point that's in the direction we want
    t = t1 if t1 > 0 else t2
    
    intersectX = lineStartX + t * dx
    intersectY = lineStartY + t * dy
    
    return intersectX, intersectY


def findRectangleEdgeIntersection(rectLeft: float, rectTop: float, rectWidth: float, rectHeight: float,
                                  lineStartX: float, lineStartY: float, lineEndX: float, lineEndY: float) -> Tuple[float, float]:
    """
    Find where a line from lineStart to lineEnd intersects the edge of a rectangle.
    Returns the intersection point on the rectangle edge closest to lineEnd.
    """
    rectRight = rectLeft + rectWidth
    rectBottom = rectTop + rectHeight
    
    # Direction vector
    dx = lineEndX - lineStartX
    dy = lineEndY - lineStartY
    
    if dx == 0 and dy == 0:
        return lineStartX, lineStartY
    
    # Find intersections with all four edges and choose the closest valid one
    intersections = []
    
    # Left edge (x = rectLeft)
    if dx != 0:
        t = (rectLeft - lineStartX) / dx
        y = lineStartY + t * dy
        if 0 <= t <= 1 and rectTop <= y <= rectBottom:
            intersections.append((rectLeft, y, t))
    
    # Right edge (x = rectRight) 
    if dx != 0:
        t = (rectRight - lineStartX) / dx
        y = lineStartY + t * dy
        if 0 <= t <= 1 and rectTop <= y <= rectBottom:
            intersections.append((rectRight, y, t))
    
    # Top edge (y = rectTop)
    if dy != 0:
        t = (rectTop - lineStartY) / dy
        x = lineStartX + t * dx
        if 0 <= t <= 1 and rectLeft <= x <= rectRight:
            intersections.append((x, rectTop, t))
    
    # Bottom edge (y = rectBottom)
    if dy != 0:
        t = (rectBottom - lineStartY) / dy
        x = lineStartX + t * dx
        if 0 <= t <= 1 and rectLeft <= x <= rectRight:
            intersections.append((x, rectBottom, t))
    
    if not intersections:
        # No valid intersection found, return the closest rectangle corner
        centerX = rectLeft + rectWidth / 2
        centerY = rectTop + rectHeight / 2
        return centerX, centerY
    
    # Return the intersection with the largest t value (closest to lineEnd)
    intersections.sort(key=lambda x: x[2], reverse=True)
    return intersections[0][0], intersections[0][1]


def calculateLineEndpoints(srcEntity: "WFEntity", dstEntity: "WFEntity") -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    Calculate the actual start and end points for a line between two entities,
    taking into account their shapes (circle/ellipse vs rectangle).
    Uses current entity positions for dynamic updates.
    Returns (startPoint, endPoint) as ((x1, y1), (x2, y2))
    """
    from workflow_designer.wfd_scene import EntityType
    
    # Get current entity centers (dynamic positions)
    srcCenterX, srcCenterY = srcEntity.shape.getCurrentCenter()
    dstCenterX, dstCenterY = dstEntity.shape.getCurrentCenter()
    
    # Calculate start point (where line exits source entity)
    if srcEntity.entityType == EntityType.STATUS:  # Ellipse/Circle
        # Use original radii (shape doesn't change, only position)
        startX, startY = findCircleEdgeIntersection(
            srcCenterX, srcCenterY, 
            srcEntity.shape.rect.rx, srcEntity.shape.rect.ry,
            srcCenterX, srcCenterY, dstCenterX, dstCenterY
        )
    else:  # Rectangle (Workflow)
        # Use current bounds for rectangle
        srcLeft, srcTop, srcWidth, srcHeight = srcEntity.shape.getCurrentBounds()
        startX, startY = findRectangleEdgeIntersection(
            srcLeft, srcTop, srcWidth, srcHeight,
            srcCenterX, srcCenterY, dstCenterX, dstCenterY
        )
    
    # Calculate end point (where line enters destination entity)
    if dstEntity.entityType == EntityType.STATUS:  # Ellipse/Circle
        # Use original radii (shape doesn't change, only position)
        endX, endY = findCircleEdgeIntersection(
            dstCenterX, dstCenterY,
            dstEntity.shape.rect.rx, dstEntity.shape.rect.ry,
            dstCenterX, dstCenterY, srcCenterX, srcCenterY
        )
    else:  # Rectangle (Workflow)  
        # Use current bounds for rectangle
        dstLeft, dstTop, dstWidth, dstHeight = dstEntity.shape.getCurrentBounds()
        endX, endY = findRectangleEdgeIntersection(
            dstLeft, dstTop, dstWidth, dstHeight,
            dstCenterX, dstCenterY, srcCenterX, srcCenterY
        )
    
    return (startX, startY), (endX, endY)


# Inspired by https://forum.qt.io/topic/109749/how-to-create-an-arrow-in-qt/6
# Probably worth converting all to Q primitives (QPointF, QLineF, etc.)
def drawArrow(painter: QPainter, srcPoint: tuple, dstPoint: tuple, headSize: int = 5):
    dx = srcPoint[0] - dstPoint[0]
    dy = srcPoint[1] - dstPoint[1]

    angle = math.atan2(-dy, dx)

    arrowP1X = dstPoint[0] + math.sin(angle + (math.pi / 3)) * headSize
    arrowP1Y = dstPoint[1] + math.cos(angle + (math.pi / 3)) * headSize
    
    arrowP2X = dstPoint[0] + math.sin(angle + math.pi - (math.pi / 3)) * headSize
    arrowP2Y = dstPoint[1] + math.cos(angle + math.pi - (math.pi / 3)) * headSize

    painter.drawLine(
            srcPoint[0],
            srcPoint[1],
            dstPoint[0],
            dstPoint[1]
        )

    pointList = [
            QPoint(dstPoint[0], dstPoint[1]),
            QPoint(arrowP1X, arrowP1Y),
            QPoint(arrowP2X, arrowP2Y)
        ]
    painter.drawPolygon(pointList, Qt.OddEvenFill)
    
def addArrowToLineItem(graphicsItem: QGraphicsLineItem, headSize: int = 5):
    x1 = graphicsItem.line().x1()
    y1 = graphicsItem.line().y1()
    x2 = graphicsItem.line().x2()
    y2 = graphicsItem.line().y2()
    #dx = graphicsItem.line().dx.
    #dy = graphicsItem.line().dy
    dx = x2 - x1
    dy = y2 - y1

    angle = math.atan2(-dy, dx)

    arrowP1X = x2 + math.sin(angle + (math.pi / 6)) * headSize
    arrowP1Y = y2 + math.cos(angle + (math.pi / 6)) * headSize
    
    arrowP2X = x2 + math.sin(angle + math.pi - (math.pi / 6)) * headSize
    arrowP2Y = y2 + math.cos(angle + math.pi - (math.pi / 6)) * headSize

    pointList = [
            QPointF(x2, y2),
            QPointF(arrowP1X, arrowP1Y),
            QPointF(arrowP2X, arrowP2Y),
        ]
    
    polygon = QPolygonF(pointList)
    arrowItem = QGraphicsPolygonItem(polygon, graphicsItem)

    # Set same pen as line
    arrowItem.setPen(graphicsItem.pen())
    
    # Fill arrow with same color as pen
    arrowItem.setBrush(QBrush(graphicsItem.pen().color()))
    
    return arrowItem


class SmartArrow(QObject):
    """
    Dynamic arrow that maintains references to source and destination entities
    and updates automatically when they move.
    """
    
    clicked = Signal()
    
    def __init__(self, srcEntity: "WFEntity", dstEntity: "WFEntity", parent=None):
        super().__init__(parent)
        
        self.srcEntity = srcEntity
        self.dstEntity = dstEntity
        self.headSize = 8
        
        # Create the graphics items
        self.lineItem: QGraphicsLineItem = QGraphicsLineItem()
        self.arrowItem: QGraphicsPolygonItem = QGraphicsPolygonItem()
        
        # Set visual properties
        pen = QPen(Qt.black, 2)
        self.lineItem.setPen(pen)
        self.arrowItem.setPen(pen)
        self.arrowItem.setBrush(QBrush(Qt.black))
        
        # Selection support
        self._is_selected = False
        self._original_pen: QPen = pen
        self._selection_manager = None
        
        # Node management (SmartArrow doesn't use nodes, but needs the attribute for compatibility)
        self._node_manager: Optional['LineNodeManager'] = None
        
        # Make items selectable and setup click handling
        self._setupSelection()
        
        # Connect to entity movement signals
        self.connectToEntities()
        
        # Initial calculation
        self.updateGeometry()
    
    def connectToEntities(self):
        """Connect to entity movement signals for automatic updates"""
        if hasattr(self.srcEntity.shape, 'moved'):
            self.srcEntity.shape.moved.connect(self.updateGeometry)
        if hasattr(self.dstEntity.shape, 'moved'):  
            self.dstEntity.shape.moved.connect(self.updateGeometry)
    
    def updateGeometry(self):
        """Recalculate line and arrow positions based on current entity positions"""
        try:
            # Calculate proper edge intersection points
            startPoint, endPoint = calculateLineEndpoints(self.srcEntity, self.dstEntity)
            
            # Update line geometry
            self.lineItem.setLine(startPoint[0], startPoint[1], endPoint[0], endPoint[1])
            
            # Calculate arrow direction with consistent math
            dx = endPoint[0] - startPoint[0]
            dy = endPoint[1] - startPoint[1]
            
            if dx == 0 and dy == 0:
                return  # No arrow for zero-length line
                
            # Use consistent angle calculation (positive dy for correct direction)  
            angle = math.atan2(dy, dx)
            
            # Calculate arrow head points (30-degree wings)
            wingAngle = math.pi / 6  # 30 degrees
            
            arrowP1X = endPoint[0] - self.headSize * math.cos(angle - wingAngle)
            arrowP1Y = endPoint[1] - self.headSize * math.sin(angle - wingAngle)
            
            arrowP2X = endPoint[0] - self.headSize * math.cos(angle + wingAngle)  
            arrowP2Y = endPoint[1] - self.headSize * math.sin(angle + wingAngle)
            
            # Create arrow polygon
            pointList = [
                QPointF(endPoint[0], endPoint[1]),  # Arrow tip
                QPointF(arrowP1X, arrowP1Y),        # Wing 1
                QPointF(arrowP2X, arrowP2Y)         # Wing 2
            ]
            
            polygon = QPolygonF(pointList)
            self.arrowItem.setPolygon(polygon)
            
        except Exception as e:
            from workflow_designer.wfd_logger import logger
            logger.error(f"Error updating arrow geometry: {e}")
    
    def getGraphicsItems(self) -> Tuple[QGraphicsLineItem, QGraphicsPolygonItem]:
        """Return the graphics items for adding to scene"""
        return self.lineItem, self.arrowItem
    
    def setVisible(self, visible: bool):
        """Set visibility of both line and arrow"""
        self.lineItem.setVisible(visible)
        self.arrowItem.setVisible(visible)
    
    def setPen(self, pen):
        """Set pen for both line and arrow"""
        self.lineItem.setPen(pen)
        self.arrowItem.setPen(pen)
    
    def _setupSelection(self):
        """Setup click handling and selection for arrow items"""
        # Make items selectable
        self.lineItem.setFlag(QGraphicsItem.ItemIsSelectable)
        self.arrowItem.setFlag(QGraphicsItem.ItemIsSelectable)
        
        # Setup click handling for line
        original_line_press = self.lineItem.mousePressEvent
        def line_click_handler(event):
            if event.button() == Qt.LeftButton:
                self.clicked.emit()
                if self._selection_manager:
                    self._selection_manager.select_item(self)
            original_line_press(event)
        self.lineItem.mousePressEvent = line_click_handler
        
        # Setup click handling for arrow
        original_arrow_press = self.arrowItem.mousePressEvent
        def arrow_click_handler(event):
            if event.button() == Qt.LeftButton:
                self.clicked.emit()
                if self._selection_manager:
                    self._selection_manager.select_item(self)
            original_arrow_press(event)
        self.arrowItem.mousePressEvent = arrow_click_handler
    
    def set_selection_manager(self, selection_manager):
        """Set the selection manager for this arrow"""
        self._selection_manager = selection_manager
    
    def setSelected(self, selected: bool, selection_color: QColor):
        """Set selection state with visual feedback"""
        if self._is_selected == selected:
            return
            
        self._is_selected = selected
        
        if selected:
            # Apply selection color
            selection_pen = QPen(selection_color, 3)
            self.lineItem.setPen(selection_pen)
            self.arrowItem.setPen(selection_pen)
            self.arrowItem.setBrush(QBrush(selection_color))
        else:
            # Restore original appearance
            self.lineItem.setPen(self._original_pen)
            self.arrowItem.setPen(self._original_pen)
            self.arrowItem.setBrush(QBrush(self._original_pen.color()))
    
    def isSelected(self) -> bool:
        """Check if arrow is currently selected"""
        return self._is_selected
    
    # Node system compatibility methods (SmartArrow doesn't support nodes)
    def show_nodes(self):
        """SmartArrow doesn't support interactive nodes - no-op"""
        pass
    
    def hide_nodes(self):
        """SmartArrow doesn't support interactive nodes - no-op"""
        pass
    
    def get_node_graphics_items(self) -> List[QGraphicsItem]:
        """SmartArrow doesn't support interactive nodes - return empty list"""
        return []


class MultiSegmentArrow(QObject):
    """
    Dynamic arrow that handles multiple segments with waypoints.
    Only the first and last segments follow entity movement; middle segments remain fixed.
    Supports interactive waypoint management with node visualization.
    """
    
    clicked = Signal()
    
    def __init__(self, srcEntity: "WFEntity", dstEntity: "WFEntity", waypoints: list[Tuple[float, float]] = None, parent=None):
        super().__init__(parent)
        
        self.srcEntity = srcEntity
        self.dstEntity = dstEntity
        # Convert static waypoints to InteractiveWaypoint objects
        self.interactive_waypoints = self._convert_waypoints_to_interactive(waypoints or [])
        self.headSize = 8
        
        # Create line segments and arrowhead
        self.lineItems: list[QGraphicsLineItem] = []
        self.arrowItem: QGraphicsPolygonItem = QGraphicsPolygonItem()
        
        # Create line items for each segment
        self._createLineSegments()
        
        # Set visual properties for all items
        pen = QPen(Qt.black, 2)
        for lineItem in self.lineItems:
            lineItem.setPen(pen)
        self.arrowItem.setPen(pen)
        self.arrowItem.setBrush(QBrush(Qt.black))
        
        # Selection support
        self._is_selected = False
        self._original_pen: QPen = pen
        self._selection_manager = None
        
        # Node management for interactive waypoints
        self._node_manager: Optional['LineNodeManager'] = None
        
        # Setup selection for all segments
        self._setupSelection()
        
        # Connect to entity movement signals
        self.connectToEntities()
        
        # Initial calculation
        self.updateGeometry()
    
    def _convert_waypoints_to_interactive(self, waypoints: List[Tuple[float, float]]) -> List['InteractiveWaypoint']:
        """Convert static waypoint list to InteractiveWaypoint objects"""
        from workflow_designer.wfd_interactive_nodes import InteractiveWaypoint
        return [InteractiveWaypoint(pos, is_user_created=False) for pos in waypoints]
    
    def _createLineSegments(self):
        """Create QGraphicsLineItem objects for each segment of the path"""
        # Calculate total number of segments needed
        numSegments = len(self.interactive_waypoints) + 1  # Source to first waypoint, waypoints to waypoints, last waypoint to dest
        
        # Create line items for each segment
        for i in range(numSegments):
            lineItem = QGraphicsLineItem()
            self.lineItems.append(lineItem)
            # Setup selection for this line segment
            self._setupLineSelection(lineItem)
    
    def connectToEntities(self):
        """Connect to entity movement signals for automatic updates"""
        if hasattr(self.srcEntity.shape, 'moved'):
            self.srcEntity.shape.moved.connect(self.updateGeometry)
        if hasattr(self.dstEntity.shape, 'moved'):  
            self.dstEntity.shape.moved.connect(self.updateGeometry)
    
    def updateGeometry(self):
        """Recalculate line segments and arrow position based on current entity positions"""
        try:
            # Build complete path: source → waypoints → destination
            pathPoints = []
            
            # Get source entity edge point
            if not self.interactive_waypoints:
                # No waypoints - direct connection like SmartArrow
                startPoint, endPoint = calculateLineEndpoints(self.srcEntity, self.dstEntity)
                pathPoints = [startPoint, endPoint]
            else:
                # Calculate edge intersections to/from waypoints
                srcCenterX, srcCenterY = self.srcEntity.shape.getCurrentCenter()
                dstCenterX, dstCenterY = self.dstEntity.shape.getCurrentCenter()
                
                # First waypoint determines source edge intersection
                first_waypoint = self.interactive_waypoints[0]
                startPoint = self._calculateEntityEdgePoint(self.srcEntity, first_waypoint.x, first_waypoint.y)
                pathPoints.append(startPoint)
                
                # Add all waypoints
                for waypoint in self.interactive_waypoints:
                    pathPoints.append(waypoint.position)
                
                # Last waypoint determines destination edge intersection  
                last_waypoint = self.interactive_waypoints[-1]
                endPoint = self._calculateEntityEdgePoint(self.dstEntity, last_waypoint.x, last_waypoint.y)
                pathPoints.append(endPoint)
            
            # Update line segments
            for i, lineItem in enumerate(self.lineItems):
                if i < len(pathPoints) - 1:
                    startPt = pathPoints[i]
                    endPt = pathPoints[i + 1]
                    lineItem.setLine(startPt[0], startPt[1], endPt[0], endPt[1])
                    lineItem.setVisible(True)
                else:
                    lineItem.setVisible(False)  # Hide unused segments
            
            # Update arrow on the final segment
            if len(pathPoints) >= 2:
                self._updateArrowhead(pathPoints[-2], pathPoints[-1])
            
        except Exception as e:
            from workflow_designer.wfd_logger import logger
            logger.error(f"Error updating multi-segment arrow geometry: {e}")
    
    def _calculateEntityEdgePoint(self, entity: "WFEntity", targetX: float, targetY: float) -> Tuple[float, float]:
        """Calculate where a line from entity center to target point intersects the entity edge"""
        from workflow_designer.wfd_scene import EntityType
        
        centerX, centerY = entity.shape.getCurrentCenter()
        
        if entity.entityType == EntityType.STATUS:  # Ellipse/Circle
            return findCircleEdgeIntersection(
                centerX, centerY,
                entity.shape.rect.rx, entity.shape.rect.ry,
                centerX, centerY, targetX, targetY
            )
        else:  # Rectangle (Workflow)
            left, top, width, height = entity.shape.getCurrentBounds()
            return findRectangleEdgeIntersection(
                left, top, width, height,
                centerX, centerY, targetX, targetY
            )
    
    def _updateArrowhead(self, startPoint: Tuple[float, float], endPoint: Tuple[float, float]):
        """Update arrowhead based on final segment direction"""
        dx = endPoint[0] - startPoint[0]
        dy = endPoint[1] - startPoint[1]
        
        if dx == 0 and dy == 0:
            self.arrowItem.setVisible(False)
            return
        
        # Calculate arrow direction
        angle = math.atan2(dy, dx)
        
        # Calculate arrow head points (30-degree wings)
        wingAngle = math.pi / 6  # 30 degrees
        
        arrowP1X = endPoint[0] - self.headSize * math.cos(angle - wingAngle)
        arrowP1Y = endPoint[1] - self.headSize * math.sin(angle - wingAngle)
        
        arrowP2X = endPoint[0] - self.headSize * math.cos(angle + wingAngle)  
        arrowP2Y = endPoint[1] - self.headSize * math.sin(angle + wingAngle)
        
        # Create arrow polygon
        pointList = [
            QPointF(endPoint[0], endPoint[1]),  # Arrow tip
            QPointF(arrowP1X, arrowP1Y),        # Wing 1
            QPointF(arrowP2X, arrowP2Y)         # Wing 2
        ]
        
        polygon = QPolygonF(pointList)
        self.arrowItem.setPolygon(polygon)
        self.arrowItem.setVisible(True)
    
    def getGraphicsItems(self) -> list[QGraphicsLineItem]:
        """Return all graphics items for adding to scene"""
        items = self.lineItems.copy()
        items.append(self.arrowItem)
        return items
    
    def setVisible(self, visible: bool):
        """Set visibility of all line segments and arrow"""
        for lineItem in self.lineItems:
            lineItem.setVisible(visible)
        self.arrowItem.setVisible(visible)
    
    def setPen(self, pen):
        """Set pen for all line segments and arrow"""
        for lineItem in self.lineItems:
            lineItem.setPen(pen)
        self.arrowItem.setPen(pen)
    
    def _setupSelection(self):
        """Setup click handling and selection for all line segments"""
        # Make arrow item selectable
        self.arrowItem.setFlag(QGraphicsItem.ItemIsSelectable)
        
        # Setup click handling for arrow
        original_arrow_press = self.arrowItem.mousePressEvent
        def arrow_click_handler(event):
            if event.button() == Qt.LeftButton:
                self.clicked.emit()
                if self._selection_manager:
                    self._selection_manager.select_item(self)
            original_arrow_press(event)
        self.arrowItem.mousePressEvent = arrow_click_handler
    
    def _setupLineSelection(self, lineItem: QGraphicsLineItem):
        """Setup click handling for a specific line segment"""
        lineItem.setFlag(QGraphicsItem.ItemIsSelectable)
        
        original_press = lineItem.mousePressEvent
        def line_click_handler(event):
            if event.button() == Qt.LeftButton:
                self.clicked.emit()
                if self._selection_manager:
                    self._selection_manager.select_item(self)
            original_press(event)
        lineItem.mousePressEvent = line_click_handler
    
    def set_selection_manager(self, selection_manager):
        """Set the selection manager for this arrow"""
        self._selection_manager = selection_manager
    
    def setSelected(self, selected: bool, selection_color: QColor):
        """Set selection state with visual feedback for all segments"""
        if self._is_selected == selected:
            return
            
        self._is_selected = selected
        
        if selected:
            # Apply selection color to all segments
            selection_pen = QPen(selection_color, 3)
            for lineItem in self.lineItems:
                lineItem.setPen(selection_pen)
            self.arrowItem.setPen(selection_pen)
            self.arrowItem.setBrush(QBrush(selection_color))
        else:
            # Restore original appearance for all segments
            for lineItem in self.lineItems:
                lineItem.setPen(self._original_pen)
            self.arrowItem.setPen(self._original_pen)
            self.arrowItem.setBrush(QBrush(self._original_pen.color()))
    
    def isSelected(self) -> bool:
        """Check if arrow is currently selected"""
        return self._is_selected
    
    def get_interactive_waypoints(self) -> List['InteractiveWaypoint']:
        """Get the list of interactive waypoints"""
        return self.interactive_waypoints
    
    def get_current_path_points(self) -> List[Tuple[float, float]]:
        """Get the current complete path including entity edge points"""
        if not self.interactive_waypoints:
            # No waypoints - direct connection
            startPoint, endPoint = calculateLineEndpoints(self.srcEntity, self.dstEntity)
            return [startPoint, endPoint]
        else:
            # Build path with edge intersections
            path_points = []
            
            # First waypoint determines source edge intersection
            first_waypoint = self.interactive_waypoints[0]
            startPoint = self._calculateEntityEdgePoint(self.srcEntity, first_waypoint.x, first_waypoint.y)
            path_points.append(startPoint)
            
            # Add all waypoints
            for waypoint in self.interactive_waypoints:
                path_points.append(waypoint.position)
            
            # Last waypoint determines destination edge intersection  
            last_waypoint = self.interactive_waypoints[-1]
            endPoint = self._calculateEntityEdgePoint(self.dstEntity, last_waypoint.x, last_waypoint.y)
            path_points.append(endPoint)
            
            return path_points
    
    def add_waypoint_at_index(self, waypoint: 'InteractiveWaypoint', segment_index: int):
        """Add a waypoint at the specified segment index"""
        # Insert waypoint at the correct position
        # segment_index 0 means between source and first waypoint (or destination if no waypoints)
        if segment_index <= 0:
            self.interactive_waypoints.insert(0, waypoint)
        elif segment_index >= len(self.interactive_waypoints):
            self.interactive_waypoints.append(waypoint)
        else:
            self.interactive_waypoints.insert(segment_index, waypoint)
        
        # Recreate line segments with new waypoint count
        self._recreateLineSegments()
        
        # Update geometry
        self.updateGeometry()
    
    def remove_waypoint(self, waypoint: 'InteractiveWaypoint'):
        """Remove a waypoint from the list"""
        if waypoint in self.interactive_waypoints:
            self.interactive_waypoints.remove(waypoint)
            
            # Recreate line segments with new waypoint count
            self._recreateLineSegments()
            
            # Update geometry
            self.updateGeometry()
    
    def _recreateLineSegments(self):
        """Recreate line segments when waypoint count changes"""
        # Store reference to scene from existing line items before clearing
        scene = None
        if self.lineItems:
            scene = self.lineItems[0].scene()
        
        # Remove old line items from scene if they exist
        if scene:
            for old_item in self.lineItems:
                if old_item.scene():
                    scene.removeItem(old_item)
        
        # Clear existing line items
        self.lineItems.clear()
        
        # Create new line segments
        self._createLineSegments()
        
        # Add new line items to scene if we have a scene reference
        if scene:
            for new_item in self.lineItems:
                scene.addItem(new_item)
        
        # Apply current visual properties
        for lineItem in self.lineItems:
            if self._is_selected:
                # Apply selection appearance
                from workflow_designer.wfd_selection_manager import ThemeDetector
                selection_color = ThemeDetector.get_selection_color()
                selection_pen = QPen(selection_color, 3)
                lineItem.setPen(selection_pen)
            else:
                # Apply normal appearance
                lineItem.setPen(self._original_pen)
        
        # If line was selected, ensure nodes are shown after recreation
        if self._is_selected and self._node_manager:
            self._node_manager.create_nodes(self.interactive_waypoints)
            self._node_manager.show_nodes()
    
    def create_node_manager(self, selection_color: QColor) -> 'LineNodeManager':
        """Create and return a node manager for this arrow"""
        from workflow_designer.wfd_interactive_nodes import LineNodeManager
        
        if self._node_manager is None:
            self._node_manager = LineNodeManager(self, selection_color)
            
            # Connect signals
            self._node_manager.waypoint_moved.connect(self._on_waypoint_moved)
            self._node_manager.waypoint_added.connect(self._on_waypoint_added)
            self._node_manager.waypoint_removed.connect(self._on_waypoint_removed)
            self._node_manager.geometry_update_requested.connect(self.updateGeometry)
        
        return self._node_manager
    
    def show_nodes(self):
        """Show interactive nodes if they exist"""
        if self._node_manager:
            self._node_manager.create_nodes(self.interactive_waypoints)
            self._node_manager.show_nodes()
    
    def hide_nodes(self):
        """Hide interactive nodes if they exist"""
        if self._node_manager:
            self._node_manager.hide_nodes()
    
    def get_node_graphics_items(self) -> List[QGraphicsItem]:
        """Get all node graphics items for adding to scene"""
        if self._node_manager:
            return self._node_manager.get_graphics_items()
        return []
    
    def _on_waypoint_moved(self, waypoint: 'InteractiveWaypoint'):
        """Handle waypoint movement from node manager"""
        # Update geometry in real-time
        self.updateGeometry()
    
    def _on_waypoint_added(self, waypoint: 'InteractiveWaypoint', segment_index: int):
        """Handle waypoint addition from node manager"""
        self.add_waypoint_at_index(waypoint, segment_index)
    
    def _on_waypoint_removed(self, waypoint: 'InteractiveWaypoint'):
        """Handle waypoint removal from node manager"""
        self.remove_waypoint(waypoint)
