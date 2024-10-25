from dataclasses import dataclass

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsItem, QGraphicsLineItem, QGraphicsRectItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainterPath, QPen, QBrush

NODEPROPS = ['FillColor', 'TextColor', 'Text', 'LabelEdit', 'Alignment', 'DrawColor', 'Shadow']
NODEATTRIBS = ['Font', 'LayoutNode', 'Shape']
LINKPROPS = ['DrawColor', 'Shadow', 'DashStyle']
LINKATTRIBS = ['LayoutLink', 'Point']

class Rect:
    def __init__(self, left: float, top: float, width: float, height: float):
        self.left = left
        self.top = top
        self.width = width
        self.height = height

        self.rx = width / 2
        self.ry = height / 2
        self.cx = left + self.rx
        self.cy = top + self.ry

@dataclass
class Node:
    nodeRect: Rect
    nodeProps: dict
    nodeAttribs: dict[str, dict]
    
@dataclass
class Link:
    linkProps: dict
    linkAttribs: dict[str, dict]

class MakeClickableMixin(QObject):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def makeClickable(self, item: QGraphicsItem):
        item.setFlag(QGraphicsItem.ItemIsSelectable)

        originalMouseClickEvent = item.mousePressEvent

        def clickableMousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self.clicked.emit()
                print("Click even emmited")

            originalMouseClickEvent(event)

        item.mousePressEvent = clickableMousePressEvent

class MakeMovableMixin(QObject):
    pressed = Signal()
    moved = Signal()
    released = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.moving = False
        self.dx = 0
        self.dy = 0

    def makeMovable(self, item: QGraphicsItem):
        item.setFlag(QGraphicsItem.ItemIsSelectable)

        originalMousePressEvent = item.mousePressEvent
        originalMouseMoveEvent = item.mouseMoveEvent
        originalMouseReleaseEvent = item.mouseReleaseEvent

        def clickableMousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self.moving = True

                self.dx = item.pos().x() - event.scenePos().x()
                self.dy = item.pos().y() - event.scenePos().y()

                self.pressed.emit()

            originalMousePressEvent(event)

        item.mousePressEvent = clickableMousePressEvent

        def clickableMouseMoveEvent(event):
            if self.moving:
                item.setPos(event.scenePos().x() + self.dx, event.scenePos().y() + self.dy)

                self.moved.emit()

            originalMouseMoveEvent(event)

        item.mouseMoveEvent = clickableMouseMoveEvent

        def clickableMouseReleaseEvent(event):
            if event.button() == Qt.LeftButton:
                self.moving = False

                self.released.emit()

            originalMouseReleaseEvent(event)

        item.mouseReleaseEvent = clickableMouseReleaseEvent

class WFDClickableEllipse(QGraphicsEllipseItem):
    def __init__(self, *args, **kwargs):
        QGraphicsEllipseItem.__init__(self, *args, **kwargs)

        self.setBrush(QBrush(Qt.blue))
        self.setPen(QPen(Qt.black))
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable)

        #self.clickableHandler = MakeClickableMixin()
        #self.clickableHandler.makeClickable(self)
        self.clickableHandler = MakeMovableMixin()
        self.clickableHandler.makeMovable(self)
        self.clickableHandler.moved.connect(self.test)

    def test(self):
        print("test")

    def shape(self):
        path = QPainterPath()
        path.addEllipse(self.rect())
        return path

    def contains(self, point):
        ellipse_path = self.shape()
        return ellipse_path.contains(point)

class WFDClickableRect(QGraphicsRectItem):
    def __init__(self, *args, **kwargs):
        QGraphicsRectItem.__init__(self, *args, **kwargs)

        self.setBrush(QBrush(Qt.blue))
        self.setPen(QPen(Qt.black))
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)

        self.clickableHandler = MakeClickableMixin()
        self.clickableHandler.makeClickable(self)

        self.clickableHandler = MakeMovableMixin()
        self.clickableHandler.makeMovable(self)

class WFDClickableLine(QGraphicsLineItem):
    def __init__(self, *args, **kwargs):
        QGraphicsLineItem.__init__(self, *args, **kwargs)

        #self.setBrush(QBrush(Qt.blue))
        self.setPen(QPen(Qt.black))
        self.setFlag(QGraphicsLineItem.ItemIsSelectable)

        self.clickableHandler = MakeClickableMixin()
        self.clickableHandler.makeClickable(self)

class WFDLineSegments:
    def __init__(self, startItem, endItem, points: list):
        self.startItem = startItem
        self.endItem = endItem

        self.points = points

        # Create lines using pairs, not last item is popped as it incomplete
        # pair
        self.lines = [WFDLine(points[0])]
        for i in range(1, len(points)):
            self.lines[-1].end = points[i]
            self.lines.append(WFDLine(points[i]))
        self.lines.pop()

class WFDLine:
    def __init__(self, start, end=None):
        self.start = start
        self.end = end
