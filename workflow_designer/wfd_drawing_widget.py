from PySide6.QtWidgets import QFrame
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import QPoint

from .wfd_objects import Node as WFN

_DEF_DW_SZ_X = 600
_DEF_DW_SZ_Y = 600

class DrawingWidget(QFrame):
    def __init__(self, nodeList: WFN, parent=None):
        super().__init__(parent)


        print("DW")
        print(nodeList)
        self.nodeList: WFN = nodeList

        self.setMinimumSize(_DEF_DW_SZ_X, _DEF_DW_SZ_Y)

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(QColor(0, 0, 0), 2)
        painter.setPen(pen)

        #painter.drawLine(10, 10, 200, 200)

        print("Nodes")
        for node in self.nodeList:
            painter.drawEllipse(QPoint(node.nodeRect.cx, node.nodeRect.cy), node.nodeRect.rx, node.nodeRect.ry)


