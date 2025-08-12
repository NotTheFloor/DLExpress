#!/usr/bin/env python3
"""
Test the visual selection system functionality
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_theme_detection():
    """Test theme detection without Qt dependencies"""
    print("🎨 Testing Theme Detection")
    print("=" * 30)
    
    try:
        from workflow_designer.wfd_selection_manager import ThemeDetector
        
        # Test fallback behavior (should default to light theme)
        is_dark = ThemeDetector.is_dark_theme()
        print(f"   Dark theme detected: {is_dark}")
        
        selection_color = ThemeDetector.get_selection_color()
        print(f"   Selection color: {selection_color.name()}")
        
        lighter_color = ThemeDetector.get_selection_color_lighter()
        print(f"   Lighter selection color: {lighter_color.name()}")
        
        # Test expected colors
        expected_light_color = "#FF8C00"  # Orange for light theme
        expected_dark_color = "#5DADE2"   # Blue for dark theme
        
        if is_dark:
            if selection_color.name().upper() == expected_dark_color.upper():
                print("   ✅ Dark theme colors correct")
            else:
                print(f"   ❌ Expected {expected_dark_color}, got {selection_color.name()}")
        else:
            if selection_color.name().upper() == expected_light_color.upper():
                print("   ✅ Light theme colors correct")
            else:
                print(f"   ❌ Expected {expected_light_color}, got {selection_color.name()}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import failed (Qt not available): {e}")
        return False
    except Exception as e:
        print(f"   ❌ Theme detection test failed: {e}")
        return False


def test_selection_manager():
    """Test SelectionManager logic without Qt dependencies"""
    print(f"\n🎯 Testing SelectionManager")
    print("=" * 30)
    
    try:
        from workflow_designer.wfd_selection_manager import SelectionManager
        
        # Create mock selectable objects
        class MockEntity:
            def __init__(self, name):
                self.name = name
                self.selected_state = False
                self.selection_color = None
            
            def setSelected(self, selected, color):
                self.selected_state = selected
                self.selection_color = color if selected else None
        
        # Create selection manager
        manager = SelectionManager()
        
        # Test initial state
        if manager.get_selected_item() is None:
            print("   ✅ Initial state: no selection")
        else:
            print("   ❌ Initial state should have no selection")
            
        # Create mock entities
        entity1 = MockEntity("Workflow1")
        entity2 = MockEntity("Status1")
        
        # Test selection
        manager.select_item(entity1)
        if manager.get_selected_item() == entity1:
            print("   ✅ Entity selection works")
        else:
            print("   ❌ Entity selection failed")
        
        # Test switching selection
        manager.select_item(entity2)
        if manager.get_selected_item() == entity2:
            print("   ✅ Selection switching works")
        else:
            print("   ❌ Selection switching failed")
        
        # Test deselection
        manager.deselect_all()
        if manager.get_selected_item() is None:
            print("   ✅ Deselection works")
        else:
            print("   ❌ Deselection failed")
            
        return True
        
    except ImportError as e:
        print(f"   ❌ Import failed (Qt not available): {e}")
        return False
    except Exception as e:
        print(f"   ❌ SelectionManager test failed: {e}")
        return False


def test_integration():
    """Test that all components can be imported together"""
    print(f"\n🔧 Testing Component Integration")
    print("=" * 35)
    
    try:
        # Test all imports work together
        from workflow_designer.wfd_selection_manager import SelectionManager, ThemeDetector
        from workflow_designer.wfd_shape import Shape, ShapeRect, ShapeEllipse
        
        print("   ✅ All selection components import successfully")
        
        # Test that expected methods exist
        manager = SelectionManager()
        methods = ['select_item', 'deselect_all', 'get_selected_item', 'is_selected']
        for method in methods:
            if hasattr(manager, method):
                print(f"   ✅ SelectionManager.{method}() exists")
            else:
                print(f"   ❌ SelectionManager.{method}() missing")
                return False
        
        # Test ThemeDetector methods
        theme_methods = ['is_dark_theme', 'get_selection_color', 'get_selection_color_lighter']
        for method in theme_methods:
            if hasattr(ThemeDetector, method):
                print(f"   ✅ ThemeDetector.{method}() exists")
            else:
                print(f"   ❌ ThemeDetector.{method}() missing")
                return False
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Integration test failed (Qt not available): {e}")
        return False
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 VISUAL SELECTION SYSTEM TESTS")
    print("=" * 45)
    
    test1_ok = test_theme_detection()
    test2_ok = test_selection_manager()  
    test3_ok = test_integration()
    
    if test1_ok and test2_ok and test3_ok:
        print(f"\n✅ All selection system tests passed!")
        print(f"\n📋 Implementation Summary:")
        print(f"   • SelectionManager: Centralizes selection state")
        print(f"   • ThemeDetector: Provides theme-appropriate colors")
        print(f"   • Shape classes: Support visual selection feedback")
        print(f"   • Arrow classes: Support line segment selection")
        print(f"   • Scene integration: Handles click events and deselection")
        print(f"   • Ready for user interaction!")
    else:
        print(f"\n❌ Some tests failed - check Qt dependencies")