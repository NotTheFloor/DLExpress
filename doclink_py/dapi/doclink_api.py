import logging
import json

from dataclasses import dataclass, asdict

from .http_handler import HTTPHandler

from doclink_py.doclink_types.propertys import Property  
from doclink_py.doclink_types.documents import DocumentType, DocumentTypeProperty
from doclink_py import doclink_types, utilities
from doclink_py.doclink_sprocs import SQLDAT_DIR, STAGING_FROM_PROP


BASE_URL: str = "http://local_host/"
LOGIN_CLOUD_URL: str = "LoginCloud"
LOGIN_ON_PREM_URL: str = "LoginOnPremise"
LOGOUT_URL: str = "Logout"
GET_ALL_DOCUMENT_TYPES_URL: str = "DocumentTypes"
GET_DOCUMENT_TYPE_URL: str = "DocumentType"
GET_ALL_PROPERTIES_URL: str = "Properties"
GET_PROPERTY_URL: str = "Property"
GET_ACCESSABLE_ITEMS_URL: str = "AccessibleItems"
GET_TABLE_SCHEMA_URL: str = "TableSchema"
QUERY_TABLE_URL: str = "QueryTable"

WORKFLOW_TABLE_NAME: str = "Workflows"
WORKFLOW_ACTIVITIES_TABLE_NAME: str = "WorkflowActivities"
DIST_STAMP_TABLE_NAME: str = "DynamicUI"
DIST_STAMP_FIELD_TABLE_NAME: str = "DynamicUIField"
AI_PROFILE_TABLE_NAME: str = "AIProfiles"
EVENT_TASK_TABLE_NAME: str = "EventAutomatedTasks"

DOC_EXPORT_BY_PROP_FILE_NAME: str = "DocExportByProp.sql"


@dataclass
class DocLinkAPICredentails:
    URL: str
    UserId: str
    Password: str
    MachineName: str | None = "Stager"
    SiteCode: str | None = None


class DocLinkAPI:
    def __init__(self, base_url: str = BASE_URL) -> None:
        self.http_handler: HTTPHandler = None

        self._gai_has_run = False
        self.gai_cache: dict[str, list] = {}

    def connect(self, credentials: DocLinkAPICredentails) -> None:
        "Automatically logs into cloud or on prem depending on site code"

        self.http_handler = HTTPHandler(credentials.URL)

        if credentials.SiteCode:
            logging.debug("Site code found, logging into cloud")
            self.login_cloud(credentials)
        else:
            logging.debug("No site code found, logging into on prem")
            self.login_on_prem(credentials)

    def login_cloud(self, credentials: DocLinkAPICredentails) -> None:
        """Login to the DocLink API."""

        logging.info(
            f"Sending login request to sitecode {credentials.SiteCode} with username {credentials.UserId} and machinename {credentials.MachineName}"
        )
        response: dict = self.http_handler.post_request(
            LOGIN_CLOUD_URL, asdict(credentials), requires_auth=False
        )
        self.http_handler.logged_in(response)

    def login_on_prem(self, credentials: DocLinkAPICredentails) -> None:
        """Login to the DocLink API on prem. NOTE: This is defiend in the API but I have not gotten it to work yet"""

        self.http_handler.set_mode_on_prem()

        logging.info(
            f"Sending login request to on prem with username {credentials.UserId} and machinename {credentials.MachineName}"
        )
        response: dict = self.http_handler.post_request(
            LOGIN_ON_PREM_URL, asdict(credentials), requires_auth=False
        )
        self.http_handler.logged_in(response)

    def disconnect(self) -> None:
        """Logout of the DocLink API."""

        logging.debug("Sending logout request")
        response: dict | list = self.http_handler.post_request(LOGOUT_URL, {})
        self.http_handler.logged_out()

    def get_doc_types_with_props(self, _) -> list[DocumentType]:
        """Get all document types."""

        logging.info("Sending get all document types request")
        response: dict = self.http_handler.get_request(GET_ALL_DOCUMENT_TYPES_URL)

        properties = self.get_properties()

        doc_types: list[DocumentType] = []
        for doc_type in response:
            # Convert inner properties to dataclass
            doc_type["DocumentTypeProperties"] = [
                DocumentTypeProperty(**prop)
                for prop in doc_type["DocumentTypeProperties"]
            ]
            for doc_type_property in doc_type["DocumentTypeProperties"]:
                # Add property to doc type property
                doc_type_property.Property = next(
                    prop
                    for prop in properties
                    if prop.PropertyId == doc_type_property.PropertyId
                )
            doc_types.append(DocumentType(**doc_type))

        return doc_types

    def get_properties(self) -> list[Property]:
        """Get all properties."""

        logging.info("Sending get all properties request")
        response: dict = self.http_handler.get_request(GET_ALL_PROPERTIES_URL)

        propertys = [Property(**prop) for prop in response]

        return propertys

    def get_document_type(self, document_type_id: int) -> None:
        """Get a specific document type."""

        logging.info(f"Sending get document type request for {document_type_id}")
        response: dict = self.http_handler.get_request(
            GET_DOCUMENT_TYPE_URL,
            {"documentTypeId": int(document_type_id)},
        )
        print(json.dumps(response, indent=4))

    def get_property(self, property_id: int) -> None:
        """Get a specific property."""

        logging.info(f"Sending get property request for {property_id}")
        response: dict = self.http_handler.get_request(
            GET_PROPERTY_URL, {"propertyId": int(property_id)}
        )
        print(json.dumps(response, indent=4))

    def get_document_type_propertys(self) -> None:
        """Not implemented by API."""

        logging.debug("Get_doc_type_propertys not implemented by API")
        raise NotImplementedError("Support by SQL but not API")

    def check_if_sproc_exists(self, sproc_name: str) -> int:
        """Checks if a sproc exists in the database"""

        logging.info(f"Checking if sproc {sproc_name} exists")
        response: dict = self._get_accessable_items(refresh=True)

        exists = 0
        if sproc_name in response["Procedures"]:
            exists = 1

        return exists

    def does_table_exist(self, table_name: str) -> bool:
        """Checks if a table exists in the database"""

        # self._get_accessable_items()

        logging.info(f"Checking if table {table_name} exists")
        response: dict = self._get_accessable_items(True)

        return table_name in response["Tables"]

    def commit_sproc_from_file(self, sproc_name: str, action: str) -> None:
        raise NotImplementedError("Not implemented by API")

    def drop_staging_tables(self) -> None:
        """Drops the staging tables for the given document type."""

        logging.info("drop_staging_tables not implemented")
        raise NotImplementedError("drop_staging_tables not implemented by API")

    def query_table(self, table_name: str) -> None:
        """Get a specific property."""

        if table_name not in self._get_accessable_items()["Tables"]:
            logging.debug(f"Table {table_name} not found")
            raise Exception(
                "TABLE_NOT_WHITELISTED", f"Table {table_name} not whitelisted"
            )

        data = {"TableName": table_name, "Filters": []}

        logging.info(f"Sending query table request for table {table_name}")
        response: dict = self.http_handler.post_request(QUERY_TABLE_URL, data)

        return response

    def create_staging_tables(self, header_fields: str, detail_fields: str):
        """Creates the staging tables for the given document type."""

        query = utilities.get_query_from_file(SQLDAT_DIR, f"{STAGING_FROM_PROP}.sqldat")
        query = query.format(
            HEADER_COLUMNS=header_fields,
            DETAIL_COLUMNS=detail_fields,
        )
        with open("StagingFromProp.sql", "w") as f:
            f.write(query)

    def get_table_schema(self, table_name: str) -> None:
        """Get a specific property."""

        logging.info(f"Sending query table request for table {table_name}")
        response: dict = self.http_handler.get_request(
            GET_TABLE_SCHEMA_URL, {"tableName": table_name}
        )
        print(json.dumps(response, indent=4))

    def get_workflows(self) -> list[doclink_types.workflows.Workflow]:
        """Get all workflows."""

        logging.info("Getting workflows from API")
        try:
            response: dict = self.query_table(WORKFLOW_TABLE_NAME)
        except Exception as e:
            if e.args[0] == "TABLE_NOT_WHITELISTED":
                logging.debug("Workflows table not whitelisted")
                return []
            raise e

        workflows = [
            doclink_types.workflows.Workflow(
                **utilities.api_row_to_json(row, response["Columns"])
            )
            for row in response["Rows"]
        ]

        return workflows

    def get_workflow_activities(self) -> list[doclink_types.workflows.WorkflowActivity]:
        """Get all workflow activities."""

        logging.info("Getting workflow activities from API")
        try:
            response: dict = self.query_table(WORKFLOW_ACTIVITIES_TABLE_NAME)
        except Exception as e:
            if e.args[0] == "TABLE_NOT_WHITELISTED":
                logging.debug("Workflow activities table not whitelisted")
                return []
            raise e

        workflow_activities = [
            doclink_types.workflows.WorkflowActivity(
                **utilities.api_row_to_json(row, response["Columns"])
            )
            for row in response["Rows"]
        ]

        return workflow_activities

    def get_dist_stamps(self) -> list[doclink_types.stamps.DistributionStamp]:
        """Get all distribution stamps."""

        logging.info("Getting distribution stamps from API")
        try:
            response: dict = self.query_table(DIST_STAMP_TABLE_NAME)
        except Exception as e:
            if e.args[0] == "TABLE_NOT_WHITELISTED":
                logging.debug("Distribution stamps table not whitelisted")
                return []
            raise e

        dist_stamps = [
            doclink_types.stamps.DistributionStamp(
                **utilities.api_row_to_json(row, response["Columns"])
            )
            for row in response["Rows"]
        ]

        return dist_stamps

    def get_dist_stamp_fields(self) -> list[doclink_types.stamps.DistributionStampField]:
        """Get all distribution stamp fields."""

        logging.info("Getting distribution stamp fields from API")
        try:
            response: dict = self.query_table(DIST_STAMP_FIELD_TABLE_NAME)
        except Exception as e:
            if e.args[0] == "TABLE_NOT_WHITELISTED":
                logging.debug("Distribution stamp fields table not whitelisted")
                return []
            raise e

        dist_stamp_fields = [
            doclink_types.stamps.DistributionStampField(
                **utilities.api_row_to_json(row, response["Columns"])
            )
            for row in response["Rows"]
        ]

        return dist_stamp_fields

    def get_dist_stamp_with_fields(self) -> list[doclink_types.stamps.DistributionStamp]:
        """Get all distribution stamps with fields."""

        logging.info("Getting distribution stamps with fields from API")
        dist_stamps = self.get_dist_stamps()
        dist_stamp_fields = self.get_dist_stamp_fields()

        if not dist_stamps or not dist_stamp_fields:
            logging.debug(
                "No distribution stamps or fields present during combo request"
            )
            return []

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

        query = utilities.get_query_from_file(SQLDAT_DIR, f"{sproc_name}.sqldat")
        query = query.format(
            ACTION=action,
            HEADER_COLUMNS=header_columns,
            DETAIL_COLUMNS=detail_columns,
            SELECT_HEADER_PROP_IDS=header_prop_ids,
            PIVOT_HEADER_PROP_IDS=header_prop_ids[1:],
            SELECT_DETAIL_PROP_IDS=detail_prop_ids,
            PIVOT_DETAIL_PROP_IDS=detail_prop_ids[1:],
        )
        with open(DOC_EXPORT_BY_PROP_FILE_NAME, "w") as f:
            f.write(query)

    def create_basic_sproc(self, sproc_name: str, action: str) -> None:
        """Creates basic sproc."""

        query = utilities.get_query_from_file(SQLDAT_DIR, f"{sproc_name}.sqldat")
        query = query.format(ACTION=action)
        with open(f"{sproc_name}.sql", "w") as f:
            f.write(query)

    def get_automated_task_sequence_number(self, activity_id: int) -> int:
        """Gets the automated task sequence for the given activity id."""

        logging.info("get_automated_task_sequence_number not implemented")
        raise NotImplementedError(
            "'get_automated_task_sequence_number' Not implemented by API"
        )

    def create_triggered_event(
        self,
        task_name: str,
        activity_id: int,
        start_active: bool,
    ) -> int:
        """Creates the triggered event for the given task name."""

        logging.info("create_triggered_event not implemented")
        raise NotImplementedError("'create_triggered_event' Not implemented by API")

    def add_event_database_action(
        self, event_id: int, action_name: str, sproc_name: str
    ) -> int:
        """Creates the event database action."""

        logging.info("add_event_database_action not implemented")
        raise NotImplementedError("'add_event_database_action' Not implemented by API")

    def add_event_db_action_param(
        self, event_db_action_id: int, param_name: str, param_value: str
    ) -> None:
        """Creates the event database action parameter."""

        logging.info("add_event_db_action_param not implemented")
        raise NotImplementedError("'add_event_db_action_param' Not implemented by API")

    def create_scheduled_event(self, task_name, start_active) -> int:
        """Creates the scheduled event for the given task name."""

        logging.info("create_scheduled_event not implemented")
        raise NotImplementedError("'create_scheduled_event' Not implemented by API")

    # TODO: Implement in API
    def get_event_config_id_from_task_id(self, task_id: int) -> int:
        """Gets the event config id from the task id."""

        logging.info("get_event_config_id_from_task_id not implemented")
        raise NotImplementedError(
            "'get_event_config_id_from_task_id' Not implemented by API"
        )

    def add_schedule_for_event_by_config_id(
        self, event_config_id: int, interval_period: int, interval_type: int
    ) -> None:
        """Adds the schedule for the given event config id."""

        logging.info("add_schedule_for_event_by_config_id not implemented")
        raise NotImplementedError(
            "'add_schedule_for_event_by_config_id' Not implemented by API"
        )

    def add_schedule_for_event_by_task_id(
        self, task_id: int, interval_period: int, interval_type: int
    ) -> int:
        """Adds the schedule for the given task id."""

        logging.info("add_schedule_for_event_by_task_id not implemented")
        raise NotImplementedError(
            "'add_schedule_for_event_by_task_id' Not implemented by API"
        )

    def enable_ai_for_document_type(self, doc_type_id: int) -> None:
        """Enables AI for the given document type."""

        logging.info("enable_ai_for_document_type not implemented")
        raise NotImplementedError(
            "'enable_ai_for_document_type' Not implemented by API"
        )

    def enable_ri_for_document_type(self, doc_type_id: int, ri_method: int) -> None:
        """Enables RI for the given document type."""

        logging.info("enable_ri_for_document_type not implemented")
        raise NotImplementedError(
            "'enable_ri_for_document_type' Not implemented by API"
        )

    def create_auto_index(self, ai_name: str, ai_script: str) -> int:
        """Creates the auto index for the given document type."""

        logging.info("create_auto_index not implemented")
        raise NotImplementedError("'create_auto_index' Not implemented by API")

    # TODO: Implement in API
    def get_doc_type_ai_sequence(self, doc_type_id: int) -> int:
        """Gets the auto index sequence for the given document type."""

        logging.info("get_doc_type_ai_sequence not implemented")
        raise NotImplementedError("'get_doc_type_ai_sequence' Not implemented by API")

    def attach_auto_index_to_doc_type(
        self, doc_type_id: int, ai_profile_id: int, execution_context: int = 0
    ) -> int:
        """Attaches the auto index to the given document type."""

        logging.info("attach_auto_index_to_doc_type not implemented")
        raise NotImplementedError(
            "'attach_auto_index_to_doc_type' Not implemented by API"
        )

    def add_auto_index_return_property(
        self, ai_profile_id: int, property_name: str, column_name: str
    ):
        """Adds the return property to the given auto index."""

        logging.info("add_auto_index_return_property not implemented")
        raise NotImplementedError(
            "'add_auto_index_return_property' Not implemented by API"
        )

    # TODO: Implement in API
    def doc_ri_schedule_exists(self, doc_type_id: int) -> bool:
        """Checks if the doc ri schedule exists for the given document type."""

        logging.info("doc_ri_schedule_exists not implemented")
        raise NotImplementedError("'doc_ri_schedule_exists' Not implemented by API")

    # TODO: Implement in API
    def get_doc_ri_schedule_attributes(self, doc_type_id: int) -> tuple[int, int]:
        """Gets the schedule interval and schedule interval type by doc id."""

        logging.info("get_doc_ri_schedule_attributes not implemented")
        raise NotImplementedError(
            "'get_doc_ri_schedule_attributes' Not implemented by API"
        )

    def create_doc_ri_schedule(
        self,
        doc_type_id: int,
        processing_interval: int,
        processing_interval_type: int,
    ) -> None:
        """Creates the doc ri schedule for the given document type."""

        logging.info("create_doc_ri_schedule not implemented")
        raise NotImplementedError("'create_doc_ri_schedule' Not implemented by API")

    def update_doc_ri_schedule(
        self,
        doc_type_id: int,
        processing_interval: int,
        processing_interval_type: int,
    ) -> None:
        """Updates the doc ri schedule for the given document type."""

        logging.info("update_doc_ri_schedule not implemented")
        raise NotImplementedError("'update_doc_ri_schedule' Not implemented by API")

    # TODO: TEST
    def get_ai_profiles(self):
        """Gets the ai profiles of the database."""

        logging.info("Getting AI Profiles from API")
        try:
            response: dict = self.query_table(AI_PROFILE_TABLE_NAME)
        except Exception as e:
            if e.args[0] == "TABLE_NOT_WHITELISTED":
                logging.debug("AI Profile table not whitelisted")
                return []
            raise e

        return [ai_profile[0] for ai_profile in response["Rows"]]

    # TODO: Implement in API
    def get_event_task_names(self):
        """Gets the event task names of the database."""

        logging.info("Getting Event Task Names from API")
        try:
            response: dict = self.query_table(EVENT_TASK_TABLE_NAME)
        except Exception as e:
            if e.args[0] == "TABLE_NOT_WHITELISTED":
                logging.debug("Event Task Name table not whitelisted")
                return []
            raise e

        return [event_task[0] for event_task in response["Rows"]]

    def run_query(self, query):
        """Run a query"""

        logging.info("run_query not implemented")
        raise NotImplementedError("'run_query' Not implemented by API")

    # TODO: Implement in API
    def compare_sproc_from_file(self, sproc_name: str) -> bool:
        """Compares the sproc from a file to the database."""

        logging.info("compare_sproc_from_file not implemented")
        raise NotImplementedError("'compare_sproc_from_file' Not implemented by API")

    def _get_accessable_items(self, refresh: bool = False) -> dict[str, list]:
        """Private function do get a dict of lists of available tables and sprocs"""

        if self._gai_has_run and not refresh:
            return self.gai_cache

        logging.info("Sending get accessable items request")
        response: dict = self.http_handler.get_request(GET_ACCESSABLE_ITEMS_URL)

        # Pull names out of inner dicts for ease of processing
        self.gai_cache["Tables"] = [table["Name"] for table in response["Tables"]]
        self.gai_cache["Procedures"] = [
            sproc["Name"] for sproc in response["Procedures"]
        ]

        self._gai_has_run = True

        return self.gai_cache
