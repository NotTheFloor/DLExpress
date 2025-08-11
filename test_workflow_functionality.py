#!/usr/bin/env python3
"""
Integration test script for the Workflow Designer functionality.
Tests the complete workflow without requiring database connection.
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow_designer.wfd_xml import createObjectListFromXMLFile
from workflow_designer.wfd_scene import convertStatusFromXML, convertWorkflowFromXML, parseXmlColor
from workflow_designer.wfd_logger import logger
import logging

def test_xml_parsing():
    """Test XML file parsing functionality"""
    print("=== Testing XML Parsing ===")
    
    test_files = ['test_data.xml', 'test_data2.xml']
    
    for filename in test_files:
        try:
            nodes, links = createObjectListFromXMLFile(filename)
            print(f"✅ {filename}: {len(nodes)} nodes, {len(links)} links")
            
            # Test node properties
            for node in nodes:
                print(f"   Node: {node.nodeProps.get('Text', 'No text')} - {node.nodeAttribs['LayoutNode']['Type']}")
                
            # Test link properties  
            for link in links:
                org_key = link.linkAttribs['LayoutLink']['OrgKey']
                dst_key = link.linkAttribs['LayoutLink']['DstKey']
                print(f"   Link: {org_key} -> {dst_key}")
                
        except Exception as e:
            print(f"❌ {filename}: FAILED - {e}")
            return False
    
    return True

def test_color_parsing():
    """Test XML color parsing"""
    print("\n=== Testing Color Parsing ===")
    
    test_colors = ['-1', '-16777216', '255', '16711680']  # White, Black, Blue, Red
    
    for color_str in test_colors:
        try:
            color = parseXmlColor(color_str)
            print(f"✅ Color '{color_str}' -> RGB({color.red()}, {color.green()}, {color.blue()})")
        except Exception as e:
            print(f"❌ Color '{color_str}': FAILED - {e}")
            return False
    
    return True

def test_entity_conversion():
    """Test XML to entity conversion"""
    print("\n=== Testing Entity Conversion ===")
    
    try:
        # Initialize Qt before doing entity conversion (needed for fonts)
        from PySide6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
            
        nodes, links = createObjectListFromXMLFile('test_data.xml')
        
        # Find a status node and workflow node
        status_node = None
        workflow_node = None
        
        for node in nodes:
            if node.nodeAttribs['LayoutNode']['Type'] == 'Status':
                status_node = node
            elif node.nodeAttribs['LayoutNode']['Type'] == 'Workflow':
                workflow_node = node
                
        if status_node:
            status_entity = convertStatusFromXML(status_node)
            print(f"✅ Status entity: {status_entity.title}")
            
        if workflow_node:
            workflow_entity = convertWorkflowFromXML(workflow_node, ['Status1', 'Status2'])
            print(f"✅ Workflow entity: {workflow_entity.title}")
            
        return True
        
    except Exception as e:
        print(f"❌ Entity conversion failed: {e}")
        return False

def test_qt_components():
    """Test Qt graphics components"""
    print("\n=== Testing Qt Components ===")
    
    try:
        from PySide6.QtWidgets import QApplication, QGraphicsScene
        from PySide6.QtCore import Qt
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Test scene creation
        scene = QGraphicsScene()
        print("✅ QGraphicsScene creation")
        
        # Test shape creation
        from workflow_designer.wfd_shape import ShapeRect, ShapeEllipse  
        from workflow_designer.wfd_objects import Rect
        
        rect = Rect(10, 10, 100, 50)
        shape_rect = ShapeRect(rect)
        shape_ellipse = ShapeEllipse(rect)
        
        print("✅ Shape objects creation")
        
        # Test adding to scene
        scene.addItem(shape_rect.graphicsItem)
        scene.addItem(shape_ellipse.graphicsItem)
        
        print(f"✅ Scene items: {len(scene.items())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Qt components test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Workflow Designer Integration Tests")
    print("=" * 50)
    
    # Set logging to show detailed information
    logger.logger.setLevel(logging.INFO)
    
    tests = [
        test_xml_parsing,
        test_color_parsing,
        test_entity_conversion,
        test_qt_components
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
        print("🎉 All tests passed! The workflow system is functional.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())