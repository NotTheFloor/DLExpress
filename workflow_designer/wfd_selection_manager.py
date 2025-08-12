from typing import Optional, TYPE_CHECKING
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
    """Manages selection state for workflow designer items"""
    
    selectionChanged = Signal(object)  # Emits selected item or None
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._selected_item: Optional[object] = None
        self.selection_color = ThemeDetector.get_selection_color()
        self.selection_color_light = ThemeDetector.get_selection_color_lighter()
        
    def select_item(self, item: object):
        """Select an item (entity or line), deselecting the previous one"""
        if self._selected_item == item:
            return  # Already selected
            
        # Deselect previous item
        if self._selected_item is not None:
            self._deselect_current()
        
        # Select new item
        self._selected_item = item
        self._apply_selection(item)
        self.selectionChanged.emit(item)
    
    def deselect_all(self):
        """Deselect all items"""
        if self._selected_item is not None:
            self._deselect_current()
            self._selected_item = None
            self.selectionChanged.emit(None)
    
    def get_selected_item(self) -> Optional[object]:
        """Get currently selected item"""
        return self._selected_item
    
    def is_selected(self, item: object) -> bool:
        """Check if an item is currently selected"""
        return self._selected_item == item
    
    def _apply_selection(self, item: object):
        """Apply visual selection to an item"""
        # Check if it's an entity (WFEntity)
        if hasattr(item, 'shape') and hasattr(item.shape, 'setSelected'):
            item.shape.setSelected(True, self.selection_color)
        # Check if it's an arrow (SmartArrow or MultiSegmentArrow)
        elif hasattr(item, 'setSelected'):
            item.setSelected(True, self.selection_color)
        # Fallback for other selectable items
        elif hasattr(item, 'setPen'):
            # Store original pen if not already stored
            if not hasattr(item, '_original_pen'):
                item._original_pen = item.pen()
            from PySide6.QtGui import QPen
            selection_pen = QPen(self.selection_color, 3)
            item.setPen(selection_pen)
    
    def _deselect_current(self):
        """Remove visual selection from current item"""
        if self._selected_item is None:
            return
            
        item = self._selected_item
        
        # Check if it's an entity (WFEntity)
        if hasattr(item, 'shape') and hasattr(item.shape, 'setSelected'):
            item.shape.setSelected(False, self.selection_color)
        # Check if it's an arrow (SmartArrow or MultiSegmentArrow)
        elif hasattr(item, 'setSelected'):
            item.setSelected(False, self.selection_color)
        # Fallback for other selectable items
        elif hasattr(item, 'setPen') and hasattr(item, '_original_pen'):
            item.setPen(item._original_pen)
            delattr(item, '_original_pen')
    
    def update_theme(self):
        """Update colors based on current theme (call when theme changes)"""
        old_selection_color = self.selection_color
        self.selection_color = ThemeDetector.get_selection_color()
        self.selection_color_light = ThemeDetector.get_selection_color_lighter()
        
        # Reapply selection with new colors if something is selected
        if self._selected_item is not None:
            # First remove old selection
            self._deselect_current()
            # Then reapply with new colors
            self._apply_selection(self._selected_item)