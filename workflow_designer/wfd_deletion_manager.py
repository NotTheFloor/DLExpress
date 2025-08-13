"""
Object deletion manager with cascading deletion support.

This module provides centralized deletion logic for workflow designer objects
with proper relationship management and Qt graphics cleanup.
"""

from typing import List, Set, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass

from .wfd_logger import logger

if TYPE_CHECKING:
    from .wfd_scene import WFEntity, WFWorkflow, WFStatus, WFLineGroup, WFScene
    from .wfd_selection_manager import SelectionManager


@dataclass
class DeletionResult:
    """
    Information about what was deleted - designed for future undo functionality.
    
    This class captures all necessary information to potentially reverse a deletion
    operation in the future. While undo is not currently implemented, this structure
    provides the foundation for adding that capability later.
    """
    deleted_workflows: List['WFWorkflow']
    deleted_statuses: List['WFStatus'] 
    deleted_lines: List['WFLineGroup']
    total_items_deleted: int
    
    # Future undo support - these would store the state needed for restoration
    original_scene_state: Dict[str, Any] = None  # Could store original positions, properties, etc.
    deletion_timestamp: float = None  # When deletion occurred
    deletion_order: List[str] = None  # Order of deletions for proper undo sequencing
    
    def __post_init__(self):
        self.total_items_deleted = len(self.deleted_workflows) + len(self.deleted_statuses) + len(self.deleted_lines)
        
        if self.deletion_timestamp is None:
            import time
            self.deletion_timestamp = time.time()
        
        if self.deletion_order is None:
            self.deletion_order = []
    
    def getUndoInfo(self) -> Dict[str, Any]:
        """
        Get information needed for future undo implementation.
        
        Returns:
            dict: Undo information structure (for future use)
        """
        return {
            'workflows_count': len(self.deleted_workflows),
            'statuses_count': len(self.deleted_statuses),
            'lines_count': len(self.deleted_lines),
            'timestamp': self.deletion_timestamp,
            'total_items': self.total_items_deleted,
            # Future: Could include serialized object states, positions, etc.
        }


class DeletionManager:
    """
    Manages deletion of workflow designer objects with cascading relationship cleanup.
    
    Handles three types of objects:
    - Lines (WFLineGroup): Simple deletion
    - Statuses (WFStatus): Delete status + all connected lines  
    - Workflows (WFWorkflow): Delete workflow + all connected lines
    """
    
    def __init__(self, scene: 'WFScene', qt_graphics_scene=None):
        self.scene = scene
        self.qt_graphics_scene = qt_graphics_scene  # Qt QGraphicsScene for graphics cleanup
    
    def deleteSelected(self, selection_manager: 'SelectionManager') -> DeletionResult:
        """
        Delete currently selected items with cascading.
        
        Args:
            selection_manager: The selection manager containing selected items
            
        Returns:
            DeletionResult: Information about what was deleted
        """
        selected_items = selection_manager.get_selected_items()
        
        if not selected_items:
            logger.info("No items selected for deletion")
            return DeletionResult([], [], [], 0)
        
        # Separate items by type
        entities_to_delete = []
        lines_to_delete = []
        
        for item in selected_items:
            item_type = type(item).__name__
            if hasattr(item, 'entityType'):  # WFEntity (WFStatus or WFWorkflow)
                entities_to_delete.append(item)
                logger.debug(f"Classified as entity: {item_type}")
            elif hasattr(item, 'srcEntity'):  # WFLineGroup
                lines_to_delete.append(item)
                logger.debug(f"Classified as line: {item_type}")
            else:
                logger.warning(f"Unknown item type for deletion: {item_type} (entityType={hasattr(item, 'entityType')}, srcEntity={hasattr(item, 'srcEntity')})")
        
        logger.info(f"Deleting selection: {len(entities_to_delete)} entities, {len(lines_to_delete)} lines")
        
        # Clear selection before deletion to avoid issues
        selection_manager.deselect_all()
        
        # Perform deletion with cascading
        if entities_to_delete:
            return self.deleteEntities(entities_to_delete, additional_lines=lines_to_delete)
        else:
            return self.deleteLines(lines_to_delete)
    
    def deleteEntities(self, entities: List['WFEntity'], additional_lines: List['WFLineGroup'] = None) -> DeletionResult:
        """
        Delete entities and cascade to all connected lines.
        
        Args:
            entities: List of WFEntity objects to delete
            additional_lines: Additional lines to delete (beyond cascaded ones)
            
        Returns:
            DeletionResult: Information about what was deleted
        """
        if not entities:
            return DeletionResult([], [], [], 0)
        
        # Collect all lines that need to be deleted (cascading)
        lines_to_delete = set()
        
        # Add lines connected to entities being deleted
        for entity in entities:
            connected_lines = entity.getAllConnectedLines()
            lines_to_delete.update(connected_lines)
            logger.debug(f"Entity {entity.entityKey}: found {len(connected_lines)} connected lines")
        
        # Add any additional lines specified
        if additional_lines:
            lines_to_delete.update(additional_lines)
        
        # Convert back to list for consistent processing
        lines_list = list(lines_to_delete)
        
        logger.info(f"Cascading deletion: {len(entities)} entities will delete {len(lines_list)} lines")
        
        # Delete lines first to clean up relationships
        line_result = self.deleteLines(lines_list)
        
        # Now delete the entities
        workflows_deleted = []
        statuses_deleted = []
        
        for entity in entities:
            if hasattr(entity, 'title') and hasattr(entity, 'statuses'):  # WFWorkflow
                workflows_deleted.append(entity)
                self._deleteWorkflowFromScene(entity)
            else:  # WFStatus
                statuses_deleted.append(entity) 
                self._deleteStatusFromScene(entity)
        
        return DeletionResult(
            deleted_workflows=workflows_deleted,
            deleted_statuses=statuses_deleted,
            deleted_lines=line_result.deleted_lines,
            total_items_deleted=0  # Will be calculated in __post_init__
        )
    
    def deleteLines(self, lines: List['WFLineGroup']) -> DeletionResult:
        """
        Delete line objects with proper cleanup.
        
        Args:
            lines: List of WFLineGroup objects to delete
            
        Returns:
            DeletionResult: Information about what was deleted
        """
        if not lines:
            return DeletionResult([], [], [], 0)
        
        logger.info(f"Deleting {len(lines)} lines")
        
        deleted_lines = []
        
        for line in lines:
            if self._deleteLineFromScene(line):
                deleted_lines.append(line)
        
        return DeletionResult(
            deleted_workflows=[],
            deleted_statuses=[],
            deleted_lines=deleted_lines,
            total_items_deleted=0  # Will be calculated in __post_init__
        )
    
    def _deleteWorkflowFromScene(self, workflow: 'WFWorkflow') -> bool:
        """Remove a workflow from the scene and clean up graphics items"""
        try:
            # Remove from scene collection
            if workflow in self.scene.workflows:
                self.scene.workflows.remove(workflow)
                logger.debug(f"Removed workflow {workflow.entityKey} from scene collection")
            
            # Clean up graphics items will be handled in Phase 4
            self._removeEntityGraphicsItems(workflow)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting workflow {workflow.entityKey}: {e}")
            return False
    
    def _deleteStatusFromScene(self, status: 'WFStatus') -> bool:
        """Remove a status from the scene and clean up graphics items"""
        try:
            # Remove from scene collection
            if status in self.scene.statuses:
                self.scene.statuses.remove(status)
                logger.debug(f"Removed status {status.entityKey} from scene collection")
            
            # Clean up graphics items will be handled in Phase 4
            self._removeEntityGraphicsItems(status)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting status {status.entityKey}: {e}")
            return False
    
    def _deleteLineFromScene(self, line: 'WFLineGroup') -> bool:
        """Remove a line from the scene and clean up all references"""
        try:
            # Remove from entity tracking lists
            line.srcEntity.removeSourceLine(line)
            line.dstEntity.removeDestLine(line)
            
            # Remove from scene collection
            if line in self.scene.lines:
                self.scene.lines.remove(line)
                logger.debug(f"Removed line from {line.srcEntity.entityKey} to {line.dstEntity.entityKey}")
            
            # Clean up graphics items will be handled in Phase 4
            self._removeLineGraphicsItems(line)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting line: {e}")
            return False
    
    def _removeEntityGraphicsItems(self, entity: 'WFEntity'):
        """Remove entity graphics items from Qt scene"""
        try:
            if not self.qt_graphics_scene:
                logger.debug(f"No Qt graphics scene available for entity {entity.entityKey} cleanup")
                return
            
            # Remove main shape graphics item
            if entity.shape and entity.shape.graphicsItem:
                if entity.shape.graphicsItem.scene() == self.qt_graphics_scene:
                    self.qt_graphics_scene.removeItem(entity.shape.graphicsItem)
                    logger.debug(f"Removed main graphics item for entity {entity.entityKey}")
            
            # Remove text items (they should be children of the main item, but clean up just in case)
            for text_item in entity.textItems:
                if text_item.scene() == self.qt_graphics_scene:
                    self.qt_graphics_scene.removeItem(text_item)
                    logger.debug(f"Removed text item for entity {entity.entityKey}")
            
            # Clear text items list
            entity.textItems.clear()
            
        except Exception as e:
            logger.error(f"Error removing graphics items for entity {entity.entityKey}: {e}")
    
    def _removeLineGraphicsItems(self, line: 'WFLineGroup'):
        """Remove line graphics items from Qt scene"""
        try:
            if not self.qt_graphics_scene:
                logger.debug("No Qt graphics scene available for line cleanup")
                return
            
            # Remove all line graphics items
            if hasattr(line, 'get_all_graphics_items'):
                # Use the method from WFLineGroup to get all items
                all_items = line.get_all_graphics_items()
            else:
                # Fallback to lineSegments
                all_items = line.lineSegments
            
            for item in all_items:
                try:
                    # Handle both wrapped objects and raw Qt items
                    graphics_item = item.graphicsItem if hasattr(item, 'graphicsItem') else item
                    
                    if graphics_item and graphics_item.scene() == self.qt_graphics_scene:
                        self.qt_graphics_scene.removeItem(graphics_item)
                        logger.debug(f"Removed line graphics item")
                        
                except Exception as item_error:
                    logger.error(f"Error removing individual line item: {item_error}")
            
            # Clear the lineSegments list
            line.lineSegments.clear()
            
            # Disconnect Qt signals to prevent crashes on deleted objects
            try:
                if hasattr(line.arrow, 'srcEntity') and hasattr(line.arrow.srcEntity.shape, 'moved'):
                    line.arrow.srcEntity.shape.moved.disconnect(line.arrow.updateGeometry)
                if hasattr(line.arrow, 'dstEntity') and hasattr(line.arrow.dstEntity.shape, 'moved'):
                    line.arrow.dstEntity.shape.moved.disconnect(line.arrow.updateGeometry)
            except Exception as signal_error:
                logger.debug(f"Signal disconnection warning (expected): {signal_error}")
                
        except Exception as e:
            logger.error(f"Error removing graphics items for line: {e}")
    
    def canDelete(self, items: List[Any]) -> bool:
        """
        Check if the given items can be deleted.
        
        Args:
            items: List of items to check
            
        Returns:
            bool: True if all items can be deleted
        """
        if not items:
            return False
        
        # Currently all workflow designer objects can be deleted
        # Future: Could add business logic constraints here
        return True
    
    def getImpactedItems(self, entities: List['WFEntity']) -> Dict[str, int]:
        """
        Get information about what would be deleted if entities are removed.
        
        Args:
            entities: Entities to analyze
            
        Returns:
            dict: Impact information (for UI confirmation dialogs)
        """
        lines_impacted = set()
        
        for entity in entities:
            lines_impacted.update(entity.getAllConnectedLines())
        
        return {
            'entities': len(entities),
            'cascaded_lines': len(lines_impacted),
            'total_items': len(entities) + len(lines_impacted)
        }


# FUTURE UNDO/REDO IMPLEMENTATION NOTES:
# 
# The current deletion system is designed with undo/redo in mind:
# 
# 1. DeletionResult captures all deleted objects and metadata
# 2. Deletion methods are atomic and reversible in principle
# 3. Bidirectional relationships make restoration possible
# 4. Graphics cleanup is separated from logical deletion
# 
# To implement undo/redo in the future:
# 
# 1. Create UndoCommand class implementing Command pattern
# 2. Store object serialization data in DeletionResult.original_scene_state
# 3. Implement DeletionManager.undoDelete() method 
# 4. Add UndoStack to WFScene to manage command history
# 5. Extend graphics cleanup to store Qt item states for restoration
# 
# The current architecture makes this future enhancement straightforward
# without requiring major refactoring of the existing deletion system.