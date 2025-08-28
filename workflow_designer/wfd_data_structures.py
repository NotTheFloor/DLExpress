"""
Data structures for workflow designer entities.
This module defines standard data dictionary structures for creating workflow
and status entities, designed for loose coupling and non-Qt usage.
"""

from typing import Dict, Any, Optional, Union
from dataclasses import dataclass


@dataclass
class Position:
    """Position and size information for entities"""
    x: float
    y: float
    width: float = 53.0  # Default status size
    height: float = 53.0  # Default status size


@dataclass
class EntityProperties:
    """Common properties for workflow entities"""
    fill_color: Optional[str] = None
    text_color: Optional[str] = None
    draw_color: Optional[str] = None
    shadow: Optional[str] = None


@dataclass
class FontProperties:
    """Font properties for entity text"""
    name: str = "Microsoft Sans Serif"
    size: str = "8.25"
    bold: str = "True"
    italic: str = "False"
    strikeout: str = "False"
    underline: str = "False"


def create_position_dict(x: float, y: float, width: float = 53.0, height: float = 53.0) -> Dict[str, float]:
    """Create a position dictionary"""
    # Validate parameters to prevent None values
    if x is None:
        raise ValueError("Position x coordinate cannot be None")
    if y is None:
        raise ValueError("Position y coordinate cannot be None")
    if width is None:
        raise ValueError("Position width cannot be None")
    if height is None:
        raise ValueError("Position height cannot be None")
    
    return {
        "x": float(x),
        "y": float(y),
        "width": float(width),
        "height": float(height)
    }


def create_properties_dict(
    fill_color: Optional[str] = None,
    text_color: Optional[str] = None,
    draw_color: Optional[str] = None,
    shadow: Optional[str] = None
) -> Dict[str, Any]:
    """Create a properties dictionary with default values"""
    return {
        "fill_color": fill_color or "-1",  # Default white background
        "text_color": text_color or "-16777216",  # Default black text
        "draw_color": draw_color or "-16777216",  # Default black outline
        "shadow": shadow
    }


def create_font_dict(
    name: str = "Microsoft Sans Serif",
    size: str = "8.25",
    bold: str = "True",
    italic: str = "False",
    strikeout: str = "False",
    underline: str = "False"
) -> Dict[str, str]:
    """Create a font dictionary with default values"""
    return {
        "Name": name,
        "Size": size,
        "Bold": bold,
        "Italic": italic,
        "Strikeout": strikeout,
        "Underline": underline
    }


def create_layout_node_dict(
    key: str,
    node_type: str,
    workflow_key: str,
    can_delete: str = "True",
    is_hidden: str = "False",
    is_default: str = "False",
    class_name: Optional[str] = None
) -> Dict[str, str]:
    """Create a layout node dictionary for XML attributes"""
    layout_node = {
        "Key": key,
        "Type": node_type,
        "CanDelete": can_delete,
        "WorkflowKey": workflow_key,
        "IsHidden": is_hidden,
        "IsDefault": is_default
    }
    
    if class_name:
        layout_node["Class"] = class_name
    elif node_type == "Status":
        layout_node["Class"] = "StatusLayoutNode"
    elif node_type == "Workflow":
        layout_node["Class"] = "WorkflowLayoutNode"
    
    return layout_node


def create_status_data_dict(
    key: str,
    position: Dict[str, float],
    title: str,
    workflow_key: str,
    properties: Optional[Dict[str, Any]] = None,
    font: Optional[Dict[str, str]] = None,
    is_default: bool = False
) -> Dict[str, Any]:
    """Create a complete status data dictionary"""
    props = properties or create_properties_dict()
    font_props = font or create_font_dict()
    
    return {
        "key": key,
        "type": "Status",
        "position": position,
        "title": title,
        "workflow_key": workflow_key,
        "properties": props,
        "font": font_props,
        "layout_node": create_layout_node_dict(
            key=key,
            node_type="Status",
            workflow_key=workflow_key,
            is_default=str(is_default).capitalize()
        )
    }


def create_workflow_data_dict(
    key: str,
    position: Dict[str, float],
    title: str,
    workflow_key: str,
    properties: Optional[Dict[str, Any]] = None,
    font: Optional[Dict[str, str]] = None,
    tooltip: Optional[str] = None
) -> Dict[str, Any]:
    """Create a complete workflow data dictionary"""
    # Workflows typically have different default dimensions
    if "width" not in position:
        position["width"] = 127.0
    if "height" not in position:
        position["height"] = 174.0
        
    props = properties or create_properties_dict()
    font_props = font or create_font_dict()
    
    layout_node = create_layout_node_dict(
        key=key,
        node_type="Workflow",
        workflow_key=workflow_key,
        class_name="WorkflowLayoutNode"
    )
    
    if tooltip:
        layout_node["Tooltip"] = tooltip
    
    return {
        "key": key,
        "type": "Workflow",
        "position": position,
        "title": title,
        "workflow_key": workflow_key,
        "properties": props,
        "font": font_props,
        "layout_node": layout_node,
        "tooltip": tooltip
    }


def validate_entity_data(entity_data: Dict[str, Any]) -> bool:
    """Validate that an entity data dictionary has required fields"""
    required_fields = ["key", "type", "position", "title", "workflow_key", "properties", "layout_node"]
    
    for field in required_fields:
        if field not in entity_data:
            return False
    
    # Validate position has required coordinates
    pos = entity_data["position"]
    if not all(coord in pos for coord in ["x", "y", "width", "height"]):
        return False
    
    # Validate type is valid
    if entity_data["type"] not in ["Status", "Workflow"]:
        return False
    
    return True


def validate_position_dict(position: Dict[str, float]) -> bool:
    """Validate that a position dictionary has required fields"""
    required_fields = ["x", "y", "width", "height"]
    return all(field in position and isinstance(position[field], (int, float)) for field in required_fields)