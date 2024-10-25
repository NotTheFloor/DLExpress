import random

from PySide6.QtWidgets import QFrame, QGraphicsView, QVBoxLayout
from PySide6.QtGui import QPainter, QPen, QColor, QFontMetrics
from PySide6.QtCore import QPoint, QRect

from .wfd_utilities import drawArrow

_DEF_DW_SZ_X = 1400
_DEF_DW_SZ_Y = 900
_TITLE_OFFS_X = 5
_TITLE_OFFS_Y = 12

class DrawingWidget(QFrame):
    def __init__(self, sceneDict: dict, parent=None):
        super().__init__(parent)

        self.sceneDict: dict = sceneDict
        self.currentWorkflow = list(sceneDict.keys())[0]

        self.setMinimumSize(_DEF_DW_SZ_X, _DEF_DW_SZ_Y)

        layout = QVBoxLayout(self)
        self.setLayout(layout)


        self.view = QGraphicsView()
        layout.addWidget(self.view)

        self.view.setScene(self.sceneDict[self.currentWorkflow])


    def change_workflow(self, wfTitle):
        self.currentWorkflow = wfTitle
        #self.update()
        self.view.setScene(self.sceneDict[self.currentWorkflow])

    def unused(self):
        painter = QPainter(self)
        pen = QPen(QColor(0, 0, 0), 2)
        painter.setPen(pen)

        fontMetric = QFontMetrics(painter.font())

        currentScene = self.sceneDict[self.currentWorkflow]

        for key, workflow in currentScene["workflows"].items():
            painter.drawRect(QRect(workflow.nodeRect.left, workflow.nodeRect.top, workflow.nodeRect.width, workflow.nodeRect.height))
            painter.drawText(
                    QPoint(workflow.nodeRect.left + _TITLE_OFFS_X, workflow.nodeRect.top + _TITLE_OFFS_Y), 
                    workflow.nodeAttribs["LayoutNode"]["Tooltip"]
                )

            offset = 1
            for wfStatus in currentScene["workflowStatuses"][key]:
                painter.drawText(
                        QPoint(workflow.nodeRect.left + _TITLE_OFFS_X + 5, workflow.nodeRect.top + 12 + (offset * 15)), 
                        wfStatus.Title
                    )
                offset += 1

        for key, status in currentScene["statuses"].items():
            painter.drawEllipse(QPoint(status.nodeRect.cx, status.nodeRect.cy), status.nodeRect.rx, status.nodeRect.ry)
            text = status.nodeProps['Text']
            textWidth = fontMetric.horizontalAdvance(text)
            textHeight = fontMetric.height()
            painter.drawText(
                    QPoint(status.nodeRect.cx - textWidth // 2, status.nodeRect.cy + textHeight // 4), # 4 to account for Qt baseline
                    text
                )
            

        for i in range(1, len(currentScene["linkPoints"])):
            # If new segment, skip to break line
            if currentScene["linkPoints"][i][2]:
                pen = QPen(QColor(random.randint(0,255), random.randint(0,255), 0), 2)
                continue
            
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
