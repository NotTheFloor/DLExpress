from typing import Optional
from dataclasses import dataclass

@dataclass
class AIProfile:
    """Dataclass to store DocLink AI Profile data."""

    AIProfileID: int
    Created: str
    Modified: str
    ModifiedBy: int
    ProfileName: str
    DataSourceID: str
    SourceTable: Optional[bool] = None
    QueryText: str = 'ERROR!!'      # Should not ever default value here and 
    SingleTable: bool = False       # below
    PropsInNotReq: bool = False
