from dataclasses import dataclass
from enum import Enum
from typing import Optional, TypedDict

from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem

from doclink_py.doclink_types.doclink_type_utilities import get_object_from_list
from doclink_py.doclink_types.workflows import Workflow, WorkflowPlacement
from workflow_designer.wfd_objects import Link, Node, Rect, WFDLineSegments
from workflow_designer.wfd_shape import Shape, ShapeEllipse, ShapeRect
from workflow_designer.wfd_xml import createObjectListFromXMLString

class EntityType(Enum):
    WORKFLOW = 1
    STATUS = 2

# Should move to wfd_xml
class XMLObject(TypedDict):
    nodes: list[Node]
    links: list[Link]

class BaseWFNodeObject:
    def __init__(self):
        self.rect: Optional[Rect] = None

        self.graphicsItem: Optional[QGraphicsItem] = None

class WFEntity:
    def __init__(self, entityKey, entityType):
        self.entityKey = entityKey
        self.entityType: EntityType = entityType

        self.shape: Optional[Shape] = None

        self.sourceKeys: list = []
        self.destKeys: list = []
        self.sourceLines: list = []
        self.destLines: list = []

# I think I shouldn't extend WFEntity and should use composition but whatever
class WFWorkflow(WFEntity):
    def __init__(self, entityKey, title: str, statuses: list[str], rect: Rect):
        super().__init__(entityKey, EntityType.WORKFLOW)

        self.statuses = statuses
        self.statusItems: dict[str, QGraphicsTextItem] = {}

        # This should read off nodeRect info to determine if square or circle
        self.shape = ShapeRect(rect)

class WFStatus(WFEntity):
    def __init__(self, entityKey, title: str, rect: Rect):
        super().__init__(entityKey, EntityType.STATUS)

        self.title = title

        # This should read off nodeRect info to determine if square or circle
        self.shape = ShapeEllipse(rect)

class WFScene:
    def __init__(self, dlPlacement: WorkflowPlacement, sceneWorkflow: Workflow):
        self.sceneWorkflow: Workflow = sceneWorkflow
        self.dlPlacement: WorkflowPlacement = dlPlacement

        self.workflows: list[WFWorkflow] = [] 
        self.statuses: list[WFStatus] = [] 

        nodes, links = createObjectListFromXMLString(self.dlPlacement.LayoutData)
        self.xmlObjects: XMLObject = { 
                'nodes': nodes,
                'links':links 
            }

        self.createEntitiesFromXML()

    def createEntitiesFromXML(self):
        for node in self.xmlObjects['nodes']:
            nodeKey = node.nodeAttribs["LayoutNode"]["Key"]

            if node.nodeAttribs["LayoutNode"]["Type"] == 'Status':
                if get_object_from_list(self.statuses, "entityKey", nodeKey):
                    input("Error: node key already in statuses dict")

                # Needs to be implemented
                self.statuses.append(convertStatusFromXML(node))

            elif node.nodeAttribs["LayoutNode"]["Type"] == 'Workflow':
                if get_object_from_list(self.workflows, "entityKey", nodeKey):
                    input("Error: node key already in workflows dict")

                self.workflows.append(convertWorkflowFromXML(node))

                # We need to add statusesç:w

            else:
                input("Warning: unknown node type:" + node.nodeAtrribs["LayoutNode"]["Type"])

@dataclass
class WFDScene:
    statuses: dict
    workflows: dict
    workflowStatuses: dict
    links: dict
    linkPoints: list[tuple]
    points: list[WFDLineSegments]

# Needs to be implemented
def convertStatusFromXML(node: Node) -> WFStatus:
    return WFStatus(
            node.nodeAttribs["LayoutNode"]["Key"],
            node.nodeProps["Text"],
            node.nodeRect
        )


def convertWorkflowFromXML(node: Node) -> WFWorkflow:
    return WFWorkflow(
            node.nodeAttribs["LayoutNode"]["Key"],
            node.nodeAttribs["LayoutNode"]["Tooltip"],
            [],
            node.nodeRect
        )

