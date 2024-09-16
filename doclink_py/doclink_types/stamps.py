from typing import Optional
from dataclasses import dataclass
from uuid import UUID

@dataclass
class DistributionStampField:
    """Dataclass to store DocLink distribution stamp field data."""

    DynamicUIFieldId: int
    DynamicUIId: UUID
    Name: str
    Caption: str
    Description: str
    LabelAlignment: int
    CanEdit: bool
    Required: bool
    Visible: bool
    MultiLine: bool
    JustifyWidth: bool
    MaxLength: int
    MinWidth: int
    EditHeight: int
    EditWidth: int
    Section: int
    Sequence: int
    Mapping: int
    ControlType: int
    PropertyId: int
    DataType: int
    DecimalPlaces: int
    HasLookup: bool
    SystemLookupId: int
    DisplayFieldName: str
    ValueFieldName: str
    ShowLookupButton: bool
    UseHotKey: bool
    CausesValidation: bool
    ValidationSql: str
    DefaultValidationValue: str
    Created: str
    CreatedBy: int
    Modified: str
    ModifiedBy: int
    ShowCaption: bool
    Process: bool
    ProcessingSequence: int
    Value2FieldName: str
    UseInvariantCulture: bool
    BeginLine: bool
    DefaultSystemLookupId: int
    DefaultDisplayFieldName: str
    DefaultValueFieldName: str
    DefaultValue2FieldName: str
    CustomLabel: bool
    LabelFont: str
    LabelSize: int
    LabelStyle: int
    LabelColor: int
    ValidateNumber: bool
    ValidateNumOp: int
    ValidateNumVal1: str
    ValidateNumVal2: str
    ValidateNumUseFields: bool
    CalculatedField: bool
    Calculation: str
    EditIf: bool
    EditIfOp: int
    EditIfFieldId: UUID
    EditIfValueMember: int
    EditIfValue: str
    RequiredIf: bool
    RequiredIfOp: int
    RequiredIfFieldId: UUID
    RequiredIfValueMember: int
    RequiredIfValue: str
    DefaultFromField: bool
    DefaultFieldId: UUID
    DefaultFieldMember: int
    ClearFilteredValsOnChange: bool
    SyncWhenDefaultFieldValChanges: bool
    IsSum: bool
    SumFieldId: UUID
    ReferenceID: UUID
    IncludeInTemplate: bool

    @property
    def FormattedDataType(self) -> str:
        match self.DataType:
            case 0:
                return "[varchar](250) NULL"
            case 3:
                return "[smallint]"
            case 2:
                return "[datetime]"
            case 1 | 4:
                return "[decimal](18, 2) NULL"

            case _:
                raise Exception(
                    "INVALID_DATA_TYPE",
                    "Invalid data type in match statement.",
                )

    @property
    def UserPrompt(self) -> str:
        return self.Caption.replace(" ", "").replace("#", "No")

    @property
    def prompt_string(self) -> str:
        return f",[{self.UserPrompt}]\r\n\t"

    @property
    def prompt_type_string(self) -> str:
        return f",[{self.UserPrompt}] {self.FormattedDataType}\r\n\t"

    @property
    def SelectStatement(self) -> str:
        match self.DataType:
            case 0 | 2 | 3:
                return f",[{self.DynamicUIFieldId}] --{self.UserPrompt}"
            case 1 | 4:
                return f",REPLACE([{self.DynamicUIFieldId}],'','','''') --{self.UserPrompt}"

            case _:
                raise Exception(
                    "INVALID_DATA_TYPE",
                    "Invalid data type in match statement.",
                )

    @property
    def select_statement_string(self) -> str:
        return self.SelectStatement + "\r\n\t"

    @property
    def TableName(self) -> str:
        return self.Caption


@dataclass
class DistributionStamp:
    """Dataclass to store DocLink distribution stamp data."""

    DynamicUiId: UUID
    DynamicUISecurityId: int
    Name: str
    Description: str
    HotKey: int
    HostInViewerTab: bool
    LaunchFromSearchResults: bool
    UIHostId: int
    LogicComponentId: int
    ViewerHostId: int
    HostWindowId: int
    Created: str
    CreatedBy: int
    Modified: str
    ModifiedBy: int
    ClientTabId: int
    HostInClientTab: bool
    ScriptMajorVersion: str
    ObjectScriptBuildNumber: int
    DataScriptBuildNumber: int
    CanAttach: bool
    AttachmentDocTypeId: int
    CanAttachFromExistingDocs: bool
    CanImportLineItemsFromExistingDoc: bool
    DocumentImportQueryName: str
    DocumentImportQueryDocTypes: str
    DocumentImportQueryProperties: str
    CombineAttachedDocs: bool
    CanAttachFromFileSystem: bool
    CombineAttachedFiles: bool
    AttachmentFetchQueryName: str
    AttachmentFetchDocTypes: str
    AttachmentFetchProperties: str
    AttachmentPropId: int
    CanAttachAtHeader: bool
    WSGatewayProxyAssemblyName: str
    WSGatewayProxyTypeName: str
    DistributionStampFields: Optional[list[DistributionStampField]] = None
