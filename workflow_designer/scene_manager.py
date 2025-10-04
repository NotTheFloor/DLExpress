from typing import Any 

from workflow_designer.wfd_scene import EntityType, WFScene
from workflow_designer.wfd_logger import logger

from doclink_py.models.workflows import Workflow, WorkflowActivity, WorkflowPlacement
from doclink_py.models.doclink_type_utilities import *   

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem 

from workflow_designer.wfd_entity_factory import create_doclink_status_from_data

DEF_NEW_WF_X = 10
DEF_NEW_WF_Y = 10

SQL_ENABLED = True

class WorkflowSceneManager(QObject):
    sceneSelectionChanged = Signal()

    def __init__(self, doclink, parent=None):
        super().__init__(parent)

        self.doclink = doclink

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

            self.current_workflow_key = None

            self.createScenes()
            self.buildGraphicsScenes()
            
            logger.info("WorkflowSceneManager initialization complete")
        except Exception as e:
            logger.critical(f"Failed to initialize WorkflowSceneManager: {e}")
            raise

    def handle_connection_creations(self, link_data, workflow_key):

        source = link_data['source']
        dest = link_data['target']
        source_is_external = True

        target_wf = None
        old_status_line = None
        old_status = None
        source_wf_key = None
        dest_wf_key = None
        if source['type'] == 'workflow_status_line':
            target_wf = source['entity']
            old_status_line = source
            old_status = dest
            source_wf_key = target_wf.entityKey.upper()
            dest_wf_key = workflow_key.upper()
        elif dest['type'] == 'workflow_status_line':
            source_is_external = False
            target_wf = dest['entity']
            old_status_line = dest
            old_status = source
            dest_wf_key = target_wf.entityKey.upper()
            source_wf_key = workflow_key.upper()
        else:
            # Within workflow so should always be called
            if SQL_ENABLED:
                logger.debug("Creating WorkflowNextActivity in DocLink")
                source_dl_status = get_object_from_list(self.statuses, "WorkflowActivityKey", source['key'].upper())
                if not source_dl_status:
                    logger.error(f"Failed to retrieve status by key from internal list. Key: {source['key']}")
                    return
                self.doclink.workflow_manager.add_workflow_next_acitivty(source_dl_status.WorkflowActivityID, dest['key'], wfna_key=link_data['id'])
                return

            logger.info("Status created within WF and SQL not enabled; Doing nothing")
            return

        if target_wf.entityType != EntityType.WORKFLOW:
            logger.error("target_wf is not type WORKFLOW")
            return

        target_scene = self.wfSceneDict[target_wf.entityKey.upper()]

        new_status = None
        print(f"--- {target_scene.sceneWorkflow.Title} ---")
        print(old_status_line['key'].upper())
        for status in target_scene.statuses:
            print(status.entityKey)
            if status.entityKey.upper() == old_status_line['key'].upper():
                new_status = status
                break

        if new_status is None:
            logger.error("Status inferred from status line not found in workflow")
            return

        new_workflow = None
        new_wf_status_line = None
        for workflow in target_scene.workflows:
            if workflow.entityKey.upper() == workflow_key.upper():
                new_workflow = workflow
                print("we at least found the workflow")
                print(old_status['key'])
                for status_line in workflow.status_lines:
                    print(status_line.status_key)
                    if status_line.status_key.upper() == old_status['key'].upper():
                        new_wf_status_line = status_line

        if new_wf_status_line is None:
            logger.error("Status line inferred from status not found in workflow")
            return

        if SQL_ENABLED:
            logger.debug("Adding external link")
            self.doclink.workflow_manager.add_wf_external_link(source_wf_key, source['key'], dest_wf_key, dest['key'], wf_ext_key=link_data['id'])

        if source_is_external:
            target_scene.create_connections_visual([new_status], new_wf_status_line, propogate=False, fixed_id=link_data['id'])
        else:
            target_scene.create_connections_visual([new_wf_status_line], new_status, propogate=False, fixed_id=link_data['id'])

        target_scene._refresh_graphics_scene()

    def handle_existing_workflow(self, workflow, dest_key, orig_key):

        logger.debug(f"Reciprocating workflow addition from {self.wfSceneDict[orig_key].sceneWorkflow.Title} to {self.wfSceneDict[dest_key].sceneWorkflow.Title}")

        self.wfSceneDict[dest_key].add_existing_workflow_visual((DEF_NEW_WF_X, DEF_NEW_WF_Y), orig_key, False)
        self.wfSceneDict[dest_key]._refresh_graphics_scene()
    
    def handle_new_status(self, status, workflow_key):

        wfa = create_doclink_status_from_data(status, 
                                              self.wfSceneDict[workflow_key].sceneWorkflow.WorkflowID,
                                              len(self.wfSceneDict[workflow_key].statuses) - 1
                                              )

        # Wow... that was useless
        if SQL_ENABLED:
            wfa = self.create_dl_wfa_from_our_object(wfa)

        self.statuses.append(wfa)

        logger.debug(f"Propogating new status {wfa.Title} from workflow {workflow_key}")
        for wf_key, scene in self.wfSceneDict.items():
            # Ignore self
            if wf_key == workflow_key:
                continue

            for wf in scene.workflows:
                if wf.entityKey.upper() == workflow_key.upper():
                    logger.debug(f"Adding status {wfa.Title} to {wf.title}")
                    wf.add_new_status_line(wfa)

    def create_dl_wfa_from_our_object(self, wfa) -> WorkflowActivity:
        logger.info(f"Adding workflow status {wfa.Title} to WF with ID {wfa.WorkflowID}")

        print(f"---- {wfa.WorkflowActivityKey}")
        new_wfa = self.doclink.workflow_manager.add_workflow_activity(wfa.WorkflowID, 
                                                            wfa.Title, None, 
                                                            wfa.Seq, wfa.WorkflowActivityKey)

        if not new_wfa:
            logger.error("Could not create new workflow status")
            return

        return new_wfa

    def handle_update_layout(self, wf_id, xml_data):
        logger.debug(f"Placement update for {wf_id}")

        #print(xml_data)
        if SQL_ENABLED:
            xml_data = '<?xml version="1.0" encoding="utf-16"?>\n<!--AddFlow.net diagram-->\n' + xml_data
            self.doclink.workflow_manager.update_wf_placement_by_wf_id(wf_id, xml_data)

    def get_current_workflow(self):
        if self.current_workflow_key:
            return self.wfSceneDict[self.current_workflow_key]

        logger.error(f"Error: Attempted to return workflow before current workflow key assigned")
        return None

    def change_current_workflow(self, new_key):
        if new_key not in self.wfSceneDict.keys():
            print("Keys")
            for k in self.wfSceneDict.keys():
                print(k)
            logger.error(f"Error: key {new_key} does not exist in workflow maps")

        logger.debug(f"Setting current workflow to: {new_key}")
        self.current_workflow_key = new_key

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
                    scene.graphics_scene = new_scene
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
                    print(f"Creating scene for workflow {wf.Title}")
                    print(placement.LayoutData[0:100])
                    wf_scene = WFScene(placement, wf, self)
                    print("Created wf_scene")
                    wf_scene.new_status.connect(self.handle_new_status)
                    wf_scene.existing_workflow.connect(self.handle_existing_workflow)
                    wf_scene.connection_created.connect(self.handle_connection_creations)
                    wf_scene.update_layout.connect(self.handle_update_layout)
                    self.newScenes.append(wf_scene)
                    # Store reference by WorkflowKey for later access
                    print("about to store key")
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



