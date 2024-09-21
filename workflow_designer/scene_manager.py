from doclink_py.sql.doclink_sql import DocLinkSQLCredentials, DocLinkSQL
from doclink_py.doclink_types.workflows import Workflow, WorkflowActivity, WorkflowPlacement

class WorkflowSceneManager:
    def __init__(self, doclink):

        workflows: list[Workflow] = []
        workflows = doclink.get_workflows()

        statuses: list[WorkflowActivity]
        statuses = doclink.get_workflow_activities()

        placements: list[WorkflowPlacement] = []
        placements = doclink.get_workflow_placements()

        print(workflows)
