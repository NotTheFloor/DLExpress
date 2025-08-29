"""
Link factory utilities for workflow designer.
This module provides Qt-independent functions for generating link data dictionaries
that can be used to create visual connections and XML representations.
"""

import uuid
from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from workflow_designer.wfd_scene import WFEntity, WorkflowStatusLine

from workflow_designer.wfd_logger import logger


def generate_unique_link_id() -> str:
    """Generate a unique link ID for XML representation"""
    return str(uuid.uuid4()).lower()


def create_link_data(source: Union['WFEntity', 'WorkflowStatusLine'], 
                    target: Union['WFEntity', 'WorkflowStatusLine'],
                    waypoints: List[tuple] = None) -> Dict[str, Any]:
    """
    Create link data dictionary for connecting two entities or status lines.
    
    Args:
        source: Source entity or status line
        target: Target entity or status line
        waypoints: Optional list of (x, y) waypoint coordinates
        
    Returns:
        Link data dictionary ready for XML generation and visual creation
    """
    if waypoints is None:
        waypoints = []
    
    # Generate unique link ID
    link_id = generate_unique_link_id()
    
    # Determine source key and entity
    source_key, source_entity = _extract_connection_info(source)
    target_key, target_entity = _extract_connection_info(target)
    
    if not source_key or not target_key:
        raise ValueError("Invalid source or target - unable to extract connection keys")
    
    # Create link data structure
    link_data = {
        "id": link_id,
        "source": {
            "key": source_key,
            "entity": source_entity,
            "type": _get_connection_type(source)
        },
        "target": {
            "key": target_key, 
            "entity": target_entity,
            "type": _get_connection_type(target)
        },
        "waypoints": waypoints,
        "properties": {
            "draw_color": "-16777216",  # Black
            "shadow": "False",
            "dash_style": "0"
        },
        "created_at": datetime.now().isoformat()
    }
    
    logger.debug(f"Created link data: {source_key} -> {target_key}")
    return link_data


def create_link_xml_attributes(link_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert link data to XML attributes format.
    
    Args:
        link_data: Link data dictionary from create_link_data
        
    Returns:
        Dictionary with linkAttribs and linkProps for XML generation
    """
    source = link_data["source"]
    target = link_data["target"]
    waypoints = link_data["waypoints"]
    properties = link_data["properties"]
    
    # Create LayoutLink attributes
    layout_link = {
        "OrgKey": source["key"],
        "DstKey": target["key"]
    }
    
    # Create Point elements for waypoints
    point_elements = []
    for i, (x, y) in enumerate(waypoints):
        point_elements.append({
            "X": str(float(x)),
            "Y": str(float(y))
        })
    
    # Assemble final attributes structure
    link_attribs = {
        "LayoutLink": layout_link
    }
    
    if point_elements:
        link_attribs["Point"] = point_elements
    
    link_props = {
        "DrawColor": properties["draw_color"],
        "Shadow": properties["shadow"],
        "DashStyle": properties["dash_style"]
    }
    
    return {
        "linkAttribs": link_attribs,
        "linkProps": link_props
    }


def create_connection_between_selections(selected_items: List[Union['WFEntity', 'WorkflowStatusLine']], 
                                       target: Union['WFEntity', 'WorkflowStatusLine']) -> List[Dict[str, Any]]:
    """
    Create multiple link data dictionaries connecting selected items to a target.
    
    Args:
        selected_items: List of selected entities or status lines (sources)
        target: Target entity or status line
        
    Returns:
        List of link data dictionaries
    """
    if not selected_items:
        logger.warning("No selected items provided for connection creation")
        return []
    
    if target in selected_items:
        logger.warning("Target is in selected items - cannot connect to self")
        return []
    
    link_data_list = []
    
    for source in selected_items:
        try:
            link_data = create_link_data(source, target)
            link_data_list.append(link_data)
            logger.debug(f"Created connection from {_get_connection_description(source)} to {_get_connection_description(target)}")
        except Exception as e:
            logger.error(f"Failed to create connection from {source} to {target}: {e}")
            continue
    
    logger.info(f"Created {len(link_data_list)} connection(s) to target")
    return link_data_list


def _extract_connection_info(item: Union['WFEntity', 'WorkflowStatusLine']) -> tuple[Optional[str], Optional['WFEntity']]:
    """
    Extract connection key and parent entity from an item.
    
    Args:
        item: Entity or status line
        
    Returns:
        Tuple of (connection_key, parent_entity)
    """
    if hasattr(item, 'status_key') and hasattr(item, 'workflow'):
        # WorkflowStatusLine
        if item.status_key:
            return item.status_key, item.workflow
        else:
            logger.warning(f"WorkflowStatusLine has no status_key: {item}")
            return None, None
    elif hasattr(item, 'entityKey'):
        # WFEntity (status or workflow)
        return item.entityKey, item
    else:
        logger.error(f"Unknown item type for connection: {type(item)}")
        return None, None


def _get_connection_type(item: Union['WFEntity', 'WorkflowStatusLine']) -> str:
    """Get connection type for an item"""
    if hasattr(item, 'status_key') and hasattr(item, 'workflow'):
        return "workflow_status_line"
    elif hasattr(item, 'entityKey'):
        if hasattr(item, 'statuses'):
            return "workflow" 
        else:
            return "status"
    else:
        return "unknown"


def _get_connection_description(item: Union['WFEntity', 'WorkflowStatusLine']) -> str:
    """Get human-readable description of connection item"""
    if hasattr(item, 'status_title'):
        return f"status line '{item.status_title}'"
    elif hasattr(item, 'title'):
        entity_type = "workflow" if hasattr(item, 'statuses') else "status"
        return f"{entity_type} '{item.title}'"
    else:
        return f"unknown item ({type(item).__name__})"


def validate_link_data(link_data: Dict[str, Any]) -> bool:
    """
    Validate that link data has required structure.
    
    Args:
        link_data: Link data dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check required top-level keys
        required_keys = ["id", "source", "target", "waypoints", "properties"]
        for key in required_keys:
            if key not in link_data:
                logger.error(f"Missing required key in link data: {key}")
                return False
        
        # Check source/target structure
        for endpoint in ["source", "target"]:
            endpoint_data = link_data[endpoint]
            if not isinstance(endpoint_data, dict):
                logger.error(f"Link data {endpoint} is not a dictionary")
                return False
            
            for req_key in ["key", "entity", "type"]:
                if req_key not in endpoint_data:
                    logger.error(f"Missing {req_key} in link data {endpoint}")
                    return False
        
        # Validate waypoints is a list
        if not isinstance(link_data["waypoints"], list):
            logger.error("Link data waypoints is not a list")
            return False
        
        # Validate properties is a dict
        if not isinstance(link_data["properties"], dict):
            logger.error("Link data properties is not a dictionary")
            return False
        
        logger.debug("Link data validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Error validating link data: {e}")
        return False