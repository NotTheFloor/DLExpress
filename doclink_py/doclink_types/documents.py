from typing import Optional
from dataclasses import dataclass
from uuid import UUID
from .propertys import *

@dataclass
class DocumentTypeProperty:
    """Dataclass to store DocLink document type property data."""

    DocumentTypePropertyId: int
    Created: str
    Modified: str
    ParentId: int
    ModifiedBy: int
    PropertyId: int
    SequenceNumber: int
    IndexingRelevance: int
    PropertyType: int
    ParentDocumentTypePropertyGUID: str
    DocumentTypePropertyGUID: str
    PropertyValidations: Optional[str] = None
    PropertyTypeAlias = Property  # To avoid type warnings
    Property: Optional[PropertyTypeAlias] = None

    @property
    def Name(self) -> str:
        return self.Property.FormattedUserPrompt

    @property
    def TableName(self) -> str:
        table_name = self.Name
        # if self.PropertyType == 2:
        #     table_name = "   " + table_name
        return table_name


@dataclass
class DocumentType:
    """Dataclass to store DocLink document type data."""

    DocumentTypeId: int
    Created: str
    Modified: str
    ParentID: int
    ModifiedBy: int
    Name: str
    Description: str
    KeyDocumentTypePropertyGUID: str
    DocumentTypeGUID: str
    DocumentTypeTag: str
    AIEnabled: bool
    RIEnabled: bool
    RIMethod: int
    AIMethod: int
    Active: bool
    AIAfterManualIndexAction: int
    FullTextEnabled: bool
    DocumentTypeProperties: Optional[list[DocumentTypeProperty]] = None
    AIObjectProgID: Optional[str] = None

    def get_property_by_name(self, property_name: str) -> DocumentTypeProperty:
        for property in self.DocumentTypeProperties:
            if property.Name == property_name:
                return property

        raise Exception(
            "PROPERTY_NOT_FOUND",
            f"Property {property_name} not found in document type {self.Name}",
        )

