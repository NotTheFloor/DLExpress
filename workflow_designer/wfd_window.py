from PySide6.QtWidgets import QDialog, QFormLayout, QGroupBox, QLabel, QLineEdit, QSplitter, QTextEdit, QVBoxLayout, QListView, QWidget
from PySide6.QtCore import Qt, QStringListModel

from workflow_designer.wfd_scene import WFScene

from .wfd_drawing_widget import DrawingWidget
from .wfd_objects import Node as WFN
from .scene_manager import WorkflowSceneManager
from .wfd_logger import logger

from doclink_py.sql.manager.doclink_manager import DoclinkManager
from doclink_py.models.workflows import Workflow

_DEF_WDW_SZ_X = 1600
_DEF_WDW_SZ_Y = 900
_DEF_T_RP_Y = 600
_DEF_B_RP_Y = 280

class BRTTopWorkflow(QWidget):
    def __init__(self, fixed_height=None, parent=None):
        super().__init__(parent)

        self.title = QLineEdit()
        self.cat = QLineEdit()

        gb = QGroupBox("Workflow Options", self)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)        
        form.setVerticalSpacing(1)
        if fixed_height:
            gb.setFixedHeight(fixed_height)
        gb.setLayout(form)

        form.addRow(QLabel('Title'))
        form.addRow(self.title)
        form.addRow(QLabel('Catagory'))
        form.addRow(self.cat)

    def populate(self, workflow: WFScene):
        self.title.setText(workflow.sceneWorkflow.Title)
        #self.cat.setText(workflow.Catagory)
        
class WorkflowDesignerWindow(QDialog):
    def __init__(self, doclink: DoclinkManager):
        super().__init__()

        self.setWindowTitle("Workflow Designer")
        self.setGeometry(150, 150, _DEF_WDW_SZ_X, _DEF_WDW_SZ_Y)

        self.scene_manager = WorkflowSceneManager(doclink)
        sceneDict = self.scene_manager.graphicScenes #scene_manager.build_scenes()
        wfSceneDict = self.scene_manager.wfSceneDict
        
        # Create mapping from workflow titles to WorkflowKeys
        self.title_to_key_map = {}
        for workflow in self.scene_manager.workflows:
            key = str(workflow.WorkflowKey)
            self.title_to_key_map[workflow.Title] = key
            print(f"Mapping: '{workflow.Title}' -> {key}")

        main_splitter = QSplitter(Qt.Horizontal)

        # Pass the first workflow key in original order for consistent initial display
        first_workflow_key = str(self.scene_manager.workflows[0].WorkflowKey) if self.scene_manager.workflows else None
        self.drawing_area = DrawingWidget(sceneDict, wfSceneDict, first_workflow_key)
        main_splitter.addWidget(self.drawing_area)

        right_pane = QSplitter(Qt.Vertical)

        #top_right = QTextEdit("Top right place holder")
        top_right = self.workflow_list(self.scene_manager.workflows)
        top_right.setFixedHeight(_DEF_T_RP_Y)

        self.bottom_right = BRTTopWorkflow(_DEF_B_RP_Y) #QTextEdit("Bottom right place holder")
        self.bottom_right.setFixedHeight(_DEF_B_RP_Y)

        right_pane.addWidget(top_right)
        right_pane.addWidget(self.bottom_right)

        main_splitter.addWidget(right_pane)
        main_splitter.setSizes([_DEF_WDW_SZ_X - 200, 200]) # Need to add defaults for this
        
        layout = QVBoxLayout()
        layout.addWidget(main_splitter)
        self.setLayout(layout)

        self.bottom_right.populate(self.scene_manager.get_current_workflow())

        self.scene_manager.sceneSelectionChanged.connect(self.handle_scene_selection_change)

    def handle_scene_selection_change(self):
        #self.
        logger.debug("Top level scene seleciton changed")        

    def workflow_list(self, workflows) -> QListView:
        workflow_str = [workflow.Title for workflow in workflows]
        workflow_model = QStringListModel(workflow_str) 
        workflow_list = QListView()
        workflow_list.setModel(workflow_model)
        workflow_list.setSelectionMode(QListView.SingleSelection)
        workflow_list.clicked.connect(self.change_workflow)

        self.scene_manager.change_current_workflow(self.title_to_key_map[workflow_str[0]])

        return workflow_list

    def change_workflow(self, index):
        workflow_title = index.data()
        print(f"User selected workflow: '{workflow_title}'")
        
        # Convert title to WorkflowKey using the mapping
        if workflow_title in self.title_to_key_map:
            workflow_key = self.title_to_key_map[workflow_title]
            logger.debug(f"Mapped to key: {workflow_key}")
            self.scene_manager.change_current_workflow(workflow_key)
            self.drawing_area.change_workflow(workflow_key)
            self.bottom_right.populate(self.scene_manager.get_current_workflow())
            logger.debug(f"Successfully switched to workflow: '{workflow_title}'")
        else:
            logger.error(f"Error: No workflow found for title '{workflow_title}'")

