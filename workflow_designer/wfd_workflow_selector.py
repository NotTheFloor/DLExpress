"""
Workflow selection dialog for choosing existing workflows to add to the scene.
"""

from typing import Optional, List, Dict, Any, TYPE_CHECKING
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QPushButton, QLabel, QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

if TYPE_CHECKING:
    from workflow_designer.scene_manager import WorkflowSceneManager

from workflow_designer.wfd_logger import logger


class WorkflowSelectorDialog(QDialog):
    """Dialog for selecting an existing workflow to add to the scene"""
    
    def __init__(self, scene_manager: 'WorkflowSceneManager', current_scene_key: str, parent=None):
        super().__init__(parent)
        self.scene_manager = scene_manager
        self.current_scene_key = current_scene_key
        self.selected_workflow: Optional[Dict[str, Any]] = None
        
        self.setWindowTitle("Select Workflow to Add")
        self.setModal(True)
        self.resize(600, 400)
        
        self._setup_ui()
        self._populate_workflows()
        
    def _setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title label
        title_label = QLabel("Select a workflow to add to the current scene:")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left side - workflow list
        left_widget = self._create_workflow_list_widget()
        splitter.addWidget(left_widget)
        
        # Right side - workflow details
        right_widget = self._create_details_widget()
        splitter.addWidget(right_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 300])
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("Add Workflow")
        self.ok_button.setEnabled(False)
        self.ok_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
    def _create_workflow_list_widget(self):
        """Create the workflow list widget"""
        from PySide6.QtWidgets import QWidget
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # List label
        list_label = QLabel("Available Workflows:")
        layout.addWidget(list_label)
        
        # Workflow list
        self.workflow_list = QListWidget()
        self.workflow_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.workflow_list.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.workflow_list)
        
        return widget
    
    def _create_details_widget(self):
        """Create the workflow details widget"""
        from PySide6.QtWidgets import QWidget
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Details label
        details_label = QLabel("Workflow Details:")
        layout.addWidget(details_label)
        
        # Details text area
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        layout.addWidget(self.details_text)
        
        # Status list label
        status_label = QLabel("Statuses in this workflow:")
        layout.addWidget(status_label)
        
        # Status list
        self.status_list = QListWidget()
        self.status_list.setMaximumHeight(180)
        layout.addWidget(self.status_list)
        
        layout.addStretch()
        
        return widget
        
    def _populate_workflows(self):
        """Populate the workflow list with available workflows"""
        available_workflows = self._get_available_workflows()
        
        for workflow in available_workflows:
            item = QListWidgetItem(workflow["Title"])
            item.setData(Qt.UserRole, workflow)
            
            # Add tooltip with workflow key
            item.setToolTip(f"Workflow Key: {workflow['WorkflowKey']}")
            
            self.workflow_list.addItem(item)
            
        if available_workflows:
            # Auto-select first item
            self.workflow_list.setCurrentRow(0)
        else:
            self.details_text.setText("No workflows available to add.")
            
        logger.debug(f"Populated workflow selector with {len(available_workflows)} workflows")
    
    def _get_available_workflows(self) -> List[Dict[str, Any]]:
        """Get workflows that can be added to the current scene"""
        available = []
        
        # Get all workflows except the current one being displayed
        for workflow in self.scene_manager.workflows:
            workflow_key = str(workflow.WorkflowKey)
            
            # Skip if this is the current scene's workflow
            if workflow_key.lower() == self.current_scene_key.lower():
                continue
                
            # Check if workflow is already in the current scene
            current_scene = self.scene_manager.wfSceneDict.get(self.current_scene_key)
            if current_scene:
                # Check if this workflow is already visually present
                existing_workflow = any(
                    wf.entityKey.lower() == workflow_key.lower() 
                    for wf in current_scene.workflows
                )
                if existing_workflow:
                    continue
            
            available.append({
                "Title": workflow.Title,
                "WorkflowKey": workflow_key,
                "WorkflowID": workflow.WorkflowID
            })
            
        return available
    
    def _on_selection_changed(self):
        """Handle workflow selection change"""
        current_item = self.workflow_list.currentItem()
        
        if current_item is None:
            self.ok_button.setEnabled(False)
            self.details_text.clear()
            self.status_list.clear()
            return
            
        workflow = current_item.data(Qt.UserRole)
        self.selected_workflow = workflow
        self.ok_button.setEnabled(True)
        
        # Update details
        self._update_workflow_details(workflow)
        
    def _update_workflow_details(self, workflow: Dict[str, Any]):
        """Update the workflow details display"""
        # Update details text
        details = f"Title: {workflow['Title']}\n"
        details += f"Workflow Key: {workflow['WorkflowKey']}\n"
        details += f"Workflow ID: {workflow['WorkflowID']}"
        self.details_text.setText(details)
        
        # Update status list
        self.status_list.clear()
        
        try:
            # Get status sequence for this workflow
            status_sequence = self.scene_manager.getStatusSequence(workflow['WorkflowKey'])
            
            for status in status_sequence:
                status_item = QListWidgetItem(f"{status.Seq}. {status.Title}")
                status_item.setToolTip(f"Status Key: {status.WorkflowActivityKey}")
                self.status_list.addItem(status_item)
                
            if not status_sequence:
                no_status_item = QListWidgetItem("No statuses defined")
                no_status_item.setFlags(Qt.NoItemFlags)
                self.status_list.addItem(no_status_item)
                
        except Exception as e:
            logger.error(f"Error loading statuses for workflow {workflow['WorkflowKey']}: {e}")
            error_item = QListWidgetItem("Error loading statuses")
            error_item.setFlags(Qt.NoItemFlags)
            self.status_list.addItem(error_item)
    
    def _on_double_click(self, item: QListWidgetItem):
        """Handle double-click on workflow item"""
        if item is not None:
            self.accept()
    
    def get_selected_workflow(self) -> Optional[Dict[str, Any]]:
        """Get the selected workflow data"""
        return self.selected_workflow


def select_workflow_for_scene(
    scene_manager: 'WorkflowSceneManager',
    current_scene_key: str,
    parent=None
) -> Optional[Dict[str, Any]]:
    """
    Show workflow selection dialog and return selected workflow.
    
    Args:
        scene_manager: Scene manager with workflow data
        current_scene_key: Key of the current scene
        parent: Parent widget for the dialog
        
    Returns:
        Selected workflow data dict or None if cancelled
    """
    dialog = WorkflowSelectorDialog(scene_manager, current_scene_key, parent)
    
    if dialog.exec() == QDialog.Accepted:
        selected = dialog.get_selected_workflow()
        if selected:
            logger.info(f"User selected workflow: {selected['Title']} ({selected['WorkflowKey']})")
            return selected
    
    logger.debug("Workflow selection cancelled")
    return None