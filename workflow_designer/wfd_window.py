from PySide6.QtWidgets import QDialog, QSplitter, QTextEdit, QVBoxLayout, QListView
from PySide6.QtCore import Qt, QStringListModel

from .wfd_drawing_widget import DrawingWidget
from .wfd_objects import Node as WFN
from .scene_manager import WorkflowSceneManager

from doclink_py.sql.manager.doclink_manager import DoclinkManager
from doclink_py.models.workflows import Workflow

_DEF_WDW_SZ_X = 1600
_DEF_WDW_SZ_Y = 900
_DEF_T_RP_Y = 600
_DEF_B_RP_Y = 300

class WorkflowDesignerWindow(QDialog):
    def __init__(self, doclink: DoclinkManager):
        super().__init__()

        self.setWindowTitle("Workflow Designer")
        self.setGeometry(150, 150, _DEF_WDW_SZ_X, _DEF_WDW_SZ_Y)

        scene_manager = WorkflowSceneManager(doclink)
        sceneDict = scene_manager.graphicScenes #scene_manager.build_scenes()
        wfSceneDict = scene_manager.wfSceneDict
        
        # Create mapping from workflow titles to WorkflowKeys
        self.title_to_key_map = {}
        for workflow in scene_manager.workflows:
            key = str(workflow.WorkflowKey)
            self.title_to_key_map[workflow.Title] = key
            print(f"Mapping: '{workflow.Title}' -> {key}")

        main_splitter = QSplitter(Qt.Horizontal)

        self.drawing_area = DrawingWidget(sceneDict, wfSceneDict)
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
        main_splitter.setSizes([_DEF_WDW_SZ_X - 200, 200]) # Need to add defaults for this
        
        layout = QVBoxLayout()
        layout.addWidget(main_splitter)
        self.setLayout(layout)

    def workflow_list(self, workflows) -> QListView:
        workflow_str = [workflow.Title for workflow in workflows]
        workflow_model = QStringListModel(workflow_str) 
        workflow_list = QListView()
        workflow_list.setModel(workflow_model)
        workflow_list.setSelectionMode(QListView.SingleSelection)
        workflow_list.clicked.connect(self.change_workflow)

        return workflow_list

    def change_workflow(self, index):
        workflow_title = index.data()
        print(f"User selected workflow: '{workflow_title}'")
        
        # Convert title to WorkflowKey using the mapping
        if workflow_title in self.title_to_key_map:
            workflow_key = self.title_to_key_map[workflow_title]
            print(f"Mapped to key: {workflow_key}")
            self.drawing_area.change_workflow(workflow_key)
            print(f"Successfully switched to workflow: '{workflow_title}'")
        else:
            print(f"Error: No workflow found for title '{workflow_title}'")
