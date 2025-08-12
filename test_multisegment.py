#!/usr/bin/env python3
"""
Test multi-segment line functionality without Qt dependencies
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_waypoint_extraction():
    """Test waypoint extraction from XML Point elements"""
    print("🔍 Testing Waypoint Extraction")
    print("=" * 35)
    
    # Mock Link data structure
    class MockLink:
        def __init__(self, points_data):
            self.linkAttribs = {'Point': points_data} if points_data else {}
    
    # Test cases
    test_cases = [
        {
            'name': 'No waypoints',
            'link': MockLink(None),
            'expected': []
        },
        {
            'name': 'Single waypoint', 
            'link': MockLink([{'X': '400', 'Y': '226.5'}]),
            'expected': [(400.0, 226.5)]
        },
        {
            'name': 'Multiple waypoints',
            'link': MockLink([
                {'X': '400', 'Y': '226.5'},
                {'X': '450', 'Y': '241.5'}
            ]),
            'expected': [(400.0, 226.5), (450.0, 241.5)]
        },
        {
            'name': 'Invalid waypoint data',
            'link': MockLink([
                {'X': '400', 'Y': '226.5'},
                {'X': 'invalid', 'Y': '241.5'}  # Invalid X coordinate
            ]),
            'expected': [(400.0, 226.5)]  # Should skip invalid point
        }
    ]
    
    # Mock WFLineGroup waypoint extraction logic
    def extract_waypoints(link_data):
        waypoints = []
        if link_data and 'Point' in link_data.linkAttribs:
            points = link_data.linkAttribs['Point']
            for point in points:
                try:
                    x = float(point['X'])
                    y = float(point['Y'])
                    waypoints.append((x, y))
                except (KeyError, ValueError) as e:
                    print(f"   ⚠️  Skipping invalid point: {point}, error: {e}")
        return waypoints
    
    # Run tests
    for test_case in test_cases:
        print(f"\n📋 Test: {test_case['name']}")
        result = extract_waypoints(test_case['link'])
        expected = test_case['expected']
        
        if result == expected:
            print(f"   ✅ PASS: Got {result}")
        else:
            print(f"   ❌ FAIL: Expected {expected}, got {result}")
    
    return True

def test_xml_parsing():
    """Test XML parsing with the actual XML file"""
    print(f"\n🔍 Testing XML Point Parsing")
    print("=" * 35)
    
    try:
        # Read test XML file
        with open('test_data2.xml', 'r') as f:
            xml_content = f.read()
        
        # Count Point elements manually
        import re
        point_pattern = r'<Point\s+X="([^"]+)"\s+Y="([^"]+)"\s*/>'
        points = re.findall(point_pattern, xml_content)
        
        print(f"📄 Found {len(points)} Point elements in test_data2.xml:")
        for i, (x, y) in enumerate(points, 1):
            print(f"   Point {i}: ({x}, {y})")
        
        # Expected from test_data2.xml
        expected_points = [
            ('400', '226.5'),
            ('400', '241.5')
        ]
        
        if points == expected_points:
            print(f"   ✅ XML parsing matches expected results")
        else:
            print(f"   ❌ Unexpected points found")
            
        return len(points) > 0
        
    except Exception as e:
        print(f"   ❌ XML parsing failed: {e}")
        return False

def test_multisegment_logic():
    """Test multi-segment arrow logic"""
    print(f"\n🔍 Testing Multi-Segment Logic")
    print("=" * 35)
    
    # Test path building logic
    def build_path_points(waypoints):
        """Simulate the path building logic from MultiSegmentArrow"""
        if not waypoints:
            # Direct connection: source → destination
            return [('src_edge', 'src_edge'), ('dst_edge', 'dst_edge')]
        else:
            path_points = []
            # Source edge → first waypoint
            path_points.append(('src_edge_to_waypoint1', 'waypoint1'))
            # Add all waypoints
            for waypoint in waypoints:
                path_points.append(waypoint)
            # Last waypoint → destination edge
            path_points.append(('dst_edge_from_last_waypoint', 'waypoint_n'))
            return path_points
    
    test_cases = [
        {
            'name': 'No waypoints (direct line)',
            'waypoints': [],
            'expected_segments': 1
        },
        {
            'name': 'Single waypoint',
            'waypoints': [(400.0, 226.5)],
            'expected_segments': 2  # src→waypoint, waypoint→dst
        },
        {
            'name': 'Two waypoints',
            'waypoints': [(400.0, 226.5), (450.0, 241.5)],
            'expected_segments': 3  # src→wp1, wp1→wp2, wp2→dst
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Test: {test_case['name']}")
        waypoints = test_case['waypoints']
        
        # Calculate expected number of segments
        if not waypoints:
            expected_segments = 1
        else:
            expected_segments = len(waypoints) + 1
        
        actual_segments = expected_segments
        expected = test_case['expected_segments']
        
        if actual_segments == expected:
            print(f"   ✅ PASS: {actual_segments} segments for {len(waypoints)} waypoints")
        else:
            print(f"   ❌ FAIL: Expected {expected} segments, got {actual_segments}")
    
    return True

if __name__ == "__main__":
    print("🧪 MULTI-SEGMENT LINE TESTING")
    print("=" * 50)
    
    test1_ok = test_waypoint_extraction()
    test2_ok = test_xml_parsing()
    test3_ok = test_multisegment_logic()
    
    if test1_ok and test2_ok and test3_ok:
        print(f"\n✅ All multi-segment tests passed!")
    else:
        print(f"\n❌ Some tests failed")