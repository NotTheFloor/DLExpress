from dataclasses import dataclass
from uuid import UUID

@dataclass
class Workflow:
    """Dataclass to store DocLink workflow data."""

    WorkflowID: int
    Created: str
    Modified: str
    ModifiedBy: int
    Title: str
    Description: str
    FolderID: int
    SendPackets: int
    CopyDocID: int
    WorkflowKey: UUID
    RebuildLayout: int


@dataclass
class WorkflowActivity:
    """Dataclass to store DocLink workflow activity data."""

    WorkflowActivityID: int
    Created: str
    Modified: str
    ModifiedBy: int
    WorkflowID: int
    Title: str
    Description: str
    Seq: int
    IndexBefore: int
    SystemActivity: int
    TrackingNote: int
    CompleteFlag: int
    DeleteFromQueue: int
    DeleteFromDocLink: int
    SortDesc: int
    SendDrillDownOnly: int
    WorkflowActivityKey: UUID
    EnableAutoIndex: int
    RemoveStatus: int
    DynamicUIID: int
    AgeHours: int
    RequiredDocumentNote: int
    ViewActionType: int


@dataclass
class WorkflowNextActivity:
    """Dataclass to store DocLink workflow next activity data."""

    WorkflowNextActivityID: int
    WorkflowActivityID: int
    NextWorkflowActivityKey: UUID
    DefaultNextActivity: bool
    Description: str
    WorkflowNextActivityKey: UUID
    NextActivityType: int


@dataclass
class WorkflowPlacement:
    """Dataclass to store DocLink workflow placement data."""

    WorkflowPlacementId: int
    Created: str
    Modified: str
    ModifiedBy: int
    WorkflowID: int
    LayoutData: str


@dataclass
class WorkflowQueue:
    """Dataclass to store DocLink workflow queue (catagory) data."""

    WorkflowQueueID: int
    Created: str
    CreatedBy: int
    Modified: str
    ModifiedBy: int
    WorkflowID: int
    ReadOnly: bool
    Name: str
    Description: str
    Seq: int
    Code: str
