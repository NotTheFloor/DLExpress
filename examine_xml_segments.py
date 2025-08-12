#!/usr/bin/env python3
"""
Test harness to examine multi-segment line data from the database
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def examine_database_xml():
    """Connect to database and examine XML layout data for multi-segment lines"""
    print("🔍 Examining Database XML for Multi-Segment Lines")
    print("=" * 55)
    
    try:
        from doclink_py.sql.manager.doclink_manager import DoclinkManager, DocLinkSQLCredentials
        from PySide6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        
        # Connect to database
        credentials = DocLinkSQLCredentials(
            server='192.168.68.64',
            database='doclink2', 
            username='sa',
            password='Sa2014'
        )
        
        connection = DoclinkManager(credentials)
        placements = connection.workflow_manager.get_workflow_placements()
        
        print(f"Found {len(placements)} workflow placements\n")
        
        multi_segment_count = 0
        total_links = 0
        
        for i, placement in enumerate(placements[:3]):  # Examine first 3 workflows
            print(f"📋 Workflow {i+1}: WorkflowID={placement.WorkflowID}")
            
            # Parse the XML layout data
            from workflow_designer.wfd_xml import createObjectListFromXMLString
            nodes, links = createObjectListFromXMLString(placement.LayoutData)
            
            print(f"   Nodes: {len(nodes)}, Links: {len(links)}")
            
            for j, link in enumerate(links):
                total_links += 1
                points = link.linkAttribs.get('Point', [])
                
                if points:
                    multi_segment_count += 1
                    print(f"   🔗 Link {j+1}: {len(points)} intermediate points")
                    print(f"      From: {link.linkAttribs['LayoutLink']['OrgKey'][:8]}...")
                    print(f"      To: {link.linkAttribs['LayoutLink']['DstKey'][:8]}...")
                    
                    for k, point in enumerate(points):
                        print(f"      Point {k+1}: ({point['X']}, {point['Y']})")
                        
            print()
        
        print(f"📊 Summary:")
        print(f"   Total links examined: {total_links}")
        print(f"   Multi-segment links: {multi_segment_count}")
        print(f"   Percentage with waypoints: {(multi_segment_count/total_links)*100:.1f}%")
        
        return multi_segment_count > 0
        
    except Exception as e:
        print(f"❌ Database examination failed: {e}")
        return False

def examine_local_xml():
    """Examine local test files for multi-segment structure"""
    print(f"\n🔍 Examining Local XML Files")
    print("=" * 35)
    
    try:
        from workflow_designer.wfd_xml import createObjectListFromXMLFile
        
        for filename in ['test_data.xml', 'test_data2.xml']:
            print(f"\n📄 {filename}:")
            nodes, links = createObjectListFromXMLFile(filename)
            
            for i, link in enumerate(links):
                points = link.linkAttribs.get('Point', [])
                org_key = link.linkAttribs['LayoutLink']['OrgKey'][:8]
                dst_key = link.linkAttribs['LayoutLink']['DstKey'][:8]
                
                if points:
                    print(f"   Link {i+1}: {org_key}...→{dst_key}... ({len(points)} points)")
                    for j, point in enumerate(points):
                        print(f"      Waypoint {j+1}: ({point['X']}, {point['Y']})")
                else:
                    print(f"   Link {i+1}: {org_key}...→{dst_key}... (direct)")
        
        return True
        
    except Exception as e:
        print(f"❌ Local XML examination failed: {e}")
        return False

if __name__ == "__main__":
    print("🗂️  XML MULTI-SEGMENT LINE EXAMINATION")
    print("=" * 60)
    
    local_ok = examine_local_xml()
    db_ok = examine_database_xml()
    
    if local_ok or db_ok:
        print(f"\n✅ XML examination completed successfully!")
    else:
        print(f"\n❌ XML examination failed")