from typing import Optional, TYPE_CHECKING, Tuple
from PySide6.QtCore import QObject, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QPainterPath, QPen, QColor
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QGraphicsObject, QGraphicsRectItem, QGraphicsLineItem
from shiboken6 import Object

from workflow_designer.wfd_objects import Rect


class ExtendedRect(QGraphicsRectItem):
    def __init__(self, rect: Rect, wfdParent=None, *args, **kwargs):
        super().__init__(0, 0, rect.width, rect.height, *args, **kwargs)
        self.wfdParent = wfdParent

        if wfdParent is None:
            raise ValueError("wfdParent cannot be None in ExtendedRect")

        self.setPos(rect.left, rect.top)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.wfdParent.wfdItemChange(change, value)
            
        return super().itemChange(change, value)

class ExtendedEllipse(QGraphicsEllipseItem):
    def __init__(self, rect: Rect, wfdParent=None, *args, **kwargs):
        # DEBUG: Log ellipse construction details
        from workflow_designer.wfd_logger import logger
        logger.debug(f"ExtendedEllipse construction:")
        logger.debug(f"  rect.width={rect.width}, rect.height={rect.height}")
        logger.debug(f"  rect.rx={getattr(rect, 'rx', 'N/A')}, rect.ry={getattr(rect, 'ry', 'N/A')}")
        logger.debug(f"  rect.cx={getattr(rect, 'cx', 'N/A')}, rect.cy={getattr(rect, 'cy', 'N/A')}")
        logger.debug(f"  rect.left={rect.left}, rect.top={rect.top}")
        
        super().__init__(0, 0, rect.width, rect.height, *args, **kwargs)
        
        logger.debug(f"  Created QGraphicsEllipseItem with rect: {self.rect()}")
        
        self.wfdParent = wfdParent

        if wfdParent is None:
            raise ValueError("wfdParent cannot be None in ExtendedEllipse")

        self.setPos(rect.left, rect.top)
        logger.debug(f"  Set position to: {self.pos()}")
        logger.debug(f"  Final boundingRect: {self.boundingRect()}")

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.wfdParent.wfdItemChange(change, value)
            
        return super().itemChange(change, value)


class Shape(QObject):
    clicked = Signal(bool, bool)  # Emits (has_modifier, has_connection_modifier)
    pressed = Signal()
    released = Signal()
    moved = Signal(QPointF)

    def __init__(self, rect, parent=None):
        super().__init__(parent)
        self.rect: Rect = rect
        self.graphicsItem: Optional[QGraphicsItem] = None

        # For movement
        self.moving = False
        self.dx = 0
        self.dy = 0
        
        # For selection
        self._is_selected = False
        self._original_pen: Optional[QPen] = None
        self._original_brush: Optional[QBrush] = None

    def wfdItemChange(self, change, value):
        self.moved.emit(value)
    
    def getCurrentCenter(self) -> Tuple[float, float]:
        """Get the current center coordinates from the graphics item's position"""
        # Get current position of graphics item
        pos = self.graphicsItem.pos()
        
        # Calculate current center based on graphics item position and rect size
        # NOTE: For ellipses, width/height might not be the correct dimensions
        currentCenterX = pos.x() + self.rect.width / 2
        currentCenterY = pos.y() + self.rect.height / 2
        
        # DEBUG: Log calculation details
        # from workflow_designer.wfd_logger import logger
        # logger.debug(f"getCurrentCenter() for shape type {type(self).__name__}:")
        # logger.debug(f"  Graphics pos: {pos}")
        # logger.debug(f"  Rect dimensions: width={self.rect.width}, height={self.rect.height}")
        # logger.debug(f"  Rect ellipse dims: rx={getattr(self.rect, 'rx', 'N/A')}, ry={getattr(self.rect, 'ry', 'N/A')}")
        # logger.debug(f"  Calculated center: ({currentCenterX}, {currentCenterY})")
        
        return currentCenterX, currentCenterY
    
    def getCurrentBounds(self) -> Tuple[float, float, float, float]:
        """Get current bounds (left, top, width, height) from graphics item position"""
        pos = self.graphicsItem.pos()
        
        # DEBUG: Log calculation details
        from workflow_designer.wfd_logger import logger
        logger.debug(f"getCurrentBounds() for shape type {type(self).__name__}:")
        logger.debug(f"  Graphics pos: {pos}")
        logger.debug(f"  Rect dimensions: width={self.rect.width}, height={self.rect.height}")
        logger.debug(f"  Rect ellipse dims: rx={getattr(self.rect, 'rx', 'N/A')}, ry={getattr(self.rect, 'ry', 'N/A')}")
        logger.debug(f"  Calculated bounds: ({pos.x()}, {pos.y()}, {self.rect.width}, {self.rect.height})")
        
        return pos.x(), pos.y(), self.rect.width, self.rect.height
    
    def setSelected(self, selected: bool, selection_color: QColor):
        """Set selection state with visual feedback"""
        if self._is_selected == selected:
            return
            
        self._is_selected = selected
        
        if selected:
            # Store original appearance
            if hasattr(self.graphicsItem, 'pen'):
                self._original_pen = self.graphicsItem.pen()
            if hasattr(self.graphicsItem, 'brush'):
                self._original_brush = self.graphicsItem.brush()
            
            # Apply selection appearance
            selection_pen = QPen(selection_color, 3)
            if hasattr(self.graphicsItem, 'setPen'):
                self.graphicsItem.setPen(selection_pen)
        else:
            # Restore original appearance
            if self._original_pen and hasattr(self.graphicsItem, 'setPen'):
                self.graphicsItem.setPen(self._original_pen)
            if self._original_brush and hasattr(self.graphicsItem, 'setBrush'):
                self.graphicsItem.setBrush(self._original_brush)
                
            self._original_pen = None
            self._original_brush = None
    
    def isSelected(self) -> bool:
        """Check if shape is currently selected"""
        return self._is_selected
    
    def _setupClickHandling(self):
        """Setup click event handling for graphics item"""
        if not self.graphicsItem:
            return
            
        # Store original mouse press event
        original_mouse_press = self.graphicsItem.mousePressEvent
        
        def handle_mouse_press(event):
            from PySide6.QtCore import Qt
            if event.button() == Qt.LeftButton:
                # Detect modifier keys (Ctrl on Windows/Linux, Cmd on Mac)
                modifiers = event.modifiers()
                has_modifier = bool(modifiers & (Qt.ControlModifier | Qt.MetaModifier))
                
                # Detect 'A' key for connection creation by checking the parent view
                has_connection_modifier = False
                try:
                    # Walk up the parent chain to find the graphics view
                    current_item = self.graphicsItem
                    while current_item:
                        scene = current_item.scene()
                        if scene:
                            views = scene.views()
                            if views:
                                view = views[0]  # Get first view
                                if hasattr(view, 'is_connection_mode_active'):
                                    has_connection_modifier = view.is_connection_mode_active()
                                break
                        # Try parent item if scene not found
                        current_item = current_item.parentItem()
                except:
                    pass
                
                self.clicked.emit(has_modifier, has_connection_modifier)
            # Call original handler
            original_mouse_press(event)
            
        self.graphicsItem.mousePressEvent = handle_mouse_press


class ShapeRect(Shape):
    def __init__(self, rect: Rect, fillColor=None, drawColor=None, shapeParent=None, parent=None):
        super().__init__(rect, parent)

        self.graphicsItem = ExtendedRect(
                rect=rect,
                wfdParent=self,
                parent=shapeParent
            )
        self.graphicsItem.setFlag(QGraphicsItem.ItemIsMovable)
        self.graphicsItem.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.graphicsItem.setFlag(QGraphicsItem.ItemIsSelectable)

        # Apply colors if provided
        if fillColor:
            self.graphicsItem.setBrush(QBrush(fillColor))
        else:
            self.graphicsItem.setBrush(QBrush(Qt.lightGray))
            
        if drawColor:
            self.graphicsItem.setPen(QPen(drawColor, 2))
        else:
            self.graphicsItem.setPen(QPen(Qt.black, 2))
            
        # Connect click events
        self._setupClickHandling()

class ShapeEllipse(Shape):
    def __init__(self, rect: Rect, fillColor=None, drawColor=None, shapeParent=None, parent=None):
        super().__init__(rect, parent)

        self.graphicsItem = ExtendedEllipse(
                rect=rect,
                wfdParent=self,
                parent=shapeParent
            )
        
        self.graphicsItem.setFlag(QGraphicsItem.ItemIsMovable)
        self.graphicsItem.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.graphicsItem.setFlag(QGraphicsItem.ItemIsSelectable)

        # Apply colors if provided
        if fillColor:
            self.graphicsItem.setBrush(QBrush(fillColor))
        else:
            self.graphicsItem.setBrush(QBrush(Qt.lightGray))
            
        if drawColor:
            self.graphicsItem.setPen(QPen(drawColor, 2))
        else:
            self.graphicsItem.setPen(QPen(Qt.black, 2))
            
        # Connect click events
        self._setupClickHandling()



class ShapeLine(QObject):
    moved = Signal(QPointF)

    def __init__(self, oX, oY, dX, dY, lineGroupParent=None, parent=None):
        self.lineGroupParent = lineGroupParent

        self.graphicsItem = ExtendedLine(
                oX, oY, dX, dY,
                wfdParent=self,
                parent=parent
            )
        self.graphicsItem.setFlag(QGraphicsItem.ItemIsMovable)
        self.graphicsItem.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        # self.graphicsItem.setPos(self.rect.left, self.rect.top)

        # self.graphicsItem.setBrush(QBrush(Qt.blue))
        self.graphicsItem.setPen(QPen(Qt.red))
    
    def wfdItemChange(self, change, value):
        self.moved.emit(value)

class ExtendedArrow(QGraphicsLineItem):
    def __init__(self, oX, oY, dX, dY, wfdParent=None, *args, **kwargs):
        super().__init__(oX, oY, dX, dY, *args, **kwargs)

        self.wfdParent = wfdParent 

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.wfdParent.wfdItemChange(change, value)
            
        return super().itemChange(change, value)

class ShapeArrow(QObject):
    moved = Signal(QPointF)

    def __init__(self, oX, oY, dX, dY, lineGroupParent=None, parent=None):
        self.lineGroupParent = lineGroupParent

        self.graphicsItem = ExtendedLine(
                oX, oY, dX, dY,
                wfdParent=self,
                parent=parent
            )
        self.graphicsItem.setFlag(QGraphicsItem.ItemIsMovable)
        self.graphicsItem.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        # self.graphicsItem.setPos(self.rect.left, self.rect.top)

        # self.graphicsItem.setBrush(QBrush(Qt.blue))
        self.graphicsItem.setPen(QPen(Qt.red))
    
    def wfdItemChange(self, change, value):
        self.moved.emit(value)

class ExtendedLine(QGraphicsLineItem):
    def __init__(self, oX, oY, dX, dY, wfdParent=None, *args, **kwargs):
        super().__init__(oX, oY, dX, dY, *args, **kwargs)

        self.wfdParent = wfdParent 

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.wfdParent.wfdItemChange(change, value)
            
        return super().itemChange(change, value)
