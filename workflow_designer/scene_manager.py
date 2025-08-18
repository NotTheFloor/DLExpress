from typing import Any 

from workflow_designer.wfd_scene import WFScene
from workflow_designer.wfd_logger import logger

from doclink_py.models.workflows import Workflow, WorkflowActivity, WorkflowPlacement
from doclink_py.models.doclink_type_utilities import *   

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem 

class WorkflowSceneManager(QObject):
    sceneSelectionChanged = Signal()

    def __init__(self, doclink, parent=None):
        super().__init__(parent)

        try:
            logger.info("Initializing WorkflowSceneManager")
            
            self.workflows: list[Workflow] = []
            self.workflows = doclink.workflow_manager.get_workflows()
            logger.info(f"Loaded {len(self.workflows)} workflows")

            self.statuses: list[WorkflowActivity]
            self.statuses = doclink.workflow_manager.get_workflow_activities()
            logger.info(f"Loaded {len(self.statuses)} workflow activities")

            self.workflowStatuses: dict[str, list[str]] = {}
            
            for wfs in self.workflows:
                try:
                    status_sequence = self.getStatusSequence(str(wfs.WorkflowKey))
                    self.workflowStatuses[str(wfs.WorkflowKey)] = [st.Title for st in status_sequence]
                except Exception as e:
                    logger.error(f"Error getting status sequence for workflow {wfs.WorkflowKey}: {e}")
                    self.workflowStatuses[str(wfs.WorkflowKey)] = []

            self.placements: list[WorkflowPlacement] = []
            self.placements = doclink.workflow_manager.get_workflow_placements()
            logger.info(f"Loaded {len(self.placements)} workflow placements")

            self.graphicScenes: dict[str, Any] = {}
            self.newScenes: list[WFScene] = []
            self.wfSceneDict: dict[str, WFScene] = {}  # Map of WorkflowKey -> WFScene

            self.createScenes()
            self.buildGraphicsScenes()
            
            logger.info("WorkflowSceneManager initialization complete")
        except Exception as e:
            logger.critical(f"Failed to initialize WorkflowSceneManager: {e}")
            raise

    def _sceneSelectionChanged(self, wfKey, selectionSet):
        logger.debug(f"Scene selection change for workflow key {wfKey}")
        self.sceneSelectionChanged.emit()

    def getStatusSequence(self, workflowKey: str) -> list:
        """Gets all statuses from a workflow sorted by suequence numbers"""

        workflow = get_object_from_list(self.workflows, "WorkflowKey", workflowKey.upper())
        if not workflow:
            raise ValueError(f"No workflow found with key: {workflowKey}")

        workflowID = workflow.WorkflowID
        statusList = get_all_objects_from_list(self.statuses, "WorkflowID", workflowID)

        statusList = sorted(statusList, key=lambda x: x.Seq)

        return statusList

    def buildGraphicsScenes(self):
        logger.info("Building graphics scenes")
        try:
            for scene in self.newScenes:
                try:
                    new_scene = QGraphicsScene()
                    scene_key = str(scene.sceneWorkflow.WorkflowKey)
                    logger.debug(f"Building scene for workflow {scene_key}")

                    # Add workflow and status entities
                    for ent in scene.workflows + scene.statuses:
                        try:
                            new_scene.addItem(ent.shape.graphicsItem)
                        except Exception as e:
                            logger.error(f"Error adding entity {ent.entityKey} to scene: {e}")
                    
                    # Add line segments and nodes
                    for line in scene.lines:
                        try:
                            # Get all graphics items (including nodes)
                            all_items = line.get_all_graphics_items() if hasattr(line, 'get_all_graphics_items') else line.lineSegments
                            
                            for item in all_items:
                                # Handle both wrapped objects and raw Qt items
                                if hasattr(item, 'graphicsItem'):
                                    new_scene.addItem(item.graphicsItem)
                                else:
                                    # Direct Qt graphics item (like arrow polygons and nodes)
                                    new_scene.addItem(item)
                        except Exception as e:
                            logger.error(f"Error adding line segments to scene: {e}")
                    
                    self.graphicScenes[scene_key] = new_scene
                    logger.debug(f"Successfully built scene for workflow {scene_key}")
                    
                except Exception as e:
                    logger.error(f"Error building scene for workflow {scene.sceneWorkflow.WorkflowKey}: {e}")
                    continue
                    
            logger.info(f"Successfully built {len(self.graphicScenes)} graphics scenes")
        except Exception as e:
            logger.critical(f"Failed to build graphics scenes: {e}")
            raise
                

    def createScenes(self):
        """Converts placement data into objects and in a dict with WF Title as key"""
        logger.info("Creating workflow scenes")
        
        try:
            for placement in self.placements:
                try:
                    wf = get_object_from_list(self.workflows, "WorkflowID", placement.WorkflowID)
                    if wf is None:
                        logger.error(f"No workflow found for placement WorkflowID: {placement.WorkflowID}")
                        continue
                        
                    logger.debug(f"Creating scene for workflow {wf.Title}")
                    wf_scene = WFScene(placement, wf, self)
                    self.newScenes.append(wf_scene)
                    # Store reference by WorkflowKey for later access
                    scene_key = str(wf.WorkflowKey)
                    self.wfSceneDict[scene_key] = wf_scene
                    wf_scene.sceneSelectionChanged.connect(self._sceneSelectionChanged)
                    
                except Exception as e:
                    logger.error(f"Error creating scene for placement {placement.WorkflowID}: {e}")
                    continue
                    
            logger.info(f"Successfully created {len(self.newScenes)} workflow scenes")
        except Exception as e:
            logger.critical(f"Failed to create scenes: {e}")
            raise



