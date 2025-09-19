"""
Entity factory for creating workflow designer entities.
This module provides Qt-independent functions for creating status and workflow
entities as data dictionaries.
"""

import uuid
from typing import Dict, Any, Optional, Tuple

from doclink_py.models.workflows import WorkflowActivity

from workflow_designer.wfd_data_structures import (
    create_position_dict,
    create_properties_dict,
    create_font_dict,
    create_status_data_dict,
    create_workflow_data_dict,
    validate_entity_data
)


def generate_unique_key() -> str:
    """Generate a unique GUID key for new entities"""
    return str(uuid.uuid4())

def create_doclink_status_from_data(status_data, wf_id, seq_num):
    return WorkflowActivity(
            -1,
            "Fake",
            "Fake",
            -1,
            wf_id,
            status_data.title,
            'Unsaved Status',
            seq_num,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            -1,
            status_data.entityKey, # Honestly this is the UUID for a stamp... :(
            0,
            0,
            0,
            0,
            0,
            0
        )

def create_new_status_data(
    key: Optional[str] = None,
    position: Optional[Dict[str, float]] = None,
    title: str = "New Status",
    workflow_key: str = "",
    properties: Optional[Dict[str, Any]] = None,
    font: Optional[Dict[str, str]] = None,
    is_default: bool = False
) -> Dict[str, Any]:
    """
    Create a new status entity data dictionary.
    
    Args:
        key: Unique identifier for the status (generated if None)
        position: Position dictionary with x, y, width, height
        title: Display title for the status
        workflow_key: Key of the workflow this status belongs to
        properties: Visual properties (colors, etc.)
        font: Font properties
        is_default: Whether this is the default status for the workflow
        
    Returns:
        Complete status data dictionary ready for XML generation or Qt object creation
    """
    if key is None:
        key = generate_unique_key()
    
    if position is None:
        position = create_position_dict(100, 100)  # Default position
    
    status_data = create_status_data_dict(
        key=key,
        position=position,
        title=title,
        workflow_key=workflow_key,
        properties=properties,
        font=font,
        is_default=is_default
    )
    
    if not validate_entity_data(status_data):
        raise ValueError("Invalid status data generated")
    
    return status_data


def create_workflow_data_from_existing(
    workflow_info: Dict[str, Any],
    position: Optional[Dict[str, float]] = None,
    key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a workflow entity data dictionary from existing workflow information.
    
    Args:
        workflow_info: Dictionary containing existing workflow data (from database)
                      Expected keys: Title, WorkflowKey, and optionally other properties
        position: Position dictionary with x, y, width, height
        key: Unique identifier for this visual instance (generated if None)
        
    Returns:
        Complete workflow data dictionary ready for XML generation or Qt object creation
    """
    if key is None:
        key = generate_unique_key()
    
    if position is None:
        position = create_position_dict(100, 100, width=127.0, height=174.0)
    
    title = workflow_info.get("Title", "Unnamed Workflow")
    workflow_key = str(workflow_info.get("WorkflowKey", ""))
    tooltip = workflow_info.get("Tooltip", title)
    
    workflow_data = create_workflow_data_dict(
        key=key,
        position=position,
        title=title,
        workflow_key=workflow_key,
        tooltip=tooltip
    )
    
    if not validate_entity_data(workflow_data):
        raise ValueError("Invalid workflow data generated")
    
    return workflow_data


def create_status_at_position(
    x: float,
    y: float,
    title: str = "New Status",
    workflow_key: str = "",
    width: float = 53.0,
    height: float = 53.0,
    is_default: bool = False
) -> Dict[str, Any]:
    """
    Convenience function to create a new status at a specific position.
    
    Args:
        x, y: Position coordinates
        title: Status title
        workflow_key: Parent workflow key
        width, height: Status dimensions
        is_default: Whether this is the default status
        
    Returns:
        Complete status data dictionary
    """
    position = create_position_dict(x, y, width, height)
    return create_new_status_data(
        position=position,
        title=title,
        workflow_key=workflow_key,
        is_default=is_default
    )


def create_workflow_at_position(
    x: float,
    y: float,
    workflow_info: Dict[str, Any],
    width: float = 127.0,
    height: float = 174.0
) -> Dict[str, Any]:
    """
    Convenience function to create a workflow at a specific position.
    
    Args:
        x, y: Position coordinates
        workflow_info: Existing workflow information
        width, height: Workflow dimensions
        
    Returns:
        Complete workflow data dictionary
    """
    position = create_position_dict(x, y, width, height)
    return create_workflow_data_from_existing(workflow_info, position, workflow_info['WorkflowKey'])


def update_entity_position(
    entity_data: Dict[str, Any],
    new_x: Optional[float] = None,
    new_y: Optional[float] = None,
    new_width: Optional[float] = None,
    new_height: Optional[float] = None
) -> Dict[str, Any]:
    """
    Update the position of an existing entity data dictionary.
    
    Args:
        entity_data: Existing entity data dictionary
        new_x, new_y, new_width, new_height: New position values (None to keep current)
        
    Returns:
        Updated entity data dictionary
    """
    updated_data = entity_data.copy()
    position = updated_data["position"].copy()
    
    if new_x is not None:
        position["x"] = new_x
    if new_y is not None:
        position["y"] = new_y
    if new_width is not None:
        position["width"] = new_width
    if new_height is not None:
        position["height"] = new_height
    
    updated_data["position"] = position
    return updated_data


def update_entity_properties(
    entity_data: Dict[str, Any],
    new_title: Optional[str] = None,
    new_properties: Optional[Dict[str, Any]] = None,
    new_font: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Update the properties of an existing entity data dictionary.
    
    Args:
        entity_data: Existing entity data dictionary
        new_title: New title for the entity
        new_properties: New visual properties
        new_font: New font properties
        
    Returns:
        Updated entity data dictionary
    """
    updated_data = entity_data.copy()
    
    if new_title is not None:
        updated_data["title"] = new_title
    
    if new_properties is not None:
        updated_data["properties"] = new_properties
    
    if new_font is not None:
        updated_data["font"] = new_font
    
    return updated_data


def create_default_status_for_workflow(workflow_key: str, position: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    Create a default status for a new workflow.
    
    Args:
        workflow_key: The workflow this status belongs to
        position: Position for the status (default if None)
        
    Returns:
        Status data dictionary marked as default
    """
    return create_new_status_data(
        position=position,
        title="Default Status",
        workflow_key=workflow_key,
        is_default=True
    )
