from dataclasses import dataclass

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsItem, QGraphicsLineItem, QGraphicsRectItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainterPath, QPen, QBrush

from workflow_designer.wfd_utilities import addArrowToLineItem

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

## Typical Node for a Status (For some stupid fucking reason WF are different)
## P.S. we know the reason
#   nodeProps={'FillColor': '-4144960', 'TextColor': '-16777216', 'Text': 'Unprocessed'}, 
#   nodeAttribs={
#       'Font': {'Name': 'Microsoft Sans Serif', 'Size': '8.25', 'Bold': 'True', 
#           'Italic': 'False', 'Strikeout': 'False', 'Underline': 'False'},
#       'LayoutNode': {'Key': '6539ec3e-1494-4da2-ab3d-7c96ed9fce3f', 
#           'Type': 'Status', 'CanDelete': 'True', 'WorkflowKey': 'efd1febf-7596-4f63-a731-c9b6df41a72c', 
#           'IsHidden': 'False', 'IsDefault': 'True', 'Class': 'StatusLayoutNode'}})
@dataclass
class Node:
    nodeRect: Rect
    nodeProps: dict
    nodeAttribs: dict[str, dict]
    
@dataclass
class Link:
    linkProps: dict
    linkAttribs: dict[str, dict]

# Slight issue here where everything is actually being passed as a string oh no!
@dataclass
class WFDFont:
    Name: str
    Size: float
    Bold: bool
    Italic: bool
    Strikeout: bool
    Underline: bool

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

        self.movableHandler = MakeMovableMixin()
        self.movableHandler.makeMovable(self)

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
