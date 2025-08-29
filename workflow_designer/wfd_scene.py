from dataclasses import dataclass
from enum import Enum
from typing import Optional, TypedDict, TYPE_CHECKING, Tuple, Dict, Any

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPen, QBrush
from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsLineItem, QGraphicsRectItem

from doclink_py.models.doclink_type_utilities import get_object_from_list
from doclink_py.models.workflows import Workflow, WorkflowPlacement

from workflow_designer.wfd_objects import Link, Node, Rect, WFDFont, WFDLineSegments
from workflow_designer.wfd_shape import Shape, ShapeEllipse, ShapeLine, ShapeRect
from workflow_designer.wfd_utilities import addArrowToLineItem, SmartArrow, MultiSegmentArrow
from workflow_designer.wfd_selection_manager import SelectionManager
from workflow_designer.wfd_xml import createObjectListFromXMLString
from workflow_designer.wfd_undo_system import UndoStack
from workflow_designer.wfd_logger import logger
from workflow_designer.wfd_selection_manager import ThemeDetector
from workflow_designer.wfd_undo_system import MovementTracker
from workflow_designer.wfd_entity_factory import create_status_at_position
from workflow_designer.wfd_xml_builder import add_node_to_xml_string

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


class WorkflowStatusLine(QObject):
    """Represents a selectable status line within a workflow"""
    
    def __init__(self, workflow: 'WFWorkflow', status_key: str, status_title: str, text_item, position_info: Tuple[float, float, float], parent=None):
        super().__init__(parent)
        
        self.workflow = workflow  # Parent WFWorkflow
        self.status_key = str(status_key).upper() if status_key else None
        self.status_title = status_title
        self.text_item = text_item  # QGraphicsTextItem
        self.position_info = position_info  # (x, y, height)
        self._selection_manager = None
        self._is_selected = False
        
        # Store original text color for selection feedback
        self._original_color = self.text_item.defaultTextColor()
        
    def set_selection_manager(self, selection_manager):
        """Set the selection manager for this status line"""
        self._selection_manager = selection_manager
    
    def handle_click(self, has_modifier: bool = False):
        """Handle status line click - select this status line"""
        if self._selection_manager:
            self._selection_manager.select_item(self, with_modifier=has_modifier)
    
    def set_selected(self, selected: bool):
        """Set visual selection state"""
        
        self._is_selected = selected
        if selected:
            # Highlight the text in selection color
            selection_color = ThemeDetector.get_selection_color()
            self.text_item.setDefaultTextColor(selection_color)
        else:
            # Restore original color
            self.text_item.setDefaultTextColor(self._original_color)
    
    def is_selected(self) -> bool:
        """Check if this status line is selected"""
        return self._is_selected
    
    def get_bounding_rect_in_workflow(self):
        """Get the bounding rectangle of this status line in workflow coordinates"""
        return self.text_item.boundingRect().translated(self.text_item.pos())
    
    def __str__(self):
        return f"WorkflowStatusLine(title='{self.status_title}', key='{self.status_key}')"
    
    def __repr__(self):
        return self.__str__()


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
            self.shape.clicked.connect(self._handle_click)
    
    def _handle_click(self, has_modifier: bool = False):
        """Handle entity click - select this entity"""
        if self._selection_manager:
            self._selection_manager.select_item(self, with_modifier=has_modifier)
    
    def addSourceLine(self, line: 'WFLineGroup'):
        """Add a line that originates from this entity"""
        if line not in self.sourceLines:
            self.sourceLines.append(line)
    
    def addDestLine(self, line: 'WFLineGroup'):
        """Add a line that terminates at this entity"""
        if line not in self.destLines:
            self.destLines.append(line)
    
    def removeSourceLine(self, line: 'WFLineGroup'):
        """Remove a line that originates from this entity"""
        if line in self.sourceLines:
            self.sourceLines.remove(line)
    
    def removeDestLine(self, line: 'WFLineGroup'):
        """Remove a line that terminates at this entity"""
        if line in self.destLines:
            self.destLines.remove(line)
    
    def getAllConnectedLines(self) -> list['WFLineGroup']:
        """Get all lines connected to this entity (both source and destination)"""
        return self.sourceLines + self.destLines

# I think I shouldn't extend WFEntity and should use composition but whatever
class WFWorkflow(WFEntity):
    def __init__(self, entityKey, title: str, statuses: list[str], rect: Rect, titleFont: Optional[WFDFont] = None, fillColor=None, drawColor=None, statusObjects: list = None):
        super().__init__(entityKey, EntityType.WORKFLOW)

        self.title = title
        self.statuses = statuses
        self.statusObjects = statusObjects or []  # Full status objects with keys
        self.status_positions = {}  # Maps statusKey -> (x, y, height)
        self.status_lines = []  # WorkflowStatusLine objects for selection

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

        # Create status text items and build position mapping
        for i, statusLine in enumerate(self.statuses):
            statusItem = QGraphicsTextItem(statusLine, parent=self.shape.graphicsItem)

            if titleFont:
                statusItem.setFont(createFontFromWFDFont(titleFont))

            y_pos = (titleItem.boundingRect().height() - yPadding) * (i+1)
            statusItem.setPos(DEF_ITM_X_PAD, y_pos)
            statusItem.setZValue(2)
            
            self.textItems.append(statusItem)
            
            # Map status key to position if we have status objects
            status_key = None
            if i < len(self.statusObjects):
                status_obj = self.statusObjects[i]
                # Get status key from WorkflowActivity object
                status_key = getattr(status_obj, 'WorkflowActivityKey', None)
                if status_key:
                    text_height = statusItem.boundingRect().height()
                    self.status_positions[str(status_key).upper()] = (DEF_ITM_X_PAD, y_pos, text_height)
            
            # Create WorkflowStatusLine object for this status
            status_line_obj = WorkflowStatusLine(
                workflow=self,
                status_key=status_key,
                status_title=statusLine,
                text_item=statusItem,
                position_info=(DEF_ITM_X_PAD, y_pos, statusItem.boundingRect().height())
            )
            self.status_lines.append(status_line_obj)

        self.shape.graphicsItem.setZValue(0)
        titleItem.setZValue(2)
        
        # Override click handling to support status line selection
        self._setup_smart_click_handling()
    
    def _setup_smart_click_handling(self):
        """Override the workflow's click handling to distinguish between status lines and workflow background"""
        if not self.shape or not self.shape.graphicsItem:
            return
            
        # Store original mouse press event
        original_mouse_press = self.shape.graphicsItem.mousePressEvent
        
        def smart_mouse_press(event):
            if event.button() == Qt.LeftButton:
                # Detect modifier keys (Ctrl on Windows/Linux, Cmd on Mac)
                modifiers = event.modifiers()
                has_modifier = bool(modifiers & (Qt.ControlModifier | Qt.MetaModifier))
                
                # Get click position relative to workflow
                local_pos = event.pos()
                
                # Check if click is on a status line
                clicked_status_line = self._find_status_line_at_position(local_pos)
                
                if clicked_status_line:
                    # Click on status line - select the status line and stop event propagation
                    clicked_status_line.handle_click(has_modifier)
                    # Don't call original handler - this prevents workflow selection from firing
                    return
                else:
                    # Click on workflow background - select the workflow
                    self._handle_click(has_modifier)
            
            # Only call original handler if we didn't handle a status line click
            original_mouse_press(event)
            
        self.shape.graphicsItem.mousePressEvent = smart_mouse_press
    
    def _find_status_line_at_position(self, local_pos) -> Optional['WorkflowStatusLine']:
        """Find which status line (if any) was clicked at the given local position"""
        # Get workflow width for expanding clickable area
        workflow_width = self.shape.graphicsItem.boundingRect().width()
        
        for status_line in self.status_lines:
            # Get the bounding rectangle of the status text item
            text_rect = status_line.text_item.boundingRect()
            text_pos = status_line.text_item.pos()
            
            # Create the absolute rectangle for the status text
            absolute_rect = text_rect.translated(text_pos)
            
            # Expand clickable area to extend nearly to the workflow width
            # Keep a small margin (DEF_ITM_X_PAD) from the right edge
            expanded_width = workflow_width - text_pos.x() - DEF_ITM_X_PAD
            expanded_rect = absolute_rect
            expanded_rect.setWidth(expanded_width)

            # Check if click position is within this expanded status line area
            if expanded_rect.contains(local_pos):
                return status_line
        
        return None
    
    def set_selection_manager(self, selection_manager):
        """Set the selection manager for this workflow and all its status lines"""
        super().set_selection_manager(selection_manager)
        
        # Set selection manager for all status lines
        for status_line in self.status_lines:
            status_line.set_selection_manager(selection_manager)
        
    def getStatusLineAttachmentPoint(self, statusKey: str) -> Optional[Tuple[float, float]]:
        """Get line attachment point for specific status within this workflow"""
        status_key_upper = str(statusKey).upper()
        
        if status_key_upper not in self.status_positions:
            # Fallback to center if status not found
            return None
            
        x, y, height = self.status_positions[status_key_upper]
        
        # Get current workflow bounds in scene coordinates
        bounds = self.shape.getCurrentBounds()
        workflow_left, workflow_top, workflow_width, workflow_height = bounds
        
        # Calculate attachment point: middle of status text line
        attachment_x = workflow_left + x + (workflow_width - DEF_ITM_X_PAD) / 2  # Use right edge for now
        attachment_y = workflow_top + y + (height / 2)  # Middle of text line
        
        return attachment_x, attachment_y
        
    def _calculateStatusPositions(self):
        """Recalculate status positions if font or layout changes"""
        # This method can be called to refresh positions if needed
        # Implementation would recalculate based on current text items
        pass


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

        # Extract status keys from link data for workflow line alignment
        self.srcStatusKey = self._extractStatusKey('OrgKey') if linkData else None
        self.dstStatusKey = self._extractStatusKey('DstKey') if linkData else None

        self.lineSegments: list = []  # Will contain both ShapeLine and graphics items

        # Extract waypoints from XML Point elements
        waypoints = self._extractWaypoints()

        # Always use MultiSegmentArrow for consistent interactive node support
        # MultiSegmentArrow handles the case of 0 waypoints correctly
        self.arrow = MultiSegmentArrow(srcEntity, dstEntity, waypoints, self.srcStatusKey, self.dstStatusKey)
        # Set back-reference so arrow can select the parent WFLineGroup
        self.arrow._parent_line_group = self
        # Add all graphics items from multi-segment arrow
        self.lineSegments.extend(self.arrow.getGraphicsItems())
        
        # Register this line with its source and destination entities for bidirectional tracking
        srcEntity.addSourceLine(self)
        dstEntity.addDestLine(self)
    
    def set_selection_manager(self, selection_manager):
        """Set the selection manager for the arrow"""
        if hasattr(self.arrow, 'set_selection_manager'):
            self.arrow.set_selection_manager(selection_manager)
        
        # Create node manager for MultiSegmentArrow
        if hasattr(self.arrow, 'create_node_manager'):
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
                    logger.warning(f"Invalid point data in link: {point}, error: {e}")
                    
        return waypoints
    
    def _extractStatusKey(self, keyType: str) -> Optional[str]:
        """Extract status key from link data (OrgKey or DstKey)"""
        if not self.linkData or keyType not in self.linkData.linkAttribs.get("LayoutLink", {}):
            return None
            
        key = self.linkData.linkAttribs["LayoutLink"][keyType]
        return str(key).upper() if key else None
    
    def setSelected(self, selected: bool, selection_color):
        """Set selection state - delegates to the contained arrow"""
        if hasattr(self.arrow, 'setSelected'):
            self.arrow.setSelected(selected, selection_color)
            # Show/hide nodes for MultiSegmentArrow
            if hasattr(self.arrow, 'show_nodes') and selected:
                self.arrow.show_nodes()
            elif hasattr(self.arrow, 'hide_nodes') and not selected:
                self.arrow.hide_nodes()
    
    def show_nodes(self):
        """Show interactive nodes - delegates to arrow"""
        if hasattr(self.arrow, 'show_nodes'):
            self.arrow.show_nodes()
    
    def hide_nodes(self):
        """Hide interactive nodes - delegates to arrow"""
        if hasattr(self.arrow, 'hide_nodes'):
            self.arrow.hide_nodes()

class WFScene(QObject):
    sceneSelectionChanged = Signal(str, set)

    def __init__(self, dlPlacement: WorkflowPlacement, sceneWorkflow: Workflow, sceneManager: "WorkflowSceneManager", parent=None):
        super().__init__(parent)

        self.sceneWorkflow: Workflow = sceneWorkflow
        self.dlPlacement: WorkflowPlacement = dlPlacement
        self.sceneManager = sceneManager

        self.workflows: list[WFWorkflow] = [] 
        self.statuses: list[WFStatus] = [] 
        self.lines: list[WFLineGroup] = []
        
        # Create selection manager for this scene
        self.selection_manager = SelectionManager()
        
        # Create undo/redo stack for this scene
        #self.undo_stack = UndoStack()
        #logger.debug(f"Created undo stack for scene: {self.sceneWorkflow.Title}")
        
        # Create movement tracker for this scene
        # UNDO ISSUES
        #self.movement_tracker = MovementTracker(self)
        logger.debug(f"Created movement tracker for scene: {self.sceneWorkflow.Title}")

        nodes, links = createObjectListFromXMLString(self.dlPlacement.LayoutData)
        self.xmlObjects: XMLObject = { 
                'nodes': nodes,
                'links':links 
            }

        self.createEntitiesFromXML()
        self._connectSelectionManager()
        self.selection_manager.selectionChanged.connect(self._selectionChanged)

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

                # Get status objects instead of just titles
                status_sequence = self.sceneManager.getStatusSequence(nodeKey)
                status_titles = [st.Title for st in status_sequence]
                self.workflows.append(convertWorkflowFromXML(node, status_titles, status_sequence))

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

    def _selectionChanged(self, selectionSet: set):
        self.sceneSelectionChanged.emit(self.sceneWorkflow.WorkflowKey, selectionSet)

    def add_new_status_visual(self, position: tuple[float, float], title: str = "New Status") -> WFStatus:
        """
        Add a new status entity to the scene visually and update XML.
        
        Args:
            position: (x, y) position tuple for the new status
            title: Title for the new status
            
        Returns:
            Created WFStatus entity
        """
        
        # Create status data using entity factory
        status_data = create_status_at_position(
            x=position[0],
            y=position[1], 
            title=title,
            workflow_key=str(self.sceneWorkflow.WorkflowKey)
        )
        
        # Convert data dict to WFStatus entity
        status_entity = self._create_status_entity_from_data(status_data)
        
        # Add to scene collections
        self.statuses.append(status_entity)
        status_entity.set_selection_manager(self.selection_manager)
        
        # Update the XML representation
        try:
            updated_xml = add_node_to_xml_string(self.dlPlacement.LayoutData, status_data)
            self.dlPlacement.LayoutData = updated_xml
            logger.debug(f"Added new status '{title}' at position {position}")
        except Exception as e:
            logger.error(f"Failed to update XML for new status: {e}")
            self.statuses.remove(status_entity)
            raise
        
        # Placeholder for database persistence
        self.save_new_status_to_database(status_data)
        
        return status_entity
    
    def add_existing_workflow_visual(self, position: tuple[float, float], workflow_key: str) -> WFWorkflow:
        """
        Add an existing workflow as a visual entity to the scene.
        
        Args:
            position: (x, y) position tuple for the workflow
            workflow_key: Key of the existing workflow to add
            
        Returns:
            Created WFWorkflow entity
        """
        
        # Get workflow info from scene manager
        workflow_info = self._get_workflow_info_by_key(workflow_key)
        if not workflow_info:
            raise ValueError(f"Workflow with key {workflow_key} not found")
        
        # Create workflow data using entity factory
        workflow_data = create_workflow_at_position(
            x=position[0],
            y=position[1],
            workflow_info=workflow_info
        )
        
        # Convert data dict to WFWorkflow entity
        workflow_entity = self._create_workflow_entity_from_data(workflow_data, workflow_info)
        
        # Add to scene collections
        self.workflows.append(workflow_entity)
        workflow_entity.set_selection_manager(self.selection_manager)
        
        # Update the XML representation
        try:
            updated_xml = add_node_to_xml_string(self.dlPlacement.LayoutData, workflow_data)
            self.dlPlacement.LayoutData = updated_xml
            logger.debug(f"Added existing workflow '{workflow_info['Title']}' at position {position}")
        except Exception as e:
            logger.error(f"Failed to update XML for existing workflow: {e}")
            self.workflows.remove(workflow_entity)
            raise
        
        # Placeholder for database persistence
        self.save_layout_to_database()
        
        return workflow_entity
    
    def _create_status_entity_from_data(self, status_data: Dict[str, Any]) -> WFStatus:
        """Convert status data dictionary to WFStatus entity"""
        # Create position rect
        pos = status_data["position"]
        rect = Rect(pos["x"], pos["y"], pos["width"], pos["height"])
        
        # Create font
        font_data = status_data["font"]
        
        # Validate font data before creating WFDFont object
        if not font_data:
            logger.error("No font data provided for status")
            font = DEFAULT_FONT
        else:
            size_value = font_data.get("Size", "8.25")
            if size_value is None:
                logger.error(f"Font size is None in status data: {font_data}")
                size_value = "8.25"
            
            font = WFDFont(
                font_data.get("Name", "Microsoft Sans Serif"),
                float(size_value),
                font_data.get("Bold", "True") == "True",
                font_data.get("Italic", "False") == "True", 
                font_data.get("Strikeout", "False") == "True",
                font_data.get("Underline", "False") == "True"
            )
        
        # Parse colors
        fillColor = parseXmlColor(status_data["properties"].get("fill_color", "-1"))
        drawColor = parseXmlColor(status_data["properties"].get("draw_color", "-16777216"))
        
        return WFStatus(
            status_data["key"],
            status_data["title"],
            rect,
            font,
            fillColor=fillColor,
            drawColor=drawColor
        )
    
    def _create_workflow_entity_from_data(self, workflow_data: Dict[str, Any], workflow_info: Dict[str, Any]) -> WFWorkflow:
        """Convert workflow data dictionary to WFWorkflow entity"""
        # Create position rect
        pos = workflow_data["position"] 
        rect = Rect(pos["x"], pos["y"], pos["width"], pos["height"])
        
        # Create font
        font_data = workflow_data["font"]
        
        # Validate font data before creating WFDFont object
        if not font_data:
            logger.error("No font data provided for workflow")
            font = DEFAULT_FONT
        else:
            size_value = font_data.get("Size", "8.25")
            if size_value is None:
                logger.error(f"Font size is None in workflow data: {font_data}")
                size_value = "8.25"
            
            font = WFDFont(
                font_data.get("Name", "Microsoft Sans Serif"),
                float(size_value),
                font_data.get("Bold", "True") == "True",
                font_data.get("Italic", "False") == "True",
                font_data.get("Strikeout", "False") == "True", 
                font_data.get("Underline", "False") == "True"
            )
        
        # Get status sequence for this workflow
        status_sequence = self.sceneManager.getStatusSequence(workflow_data["workflow_key"])
        status_titles = [st.Title for st in status_sequence]
        
        # Parse colors
        fillColor = parseXmlColor(workflow_data["properties"].get("fill_color", "-1"))
        drawColor = parseXmlColor(workflow_data["properties"].get("draw_color", "-16777216"))
        
        return WFWorkflow(
            workflow_data["key"],
            workflow_data["title"],
            status_titles,
            rect,
            font,
            fillColor=fillColor,
            drawColor=drawColor,
            statusObjects=status_sequence
        )
    
    def _get_workflow_info_by_key(self, workflow_key: str) -> Optional[Dict[str, Any]]:
        """Get workflow information from scene manager by key"""
        
        workflow = get_object_from_list(self.sceneManager.workflows, "WorkflowKey", workflow_key.upper())
        if workflow:
            return {
                "Title": workflow.Title,
                "WorkflowKey": str(workflow.WorkflowKey),
                "WorkflowID": workflow.WorkflowID,
                "Tooltip": workflow.Title
            }
        return None
    
    def save_new_status_to_database(self, status_data: Dict[str, Any]):
        """
        Placeholder method for saving new status to database.
        To be implemented with proper database integration.
        """
        logger.info(f"TODO: Save new status '{status_data['title']}' to database")
    
    def save_layout_to_database(self):
        """
        Placeholder method for saving updated layout to database.
        To be implemented with proper database integration.
        """
        logger.info("TODO: Save updated layout to database") 
    
    def create_connections_visual(self, selected_items: list, target) -> list[WFLineGroup]:
        """
        Create visual connections between selected items and a target.
        
        Args:
            selected_items: List of selected entities or status lines (sources)
            target: Target entity or status line
            
        Returns:
            List of created WFLineGroup objects
        """
        from workflow_designer.wfd_link_factory import create_connection_between_selections
        from workflow_designer.wfd_xml_builder import add_link_to_xml_string
        
        if not selected_items:
            logger.warning("No selected items provided for connection creation")
            return []
        
        if target in selected_items:
            logger.warning("Target is in selected items - cannot connect to self")
            return []
        
        # Create link data for all connections
        try:
            links_data = create_connection_between_selections(selected_items, target)
            if not links_data:
                logger.warning("No valid connections could be created")
                return []
        except Exception as e:
            logger.error(f"Failed to create link data: {e}")
            return []
        
        created_line_groups = []
        
        # Create visual connections and update XML for each link
        for link_data in links_data:
            try:
                # Create WFLineGroup from link data
                line_group = self._create_line_group_from_data(link_data)
                
                # Add to scene collections
                self.lines.append(line_group)
                line_group.set_selection_manager(self.selection_manager)
                
                # Update XML representation
                updated_xml = add_link_to_xml_string(self.dlPlacement.LayoutData, link_data)
                self.dlPlacement.LayoutData = updated_xml
                
                created_line_groups.append(line_group)
                
                logger.debug(f"Created connection: {link_data['source']['key']} -> {link_data['target']['key']}")
                
            except Exception as e:
                logger.error(f"Failed to create visual connection: {e}")
                continue
        
        if created_line_groups:
            logger.info(f"Created {len(created_line_groups)} connection(s)")
            # Placeholder for database persistence
            self.save_connections_to_database(links_data)
        
        return created_line_groups
    
    def _create_line_group_from_data(self, link_data: Dict[str, Any]) -> WFLineGroup:
        """
        Create a WFLineGroup from link data.
        
        Args:
            link_data: Link data dictionary from link factory
            
        Returns:
            WFLineGroup object ready for scene
        """
        from workflow_designer.wfd_objects import Link
        
        # Get source and target entities
        source_entity = link_data["source"]["entity"]
        target_entity = link_data["target"]["entity"]
        
        if not source_entity or not target_entity:
            raise ValueError("Invalid source or target entity in link data")
        
        # Create Link object for WFLineGroup
        link_obj = Link(
            linkProps={
                "DrawColor": link_data["properties"]["draw_color"],
                "Shadow": link_data["properties"]["shadow"],
                "DashStyle": link_data["properties"]["dash_style"]
            },
            linkAttribs={
                "LayoutLink": {
                    "OrgKey": link_data["source"]["key"],
                    "DstKey": link_data["target"]["key"]
                },
                "Point": [{"X": str(x), "Y": str(y)} for x, y in link_data["waypoints"]]
            }
        )
        
        # Create and return WFLineGroup
        return WFLineGroup(source_entity, target_entity, link_obj)
    
    def save_connections_to_database(self, links_data: list[Dict[str, Any]]):
        """
        Placeholder method for saving connections to database.
        To be implemented with proper database integration.
        """
        logger.info(f"TODO: Save {len(links_data)} connection(s) to database")


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


def convertWorkflowFromXML(node: Node, statuses: list[str], statusObjects: list = None) -> WFWorkflow:
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
            drawColor=drawColor,
            statusObjects=statusObjects
        )

def createFontFromWFDFont(wfdFont):
    try:
        # Validate font size
        size_value = wfdFont.Size
        if size_value is None:
            logger.warning(f"WFDFont has None size, using default: {wfdFont}")
            size_value = 8.25
        
        font = QFont(wfdFont.Name or "Microsoft Sans Serif", int(round(float(size_value))))
        font.setBold(wfdFont.Bold=='True')
        font.setItalic(wfdFont.Italic=='True')
        font.setUnderline(wfdFont.Underline=='True')
        font.setStrikeOut(wfdFont.Strikeout=='True')
        return font
    except (TypeError, ValueError) as e:
        logger.error(f"Error creating font from WFDFont {wfdFont}: {e}")
        # Return default font as fallback
        default_font = QFont("Microsoft Sans Serif", 8)
        return default_font

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
        # Handle None or empty values
        if colorStr is None or colorStr == "":
            logger.warning("parseXmlColor received None or empty string, using gray as fallback")
            return QColor(Qt.gray)
        
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
    except (ValueError, TypeError) as e:
        logger.warning(f"parseXmlColor failed to parse '{colorStr}': {e}, using gray as fallback")
        return QColor(Qt.gray)
