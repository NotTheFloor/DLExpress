import random

from PySide6.QtWidgets import QFrame, QGraphicsView, QVBoxLayout, QGraphicsScene, QRubberBand
from PySide6.QtGui import QPainter, QPen, QColor, QFontMetrics
from PySide6.QtCore import QPoint, QRect, Qt, QRectF

from .wfd_utilities import drawArrow

_DEF_DW_SZ_X = 1400
_DEF_DW_SZ_Y = 900
_TITLE_OFFS_X = 5
_TITLE_OFFS_Y = 12

class CustomGraphicsView(QGraphicsView):
    """Custom QGraphicsView that handles empty space clicks for deselection and box selection"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._wf_scene = None  # Reference to WFScene for selection manager access
        
        # Rubber band selection
        self._rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self._rubber_band_origin = QPoint()
        self._rubber_band_active = False
        self._rubber_band_enabled = False  # Only enable when clicking empty space
    
    def set_wf_scene(self, wf_scene):
        """Set the workflow scene reference for selection handling"""
        self._wf_scene = wf_scene
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Check if click is on empty space
            item = self.itemAt(event.pos())
            print(f"🎯 MOUSE PRESS: pos={event.pos()}, item={'None' if item is None else type(item).__name__}")
            
            if item is None:
                # Click on empty space - enable rubber band selection
                self._rubber_band_origin = event.pos()
                self._rubber_band_active = False  # Will be activated on drag
                self._rubber_band_enabled = True  # Enable rubber band mode
                print(f"🎯 EMPTY SPACE CLICK: rubber_band enabled, origin set to {self._rubber_band_origin}")
                
                # Detect modifier keys
                modifiers = event.modifiers()
                has_modifier = bool(modifiers & (Qt.ControlModifier | Qt.MetaModifier))
                print(f"🎯 MODIFIER KEYS: {has_modifier}")
                
                if not has_modifier and self._wf_scene and hasattr(self._wf_scene, 'selection_manager'):
                    # No modifier - deselect all immediately
                    self._wf_scene.selection_manager.deselect_all()
                    print(f"🎯 DESELECTED ALL")
            else:
                print(f"🎯 CLICKED ON ITEM: {type(item).__name__}")
                # Disable rubber band completely when clicking on items
                self._rubber_band_enabled = False
                self._rubber_band_active = False
                self._rubber_band.hide()
                print(f"🎯 RUBBER BAND DISABLED: clicked on item")
        
        # Call parent handler to maintain normal functionality
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self._rubber_band_enabled:
            # Only do rubber band logic if we clicked on empty space initially
            if not self._rubber_band_active:
                # Calculate distance moved
                distance = (event.pos() - self._rubber_band_origin).manhattanLength()
                print(f"🔄 MOUSE MOVE: pos={event.pos()}, origin={self._rubber_band_origin}, distance={distance}")
                if distance >= 3:  # Start rubber band after 3 pixels of movement
                    self._rubber_band_active = True
                    rubber_rect = QRect(self._rubber_band_origin, event.pos()).normalized()
                    self._rubber_band.setGeometry(rubber_rect)
                    self._rubber_band.show()
                    print(f"🟩 RUBBER BAND ACTIVATED: geometry={rubber_rect}")
            else:
                # Update rubber band size
                rubber_rect = QRect(self._rubber_band_origin, event.pos()).normalized()
                self._rubber_band.setGeometry(rubber_rect)
                print(f"🟦 RUBBER BAND UPDATE: geometry={rubber_rect}")
        
        # Call parent handler
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._rubber_band_active:
            print(f"🏁 MOUSE RELEASE: Finishing rubber band selection")
            
            # Get selection rectangle in widget coordinates
            widget_rect = self._rubber_band.geometry()
            print(f"📦 WIDGET RECT: {widget_rect}")
            
            # Convert to view coordinates (should be the same as widget for QGraphicsView)
            view_rect = widget_rect
            print(f"👁️ VIEW RECT: {view_rect}")
            
            # Convert view coordinates to scene coordinates
            top_left_scene = self.mapToScene(view_rect.topLeft())
            bottom_right_scene = self.mapToScene(view_rect.bottomRight())
            scene_rect = QRectF(top_left_scene, bottom_right_scene)
            print(f"🌍 SCENE RECT: {scene_rect}")
            
            # Finish rubber band selection
            self._rubber_band.hide()
            self._rubber_band_active = False
            self._rubber_band_enabled = False  # Reset for next operation
            
            # Find items within the selection rectangle
            self._select_items_in_rect(scene_rect)
        else:
            print(f"🏁 MOUSE RELEASE: button={event.button()}, rubber_band_active={self._rubber_band_active}")
        
        # Call parent handler
        super().mouseReleaseEvent(event)
        
    def _select_items_in_rect(self, scene_rect: QRectF):
        """Find and select all selectable items within the given scene rectangle"""
        print(f"🔍 BOX SELECTION: Checking items in scene_rect={scene_rect}")
        
        if not self._wf_scene or not hasattr(self._wf_scene, 'selection_manager'):
            print(f"❌ NO SCENE OR SELECTION MANAGER")
            return
            
        # Find entities (statuses and workflows) within the rectangle
        entities_to_select = set()
        lines_to_select = set()
        
        print(f"🔍 Checking {len(self._wf_scene.workflows)} workflows and {len(self._wf_scene.statuses)} statuses")
        
        # Check workflow entities
        for i, workflow in enumerate(self._wf_scene.workflows):
            in_rect = self._is_entity_in_rect(workflow, scene_rect)
            print(f"  📋 Workflow {i}: {workflow.entityKey[:8]}... in_rect={in_rect}")
            if in_rect:
                entities_to_select.add(workflow)
                
        # Check status entities  
        for i, status in enumerate(self._wf_scene.statuses):
            in_rect = self._is_entity_in_rect(status, scene_rect)
            print(f"  ⭕ Status {i}: {status.entityKey[:8]}... in_rect={in_rect}")
            if in_rect:
                entities_to_select.add(status)
                
        # Check line groups
        for i, line in enumerate(self._wf_scene.lines):
            in_rect = self._is_line_in_rect(line, scene_rect)
            print(f"  ➡️ Line {i}: in_rect={in_rect}")
            if in_rect:
                lines_to_select.add(line)
        
        print(f"📊 SELECTION RESULTS: {len(entities_to_select)} entities, {len(lines_to_select)} lines")
        
        # Apply type-based selection rules
        all_items = entities_to_select | lines_to_select
        if all_items:
            print(f"✅ SELECTING {len(all_items)} items")
            self._wf_scene.selection_manager.add_items_to_selection(all_items)
        else:
            print(f"❌ NO ITEMS TO SELECT")
            
    def _is_entity_in_rect(self, entity, scene_rect: QRectF) -> bool:
        """Check if an entity's shape is within the selection rectangle"""
        if not entity.shape or not entity.shape.graphicsItem:
            print(f"    ❌ Entity has no shape or graphics item")
            return False
            
        # Get entity bounds in scene coordinates
        item_rect = entity.shape.graphicsItem.sceneBoundingRect()
        intersects = scene_rect.intersects(item_rect)
        
        print(f"    🔍 Entity rect: {item_rect}, intersects: {intersects}")
        
        return intersects
        
    def _is_line_in_rect(self, line_group, scene_rect: QRectF) -> bool:
        """Check if any part of a line group is within the selection rectangle"""
        # Check if any of the line segments intersect with the selection rectangle
        for line_item in line_group.lineSegments:
            if hasattr(line_item, 'sceneBoundingRect'):
                item_rect = line_item.sceneBoundingRect()
                if scene_rect.intersects(item_rect):
                    return True
        return False


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
