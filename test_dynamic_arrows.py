#!/usr/bin/env python3
"""
Test script to verify that arrows now update when entities move.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow_designer.wfd_scene import WFStatus, WFWorkflow, EntityType
from workflow_designer.wfd_objects import Rect
from workflow_designer.wfd_utilities import SmartArrow, calculateLineEndpoints

def test_dynamic_arrow_updates():
    """Test that arrows follow moving entities"""
    print("🎯 Testing Dynamic Arrow Updates")
    print("=" * 40)
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QPointF
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create test entities
        statusRect = Rect(100, 100, 50, 50)  # Circle at (100,100)
        workflowRect = Rect(200, 100, 80, 60)  # Rectangle at (200,100)
        
        status = WFStatus("test-status", "Moving Status", statusRect)
        workflow = WFWorkflow("test-workflow", "Target Workflow", ["Status1"], workflowRect)
        
        print(f"✅ Created status at center: {status.shape.getCurrentCenter()}")
        print(f"✅ Created workflow at center: {workflow.shape.getCurrentCenter()}")
        
        # Create smart arrow
        smartArrow = SmartArrow(status, workflow)
        lineItem, arrowItem = smartArrow.getGraphicsItems()
        
        # Get initial line position
        initialLine = lineItem.line()
        print(f"📍 Initial line: ({initialLine.x1():.1f}, {initialLine.y1():.1f}) -> ({initialLine.x2():.1f}, {initialLine.y2():.1f})")
        
        # Test 1: Move status entity and check if arrow updates
        print(f"\n🔄 Moving status entity...")
        
        # Simulate moving the graphics item (this is what happens during drag)
        new_position = QPointF(150, 50)  # Move right and up
        status.shape.graphicsItem.setPos(new_position)
        
        # Get updated center position to verify it changed
        new_center = status.shape.getCurrentCenter()
        print(f"   Status moved to center: {new_center}")
        
        # Manually trigger arrow update (simulates what the signal would do)
        smartArrow.updateGeometry()
        
        # Check if line updated
        updatedLine = lineItem.line()
        print(f"📍 Updated line: ({updatedLine.x1():.1f}, {updatedLine.y1():.1f}) -> ({updatedLine.x2():.1f}, {updatedLine.y2():.1f})")
        
        # Verify the line start point moved
        x_moved = abs(updatedLine.x1() - initialLine.x1()) > 40  # Should move ~50 pixels
        y_moved = abs(updatedLine.y1() - initialLine.y1()) > 40  # Should move ~50 pixels
        
        print(f"   Line start X moved: {'✅' if x_moved else '❌'}")
        print(f"   Line start Y moved: {'✅' if y_moved else '❌'}")
        
        # Test 2: Verify calculateLineEndpoints uses current positions
        print(f"\n🧮 Testing calculateLineEndpoints with current positions...")
        
        startPoint, endPoint = calculateLineEndpoints(status, workflow)
        print(f"   Dynamic calculation result:")
        print(f"     Start: ({startPoint[0]:.1f}, {startPoint[1]:.1f})")
        print(f"     End: ({endPoint[0]:.1f}, {endPoint[1]:.1f})")
        
        # Verify the calculation matches the new position
        expected_center_x, expected_center_y = new_center
        start_near_expected = abs(startPoint[0] - expected_center_x) < 30  # Within radius
        
        print(f"   Start point follows new center: {'✅' if start_near_expected else '❌'}")
        
        # Test 3: Move destination entity
        print(f"\n🔄 Moving workflow entity...")
        
        workflow_new_pos = QPointF(300, 150)  
        workflow.shape.graphicsItem.setPos(workflow_new_pos)
        
        smartArrow.updateGeometry()
        final_line = lineItem.line()
        print(f"📍 Final line: ({final_line.x1():.1f}, {final_line.y1():.1f}) -> ({final_line.x2():.1f}, {final_line.y2():.1f})")
        
        # Verify end point moved
        end_x_moved = abs(final_line.x2() - updatedLine.x2()) > 90  # Should move 100 pixels
        end_y_moved = abs(final_line.y2() - updatedLine.y2()) > 40  # Should move 50 pixels
        
        print(f"   Line end X moved: {'✅' if end_x_moved else '❌'}")
        print(f"   Line end Y moved: {'✅' if end_y_moved else '❌'}")
        
        # Summary
        success = x_moved and y_moved and start_near_expected and end_x_moved and end_y_moved
        
        print(f"\n📊 Overall Test Result: {'✅ PASSED' if success else '❌ FAILED'}")
        
        if success:
            print("🎉 Arrows now follow moving entities dynamically!")
            print("   • Status circles: arrows update when dragged")
            print("   • Workflow rectangles: arrows update when dragged")  
            print("   • Edge positioning: maintained during movement")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_connection():
    """Test that movement signals properly trigger arrow updates"""
    print(f"\n🔗 Testing Signal Connections")
    print("=" * 30)
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QPointF
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create entities
        statusRect = Rect(50, 50, 40, 40)
        workflowRect = Rect(150, 50, 60, 40)
        
        status = WFStatus("test-status", "Test", statusRect)
        workflow = WFWorkflow("test-workflow", "Test", ["Status1"], workflowRect)
        
        # Create arrow and track updates
        smartArrow = SmartArrow(status, workflow)
        
        # Track if updateGeometry was called
        update_called = False
        original_update = smartArrow.updateGeometry
        
        def track_update():
            nonlocal update_called
            update_called = True
            original_update()
        
        smartArrow.updateGeometry = track_update
        
        # Trigger movement signal
        status.shape.moved.emit(QPointF(100, 100))
        
        print(f"   Signal connection works: {'✅' if update_called else '❌'}")
        
        return update_called
        
    except Exception as e:
        print(f"❌ Signal test failed: {e}")
        return False

if __name__ == "__main__":
    print("🏹 Dynamic Arrow Movement Tests")
    print("=" * 50)
    
    test1_passed = test_dynamic_arrow_updates()
    test2_passed = test_signal_connection()
    
    if test1_passed and test2_passed:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ Arrows now update dynamically when entities are dragged!")
        sys.exit(0)
    else:
        print(f"\n❌ Some tests failed. Check output above.")
        sys.exit(1)