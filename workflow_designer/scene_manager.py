from doclink_py.sql.doclink_sql import DocLinkSQLCredentials, DocLinkSQL
from doclink_py.doclink_types.workflows import Workflow, WorkflowActivity, WorkflowPlacement

class WorkflowSceneManager:
    def __init__(self, doclink):

        self.workflows: list[Workflow] = []
        self.workflows = doclink.get_workflows()

        self.statuses: list[WorkflowActivity]
        self.statuses = doclink.get_workflow_activities()

        self.placements: list[WorkflowPlacement] = []
        self.placements = doclink.get_workflow_placements()

