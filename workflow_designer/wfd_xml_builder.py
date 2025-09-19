"""
XML builder utilities for workflow designer entities.
This module provides Qt-independent functions for generating and manipulating
XML representations of workflow entities.
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from datetime import datetime

from workflow_designer.wfd_data_structures import validate_entity_data


def create_status_node_xml(status_data: Dict[str, Any]) -> ET.Element:
    """
    Create an XML Node element for a status entity.
    
    Args:
        status_data: Status data dictionary from entity factory
        
    Returns:
        XML Element representing the status node
    """
    print("CREATING NODE NODE XML")
    print(status_data)
    if not validate_entity_data(status_data):
        raise ValueError("Invalid status data provided")
    
    position = status_data["position"]
    properties = status_data["properties"]
    font = status_data["font"]
    layout_node = status_data["layout_node"]
    
    # Create the main Node element with position attributes
    node = ET.Element("Node")
    
    # Validate position values before conversion
    try:
        node.set("Left", str(int(position["x"])))
        node.set("Top", str(int(position["y"]))) 
        node.set("Width", str(int(position["width"])))
        node.set("Height", str(int(position["height"])))
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid position data in status: x={position.get('x')}, y={position.get('y')}, width={position.get('width')}, height={position.get('height')}. Error: {e}")
    
    # Add properties as child elements
    if properties.get("fill_color"):
        fill_color = ET.SubElement(node, "FillColor")
        fill_color.text = properties["fill_color"]
    
    if properties.get("text_color"):
        text_color = ET.SubElement(node, "TextColor")
        text_color.text = properties["text_color"]
    
    # Add title text
    text_elem = ET.SubElement(node, "Text")
    text_elem.text = status_data["title"]
    
    # Add font element with attributes
    font_elem = ET.SubElement(node, "Font")
    for key, value in font.items():
        font_elem.set(key, value)
    
    # Add LayoutNode element with attributes
    layout_elem = ET.SubElement(node, "LayoutNode")
    for key, value in layout_node.items():
        if key == 'WorkflowKey':
            value = value.lower()
        print(f"{key}, {value}")
        
        layout_elem.set(key, value)
    
    return node


def create_workflow_node_xml(workflow_data: Dict[str, Any]) -> ET.Element:
    """
    Create an XML Node element for a workflow entity.
    
    Args:
        workflow_data: Workflow data dictionary from entity factory
        
    Returns:
        XML Element representing the workflow node
    """
    print("CREATING WF NODE XML")
    print(workflow_data)

    if not validate_entity_data(workflow_data):
        raise ValueError("Invalid workflow data provided")
    
    position = workflow_data["position"]
    layout_node = workflow_data["layout_node"]
    
    # Create the main Node element with position attributes
    node = ET.Element("Node")
    
    # Validate position values before conversion
    try:
        node.set("Left", str(int(position["x"])))
        node.set("Top", str(int(position["y"])))
        node.set("Width", str(int(position["width"])))
        node.set("Height", str(int(position["height"])))
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid position data in workflow: x={position.get('x')}, y={position.get('y')}, width={position.get('width')}, height={position.get('height')}. Error: {e}")
    
    # Workflows have specific elements
    label_edit = ET.SubElement(node, "LabelEdit")
    label_edit.text = "False"
    
    # Shape element
    shape_elem = ET.SubElement(node, "Shape")
    shape_elem.set("Style", "Rectangle")
    shape_elem.set("Orientation", "so_0")
    
    # Alignment
    alignment = ET.SubElement(node, "Alignment")
    alignment.text = "CenterTOP"
    
    # Add LayoutNode element with attributes
    layout_elem = ET.SubElement(node, "LayoutNode")
    for key, value in layout_node.items():
        if key in ('Key', 'WorkflowKey'):
            value = value.lower()
        layout_elem.set(key, value)
    
    return node


def create_xml_root_element(nodes_count: int = 0, links_count: int = 0) -> ET.Element:
    """
    Create the root AddFlow element with current date and counts.
    
    Args:
        nodes_count: Number of nodes in the diagram
        links_count: Number of links in the diagram
        
    Returns:
        Root XML element
    """
    root = ET.Element("AddFlow")
    root.set("Nodes", str(nodes_count))
    root.set("Links", str(links_count))
    root.set("Date", datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "-07:00")
    
    # Add version element
    version = ET.SubElement(root, "Version")
    version.text = "2.2.0.2"
    
    return root


def add_node_to_xml_string(xml_string: str, entity_data: Dict[str, Any]) -> str:
    """
    Add a single node to an existing XML string.
    
    Args:
        xml_string: Existing XML layout data
        entity_data: Entity data dictionary
        
    Returns:
        Updated XML string with new node added
    """

    print("ADDING NODE XML TO STRING")
    print(entity_data)
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML string provided: {e}")
    
    # Create the appropriate node element
    if entity_data["type"] == "Status":
        new_node = create_status_node_xml(entity_data)
    elif entity_data["type"] == "Workflow":
        new_node = create_workflow_node_xml(entity_data)
    else:
        raise ValueError(f"Unknown entity type: {entity_data['type']}")
    
    # Add the new node to the root
    root.append(new_node)
    
    # Update the node count in root attributes
    current_nodes = int(root.get("Nodes", "0"))
    root.set("Nodes", str(current_nodes + 1))
    
    # Update the date
    root.set("Date", datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "-07:00")
    
    # Convert back to string
    return ET.tostring(root, encoding='unicode')


def create_link_xml_from_data(link_data: Dict[str, Any]) -> ET.Element:
    """
    Create an XML Link element from link data.
    
    Args:
        link_data: Link data dictionary from link factory
        
    Returns:
        XML Element representing the link
    """
    from workflow_designer.wfd_link_factory import create_link_xml_attributes, validate_link_data
    
    if not validate_link_data(link_data):
        raise ValueError("Invalid link data provided")
    
    print("CREATING LINK XML")
    print(link_data)
    
    # Convert link data to XML attributes format
    xml_attrs = create_link_xml_attributes(link_data)
    link_attribs = xml_attrs["linkAttribs"]
    link_props = xml_attrs["linkProps"]
    
    # Create the main Link element
    link = ET.Element("Link")
    
    # Add properties as child elements
    for prop_name, prop_value in link_props.items():
        prop_element = ET.SubElement(link, prop_name)
        prop_element.text = str(prop_value)
    
    # Add LayoutLink element
    layout_link = ET.SubElement(link, "LayoutLink")
    layout_link_data = link_attribs["LayoutLink"]
    
    for attr_name, attr_value in layout_link_data.items():
        layout_link.set(attr_name, str(attr_value))
    
    # Add Point elements if they exist
    if "Point" in link_attribs:
        for point_data in link_attribs["Point"]:
            point_element = ET.SubElement(link, "Point")
            for coord_name, coord_value in point_data.items():
                point_element.set(coord_name, str(coord_value))
    
    return link


def add_link_to_xml_string(xml_string: str, link_data: Dict[str, Any]) -> str:
    """
    Add a new link to an existing XML layout string.
    
    Args:
        xml_string: Existing XML layout data
        link_data: Link data dictionary from link factory
        
    Returns:
        Updated XML string with new link added
    """
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML string provided: {e}")

    print("ADDING LINK XML TO STRING")
    print(link_data)
    
    # Create the link element
    new_link = create_link_xml_from_data(link_data)
    
    # Add the new link to the root
    root.append(new_link)
    
    # Update the link count in root attributes
    current_links = int(root.get("Links", "0"))
    root.set("Links", str(current_links + 1))
    
    # Update the date
    root.set("Date", datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "-07:00")
    
    # Convert back to string
    link_string = ET.tostring(root, encoding='unicode')
    print(link_string)
    return link_string


def create_complete_xml_from_data(
    entities_data: List[Dict[str, Any]], 
    links_data: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Create a complete XML string from entity and link data.
    
    Args:
        entities_data: List of entity data dictionaries
        links_data: List of link data dictionaries (optional)
        
    Returns:
        Complete XML string for the layout
    """
    if links_data is None:
        links_data = []
    
    # Create root element
    root = create_xml_root_element(len(entities_data), len(links_data))
    
    # Add all entity nodes
    for entity_data in entities_data:
        if not validate_entity_data(entity_data):
            raise ValueError(f"Invalid entity data for key: {entity_data.get('key', 'unknown')}")
        
        if entity_data["type"] == "Status":
            node = create_status_node_xml(entity_data)
        elif entity_data["type"] == "Workflow":
            node = create_workflow_node_xml(entity_data)
        else:
            raise ValueError(f"Unknown entity type: {entity_data['type']}")
        
        root.append(node)
    
    # Add links 
    for link_data in links_data:
        link_xml = create_link_xml_from_data(link_data)
        root.append(link_xml)
    
    return ET.tostring(root, encoding='unicode')


def update_xml_node_position(xml_string: str, node_key: str, new_position: Dict[str, float]) -> str:
    """
    Update the position of a specific node in XML.
    
    Args:
        xml_string: Existing XML layout data
        node_key: Key of the node to update
        new_position: New position dictionary
        
    Returns:
        Updated XML string
    """
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML string provided: {e}")
    
    # Find the node with matching key
    for node in root.findall("Node"):
        layout_node = node.find("LayoutNode")
        if layout_node is not None and layout_node.get("Key") == node_key:
            # Update position attributes
            node.set("Left", str(int(new_position["x"])))
            node.set("Top", str(int(new_position["y"])))
            node.set("Width", str(int(new_position["width"])))
            node.set("Height", str(int(new_position["height"])))
            break
    else:
        raise ValueError(f"Node with key {node_key} not found in XML")
    
    # Update the date
    root.set("Date", datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "-07:00")
    
    return ET.tostring(root, encoding='unicode')


def remove_node_from_xml(xml_string: str, node_key: str) -> str:
    """
    Remove a node from XML by its key.
    
    Args:
        xml_string: Existing XML layout data
        node_key: Key of the node to remove
        
    Returns:
        Updated XML string with node removed
    """
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML string provided: {e}")
    
    # Find and remove the node with matching key
    for node in root.findall("Node"):
        layout_node = node.find("LayoutNode")
        if layout_node is not None and layout_node.get("Key") == node_key:
            root.remove(node)
            # Update the node count
            current_nodes = int(root.get("Nodes", "0"))
            root.set("Nodes", str(max(0, current_nodes - 1)))
            break
    else:
        raise ValueError(f"Node with key {node_key} not found in XML")
    
    # Update the date
    root.set("Date", datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "-07:00")
    
    return ET.tostring(root, encoding='unicode')


def format_xml_string(xml_string: str) -> str:
    """
    Format XML string with proper indentation for readability.
    
    Args:
        xml_string: Raw XML string
        
    Returns:
        Formatted XML string
    """
    try:
        root = ET.fromstring(xml_string)
        ET.indent(root, space="  ")  # 2-space indentation
        return ET.tostring(root, encoding='unicode')
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML string provided: {e}")


def extract_entities_from_xml(xml_string: str) -> List[Dict[str, Any]]:
    """
    Extract entity data dictionaries from XML string.
    This is useful for round-trip operations.
    
    Args:
        xml_string: XML layout data
        
    Returns:
        List of entity data dictionaries
    """
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML string provided: {e}")
    
    entities = []
    
    for node in root.findall("Node"):
        layout_node = node.find("LayoutNode")
        if layout_node is None:
            continue
        
        # Extract position
        position = {
            "x": float(node.get("Left", "0")),
            "y": float(node.get("Top", "0")),
            "width": float(node.get("Width", "53")),
            "height": float(node.get("Height", "53"))
        }
        
        # Extract basic properties
        entity_data = {
            "key": layout_node.get("Key", ""),
            "type": layout_node.get("Type", ""),
            "position": position,
            "workflow_key": layout_node.get("WorkflowKey", ""),
            "layout_node": dict(layout_node.attrib)
        }
        
        # Extract title from Text element
        text_elem = node.find("Text")
        entity_data["title"] = text_elem.text if text_elem is not None else ""
        
        # Extract properties
        properties = {}
        for prop in ["FillColor", "TextColor", "DrawColor"]:
            elem = node.find(prop)
            if elem is not None:
                properties[prop.lower()] = elem.text
        entity_data["properties"] = properties
        
        # Extract font properties
        font_elem = node.find("Font")
        entity_data["font"] = dict(font_elem.attrib) if font_elem is not None else {}
        
        entities.append(entity_data)
    
    return entities
