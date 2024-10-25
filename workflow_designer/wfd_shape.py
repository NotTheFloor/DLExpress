from typing import Optional
from PySide6.QtCore import QObject, QPointF, Qt, Signal
from PySide6.QtGui import QBrush, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QGraphicsRectItem

from workflow_designer.wfd_objects import Rect

def MovingSignal(cls):
    cls.move = Signal(QPointF)

    originalInit = cls.__init__

    def newInit(self, *args, **kwargs):
        originalInit(self, *args, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

    cls.__init__ = newInit

    originalItemChange = getattr(cls, 'itemChange', None)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.moved.emit(value)

        if originalItemChange:
            return originalItemChange(self, change, value)

        return super(cls, self).itemChange(change, value)

    cls.itemChange = itemChange

    return cls

class Shape(QObject):
    clicked = Signal()
    pressed = Signal()
    released = Signal()

    def __init__(self, rect, parent=None):
        super().__init__(parent)
        self.rect: Rect = rect
        self.graphicsItem: Optional[QGraphicsItem] = None

        # For movement
        self.moving = False
        self.dx = 0
        self.dy = 0

#    def makeClickable(self, item: QGraphicsItem):
#        self.graphicsItem.setFlag(QGraphicsItem.ItemIsSelectable)
#
#        originalMouseClickEvent = item.mousePressEvent
#
#        def clickableMousePressEvent(event):
#            if event.button() == Qt.LeftButton:
#                self.clicked.emit()
#                print("Click even emmited")
#
#            originalMouseClickEvent(event)
#
#        item.mousePressEvent = clickableMousePressEvent
#
#    # Sadly after some research this is all pretty much useless as Qt has built
#    # in movement control
#
#    def makeMovable(self, item: QGraphicsItem):
#        item.setFlag(QGraphicsItem.ItemIsSelectable)
#
#        originalMousePressEvent = item.mousePressEvent
#        originalMouseMoveEvent = item.mouseMoveEvent
#        originalMouseReleaseEvent = item.mouseReleaseEvent
#
#        def clickableMousePressEvent(event):
#            if event.button() == Qt.LeftButton:
#                self.moving = True
#
#                self.dx = item.pos().x() - event.scenePos().x()
#                self.dy = item.pos().y() - event.scenePos().y()
#
#                self.pressed.emit()
#
#            originalMousePressEvent(event)
#
#        item.mousePressEvent = clickableMousePressEvent
#
#        def clickableMouseMoveEvent(event):
#            if self.moving:
#                item.setPos(event.scenePos().x() + self.dx, event.scenePos().y() + self.dy)
#
#                self.moved.emit()
#
#            originalMouseMoveEvent(event)
#
#        item.mouseMoveEvent = clickableMouseMoveEvent
#
#        def clickableMouseReleaseEvent(event):
#            if event.button() == Qt.LeftButton:
#                self.moving = False
#
#                self.released.emit()
#
#            originalMouseReleaseEvent(event)
#
#        item.mouseReleaseEvent = clickableMouseReleaseEvent

@MovingSignal
class ExtendedRect(QGraphicsRectItem):
    def __init__(self, *args, **kwargs):
        QGraphicsRectItem.__init__(self, *args, **kwargs)

class ShapeRect(Shape):
    def __init__(self, rect: Rect, parent=None):
        super().__init__(rect, parent)

        self.graphicsItem = ExtendedRect(
                self.rect.left,
                self.rect.top,
                self.rect.width,
                self.rect.height
            )

        self.graphicsItem.setBrush(QBrush(Qt.blue))
        self.graphicsItem.setPen(QPen(Qt.black))

@MovingSignal
class ExtendedEllipse(QGraphicsEllipseItem):
    def __init__(self, *args, **kwargs):
        QGraphicsEllipseItem.__init__(self, *args, **kwargs)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(self.rect())
        return path

    def contains(self, point):
        ellipse_path = self.shape()
        return ellipse_path.contains(point)

class ShapeEllipse(Shape):
    def __init__(self, rect: Rect, parent=None):
        super().__init__(rect, parent)

        self.graphicsItem = ExtendedEllipse(
                self.rect.left,
                self.rect.top,
                self.rect.width,
                self.rect.height
            )
        
        self.graphicsItem.setBrush(QBrush(Qt.blue))
        self.graphicsItem.setPen(QPen(Qt.black))
