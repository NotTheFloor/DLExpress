import random

from PySide6.QtWidgets import QFrame
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtCore import QPoint, QRect

from .wfd_objects import Node
from .wfd_utilities import drawArrow

from doclink_py.sql.doclink_sql import DocLinkSQL

_DEF_DW_SZ_X = 1400
_DEF_DW_SZ_Y = 900

class DrawingWidget(QFrame):
    def __init__(self, sceneDict: dict, parent=None):
        super().__init__(parent)

        self.sceneDict: dict = sceneDict
        self.currentWorkflow = list(sceneDict.keys())[0]

        self.setMinimumSize(_DEF_DW_SZ_X, _DEF_DW_SZ_Y)

    def change_workflow(self, wfTitle):
        self.currentWorkflow = wfTitle
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(QColor(random.randint(0,255), random.randint(0,255), 0), 2)
        painter.setPen(pen)

        currentScene = self.sceneDict[self.currentWorkflow]

        for key, workflow in currentScene["workflows"].items():
            painter.drawRect(QRect(workflow.nodeRect.left, workflow.nodeRect.top, workflow.nodeRect.width, workflow.nodeRect.height))

        for key, status in currentScene["statuses"].items():
            painter.drawEllipse(QPoint(status.nodeRect.cx, status.nodeRect.cy), status.nodeRect.rx, status.nodeRect.ry)

        for i in range(1, len(currentScene["linkPoints"])):
            # If new segment, skip to break line
            if currentScene["linkPoints"][i][2]:
                    continue

            
            pen = QPen(QColor(random.randint(0,255), random.randint(0,255), 0), 2)
            painter.setPen(pen)
            # This is gross
            if i+1 == len(currentScene["linkPoints"]) or currentScene["linkPoints"][i+1][2]:
                drawArrow(painter, currentScene["linkPoints"][i-1], currentScene["linkPoints"][i])
            else:
                painter.drawLine(
                        currentScene["linkPoints"][i-1][0], 
                        currentScene["linkPoints"][i-1][1], 
                        currentScene["linkPoints"][i][0], 
                        currentScene["linkPoints"][i][1]
                        )
