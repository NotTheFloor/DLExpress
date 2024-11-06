from typing import Optional
from PySide6.QtCore import QObject, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QGraphicsObject, QGraphicsRectItem

from workflow_designer.wfd_objects import Rect

class ExtendedRect(QGraphicsRectItem):
    def __init__(self, rect: Rect, wfdParent=None, *args, **kwargs):
        super().__init__(0, 0, rect.width, rect.height, *args, **kwargs)
        self.wfdParent = wfdParent

        if wfdParent is None:
            print("wfdParent is none in Extended rect")
            quit()

        self.setPos(rect.left, rect.top)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.wfdParent.wfdItemChange(change, value)
            
        return super().itemChange(change, value)

class TestEllipse(QGraphicsEllipseItem):
    def __init__(self, rect: Rect, wfdParent= None, *args, **kwargs):
        super().__init__(rect.left, rect.top, rect.width, rect.height, *args, **kwargs)

class ExtendedEllipse(QGraphicsEllipseItem):
    def __init__(self, rect: Rect, wfdParent=None, *args, **kwargs):
        super().__init__(0, 0, rect.width, rect.height, *args, **kwargs)
        self.wfdParent = wfdParent

        if wfdParent is None:
            print("wfdParent is none in Extended ellipse")
            quit()

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


class ShapeRect(Shape):
    def __init__(self, rect: Rect, shapeParent=None, parent=None):
        super().__init__(rect, parent)


        self.graphicsItem = ExtendedRect(
                rect=rect,
                wfdParent=self,
                parent=shapeParent
            )
        self.graphicsItem.setFlag(QGraphicsItem.ItemIsMovable)
        self.graphicsItem.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        # self.graphicsItem.setPos(self.rect.left, self.rect.top)

        self.graphicsItem.setBrush(QBrush(Qt.blue))
        self.graphicsItem.setPen(QPen(Qt.black))

class ShapeEllipse(Shape):
    def __init__(self, rect: Rect, shapeParent=None, parent=None):
        super().__init__(rect, parent)

        # self.graphicsItem = QGraphicsEllipseItem(rect.left, rect.top, rect.width, rect.height, parent)
        self.graphicsItem = ExtendedEllipse(
                rect=rect,
                wfdParent=self,
                parent=shapeParent
            )
        # self.graphicsItem = TestEllipse(rect, wfdParent=None, parent=None)
        
        self.graphicsItem.setFlag(QGraphicsItem.ItemIsMovable)
        self.graphicsItem.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        # self.graphicsItem.setPos(self.rect.left, self.rect.top)

        self.graphicsItem.setBrush(QBrush(Qt.blue))
        self.graphicsItem.setPen(QPen(Qt.black))
