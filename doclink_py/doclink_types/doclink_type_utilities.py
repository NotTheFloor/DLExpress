from dataclasses import dataclass
from typing import TypeVar, Any, Optional

T = TypeVar('T')

# This method should be moved out of document types as its too useful
def get_object_from_list(dataList: list[T], attribute: str, value: Any) -> Optional[T]:
    return next((item for item in dataList if getattr(item, attribute) == value), None)

def get_all_objects_from_list(dataList: list[T], attribute: str, value: Any) -> Optional[T]:
    return [item for item in dataList if getattr(item, attribute) == value]
