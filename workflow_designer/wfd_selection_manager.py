from typing import Optional, Set, TYPE_CHECKING
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

if TYPE_CHECKING:
    from workflow_designer.wfd_scene import WFEntity
    from workflow_designer.wfd_utilities import SmartArrow, MultiSegmentArrow

class ThemeDetector:
    """Detects system theme and provides appropriate selection colors"""
    
    @staticmethod
    def is_dark_theme() -> bool:
        """Detect if the system is using dark theme"""
        try:
            app = QApplication.instance()
            if app:
                palette = app.palette()
                # Check if window background is darker than text
                bg_color = palette.color(QPalette.Window)
                text_color = palette.color(QPalette.WindowText)
                
                # Calculate luminance (simple approximation)
                bg_luminance = (bg_color.red() * 0.299 + bg_color.green() * 0.587 + bg_color.blue() * 0.114) / 255
                return bg_luminance < 0.5
        except Exception:
            pass
        
        # Fallback to light theme
        return False
    
    @staticmethod
    def get_selection_color() -> QColor:
        """Get appropriate selection color based on theme"""
        if ThemeDetector.is_dark_theme():
            return QColor("#5DADE2")  # Light blue for dark theme
        else:
            return QColor("#FF8C00")  # Bright orange for light theme
    
    @staticmethod
    def get_selection_color_lighter() -> QColor:
        """Get a lighter version of selection color for subtle highlighting"""
        if ThemeDetector.is_dark_theme():
            return QColor("#85C1E9")  # Lighter blue for dark theme
        else:
            return QColor("#FFB347")  # Lighter orange for light theme


class SelectionManager(QObject):
    """Manages multi-selection state for workflow designer items with type-based rules"""
    
    selectionChanged = Signal(set)  # Emits set of selected items
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._selected_items: Set[object] = set()
        self._selection_mode: Optional[str] = None  # "ENTITY" or "LINE" 
        self.selection_color = ThemeDetector.get_selection_color()
        self.selection_color_light = ThemeDetector.get_selection_color_lighter()
        
    def select_item(self, item: object, with_modifier: bool = False):
        """Select an item with optional modifier key support for multi-selection"""
        if with_modifier:
            self._handle_modifier_selection(item)
        else:
            # Normal click - clear selection and select only this item
            self.deselect_all()
            self._add_item_to_selection(item)
            
    def _handle_modifier_selection(self, item: object):
        """Handle Ctrl/Cmd+click selection"""
        item_type = self._get_item_type(item)
        
        if item in self._selected_items:
            # Item already selected - remove it (toggle off)
            self._remove_item_from_selection(item)
        else:
            # Check if we can add this item type to current selection
            if self._can_add_item_type(item_type):
                self._add_item_to_selection(item)
            # If type mismatch, ignore the selection (following the rules)
                
    def _add_item_to_selection(self, item: object):
        """Add an item to the selection"""
        item_type = self._get_item_type(item)
        
        # Set selection mode if this is the first item
        if not self._selected_items:
            self._selection_mode = item_type
            
        self._selected_items.add(item)
        self._apply_selection(item)
        self.selectionChanged.emit(self._selected_items.copy())
        
    def _remove_item_from_selection(self, item: object):
        """Remove an item from the selection"""
        if item in self._selected_items:
            self._selected_items.remove(item)
            self._deselect_item(item)
            
            # Clear selection mode if no items remain
            if not self._selected_items:
                self._selection_mode = None
                
            self.selectionChanged.emit(self._selected_items.copy())
    
    def deselect_all(self):
        """Deselect all items"""
        if self._selected_items:
            # Deselect all items visually
            for item in self._selected_items.copy():
                self._deselect_item(item)
            
            self._selected_items.clear()
            self._selection_mode = None
            self.selectionChanged.emit(set())
    
    def get_selected_items(self) -> Set[object]:
        """Get currently selected items"""
        return self._selected_items.copy()
    
    def get_selected_item(self) -> Optional[object]:
        """Get single selected item (for backward compatibility)"""
        if len(self._selected_items) == 1:
            return next(iter(self._selected_items))
        return None
    
    def is_selected(self, item: object) -> bool:
        """Check if an item is currently selected"""
        return item in self._selected_items
        
    def has_selection(self) -> bool:
        """Check if any items are selected"""
        return bool(self._selected_items)
        
    def get_selection_mode(self) -> Optional[str]:
        """Get current selection mode"""
        return self._selection_mode
    
    def _apply_selection(self, item: object):
        """Apply visual selection to an item"""
        # Check if it's an entity (WFEntity)
        if hasattr(item, 'shape') and hasattr(item.shape, 'setSelected'):
            item.shape.setSelected(True, self.selection_color)
        # Check if it's a line group (WFLineGroup) or arrow (SmartArrow or MultiSegmentArrow)
        elif hasattr(item, 'setSelected'):
            item.setSelected(True, self.selection_color)
            # Show nodes for MultiSegmentArrow or WFLineGroup containing one
            if hasattr(item, 'show_nodes'):
                item.show_nodes()
        # Fallback for other selectable items
        elif hasattr(item, 'setPen'):
            # Store original pen if not already stored
            if not hasattr(item, '_original_pen'):
                item._original_pen = item.pen()
            from PySide6.QtGui import QPen
            selection_pen = QPen(self.selection_color, 3)
            item.setPen(selection_pen)
    
    def _deselect_item(self, item: object):
        """Remove visual selection from a specific item"""
        # Check if it's an entity (WFEntity)
        if hasattr(item, 'shape') and hasattr(item.shape, 'setSelected'):
            item.shape.setSelected(False, self.selection_color)
        # Check if it's a line group (WFLineGroup) or arrow (SmartArrow or MultiSegmentArrow)
        elif hasattr(item, 'setSelected'):
            item.setSelected(False, self.selection_color)
            # Hide nodes for MultiSegmentArrow or WFLineGroup containing one
            if hasattr(item, 'hide_nodes'):
                item.hide_nodes()
        # Fallback for other selectable items
        elif hasattr(item, 'setPen') and hasattr(item, '_original_pen'):
            item.setPen(item._original_pen)
            delattr(item, '_original_pen')
    
    def update_theme(self):
        """Update colors based on current theme (call when theme changes)"""
        old_selection_color = self.selection_color
        self.selection_color = ThemeDetector.get_selection_color()
        self.selection_color_light = ThemeDetector.get_selection_color_lighter()
        
        # Reapply selection with new colors for all selected items
        if self._selected_items:
            for item in self._selected_items:
                # First remove old selection
                self._deselect_item(item)
                # Then reapply with new colors
                self._apply_selection(item)
                
    def _get_item_type(self, item: object) -> str:
        """Determine the type of an item for selection rules"""
        # Check if it's a line/arrow
        from workflow_designer.wfd_scene import WFLineGroup
        if isinstance(item, WFLineGroup) or hasattr(item, 'setSelected') and hasattr(item, 'show_nodes'):
            return "LINE"
        # Otherwise it's an entity (status or workflow)
        else:
            return "ENTITY"
            
    def _can_add_item_type(self, item_type: str) -> bool:
        """Check if we can add this item type to current selection based on rules"""
        if not self._selected_items:
            return True  # First item, always allowed
            
        # Current mode must match the item type
        return self._selection_mode == item_type
        
    def add_items_to_selection(self, items: Set[object]):
        """Add multiple items to selection (for box selection)"""
        if not items:
            return
            
        # Separate items by type
        entities = {item for item in items if self._get_item_type(item) == "ENTITY"}
        lines = {item for item in items if self._get_item_type(item) == "LINE"}
        
        # Priority rule: Entities take precedence over lines in box selection
        if entities:
            selected_items = entities
            selected_type = "ENTITY"
        elif lines:
            selected_items = lines  
            selected_type = "LINE"
        else:
            return
            
        # If we have existing selection, check type compatibility
        if self._selected_items and self._selection_mode != selected_type:
            # Type mismatch - clear existing selection
            self.deselect_all()
            
        # Add compatible items
        for item in selected_items:
            if item not in self._selected_items:
                self._selected_items.add(item)
                self._apply_selection(item)
                
        # Set mode if this was the first selection
        if not self._selection_mode:
            self._selection_mode = selected_type
            
        self.selectionChanged.emit(self._selected_items.copy())