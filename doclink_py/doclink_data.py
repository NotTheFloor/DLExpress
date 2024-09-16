from doclink_py.doclink_types.propertys import Property
from doclink_py.doclink_types.documents import DocumentType
from doclink_py.doclink_types.workflows import Workflow, WorkflowActivity
from doclink_py.doclink_types.stamps import DistributionStamp, DistributionStampField

import logging
from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from typing import TYPE_CHECKING

# if TYPE_CHECKING:
from doclink_py.dapi.doclink_api import DocLinkAPI
from doclink_py.sql.doclink_sql import DocLinkSQL


@dataclass
class SPROCInfo:
    sproc_name: str
    sproc_exists: bool
    action: str = None
    sproc_identical: bool = False


class StagingTableColumType(Enum):
    """Enum to store the header types for the staging tables."""

    HEADER = "header"
    DETAIL = "detail"


class CreationType(Enum):
    DOC_TYPE = 1
    DIST_STAMP = 2
    WENNSOFT = 3


class DocLinkData:
    def __init__(self):
        self.properties: list[Property] = []
        self.document_types: list[DocumentType] = []
        self.workflows: list[Workflow] = []
        self.workflow_activities: list[WorkflowActivity] = []
        self.distribution_stamps: list[DistributionStamp] = []
        self.distribution_stamp_fields: list[DistributionStampField] = []

        self.staging_table_columns: dict[StagingTableColumType, list[str]] = {}

        self.selected_doc_type: DocumentType = None
        self.selected_dist_stamp: DistributionStamp = None

        self.selected_wf_id: int = None
        self.selected_staging_wf_id: int = None
        self.selected_staged_wf_id: int = None
        self.selected_success_wf_id: int = None
        self.selected_failed_wf_id: int = None

        self.existing_ai_profiles: list[str] = []
        self.existing_event_tasks: list[str] = []

        self.sproc_info: dict[str, SPROCInfo] = {}

    # Using dependancy injection here as we move to more functional coding
    def populate_data_types(self, doclink_handler: DocLinkAPI | DocLinkSQL) -> None:
        """Gets the document types and properties from the server."""

        logging.info("Getting document types and properties...")
        logging.debug("Getting properties...")
        self.properties = doclink_handler.get_properties()
        logging.debug("Getting document types...")
        self.document_types = doclink_handler.get_doc_types_with_props(self.properties)
        logging.debug("Getting workflows...")
        self.workflows = doclink_handler.get_workflows()
        logging.debug("Getting workflow activities...")
        self.workflow_activities = doclink_handler.get_workflow_activities()
        logging.debug("Getting AI profile names...")
        self.existing_ai_profiles = doclink_handler.get_ai_profiles()
        logging.debug("Getting event task names...")
        self.existing_event_tasks = doclink_handler.get_event_task_names()
        logging.debug("Getting distribution stamp fields...")
        self.distribution_stamp_fields = doclink_handler.get_dist_stamp_fields()
        logging.debug("Getting distribution stamps w/ fields...")
        self.distribution_stamps = doclink_handler.get_dist_stamp_with_fields()
        logging.debug("Document types and properties retrieved.")

    def populate_sproc_info(
        self, doclink_handler: DocLinkAPI | DocLinkSQL, sproc_names: list[str]
    ):
        """Gets the document types and properties from the server."""

        logging.info("Getting stored procedure info...")
        for sproc_name in sproc_names:
            exists = doclink_handler.check_if_sproc_exists(sproc_name) > 0
            logging.info(f"{sproc_name} exists: {exists}")

            if sproc_name in self.sproc_info:
                logging.warning(
                    f"Stored procedure info already exists for {sproc_name}. Refreshing"
                )
                self.sproc_info[sproc_name].sproc_exists = exists
                continue

            self.sproc_info[sproc_name] = SPROCInfo(sproc_name, exists)

    def identical_sproc_check(
        self, doclink_handler: DocLinkAPI | DocLinkSQL, sproc_names: list[str]
    ):
        """Checks if the stored procedures are identical."""

        for sproc_name in sproc_names:
            if not self.sproc_info[sproc_name].sproc_exists:
                continue

            self.sproc_info[
                sproc_name
            ].sproc_identical = doclink_handler.compare_sproc_from_file(sproc_name)

    def set_sproc_action(self, sproc_name, action):
        """Sets the action for the given stored procedure."""

        if sproc_name not in self.sproc_info:
            raise Exception(
                "INVALID_SPROC_NAME",
                f"Invalid stored procedure name: {sproc_name}",
            )
        self.sproc_info[sproc_name].action = action

    def set_selected_doc_by_id(self, document_type_id: int) -> None:
        """Sets the selected document type by its ID."""

        self.selected_doc_type = self.get_document_type_by_id(document_type_id)

    def set_selected_doc_by_name(self, document_type_name: str) -> None:
        """Sets the selected document type by its name."""

        self.selected_doc_type = self.get_document_type_by_name(document_type_name)

    def set_selected_dist_stamp_by_id(self, distribution_stamp_id: int) -> None:
        """Sets the selected distribution stamp by its ID."""

        self.selected_dist_stamp = self.get_distribution_stamp_by_id(
            distribution_stamp_id
        )

    def set_selected_dist_stamp_by_uuid_id(self, distribution_stamp_uuid_id: UUID):
        """Sets the selected distribution stamp by its ID."""

        self.selected_dist_stamp = self.get_distribution_stamp_by_uuid_id(
            distribution_stamp_uuid_id
        )

    def set_selected_dist_stamp_by_name(self, distribution_stamp_name: str) -> None:
        """Sets the selected distribution stamp by its name."""

        self.selected_dist_stamp = self.get_distribution_stamp_by_name(
            distribution_stamp_name
        )

    def set_selected_object_by_name(self, creation_type: CreationType, name: str):
        """Sets the selected object by its name."""

        if creation_type == CreationType.DOC_TYPE:
            self.set_selected_doc_by_name(name)
        elif creation_type == CreationType.DIST_STAMP:
            self.set_selected_dist_stamp_by_name(name)
        else:
            raise Exception(
                "INVALID_CREATION_TYPE",
                f"Invalid creation type: {creation_type}",
            )

    def get_distribution_stamp_by_id(
        self, distribution_stamp_id: int
    ) -> DistributionStamp:
        """Gets a distribution stamp by its ID."""

        for dist_stamp in self.distribution_stamps:
            if dist_stamp.DynamicUISecurityId == distribution_stamp_id:
                return dist_stamp

        raise Exception(
            "INVALID_DISTRIBUTION_STAMP_ID",
            f"Invalid distribution stamp ID: {distribution_stamp_id}",
        )

    def get_distribution_stamp_by_uuid_id(
        self, distribution_stamp_uuid_id: UUID
    ) -> DistributionStamp:
        """Gets a distribution stamp by its ID."""

        for dist_stamp in self.distribution_stamps:
            if dist_stamp.DynamicUiId == distribution_stamp_uuid_id:
                return dist_stamp

        raise Exception(
            "INVALID_DISTRIBUTION_STAMP_ID",
            f"Invalid distribution stamp ID: {distribution_stamp_uuid_id}",
        )

    def get_distribution_stamp_by_name(
        self, distribution_stamp_name: str
    ) -> DistributionStamp:
        """Gets a distribution stamp by its name."""

        for dist_stamp in self.distribution_stamps:
            if dist_stamp.Name == distribution_stamp_name:
                return dist_stamp

        raise Exception(
            "INVALID_DISTRIBUTION_STAMP_NAME",
            f"Invalid distribution stamp name: {distribution_stamp_name}",
        )

    def get_distribution_stamp_field_by_name(
        self, distribution_stamp_field_name: str
    ) -> DistributionStampField:
        """Gets a distribution stamp field by its name."""

        for dist_stamp_field in self.distribution_stamp_fields:
            if dist_stamp_field.Name == distribution_stamp_field_name:
                return dist_stamp_field

        raise Exception(
            "INVALID_DISTRIBUTION_STAMP_FIELD_NAME",
            f"Invalid distribution stamp field name: {distribution_stamp_field_name}",
        )

    def get_distribution_stamp_field_by_caption(
        self, distribution_stamp_field_name: str
    ) -> DistributionStampField:
        """Gets a distribution stamp field by its name."""

        for dist_stamp_field in self.distribution_stamp_fields:
            if dist_stamp_field.Caption == distribution_stamp_field_name:
                return dist_stamp_field

        raise Exception(
            "INVALID_DISTRIBUTION_STAMP__FIELD_CAPTION",
            f"Invalid distribution stamp field caption: {distribution_stamp_field_name}",
        )

    def get_document_type_by_id(self, document_type_id: int) -> DocumentType:
        """Gets a document type by its ID."""

        for doc_type in self.document_types:
            if doc_type.DocumentTypeId == document_type_id:
                return doc_type

        raise Exception(
            "INVALID_DOCUMENT_TYPE_ID",
            f"Invalid document type ID: {document_type_id}",
        )

    def get_document_type_by_name(self, document_type_name: str) -> DocumentType:
        """Gets a document type by its name."""

        for doc_type in self.document_types:
            if doc_type.Name == document_type_name:
                return doc_type

        raise Exception(
            "INVALID_DOCUMENT_TYPE_NAME",
            f"Invalid document type name: {document_type_name}",
        )

    def get_property_by_id(self, property_id: int) -> Property:
        """Gets a property by its ID."""

        for prop in self.properties:
            if prop.PropertyId == property_id:
                return prop

        raise Exception("INVALID_PROPERTY_ID", f"Invalid property ID: {property_id}")

    def get_property_by_prompt(self, property_name: str) -> Property:
        """Gets a property by its name."""

        for prop in self.properties:
            if prop.UserPrompt == property_name:
                return prop

        raise Exception(
            "INVALID_PROPERTY_NAME",
            f"Invalid property name during prompt: {property_name}",
        )

    def get_property_by_fprompt(self, property_name: str) -> Property:
        """Gets a property by its name."""

        property_name = property_name.strip()
        for prop in self.properties:
            if prop.FormattedUserPrompt == property_name:
                return prop

        raise Exception(
            "INVALID_PROPERTY_NAME",
            f"Invalid property name during fprompt: {property_name}",
        )

    def get_workflow_by_id(self, workflow_id: int) -> Workflow:
        """Gets a workflow by its ID."""

        for workflow in self.workflows:
            if workflow.WorkflowID == workflow_id:
                return workflow

        raise Exception("INVALID_WORKFLOW_ID", f"Invalid workflow ID: {workflow_id}")

    def get_workflow_by_name(self, workflow_name: str) -> Workflow:
        """Gets a workflow by its name."""

        for workflow in self.workflows:
            if workflow.Title == workflow_name:
                return workflow

        raise Exception(
            "INVALID_WORKFLOW_NAME", f"Invalid workflow name: {workflow_name}"
        )

    def get_activities_by_wf_name(self, workflow_name: str) -> list[WorkflowActivity]:
        """Gets a workflow by its name."""

        workflow = self.get_workflow_by_name(workflow_name)

        return self.get_activities_by_wf_id(workflow.WorkflowID)

    def get_activities_by_wf_id(self, workflow_id: int) -> list[WorkflowActivity]:
        """Gets a workflow by its name."""

        return [
            activity
            for activity in self.workflow_activities
            if activity.WorkflowID == workflow_id
        ]

    def get_workflow_activity_by_id(
        self,
        workflow_activity_id: int,
        workflow_id: int = None,
        workflow_name: str = None,
    ) -> WorkflowActivity:
        """Gets a workflow activity by its ID."""

        activities_list = self.workflow_activities
        if workflow_id is not None:
            activities_list = self.get_activities_by_wf_id(workflow_id)
        elif workflow_name is not None:
            activities_list = self.get_activities_by_wf_name(workflow_name)

        for workflow_activity in activities_list:
            if workflow_activity.WorkflowActivityID == workflow_activity_id:
                return workflow_activity

        raise Exception(
            "INVALID_WORKFLOW_ACTIVITY_ID",
            f"Invalid workflow activity ID: {workflow_activity_id}",
        )

    def get_workflow_activity_by_name(
        self,
        workflow_activity_name: str,
        workflow_id: int = None,
        workflow_name: str = None,
    ) -> WorkflowActivity:
        """Gets a workflow activity by its name."""

        activities_list = self.workflow_activities
        if workflow_id is not None:
            activities_list = self.get_activities_by_wf_id(workflow_id)
        elif workflow_name is not None:
            activities_list = self.get_activities_by_wf_name(workflow_name)

        for workflow_activity in activities_list:
            if workflow_activity.Title == workflow_activity_name:
                return workflow_activity

        raise Exception(
            "INVALID_WORKFLOW_ACTIVITY_NAME",
            f"Invalid workflow activity name: {workflow_activity_name}",
        )

    def sprocs_exists(self, sproc_name) -> bool:
        """Returns whether the given sproc exists."""

        return self.sproc_info[sproc_name].sproc_exists

    def add_staging_table_columns(
        self, column_type: StagingTableColumType, columns: list[str]
    ) -> None:
        """Adds a staging table column."""

        if column_type not in self.staging_table_columns:
            self.staging_table_columns[column_type] = []

        self.staging_table_columns[column_type] += columns

    def create_prompt_type_string(
        self, creation_type: CreationType, column_type: StagingTableColumType
    ) -> str:
        """Creates the field string for the given staging table."""

        if creation_type == CreationType.DOC_TYPE:
            column_str = "".join(
                [
                    self.get_property_by_fprompt(column).prompt_type_string
                    for column in self.staging_table_columns[column_type]
                ]
            )
        elif creation_type == CreationType.DIST_STAMP:
            column_str = "".join(
                [
                    self.get_distribution_stamp_field_by_caption(
                        column
                    ).prompt_type_string
                    for column in self.staging_table_columns[column_type]
                ]
            )
        else:
            raise Exception(
                "INVALID_CREATION_TYPE",
                f"Invalid creation type: {creation_type}",
            )

        return column_str[:-3]

    def create_prompt_string(
        self, creation_type: CreationType, column_type: StagingTableColumType
    ) -> str:
        """Creates the field string for the given staging table."""

        if creation_type == CreationType.DOC_TYPE:
            column_str = "".join(
                [
                    self.get_property_by_fprompt(column).prompt_string
                    for column in self.staging_table_columns[column_type]
                ]
            )
        elif creation_type == CreationType.DIST_STAMP:
            column_str = "".join(
                [
                    self.get_distribution_stamp_field_by_caption(column).prompt_string
                    for column in self.staging_table_columns[column_type]
                ]
            )
        else:
            raise Exception(
                "INVALID_CREATION_TYPE",
                f"Invalid creation type: {creation_type}",
            )

        return column_str[:-3]

    def create_id_string(
        self, creation_type: CreationType, column_type: StagingTableColumType
    ) -> str:
        """Creates the field string for the given staging table."""

        if creation_type == CreationType.DOC_TYPE:
            column_str = "".join(
                [
                    self.get_property_by_fprompt(column).id_string
                    for column in self.staging_table_columns[column_type]
                ]
            )
        elif creation_type == CreationType.DIST_STAMP:
            column_str = "".join(
                [
                    self.get_distribution_stamp_field_by_caption(
                        column
                    ).select_statement_string
                    for column in self.staging_table_columns[column_type]
                ]
            )
        else:
            raise Exception(
                "INVALID_CREATION_TYPE",
                f"Invalid creation type: {creation_type}",
            )

        return column_str[:-3]

    def set_selected_workflow_data(
        self,
        selected_wf_id: int,
        selected_staging_wf_id: int,
        selected_staged_wf_id: int,
        selected_success_wf_id: int,
        selected_failed_wf_id: int,
    ) -> None:
        """Sets the selected workflow related data"""

        self.selected_wf_id = selected_wf_id
        self.selected_staging_wf_id = selected_staging_wf_id
        self.selected_staged_wf_id = selected_staged_wf_id
        self.selected_success_wf_id = selected_success_wf_id
        self.selected_failed_wf_id = selected_failed_wf_id

    def set_selected_workflow_data_by_name(
        self,
        selected_wf: str,
        selected_staging_wf: str,
        selected_staged_wf: str,
        selected_success_wf: str,
        selected_failed_wf: str,
    ) -> None:
        """Sets the selected workflow related data"""

        self.selected_wf_id = self.get_workflow_by_name(selected_wf).WorkflowID
        self.selected_staging_wf_id = self.get_workflow_activity_by_name(
            selected_staging_wf
        ).WorkflowActivityID
        self.selected_staged_wf_id = self.get_workflow_activity_by_name(
            selected_staged_wf
        ).WorkflowActivityID
        self.selected_success_wf_id = self.get_workflow_activity_by_name(
            selected_success_wf
        ).WorkflowActivityID
        self.selected_failed_wf_id = self.get_workflow_activity_by_name(
            selected_failed_wf
        ).WorkflowActivityID
