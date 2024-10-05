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

            originalMouseClickEvent(event)

        item.mousePressEvent = clickableMousePressEvent

class WFDClickableEllipse(QGraphicsEllipseItem):
    clicked = Signal()

    def __init__(self, *args, **kwargs):
        QGraphicsEllipseItem.__init__(self, *args, **kwargs)

        self.setBrush(QBrush(Qt.blue))
        self.setPen(QPen(Qt.black))
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable)

        self.clickableHandler = MakeClickableMixin()
        self.clickableHandler.makeClickable(self)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(self.rect())
        return path

    def contains(self, point):
        ellipse_path = self.shape()
        return ellipse_path.contains(point)

class WFDClickableRect(QGraphicsRectItem):
    clicked = Signal()

    def __init__(self, *args, **kwargs):
        QGraphicsRectItem.__init__(self, *args, **kwargs)

        self.setBrush(QBrush(Qt.blue))
        self.setPen(QPen(Qt.black))
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)

        self.clickableHandler = MakeClickableMixin()
        self.clickableHandler.makeClickable(self)

class WFDClickableLine(QGraphicsLineItem):
    def __init__(self, *args, **kwargs):
        QGraphicsLineItem.__init__(self, *args, **kwargs)

        #self.setBrush(QBrush(Qt.blue))
        self.setPen(QPen(Qt.black))
        self.setFlag(QGraphicsLineItem.ItemIsSelectable)

        self.clickableHandler = MakeClickableMixin()
        self.clickableHandler.makeClickable(self)

