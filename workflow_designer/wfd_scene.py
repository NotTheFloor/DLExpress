from dataclasses import dataclass
from enum import Enum
from typing import Optional, TypedDict

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontMetrics, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsLineItem, QGraphicsRectItem

from doclink_py.doclink_types.doclink_type_utilities import get_object_from_list
from doclink_py.doclink_types.workflows import Workflow, WorkflowPlacement
from workflow_designer.wfd_objects import Link, Node, Rect, WFDFont, WFDLineSegments
from workflow_designer.wfd_shape import Shape, ShapeEllipse, ShapeRect
from workflow_designer.wfd_xml import createObjectListFromXMLString

DEF_TTL_X_PAD = 1
DEF_TTL_Y_PAD = 2
DEF_ITM_X_PAD = 2
DEF_ITM_Y_PAD = 2

class EntityType(Enum):
    WORKFLOW = 1
    STATUS = 2

# Should move to wfd_xml
class XMLObject(TypedDict):
    nodes: list[Node]
    links: list[Link]


DEFAULT_FONT = WFDFont(
            'Arial',
            9.0,
            False,
            False,
            False,
            False
        )


class BaseWFNodeObject:
    def __init__(self):
        self.rect: Optional[Rect] = None

        self.graphicsItem: Optional[QGraphicsItem] = None

class WFEntity:
    def __init__(self, entityKey, entityType):
        self.entityKey = entityKey
        self.entityType: EntityType = entityType

        self.shape: Optional[Shape] = None
        self.textItems: list[QGraphicsTextItem] = []

        self.sourceKeys: list = []
        self.destKeys: list = []
        self.sourceLines: list = []
        self.destLines: list = []

# I think I shouldn't extend WFEntity and should use composition but whatever
class WFWorkflow(WFEntity):
    def __init__(self, entityKey, title: str, statuses: list[str], rect: Rect, titleFont: Optional[WFDFont] = None):
        super().__init__(entityKey, EntityType.WORKFLOW)

        self.title = title
        self.statuses = statuses
        # self.statusItems: dict[str, QGraphicsTextItem] = {}

        # This should read off nodeRect info to determine if square or circle
        self.shape = ShapeRect(rect)
        
        # Create title
        titleItem = QGraphicsTextItem(title, parent=self.shape.graphicsItem)
        if titleFont:
            titleItem.setFont(createFontFromWFDFont(titleFont))
        titleItem.setDefaultTextColor(Qt.red)
        titleItem.setPos(1, 1)
        self.shape.graphicsItem.setZValue(0)
        titleItem.setZValue(2)

        self.textItems.append(titleItem)

class WFStatus(WFEntity):
    def __init__(self, entityKey, title: str, rect: Rect, titleFont: Optional[WFDFont] = None):
        super().__init__(entityKey, EntityType.STATUS)

        self.title = title

        # This should read off nodeRect info to determine if square or circle
        self.shape = ShapeEllipse(rect)

        titleItem = QGraphicsTextItem(title, parent=self.shape.graphicsItem)
        
        if titleFont:
            titleItem.setFont(createFontFromWFDFont(titleFont))
        titleItem.setDefaultTextColor(Qt.red)

        centerTextItem(titleItem, 
                       self.shape.graphicsItem.boundingRect().width(),
                       self.shape.graphicsItem.boundingRect().height())


        self.shape.graphicsItem.setZValue(0)
        titleItem.setZValue(2)

        self.textItems.append(titleItem)

class WFScene:
    def __init__(self, dlPlacement: WorkflowPlacement, sceneWorkflow: Workflow, statusInfo: dict[str, list[str]]):
        self.sceneWorkflow: Workflow = sceneWorkflow
        self.dlPlacement: WorkflowPlacement = dlPlacement
        self.statusInfo = statusInfo

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

                self.workflows.append(convertWorkflowFromXML(node, self.statusInfo[nodeKey.upper()]))

                # We need to add statuses

            else:
                input("Warning: unknown node type:" + node.nodeAttribs["LayoutNode"]["Type"])

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
    font = DEFAULT_FONT
    if 'Font' in node.nodeAttribs:
        font = WFDFont(**node.nodeAttribs['Font'])
    return WFStatus(
            node.nodeAttribs["LayoutNode"]["Key"],
            node.nodeProps["Text"],
            node.nodeRect,
            font
        )


def convertWorkflowFromXML(node: Node, statuses: list[str]) -> WFWorkflow:
    font = DEFAULT_FONT
    if 'Font' in node.nodeAttribs:
        font = WFDFont(**node.nodeAttribs['Font'])
    return WFWorkflow(
            node.nodeAttribs["LayoutNode"]["Key"],
            node.nodeAttribs["LayoutNode"]["Tooltip"],
            statuses,
            node.nodeRect,
            font
        )

def createFontFromWFDFont(wfdFont):
    font = QFont(wfdFont.Name, int(round(float(wfdFont.Size))))
    font.setBold(wfdFont.Bold=='True')
    font.setItalic(wfdFont.Italic=='True')
    font.setUnderline(wfdFont.Underline=='True')
    font.setStrikeOut(wfdFont.Strikeout=='True')
    return font

def centerTextItem(textItem: QGraphicsTextItem, width, height):
    metrics = QFontMetrics(textItem.font())
    xPadding = (textItem.boundingRect().width() - metrics.horizontalAdvance(textItem.toPlainText())) / 2
    yPadding = (textItem.boundingRect().height() - metrics.height()) / 2
    dX = (width / 2) - (metrics.horizontalAdvance(textItem.toPlainText()) / 2) - xPadding
    dY = (height / 2) - (metrics.height() / 2) - yPadding #- metrics.ascent() - (metrics.xHeight()/2)
    textItem.setPos(dX, dY)
