from typing import Optional, TYPE_CHECKING, Tuple
from PySide6.QtCore import QObject, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QPainterPath, QPen
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
        super().__init__(0, 0, rect.width, rect.height, *args, **kwargs)
        self.wfdParent = wfdParent

        if wfdParent is None:
            raise ValueError("wfdParent cannot be None in ExtendedEllipse")

        self.setPos(rect.left, rect.top)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.wfdParent.wfdItemChange(change, value)
            
        return super().itemChange(change, value)


class Shape(QObject):
    clicked = Signal()
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

    def wfdItemChange(self, change, value):
        self.moved.emit(value)
    
    def getCurrentCenter(self) -> Tuple[float, float]:
        """Get the current center coordinates from the graphics item's position"""
        # Get current position of graphics item
        pos = self.graphicsItem.pos()
        
        # Calculate current center based on graphics item position and rect size
        currentCenterX = pos.x() + self.rect.width / 2
        currentCenterY = pos.y() + self.rect.height / 2
        
        return currentCenterX, currentCenterY
    
    def getCurrentBounds(self) -> Tuple[float, float, float, float]:
        """Get current bounds (left, top, width, height) from graphics item position"""
        pos = self.graphicsItem.pos()
        return pos.x(), pos.y(), self.rect.width, self.rect.height


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

        # Apply colors if provided
        if fillColor:
            self.graphicsItem.setBrush(QBrush(fillColor))
        else:
            self.graphicsItem.setBrush(QBrush(Qt.lightGray))
            
        if drawColor:
            self.graphicsItem.setPen(QPen(drawColor, 2))
        else:
            self.graphicsItem.setPen(QPen(Qt.black, 2))

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

        # Apply colors if provided
        if fillColor:
            self.graphicsItem.setBrush(QBrush(fillColor))
        else:
            self.graphicsItem.setBrush(QBrush(Qt.lightGray))
            
        if drawColor:
            self.graphicsItem.setPen(QPen(drawColor, 2))
        else:
            self.graphicsItem.setPen(QPen(Qt.black, 2))



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
