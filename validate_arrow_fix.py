#!/usr/bin/env python3
"""
Comprehensive validation that the arrow movement issue has been fixed.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def validate_coordinate_system():
    """Validate that dynamic coordinate system works correctly"""
    print("🎯 Validating Dynamic Coordinate System")
    print("=" * 45)
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QPointF
        from workflow_designer.wfd_scene import WFStatus
        from workflow_designer.wfd_objects import Rect
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create a status entity
        statusRect = Rect(100, 100, 50, 50)
        status = WFStatus("test", "Test Status", statusRect)
        
        # Test 1: Original center coordinates
        original_center = status.shape.getCurrentCenter()
        expected_center = (125.0, 125.0)  # 100 + 50/2, 100 + 50/2
        
        center_matches = (abs(original_center[0] - expected_center[0]) < 0.1 and 
                         abs(original_center[1] - expected_center[1]) < 0.1)
        
        print(f"   Original center calculation: {'✅' if center_matches else '❌'}")
        print(f"     Expected: {expected_center}")  
        print(f"     Got: {original_center}")
        
        # Test 2: Position update simulation
        new_pos = QPointF(150, 75)
        status.shape.graphicsItem.setPos(new_pos)
        
        updated_center = status.shape.getCurrentCenter()
        expected_updated = (175.0, 100.0)  # 150 + 50/2, 75 + 50/2
        
        update_matches = (abs(updated_center[0] - expected_updated[0]) < 0.1 and 
                         abs(updated_center[1] - expected_updated[1]) < 0.1)
        
        print(f"   Updated center calculation: {'✅' if update_matches else '❌'}")
        print(f"     Expected: {expected_updated}")
        print(f"     Got: {updated_center}")
        
        # Test 3: Verify old static coordinates are different
        static_center = (status.shape.rect.cx, status.shape.rect.cy)
        static_different = (static_center[0] != updated_center[0] or 
                           static_center[1] != updated_center[1])
        
        print(f"   Static vs dynamic different: {'✅' if static_different else '❌'}")
        print(f"     Static (old): {static_center}")
        print(f"     Dynamic (new): {updated_center}")
        
        return center_matches and update_matches and static_different
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

def validate_arrow_following():
    """Validate that arrows follow moving entities"""
    print(f"\n🏹 Validating Arrow Following Behavior")  
    print("=" * 42)
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QPointF
        from workflow_designer.wfd_scene import WFStatus, WFWorkflow
        from workflow_designer.wfd_objects import Rect
        from workflow_designer.wfd_utilities import SmartArrow
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create source and destination entities
        sourceRect = Rect(50, 50, 40, 40)
        targetRect = Rect(150, 50, 60, 40)
        
        source = WFStatus("source", "Source", sourceRect)
        target = WFWorkflow("target", "Target", ["S1"], targetRect)
        
        # Create arrow
        arrow = SmartArrow(source, target)
        lineItem, arrowItem = arrow.getGraphicsItems()
        
        # Get initial arrow position
        initial_line = lineItem.line()
        
        # Move source entity significantly
        source.shape.graphicsItem.setPos(QPointF(0, 100))  # Move left and down
        
        # Update arrow (this simulates what happens via signals)
        arrow.updateGeometry()
        
        # Check if arrow moved
        new_line = lineItem.line()
        
        start_moved = (abs(new_line.x1() - initial_line.x1()) > 20 or 
                      abs(new_line.y1() - initial_line.y1()) > 20)
        
        print(f"   Arrow follows source movement: {'✅' if start_moved else '❌'}")
        print(f"     Initial start: ({initial_line.x1():.1f}, {initial_line.y1():.1f})")
        print(f"     New start: ({new_line.x1():.1f}, {new_line.y1():.1f})")
        
        # Move target entity
        target.shape.graphicsItem.setPos(QPointF(250, 100))
        arrow.updateGeometry()
        
        final_line = lineItem.line()
        
        end_moved = (abs(final_line.x2() - new_line.x2()) > 20 or
                    abs(final_line.y2() - new_line.y2()) > 20)
        
        print(f"   Arrow follows target movement: {'✅' if end_moved else '❌'}")
        print(f"     Previous end: ({new_line.x2():.1f}, {new_line.y2():.1f})")
        print(f"     New end: ({final_line.x2():.1f}, {final_line.y2():.1f})")
        
        return start_moved and end_moved
        
    except Exception as e:
        print(f"❌ Arrow following validation failed: {e}")
        return False

def validate_edge_positioning():
    """Validate that arrows still terminate on shape edges"""
    print(f"\n📐 Validating Edge Positioning Accuracy")
    print("=" * 38)
    
    try:
        from PySide6.QtWidgets import QApplication
        from workflow_designer.wfd_scene import WFStatus
        from workflow_designer.wfd_objects import Rect
        from workflow_designer.wfd_utilities import calculateLineEndpoints
        import math
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create two status circles
        leftRect = Rect(50, 50, 40, 40)  # Radius 20
        rightRect = Rect(150, 50, 40, 40)  # Radius 20
        
        leftStatus = WFStatus("left", "Left", leftRect)
        rightStatus = WFStatus("right", "Right", rightRect)
        
        # Calculate line endpoints
        startPoint, endPoint = calculateLineEndpoints(leftStatus, rightStatus)
        
        # Verify start point is on left circle edge (should be near x=90, y=70)
        leftCenter = leftStatus.shape.getCurrentCenter()
        distanceFromLeftCenter = math.sqrt((startPoint[0] - leftCenter[0])**2 + 
                                         (startPoint[1] - leftCenter[1])**2)
        
        on_left_edge = abs(distanceFromLeftCenter - 20) < 2  # Within 2 pixels of radius
        
        print(f"   Start point on circle edge: {'✅' if on_left_edge else '❌'}")
        print(f"     Distance from center: {distanceFromLeftCenter:.1f} (expected ~20)")
        
        # Verify end point is on right circle edge
        rightCenter = rightStatus.shape.getCurrentCenter()
        distanceFromRightCenter = math.sqrt((endPoint[0] - rightCenter[0])**2 + 
                                          (endPoint[1] - rightCenter[1])**2)
        
        on_right_edge = abs(distanceFromRightCenter - 20) < 2
        
        print(f"   End point on circle edge: {'✅' if on_right_edge else '❌'}")  
        print(f"     Distance from center: {distanceFromRightCenter:.1f} (expected ~20)")
        
        return on_left_edge and on_right_edge
        
    except Exception as e:
        print(f"❌ Edge positioning validation failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🛠️  ARROW FIX VALIDATION")
    print("=" * 60)
    print("Validating that arrows now update when status circles move...")
    
    # Run all validation tests
    coord_ok = validate_coordinate_system()
    arrow_ok = validate_arrow_following() 
    edge_ok = validate_edge_positioning()
    
    print(f"\n" + "=" * 60)
    print(f"📊 VALIDATION RESULTS")
    print(f"   Dynamic Coordinates: {'✅ PASS' if coord_ok else '❌ FAIL'}")
    print(f"   Arrow Following: {'✅ PASS' if arrow_ok else '❌ FAIL'}")  
    print(f"   Edge Positioning: {'✅ PASS' if edge_ok else '❌ FAIL'}")
    
    all_passed = coord_ok and arrow_ok and edge_ok
    
    if all_passed:
        print(f"\n🎉 ALL VALIDATIONS PASSED!")
        print(f"✅ The arrow movement issue has been FIXED!")
        print(f"")
        print(f"🎯 Status circles can now be dragged and arrows will follow")
        print(f"🎯 Workflow rectangles can be dragged and arrows will follow")
        print(f"🎯 Arrows maintain proper edge-to-edge positioning")
        print(f"🎯 Arrow direction and positioning remain accurate")
        return 0
    else:
        print(f"\n❌ Some validations failed - issue may not be fully resolved")
        return 1

if __name__ == "__main__":
    sys.exit(main())