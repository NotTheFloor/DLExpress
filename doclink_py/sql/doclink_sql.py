import logging
import json

from typing import Optional, TYPE_CHECKING

from dataclasses import dataclass

from .sql_handler import SQLHandler
from ..sql_queries import *
from ..utilities import get_query_from_file, row_to_json

import doclink_py.doclink_types as doclink_types
from doclink_py.doclink_sprocs import SQLDAT_DIR, STAGING_FROM_PROP

SCHEMA_NAME = "dbo"


@dataclass
class DocLinkSQLCredentials:
    """Dataclass to store DocLink SQL credentials."""

    server_name: str
    database_name: str
    username: str
    password: str


class DocLinkSQL:
    """Mid level class to handle SQL connections to DocLink."""

    def __init__(self, credentials: DocLinkSQLCredentials = None) -> None:
        self.credentials = credentials

        self.sql_handler: SQLHandler = None
        self.sqldat_dir: str = SQLDAT_DIR

    def connect(self, credentials: DocLinkSQLCredentials = None) -> None:
        if credentials:
            self.credentials = credentials
        elif not self.credentials:
            raise Exception("NO_CREDENTIALS", "No credentials provided for SQL Login.")

        self.sql_handler = SQLHandler()
        self.sql_handler.connect(
            self.credentials.server_name,
            self.credentials.database_name,
            self.credentials.username,
            self.credentials.password,
        )

    def disconnect(self) -> None:
        if self.sql_handler:
            self.sql_handler.disconnect()

    def check_if_sproc_exists(self, sproc_name: str) -> int:
        """Checks if a sproc exists in the database. Returns number of times it exists"""

        logging.debug(f"Checking if sproc {sproc_name} exists...")
        query = f"SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[{SCHEMA_NAME}].[{sproc_name}]') AND type = N'P'"
        response = self.sql_handler.query_and_fetch_all(query)

        return len(response)

    def commit_sproc_from_file(
        self, sproc_name: str, action: Optional[str] = "CREATE"
    ) -> None:
        """Commits a sproc from a file to the database."""

        logging.debug(f"Committing sproc from file {sproc_name}...")

        query = get_query_from_file(self.sqldat_dir, f"{sproc_name}.sqldat")
        query = query.format(ACTION=action)
        self.sql_handler.query_and_commit(query)
        logging.debug(f"Stored procedure {sproc_name} added.")

    def get_properties(self) -> list[doclink_types.propertys.Property]:
        """Gets the properties of the database."""

        logging.debug("Getting database properties...")

        query = GET_PROPERTIES
        response = self.sql_handler.query_and_fetch_all(query)

        properties = [doclink_types.propertys.Property(**row_to_json(row)) for row in response]

        return properties

    def get_document_types(self) -> list[doclink_types.documents.DocumentType]:
        """Gets the document types of the database."""

        logging.debug("Getting document types...")

        query = GET_DOCUMENT_TYPES
        response = self.sql_handler.query_and_fetch_all(query)

        document_types = [
                doclink_types.documents.DocumentType(**row_to_json(row)) for row in response
        ]

        return document_types

    def get_document_type_propertys(
        self, properties: list[doclink_types.propertys.Property] = None
    ) -> list[doclink_types.documents.DocumentTypeProperty]:
        """Gets the document types of the database."""

        logging.debug("Getting document type props...")

        if not properties:
            logging.debug("Getting properties...")
            properties = self.get_properties()

        # Convert to dict to imrpove search/assignment time (O(n^2) to O(1))
        properties_dict = {prop.PropertyId: prop for prop in properties}

        query = GET_DOCUMENT_TYPE_PROPERTY
        response = self.sql_handler.query_and_fetch_all(query)

        document_type_propertys = [
            doclink_types.documents.DocumentTypeProperty(**row_to_json(row)) for row in response
        ]

        for doc_type_prop in document_type_propertys:
            doc_type_prop.Property = properties_dict[doc_type_prop.PropertyId]

        return document_type_propertys

    def get_doc_types_with_props(
        self, properties: list[doclink_types.propertys.Property] = None
    ) -> doclink_types.documents.DocumentType:
        """Gets the document types of the database."""

        logging.debug("Getting document types with props...")

        doc_types = self.get_document_types()
        doc_type_props = self.get_document_type_propertys(properties)

        for doc_type in doc_types:
            doc_type_props_for_doc_type = [
                doc_type_prop
                for doc_type_prop in doc_type_props
                if doc_type_prop.ParentId == doc_type.DocumentTypeId
            ]
            doc_type.DocumentTypeProperties = doc_type_props_for_doc_type

        return doc_types

    def drop_staging_tables(self) -> None:
        """Drops the staging tables for the given document type."""

        query = DROP_STAGING_TABLES_QUERY
        self.sql_handler.query_and_commit(query)

    def create_staging_tables(self, header_fields: str, detail_fields: str):
        """Creates the staging tables for the given document type."""

        query = get_query_from_file(SQLDAT_DIR, f"{STAGING_FROM_PROP}.sqldat")
        query = query.format(
            HEADER_COLUMNS=header_fields,
            DETAIL_COLUMNS=detail_fields,
        )
        self.sql_handler.query_and_commit(query)

    def get_workflows(self) -> list[doclink_types.workflows.Workflow]:
        """Gets the workflows of the database."""

        logging.debug("Getting workflows...")

        query = GET_WORKFLOWS_QUERY
        response = self.sql_handler.query_and_fetch_all(query)

        workflows = [doclink_types.workflows.Workflow(**row_to_json(row)) for row in response]

        return workflows

    def get_workflow_activities(self) -> list[doclink_types.workflows.WorkflowActivity]:
        """Gets the workflow activities of the database."""

        logging.debug("Getting workflow activities...")

        query = GET_WORKFLOW_ACTIVITIES_QUERY
        response = self.sql_handler.query_and_fetch_all(query)

        workflow_activities = [
            doclink_types.workflows.WorkflowActivity(**row_to_json(row)) for row in response
        ]

        return workflow_activities

    def get_workflow_queues(self) -> list[doclink_types.workflows.WorkflowActivity]:
        """Gets the workflow queues of the database."""

        logging.debug("Getting workflow queues (catagories)...")

        query = GET_WORKFLOW_QUEUES_QUERY
        response = self.sql_handler.query_and_fetch_all(query)

        workflow_queue = [
            doclink_types.workflows.WorkflowQueue(**row_to_json(row)) for row in response
        ]

        return workflow_queue

    def get_workflow_next_activities(self) -> list[doclink_types.workflows.WorkflowNextActivity]:
        """Gets the workflow queues of the database."""

        logging.debug("Getting workflow next activity...")

        query = GET_WORKFLOW_NEXT_ACTIVITY_QUERY
        response = self.sql_handler.query_and_fetch_all(query)

        workflow_next_activity = [
            doclink_types.workflows.WorkflowNextActivity(**row_to_json(row)) for row in response
        ]

        return workflow_next_activity

    def get_workflow_placements(self) -> list[doclink_types.workflows.WorkflowPlacement]:
        """Gets the workflow placements of the database."""

        logging.debug("Getting workflow placement...")

        query = GET_WORKFLOW_PLACEMENT_QUERY
        response = self.sql_handler.query_and_fetch_all(query)

        workflow_placement = [
            doclink_types.workflows.WorkflowPlacement(**row_to_json(row)) for row in response
        ]

        return workflow_placement

    def get_dist_stamps(self) -> list[doclink_types.stamps.DistributionStamp]:
        """Gets the dist stamps of the database."""

        logging.debug("Getting dist stamps...")

        query = GET_DIST_STAMPS
        response = self.sql_handler.query_and_fetch_all(query)

        dist_stamps = [
            doclink_types.stamps.DistributionStamp(**row_to_json(row)) for row in response
        ]

        return dist_stamps

    def get_dist_stamp_fields(self) -> list[doclink_types.stamps.DistributionStampField]:
        """Gets the dist stamp fields of the database."""

        logging.debug("Getting dist stamp fields...")

        query = GET_DIST_STAMP_FIELDS
        response = self.sql_handler.query_and_fetch_all(query)

        dist_stamp_fields = [
            doclink_types.stamps.DistributionStampField(**row_to_json(row)) for row in response
        ]

        return dist_stamp_fields

    def get_dist_stamp_with_fields(self) -> list[doclink_types.stamps.DistributionStamp]:
        """Gets the dist stamps of the database."""

        logging.debug("Getting dist stamps...")

        dist_stamps = self.get_dist_stamps()
        dist_stamp_fields = self.get_dist_stamp_fields()

        for dist_stamp in dist_stamps:
            dist_stamp_fields_for_dist_stamp = [
                dist_stamp_field
                for dist_stamp_field in dist_stamp_fields
                if dist_stamp_field.DynamicUIId == dist_stamp.DynamicUiId
            ]
            dist_stamp.DistributionStampFields = dist_stamp_fields_for_dist_stamp

        return dist_stamps

    def create_doc_export_by_prop_sproc(
        self,
        sproc_name: str,
        action: str,
        header_columns: list[str],
        detail_columns: list[str],
        header_prop_ids: list[str],
        detail_prop_ids: list[str],
    ):
        """Creates the doc export by prop sproc."""

        query = get_query_from_file(SQLDAT_DIR, f"{sproc_name}.sqldat")
        query = query.format(
            ACTION=action,
            HEADER_COLUMNS=header_columns,
            DETAIL_COLUMNS=detail_columns,
            SELECT_HEADER_PROP_IDS=header_prop_ids,
            PIVOT_HEADER_PROP_IDS=header_prop_ids[1:],
            SELECT_DETAIL_PROP_IDS=detail_prop_ids,
            PIVOT_DETAIL_PROP_IDS=detail_prop_ids[1:],
        )
        self.sql_handler.query_and_commit(query)

    def create_basic_sproc(self, sproc_name: str, action: str) -> None:
        """Creates basic sproc."""

        query = get_query_from_file(SQLDAT_DIR, f"{sproc_name}.sqldat")
        query = query.format(ACTION=action)
        self.sql_handler.query_and_commit(query)

    def get_automated_task_sequence_number(self, activity_id: int) -> int:
        """Gets the automated task sequence for the given activity id."""

        logging.debug("Getting automated task sequence...")

        query = COUNT_TASKS_WITH_ACTIVITY_QUERY.format(ACTIVITY_ID=activity_id)
        response = self.sql_handler.query_and_fetch_one(query)

        return response[0] + 1

    def create_triggered_event(
        self,
        task_name: str,
        activity_id: int,
        start_active: bool,
    ) -> int:
        """Creates the triggered event for the given task name."""

        logging.debug("Creating triggered event...")

        sequence = self.get_automated_task_sequence_number(activity_id)

        query = ADD_TRIGGER_EVENT_QUERY.format(
            TASK_NAME=task_name,
            STATUS_ID=activity_id,
            START_ACTIVE=int(start_active),
            SEQ=sequence,
        )
        self.sql_handler.query_and_commit(query)

        return self.sql_handler.get_identity()

    def add_event_database_action(
        self, event_id: int, action_name: str, sproc_name: str
    ) -> int:
        """Creates the event database action."""

        query = ADD_DATABASE_ACTION_QUERY.format(
            EVENT_TASK_ID=event_id,
            DB_ACTION_NAME=action_name,
            SPROC_NAME=sproc_name,
        )
        self.sql_handler.query_and_commit(query)

        return self.sql_handler.get_identity()

    def add_event_db_action_param(
        self, event_db_action_id: int, param_name: str, param_value: str
    ) -> None:
        """Adds the event db action param."""

        query = ADD_DB_ACTION_PARAMETER_QUERY.format(
            EVENT_DB_ACTION_ID=event_db_action_id,
            PARAM_NAME=param_name,
            PARAM_VALUE=param_value,
        )
        self.sql_handler.query_and_commit(query)

    def create_scheduled_event(self, task_name, start_active) -> int:
        """Creates the scheduled event for the given task name."""

        logging.debug("Creating scheduled event...")

        query = ADD_EVENT_CONFIG_QUERY.format(
            TASK_NAME=task_name,
            START_ACTIVE=int(start_active),
        )
        self.sql_handler.query_and_commit(query)

        return self.sql_handler.get_identity()

    def get_event_config_id_from_task_id(self, task_id: int) -> int:
        """Gets the event config id from the task id."""

        logging.debug("Getting event config id from task id...")

        query = GET_EVENT_CNF_ID_FROM_TASK_ID.format(TASK_ID=task_id)
        response = self.sql_handler.query_and_fetch_one(query)

        return response[0]

    def add_schedule_for_event_by_config_id(
        self, event_config_id: int, interval_period: int, interval_type: int
    ) -> None:
        """Adds the schedule for the given event config id."""

        query = ADD_EVENT_SCHEDULE_QUERY.format(
            EVENT_CONFIG_ID=event_config_id,
            INTERVAL_PERIOD=interval_period,
            INTERVAL_TYPE=interval_type,
        )
        self.sql_handler.query_and_commit(query)

    def add_schedule_for_event_by_task_id(
        self, task_id: int, interval_period: int, interval_type: int
    ) -> int:
        """Adds the schedule for the given task id."""

        event_config_id = self.get_event_config_id_from_task_id(task_id)
        self.add_schedule_for_event_by_config_id(
            event_config_id, interval_period, interval_type
        )

        return event_config_id

    def enable_ai_for_document_type(self, doc_type_id: int) -> None:
        """Enables AI for the given document type."""

        query = ENABLE_AI_QUERY.format(DOC_TYPE_ID=doc_type_id)
        self.sql_handler.query_and_commit(query)

    def enable_ri_for_document_type(self, doc_type_id: int, ri_method: int) -> None:
        """Enables RI for the given document type."""

        query = ENABLE_RI_QUERY.format(DOC_TYPE_ID=doc_type_id, RI_METHOD=ri_method)
        self.sql_handler.query_and_commit(query)

    def create_auto_index(self, ai_name: str, ai_script: str) -> int:
        """Creates the auto index for the given document type."""

        query = ADD_AI_QUERY.format(AI_NAME=ai_name, AI_SCRIPT=ai_script)
        self.sql_handler.query_and_commit(query)

        return self.sql_handler.get_identity()

    def get_doc_type_ai_sequence(self, doc_type_id: int) -> int:
        """Gets the auto index sequence for the given document type."""

        query = COUNT_AI_PROFILES_QUERY.format(DOC_TYPE_ID=doc_type_id)
        result = self.sql_handler.query_and_fetch_one(query)

        return result[0] + 1

    def attach_auto_index_to_doc_type(
        self, doc_type_id: int, ai_profile_id: int, execution_context: int = 0
    ) -> int:
        """Attaches the auto index to the given document type."""

        sequence = self.get_doc_type_ai_sequence(doc_type_id)

        query = ADD_DOC_TYPE_AI_QUERY.format(
            DOC_TYPE_ID=doc_type_id,
            SEQ_COUNT=sequence,
            AI_PROFILE_ID=ai_profile_id,
            EXECUTION_CONTEXT=execution_context,
        )
        self.sql_handler.query_and_commit(query)

        return self.sql_handler.get_identity()

    def add_auto_index_return_property(
        self, ai_profile_id: int, property_name: str, column_name: str
    ):
        """Adds the return property to the given auto index."""

        query = ADD_RETURN_PROP_TO_AI_QUERY.format(
            AI_PROFILE_ID=ai_profile_id,
            PROP_ID=property_name,
            COLUMN_NAME=column_name,
        )
        self.sql_handler.query_and_commit(query)

    def doc_ri_schedule_exists(self, doc_type_id: int) -> bool:
        """Checks if the doc ri schedule exists for the given document type."""

        query = GET_RI_SCHEDULE_QUERY.format(DOC_TYPE_ID=doc_type_id)
        result = self.sql_handler.query_and_fetch_one(query)

        return result is not None

    def get_doc_ri_schedule_attributes(self, doc_type_id: int) -> tuple[int, int]:
        """Gets the schedule interval and schedule interval type by doc id."""

        query = GET_RI_SCHEDULE_QUERY.format(DOC_TYPE_ID=doc_type_id)
        result = self.sql_handler.query_and_fetch_one(query)

        return result[12], result[13]

    def create_doc_ri_schedule(
        self,
        doc_type_id: int,
        processing_interval: int,
        processing_interval_type: int,
    ) -> None:
        """Creates the doc ri schedule for the given document type."""

        query = UPDATE_RI_SCHEDULE_QUERY.format(
            DOC_TYPE_ID=doc_type_id,
            PROCESSING_INTERVAL=processing_interval,
            PROCESSING_INTERVAL_TYPE=processing_interval_type,
        )
        self.sql_handler.query_and_commit(query)

    def update_doc_ri_schedule(
        self,
        doc_type_id: int,
        processing_interval: int,
        processing_interval_type: int,
    ) -> None:
        """Updates the doc ri schedule for the given document type."""

        query = UPDATE_RI_SCHEDULE_QUERY.format(
            DOC_TYPE_ID=doc_type_id,
            PROCESSING_INTERVAL=processing_interval,
            PROCESSING_INTERVAL_TYPE=processing_interval_type,
        )
        self.sql_handler.query_and_commit(query)

    def get_ai_profiles(self):
        """Gets the ai profiles of the database."""

        logging.debug("Getting ai profiles...")

        query = GET_AI_PROFILE_NAMES
        response = self.sql_handler.query_and_fetch_all(query)

        return [ai_profile[0] for ai_profile in response]

    def get_event_task_names(self):
        """Gets the event task names of the database."""

        logging.debug("Getting event task names...")

        query = GET_EVENT_TASK_NAMES
        response = self.sql_handler.query_and_fetch_all(query)

        return [event_task[0] for event_task in response]

    def run_query(self, query):
        self.sql_handler.query_and_commit(query)

    def compare_sproc_from_file(self, sproc_name: str) -> bool:
        """Compares the sproc from a file to the database."""

        logging.debug(f"Comparing sproc from file {sproc_name}...")

        query = GET_SPROC_TEXT_QUERY.format(SPROC_NAME=sproc_name)
        raw_sproc = self.sql_handler.query_and_fetch_all(query)
        sproc_string = ""
        for sproc_line in raw_sproc:
            sproc_string += sproc_line[0]

        file_sproc = get_query_from_file("sproc_data", f"{sproc_name}.sqldat")
        file_sproc = file_sproc.format(ACTION="CREATE")

        return sproc_string == file_sproc
