from PySide6.QtWidgets import QDialog, QSplitter, QTextEdit, QVBoxLayout, QListView
from PySide6.QtCore import Qt, QStringListModel

from .wfd_drawing_widget import DrawingWidget
from .wfd_objects import Node as WFN
from .scene_manager import WorkflowSceneManager

from doclink_py.sql.doclink_sql import DocLinkSQL
from doclink_py.doclink_types.workflows import Workflow

_DEF_WDW_SZ_X = 800
_DEF_WDW_SZ_Y = 600
_DEF_T_RP_Y = 400
_DEF_B_RP_Y = 200

class WorkflowDesignerWindow(QDialog):
    def __init__(self, doclink: DocLinkSQL):
        super().__init__()

        self.setWindowTitle("Workflow Designer")
        self.setGeometry(150, 150, _DEF_WDW_SZ_X, _DEF_WDW_SZ_Y)

        scene_manager = WorkflowSceneManager(doclink)

        main_splitter = QSplitter(Qt.Horizontal)

        self.drawing_area = DrawingWidget(doclink)
        main_splitter.addWidget(self.drawing_area)

        right_pane = QSplitter(Qt.Vertical)

        #top_right = QTextEdit("Top right place holder")
        top_right = self.workflow_list(scene_manager.workflows)
        top_right.setFixedHeight(_DEF_T_RP_Y)

        bottom_right = QTextEdit("Bottom right place holder")
        bottom_right.setFixedHeight(_DEF_B_RP_Y)

        right_pane.addWidget(top_right)
        right_pane.addWidget(bottom_right)

        main_splitter.addWidget(right_pane)
        main_splitter.setSizes([600, 200]) # Need to add defaults for this
        
        layout = QVBoxLayout()
        layout.addWidget(main_splitter)
        self.setLayout(layout)

    def workflow_list(self, workflows) -> QListView:
        workflow_str = [workflow.Title for workflow in workflows]
        workflow_model = QStringListModel(workflow_str) 
        workflow_list = QListView()
        workflow_list.setModel(workflow_model)
        workflow_list.setSelectionMode(QListView.SingleSelection)

        return workflow_list
