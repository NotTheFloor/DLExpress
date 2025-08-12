from dataclasses import dataclass
from enum import Enum
from typing import Optional, TypedDict, TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPen, QBrush
from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsLineItem, QGraphicsRectItem

from doclink_py.models.doclink_type_utilities import get_object_from_list
from doclink_py.models.workflows import Workflow, WorkflowPlacement

from workflow_designer.wfd_objects import Link, Node, Rect, WFDFont, WFDLineSegments
from workflow_designer.wfd_shape import Shape, ShapeEllipse, ShapeLine, ShapeRect
from workflow_designer.wfd_utilities import addArrowToLineItem, SmartArrow, MultiSegmentArrow
from workflow_designer.wfd_selection_manager import SelectionManager
from workflow_designer.wfd_xml import createObjectListFromXMLString

if TYPE_CHECKING:
    from workflow_designer.scene_manager import WorkflowSceneManager

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
        
        # Selection manager will be set when entity is added to scene
        self._selection_manager = None
    
    def set_selection_manager(self, selection_manager):
        """Set the selection manager for this entity"""
        self._selection_manager = selection_manager
        
        # Connect click events to selection
        if self.shape:
            self.shape.clicked.connect(lambda: self._handle_click())
    
    def _handle_click(self):
        """Handle entity click - select this entity"""
        if self._selection_manager:
            self._selection_manager.select_item(self)

# I think I shouldn't extend WFEntity and should use composition but whatever
class WFWorkflow(WFEntity):
    def __init__(self, entityKey, title: str, statuses: list[str], rect: Rect, titleFont: Optional[WFDFont] = None, fillColor=None, drawColor=None):
        super().__init__(entityKey, EntityType.WORKFLOW)

        self.title = title
        self.statuses = statuses

        # This should read off nodeRect info to determine if square or circle
        self.shape = ShapeRect(rect, fillColor=fillColor, drawColor=drawColor)
        
        # Create title
        titleItem = QGraphicsTextItem(title, parent=self.shape.graphicsItem)
        if titleFont:
            titleItem.setFont(createFontFromWFDFont(titleFont))
        titleItem.setDefaultTextColor(Qt.red)
        titleItem.setPos(0, 0)
        self.textItems.append(titleItem)
        yPadding = (titleItem.boundingRect().height() - QFontMetrics(titleItem.font()).height()) / 2

        for i, statusLine in enumerate(self.statuses):
            statusItem = QGraphicsTextItem(statusLine, parent=self.shape.graphicsItem)

            if titleFont:
                statusItem.setFont(createFontFromWFDFont(titleFont))

            statusItem.setPos(DEF_ITM_X_PAD, (titleItem.boundingRect().height() - yPadding) * (i+1))
            statusItem.setZValue(2)
            
            self.textItems.append(statusItem)

        self.shape.graphicsItem.setZValue(0)
        titleItem.setZValue(2)


class WFStatus(WFEntity):
    def __init__(self, entityKey, title: str, rect: Rect, titleFont: Optional[WFDFont] = None, fillColor=None, drawColor=None):
        super().__init__(entityKey, EntityType.STATUS)

        self.title = title

        # This should read off nodeRect info to determine if square or circle
        self.shape = ShapeEllipse(rect, fillColor=fillColor, drawColor=drawColor)

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

class WFLineGroup:
    def __init__(self, srcEntity: WFEntity, dstEntity: WFEntity, linkData: Link = None):
        self.srcEntity = srcEntity
        self.dstEntity = dstEntity
        self.linkData = linkData

        self.lineSegments: list = []  # Will contain both ShapeLine and graphics items

        # Extract waypoints from XML Point elements
        waypoints = self._extractWaypoints()

        # Always use MultiSegmentArrow for consistent interactive node support
        # MultiSegmentArrow handles the case of 0 waypoints correctly
        self.arrow = MultiSegmentArrow(srcEntity, dstEntity, waypoints)
        # Add all graphics items from multi-segment arrow
        self.lineSegments.extend(self.arrow.getGraphicsItems())
    
    def set_selection_manager(self, selection_manager):
        """Set the selection manager for the arrow"""
        if hasattr(self.arrow, 'set_selection_manager'):
            self.arrow.set_selection_manager(selection_manager)
        
        # Create node manager for MultiSegmentArrow
        if hasattr(self.arrow, 'create_node_manager'):
            from workflow_designer.wfd_selection_manager import ThemeDetector
            selection_color = ThemeDetector.get_selection_color()
            node_manager = self.arrow.create_node_manager(selection_color)
    
    def get_all_graphics_items(self):
        """Get all graphics items including line segments and nodes"""
        items = self.lineSegments.copy()
        
        # Add node graphics items if they exist
        if hasattr(self.arrow, 'get_node_graphics_items'):
            items.extend(self.arrow.get_node_graphics_items())
            
        return items
    
    def _extractWaypoints(self) -> list[tuple[float, float]]:
        """Extract waypoint coordinates from XML Point elements"""
        waypoints = []
        
        if self.linkData and 'Point' in self.linkData.linkAttribs:
            points = self.linkData.linkAttribs['Point']
            for point in points:
                try:
                    x = float(point['X'])
                    y = float(point['Y'])
                    waypoints.append((x, y))
                except (KeyError, ValueError) as e:
                    from workflow_designer.wfd_logger import logger
                    logger.warning(f"Invalid point data in link: {point}, error: {e}")
                    
        return waypoints

class WFScene:
    def __init__(self, dlPlacement: WorkflowPlacement, sceneWorkflow: Workflow, sceneManager: "WorkflowSceneManager"):
        self.sceneWorkflow: Workflow = sceneWorkflow
        self.dlPlacement: WorkflowPlacement = dlPlacement
        self.sceneManager = sceneManager

        self.workflows: list[WFWorkflow] = [] 
        self.statuses: list[WFStatus] = [] 
        self.lines: list[WFLineGroup] = []
        
        # Create selection manager for this scene
        self.selection_manager = SelectionManager()

        nodes, links = createObjectListFromXMLString(self.dlPlacement.LayoutData)
        self.xmlObjects: XMLObject = { 
                'nodes': nodes,
                'links':links 
            }

        self.createEntitiesFromXML()
        self._connectSelectionManager()

    def getWorkflowByKey(self, key) -> Optional[WFWorkflow]:
        return get_object_from_list(self.workflows, "entityKey", key)

    def getStatusByKey(self, key) -> Optional[WFStatus]:
        return get_object_from_list(self.statuses, "entityKey", key)

    def getEntityByKey(self, key) -> Optional[WFEntity]:
        foundStatus = self.getStatusByKey(key)
        if foundStatus:
            return foundStatus

        return self.getWorkflowByKey(key)

    def createEntitiesFromXML(self):
        for node in self.xmlObjects['nodes']:
            nodeKey = node.nodeAttribs["LayoutNode"]["Key"]

            if node.nodeAttribs["LayoutNode"]["Type"] == 'Status':
                if get_object_from_list(self.statuses, "entityKey", nodeKey):
                    raise ValueError(f"Duplicate node key in statuses: {nodeKey}")

                # Needs to be implemented
                self.statuses.append(convertStatusFromXML(node))

            elif node.nodeAttribs["LayoutNode"]["Type"] == 'Workflow':
                if get_object_from_list(self.workflows, "entityKey", nodeKey):
                    raise ValueError(f"Duplicate node key in workflows: {nodeKey}")

                self.workflows.append(convertWorkflowFromXML(node, self.sceneManager.workflowStatuses[nodeKey.upper()]))

                # We need to add statuses

            else:
                raise ValueError(f"Unknown node type: {node.nodeAttribs['LayoutNode']['Type']}")


        for link in self.xmlObjects['links']:
            orgKey = link.linkAttribs["LayoutLink"]["OrgKey"]
            dstKey = link.linkAttribs["LayoutLink"]["DstKey"]
            orgEntity = self.getEntityByKey(orgKey)
            dstEntity = self.getEntityByKey(dstKey)

            if orgEntity is None:
                wfActivity = get_object_from_list(self.sceneManager.statuses, "WorkflowActivityKey", str(orgKey).upper())
                if wfActivity:
                    orgEntity = self.getWorkflowByKey(
                        str(get_object_from_list(
                            self.sceneManager.workflows, 
                            "WorkflowID", 
                            wfActivity.WorkflowID
                        ).WorkflowKey).lower())
                
            if dstEntity is None:
                wfActivity = get_object_from_list(self.sceneManager.statuses, "WorkflowActivityKey", str(dstKey).upper())
                if wfActivity:
                    dstEntity = self.getWorkflowByKey(
                        str(get_object_from_list(
                            self.sceneManager.workflows, 
                            "WorkflowID", 
                            wfActivity.WorkflowID
                        ).WorkflowKey).lower())

            
            if orgEntity is None or dstEntity is None:
                raise ValueError(f"Invalid link entities: orgEntity={orgEntity}, dstEntity={dstEntity}")

            self.lines.append(WFLineGroup(orgEntity, dstEntity, link))
    
    def _connectSelectionManager(self):
        """Connect all entities and lines to the selection manager"""
        # Connect workflow entities
        for workflow in self.workflows:
            workflow.set_selection_manager(self.selection_manager)
        
        # Connect status entities  
        for status in self.statuses:
            status.set_selection_manager(self.selection_manager)
        
        # Connect line groups
        for line in self.lines:
            line.set_selection_manager(self.selection_manager)


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
    
    # Extract colors from XML
    fillColor = None
    if 'FillColor' in node.nodeProps:
        fillColor = parseXmlColor(node.nodeProps['FillColor'])
    
    drawColor = None  
    if 'DrawColor' in node.nodeProps:
        drawColor = parseXmlColor(node.nodeProps['DrawColor'])
    
    return WFStatus(
            node.nodeAttribs["LayoutNode"]["Key"],
            node.nodeProps["Text"],
            node.nodeRect,
            font,
            fillColor=fillColor,
            drawColor=drawColor
        )


def convertWorkflowFromXML(node: Node, statuses: list[str]) -> WFWorkflow:
    font = DEFAULT_FONT
    if 'Font' in node.nodeAttribs:
        font = WFDFont(**node.nodeAttribs['Font'])
    
    # Extract colors from XML
    fillColor = None
    if 'FillColor' in node.nodeProps:
        fillColor = parseXmlColor(node.nodeProps['FillColor'])
    
    drawColor = None
    if 'DrawColor' in node.nodeProps:
        drawColor = parseXmlColor(node.nodeProps['DrawColor'])
        
    return WFWorkflow(
            node.nodeAttribs["LayoutNode"]["Key"],
            node.nodeAttribs["LayoutNode"]["Tooltip"],
            statuses,
            node.nodeRect,
            font,
            fillColor=fillColor,
            drawColor=drawColor
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

def parseXmlColor(colorStr: str) -> QColor:
    """Convert XML color string (like '-1', '-16777216') to QColor"""
    try:
        colorInt = int(colorStr)
        if colorInt == -1:
            return QColor(Qt.white)
        elif colorInt == -16777216:
            return QColor(Qt.black)
        else:
            # Convert from signed 32-bit int to RGB
            if colorInt < 0:
                colorInt = colorInt + 2**32
            r = (colorInt >> 16) & 0xFF
            g = (colorInt >> 8) & 0xFF  
            b = colorInt & 0xFF
            return QColor(r, g, b)
    except ValueError:
        return QColor(Qt.gray)
