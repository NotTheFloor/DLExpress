import random

from PySide6.QtWidgets import QFrame, QGraphicsView, QVBoxLayout, QGraphicsScene
from PySide6.QtGui import QPainter, QPen, QColor, QFontMetrics
from PySide6.QtCore import QPoint, QRect, Qt

from .wfd_utilities import drawArrow

_DEF_DW_SZ_X = 1400
_DEF_DW_SZ_Y = 900
_TITLE_OFFS_X = 5
_TITLE_OFFS_Y = 12

class CustomGraphicsView(QGraphicsView):
    """Custom QGraphicsView that handles empty space clicks for deselection"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._wf_scene = None  # Reference to WFScene for selection manager access
    
    def set_wf_scene(self, wf_scene):
        """Set the workflow scene reference for selection handling"""
        self._wf_scene = wf_scene
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Check if click is on empty space
            item = self.itemAt(event.pos())
            if item is None and self._wf_scene and hasattr(self._wf_scene, 'selection_manager'):
                # Click on empty space - deselect all
                self._wf_scene.selection_manager.deselect_all()
        
        # Call parent handler to maintain normal functionality
        super().mousePressEvent(event)


class DrawingWidget(QFrame):
    def __init__(self, sceneDict: dict, sceneManagerDict: dict = None, initial_workflow_key: str = None, parent=None):
        super().__init__(parent)

        self.sceneDict: dict = sceneDict  # Qt graphics scenes
        self.sceneManagerDict: dict = sceneManagerDict or {}  # WFScene objects
        # Use provided initial workflow key, or fall back to first available key
        if initial_workflow_key and initial_workflow_key in sceneDict:
            self.currentWorkflow = initial_workflow_key
        else:
            # Fallback to first available workflow
            self.currentWorkflow = next(iter(sceneDict.keys())) if sceneDict else None

        self.setMinimumSize(_DEF_DW_SZ_X, _DEF_DW_SZ_Y)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.view = CustomGraphicsView()
        layout.addWidget(self.view)

        # Set initial scene if we have workflows
        if self.currentWorkflow:
            self.view.setScene(self.sceneDict[self.currentWorkflow])
            
            # Set the WFScene reference if available
            if self.currentWorkflow in self.sceneManagerDict:
                self.view.set_wf_scene(self.sceneManagerDict[self.currentWorkflow])


    def change_workflow(self, wfTitle):
        self.currentWorkflow = wfTitle
        #self.update()
        self.view.setScene(self.sceneDict[self.currentWorkflow])
        
        # Update WFScene reference when switching workflows
        if self.currentWorkflow in self.sceneManagerDict:
            self.view.set_wf_scene(self.sceneManagerDict[self.currentWorkflow])

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
