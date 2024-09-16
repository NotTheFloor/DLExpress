from dataclasses import dataclass

@dataclass
class Property:
    """Dataclass to store DocLink property data."""

    PropertyId: int
    Created: str
    Modified: str
    ParentId: int
    ModifiedBy: int
    PropertyName: str
    UserPrompt: str
    DataType: int
    PropertyTag: str
    DecimalPlaces: int
    HasLookup: bool
    SystemLookupId: int
    ShowLookupButton: bool
    UseHotKey: bool
    CausesValidation: bool
    ValidationSql: str
    ControlType: int
    EditWidth: int
    HiddenProperty: bool
    FieldName: str

    @property
    def FormattedDataType(self) -> str:
        match self.DataType:
            case 0 | 3:
                return "[varchar](250) NULL"
            case 1:
                return "[int] NULL"
            case 2:
                return "[datetime] NULL"
            case 4:
                return "[decimal](18, 2) NULL"

            case _:
                raise Exception(
                    "INVALID_DATA_TYPE",
                    "Invalid data type in match statement.",
                )

    @property
    def FormattedUserPrompt(self):
        return self.UserPrompt.replace(" ", "").replace("#", "No").strip()

    @property
    def prompt_type_string(self) -> str:
        return f",[{self.FormattedUserPrompt}] {self.FormattedDataType}\r\n\t"

    @property
    def prompt_string(self) -> str:
        return f",[{self.FormattedUserPrompt}]\r\n\t"

    @property
    def id_string(self) -> str:
        return f",[{self.PropertyId}]\r\n\t"

