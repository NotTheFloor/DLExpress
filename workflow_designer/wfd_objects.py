from dataclasses import dataclass

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsItem, QGraphicsLineItem, QGraphicsRectItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QBrush

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

class WFDClickableObject(QGraphicsItem, QObject):
    clicked = Signal()

    def __init__(self, *args, **kwargs):
        QGraphicsItem.__init__(self, *args, **kwargs)
        QObject.__init__(self)
        self.setFlag(QGraphicsItem.ItemIsSelectable)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class WFDClickableEllipse(QGraphicsEllipseItem, QObject):
    clicked = Signal()

    def __init__(self, *args, **kwargs):
        QGraphicsEllipseItem.__init__(self, *args, **kwargs)
        QObject.__init__(self)

        self.setBrush(QBrush(Qt.blue))
        self.setPen(QPen(Qt.black))
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class WFDClickableRect(QGraphicsRectItem, QObject):
    clicked = Signal()

    def __init__(self, *args, **kwargs):
        QGraphicsRectItem.__init__(self, *args, **kwargs)
        QObject.__init__(self)

        self.setBrush(QBrush(Qt.blue))
        self.setPen(QPen(Qt.black))
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class WFDClickableLine(QGraphicsLineItem, QObject):
    clicked = Signal()

    def __init__(self, *args, **kwargs):
        QGraphicsLineItem.__init__(self, *args, **kwargs)
        QObject.__init__(self)

        #self.setBrush(QBrush(Qt.blue))
        self.setPen(QPen(Qt.black))
        self.setFlag(QGraphicsLineItem.ItemIsSelectable)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

