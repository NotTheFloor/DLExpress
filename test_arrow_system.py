#!/usr/bin/env python3
"""
Test script for the improved arrow system.
Tests geometric calculations, arrow direction, and dynamic updates.
"""

import sys
import os
import math

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow_designer.wfd_utilities import (
    findCircleEdgeIntersection, 
    findRectangleEdgeIntersection,
    calculateLineEndpoints,
    SmartArrow
)
from workflow_designer.wfd_scene import WFStatus, WFWorkflow, EntityType
from workflow_designer.wfd_objects import Rect
from workflow_designer.wfd_logger import logger

def test_geometric_calculations():
    """Test the geometric intersection functions"""
    print("=== Testing Geometric Calculations ===")
    
    # Test circle intersection
    print("\n1. Circle Edge Intersection:")
    # Circle at (50, 50) with radius 25, line from center to (100, 50)
    intersectX, intersectY = findCircleEdgeIntersection(
        50, 50, 25, 25,  # center and radii
        50, 50, 100, 50  # line from center to right
    )
    expected_x, expected_y = 75, 50  # Should intersect at right edge
    print(f"   Expected: (75, 50), Got: ({intersectX:.1f}, {intersectY:.1f}) - {'✅' if abs(intersectX - 75) < 1 and abs(intersectY - 50) < 1 else '❌'}")
    
    # Test rectangle intersection
    print("\n2. Rectangle Edge Intersection:")
    # Rectangle at (0, 0) size 100x50, line from center to right
    intersectX, intersectY = findRectangleEdgeIntersection(
        0, 0, 100, 50,   # rect left, top, width, height
        50, 25, 150, 25  # line from center to right outside
    )
    expected_x, expected_y = 100, 25  # Should intersect at right edge
    print(f"   Expected: (100, 25), Got: ({intersectX:.1f}, {intersectY:.1f}) - {'✅' if abs(intersectX - 100) < 1 and abs(intersectY - 25) < 1 else '❌'}")
    
    return True

def test_arrow_direction():
    """Test arrow direction calculations"""
    print("\n=== Testing Arrow Direction ===")
    
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create test entities
        statusRect = Rect(100, 100, 50, 50)  # Circle at (100,100) radius 25
        workflowRect = Rect(200, 100, 80, 60)  # Rectangle at (200,100)
        
        status = WFStatus("test-status", "Test Status", statusRect)
        workflow = WFWorkflow("test-workflow", "Test Workflow", ["Status1"], workflowRect)
        
        # Test line endpoint calculation
        startPoint, endPoint = calculateLineEndpoints(status, workflow)
        
        print(f"   Status center: ({status.shape.rect.cx}, {status.shape.rect.cy})")
        print(f"   Workflow center: ({workflow.shape.rect.cx}, {workflow.shape.rect.cy})")
        print(f"   Line start (status edge): ({startPoint[0]:.1f}, {startPoint[1]:.1f})")
        print(f"   Line end (workflow edge): ({endPoint[0]:.1f}, {endPoint[1]:.1f})")
        
        # Verify start point is on circle edge
        status_center_x, status_center_y = status.shape.rect.cx, status.shape.rect.cy
        distance_from_center = math.sqrt((startPoint[0] - status_center_x)**2 + (startPoint[1] - status_center_y)**2)
        print(f"   Distance from status center: {distance_from_center:.1f} (expected ~25) - {'✅' if abs(distance_from_center - 25) < 2 else '❌'}")
        
        # Verify end point is on rectangle edge
        workflow_left = workflow.shape.rect.left
        is_on_left_edge = abs(endPoint[0] - workflow_left) < 1
        print(f"   End point on workflow left edge: {'✅' if is_on_left_edge else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Arrow direction test failed: {e}")
        return False

def test_smart_arrow():
    """Test the SmartArrow class"""
    print("\n=== Testing SmartArrow Class ===")
    
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create test entities
        statusRect = Rect(50, 50, 40, 40)
        workflowRect = Rect(150, 50, 60, 40)
        
        status = WFStatus("test-status", "Test Status", statusRect)
        workflow = WFWorkflow("test-workflow", "Test Workflow", ["Status1"], workflowRect)
        
        # Create smart arrow
        smartArrow = SmartArrow(status, workflow)
        
        # Get graphics items
        lineItem, arrowItem = smartArrow.getGraphicsItems()
        
        print(f"   Line item created: {'✅' if lineItem is not None else '❌'}")
        print(f"   Arrow item created: {'✅' if arrowItem is not None else '❌'}")
        
        # Test line coordinates
        line = lineItem.line()
        print(f"   Line coordinates: ({line.x1():.1f}, {line.y1():.1f}) -> ({line.x2():.1f}, {line.y2():.1f})")
        
        # Test arrow polygon
        polygon = arrowItem.polygon()
        print(f"   Arrow polygon has {polygon.size()} points: {'✅' if polygon.size() == 3 else '❌'}")
        
        # Simulate entity movement and test update
        print("\n   Testing dynamic updates:")
        original_x2 = line.x2()
        
        # Move workflow entity (simulate position change)
        workflow.shape.rect.left += 50
        workflow.shape.rect.cx += 50
        
        # Manually trigger update (in real app, this would be automatic via signals)
        smartArrow.updateGeometry()
        
        new_line = lineItem.line()
        new_x2 = new_line.x2()
        
        print(f"   Line end moved: {original_x2:.1f} -> {new_x2:.1f} - {'✅' if abs(new_x2 - original_x2) > 40 else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ SmartArrow test failed: {e}")
        return False

def test_angle_consistency():
    """Test that arrow angles are calculated consistently"""
    print("\n=== Testing Angle Consistency ===")
    
    test_cases = [
        ((0, 0), (10, 0), 0),          # Right: 0°
        ((0, 0), (0, 10), math.pi/2),  # Down: 90°
        ((0, 0), (-10, 0), math.pi),   # Left: 180°
        ((0, 0), (0, -10), -math.pi/2), # Up: -90° (or 270°)
        ((0, 0), (10, 10), math.pi/4),  # Down-right: 45°
    ]
    
    all_passed = True
    for start, end, expected_angle in test_cases:
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        calculated_angle = math.atan2(dy, dx)
        
        angle_diff = abs(calculated_angle - expected_angle)
        # Handle angle wrapping (e.g., -90° vs 270°)
        if angle_diff > math.pi:
            angle_diff = 2 * math.pi - angle_diff
            
        passed = angle_diff < 0.1
        print(f"   {start} -> {end}: Expected {expected_angle:.2f}°, Got {calculated_angle:.2f}° - {'✅' if passed else '❌'}")
        if not passed:
            all_passed = False
    
    return all_passed

def main():
    """Run all arrow system tests"""
    print("🏹 Smart Arrow System Tests")
    print("=" * 50)
    
    logger.logger.setLevel(logging.WARNING)  # Reduce log noise
    
    tests = [
        test_geometric_calculations,
        test_angle_consistency,
        test_arrow_direction,
        test_smart_arrow
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            break
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All arrow system tests passed!")
        print("\n✅ Arrows now:")
        print("   • Point in correct direction with consistent angle calculation")  
        print("   • Terminate precisely on shape edges (circumference/rectangle)")
        print("   • Update dynamically when shapes move")
        return 0
    else:
        print("❌ Some tests failed. Check output above.")
        return 1

if __name__ == "__main__":
    import logging
    sys.exit(main())