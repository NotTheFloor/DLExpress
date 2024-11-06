import math
from typing import Any 

from workflow_designer.wfd_objects import Node, Link, Rect, NODEPROPS, NODEATTRIBS, LINKPROPS, LINKATTRIBS, WFDClickableRect, WFDClickableLine, WFDClickableEllipse, WFDLineSegments
from workflow_designer.wfd_scene import WFDScene, WFScene
from workflow_designer.wfd_utilities import addArrowToLineItem
from workflow_designer.wfd_xml import createObjectListFromXMLString

from doclink_py.doclink_types.workflows import Workflow, WorkflowActivity, WorkflowPlacement
from doclink_py.doclink_types.doclink_type_utilities import *   

from PySide6.QtWidgets import QGraphicsScene 

class WorkflowSceneManager:
    def __init__(self, doclink):

        self.workflows: list[Workflow] = []
        self.workflows = doclink.get_workflows()

        self.statuses: list[WorkflowActivity]
        self.statuses = doclink.get_workflow_activities()

        self.workflowStatuses: dict[str, list[str]] = {}
        
        for wfs in self.workflows:
            self.workflowStatuses[str(wfs.WorkflowKey)] = [
                    st.Title for st in self.getStatusSequence(str(wfs.WorkflowKey))
                ]

        self.placements: list[WorkflowPlacement] = []
        self.placements = doclink.get_workflow_placements()

        self.scenes: dict[str, WFDScene] = {}
        self.graphicScenes: dict[str, Any] = {}

        self.newScenes: list[WFScene] = []

        self.createScenes()
        self.buildGraphicsScenes()

    def getStatusSequence(self, workflowKey: str) -> list:
        """Gets all statuses from a workflow sorted by suequence numbers"""

        workflow = get_object_from_list(self.workflows, "WorkflowKey", workflowKey.upper())
        if not workflow:
            print("No workflow found with workflow " + workflowKey)
            quit()

        workflowID = workflow.WorkflowID
        statusList = get_all_objects_from_list(self.statuses, "WorkflowID", workflowID)

        statusList = sorted(statusList, key=lambda x: x.Seq)

        return statusList

    def buildGraphicsScenes(self):
        for scene in self.newScenes:
            new_scene = QGraphicsScene()

            for ent in scene.workflows + scene.statuses:
                new_scene.addItem(ent.shape.graphicsItem)
                
                # for textItem in ent.textItems:
                    # print("About to add")
                    # new_scene.addItem(textItem)
                    # print("Added")
                
            self.graphicScenes[str(scene.sceneWorkflow.WorkflowKey)] = new_scene
        return

        for key, scene in self.scenes.items():
            new_scene = QGraphicsScene()

            for wfKey, workflow in scene.workflows.items():
                rect = WFDClickableRect(workflow.nodeRect.left, workflow.nodeRect.top, workflow.nodeRect.width, workflow.nodeRect.height)
                new_scene.addItem(rect)

            for stKey, status in scene.statuses.items():
                ellipse = WFDClickableEllipse(status.nodeRect.cx-status.nodeRect.rx, status.nodeRect.cy-status.nodeRect.ry, status.nodeRect.rx*2, status.nodeRect.ry*2)
                new_scene.addItem(ellipse)

            for lineSegment in scene.points:
                last_item = None
                for line in lineSegment.lines:
                    last_item = WFDClickableLine(
                            line.start[0],
                            line.start[1],
                            line.end[0],
                            line.end[1]
                        )
                    new_scene.addItem(last_item)
                if last_item is None:
                    print("ERROR: no points in scene")
                    quit()
                addArrowToLineItem(last_item)


            self.graphicScenes[key] = new_scene
                

    def createScenes(self) -> dict:
        """Converts placement data into objects and in a dict with WF Title as key"""

        for placement in self.placements:
            # nodes, links = createObjectListFromXMLString(placement.LayoutData)
# 
            # scene = self.buildScene(nodes, links)
            
            wf = get_object_from_list(self.workflows, "WorkflowID", placement.WorkflowID)
            if wf is None:
                input("Error no such workflow from placement")
                quit()
            
            self.newScenes.append(WFScene(placement, wf, self.workflowStatuses))
            # self.scenes[wf.Title] = scene
            
        return self.scenes


    def buildScene(self, nodeList: list[Node], linkList: list[Link]) -> WFDScene:
        """Constructs the scene dicts from node and link objects"""

        statuses: dict = {}
        workflows: dict = {}
        workflowStatuses: dict = {} # This is so ineffecient it should be illegal
        links: dict = {}
        linkPoints: list[tuple] = []
        points: list[WFDLineSegments] = []

        for node in nodeList:
            if node.nodeAttribs["LayoutNode"]["Type"] == 'Status':
                if node.nodeAttribs["LayoutNode"]["Key"] in statuses:
                    input("Error: node key already in statuses dict")

                statuses[node.nodeAttribs["LayoutNode"]["Key"]] = node

            elif node.nodeAttribs["LayoutNode"]["Type"] == 'Workflow':
                if node.nodeAttribs["LayoutNode"]["Key"] in workflows:
                    input("Error: node key already in workflows dict")

                workflows[node.nodeAttribs["LayoutNode"]["Key"]] = node
                # Again - shamefully innefficent. This info should be fiugred
                # once and stored somewhere differently
                if node.nodeAttribs["LayoutNode"]["Key"] not in workflowStatuses:
                    statusList = self.getStatusSequence(node.nodeAttribs["LayoutNode"]["Key"])
                    workflowStatuses[node.nodeAttribs["LayoutNode"]["Key"]] = statusList

            else:
                input("Warning: unknown node type:" + node.nodeAtrribs["LayoutNode"]["Type"])

        for link in linkList:
            orgNode = statuses.get(
                    link.linkAttribs["LayoutLink"]["OrgKey"],
                    workflows.get(link.linkAttribs["LayoutLink"]["OrgKey"], None)
                    )

            if orgNode == None:
                act = get_object_from_list(self.statuses, "WorkflowActivityKey", str(link.linkAttribs["LayoutLink"]["OrgKey"]).upper())
                if act is not None:
                    orgNode = workflows.get(str(get_object_from_list(self.workflows, "WorkflowID", act.WorkflowID).WorkflowKey).lower())
                if orgNode is None:
                    input("Error: layout org key not in workflow or status list: " + link.linkAttribs["LayoutLink"]["OrgKey"])

            dstNode = statuses.get(
                    link.linkAttribs["LayoutLink"]["DstKey"],
                    workflows.get(link.linkAttribs["LayoutLink"]["DstKey"], None)
                    )
            if dstNode == None:
                act = get_object_from_list(self.statuses, "WorkflowActivityKey", str(link.linkAttribs["LayoutLink"]["DstKey"]).upper())
                if act is not None:
                    dstNode = workflows.get(str(get_object_from_list(self.workflows, "WorkflowID", act.WorkflowID).WorkflowKey).lower())
                if dstNode is None:
                    input("Error: layout dst key not in workflow or status list: " + link.linkAttribs["LayoutLink"]["DstKey"])

            if orgNode is None or dstNode is None:
                print("Error orgNode or dstNode is None")
                quit()

            # Create line segments 
            # Source point
            newSegment = []
            startItem = str(link.linkAttribs["LayoutLink"]["OrgKey"]).upper()
            endItem = str(link.linkAttribs["LayoutLink"]["DstKey"]).upper()

            x = orgNode.nodeRect.cx
            y = orgNode.nodeRect.cy
            nextX = dstNode.nodeRect.cx
            nextY = dstNode.nodeRect.cy
            if 'Point' in link.linkAttribs:
                nextX = float(link.linkAttribs['Point'][0]['X'])
                nextY = float(link.linkAttribs['Point'][0]['Y'])
            
            if orgNode.nodeAttribs["LayoutNode"]["Type"] == "Workflow":
                y = nextY
                if nextX < orgNode.nodeRect.cx:
                    x = orgNode.nodeRect.left
                else:
                    x = orgNode.nodeRect.left + orgNode.nodeRect.width
            else:
                dx = nextX - x
                dy = y - nextY
                lineAngle = math.atan2(dy, dx)
                a = orgNode.nodeRect.rx
                b = orgNode.nodeRect.ry
                top = a * b
                bottom = (b * math.cos(lineAngle))**2 + (a * math.sin(lineAngle))**2
                ellipseR = top / math.sqrt(bottom)
                x = x + math.cos(lineAngle) * ellipseR
                y = y - math.sin(lineAngle) * ellipseR

            linkPoints.append((x, y, True))
            newSegment.append((x, y))

            # Mid points
            if 'Point' in link.linkAttribs:
                for i in range(len(link.linkAttribs['Point'])):
                    linkPoints.append((float(link.linkAttribs['Point'][i]['X']), float(link.linkAttribs['Point'][i]['Y']), False))
                    newSegment.append((x, y))

            # End points
            x = dstNode.nodeRect.cx
            y = dstNode.nodeRect.cy
            if dstNode.nodeAttribs["LayoutNode"]["Type"] == "Workflow":
                if linkPoints[-1][0] < dstNode.nodeRect.cx:
                    x = dstNode.nodeRect.left
                else:
                    x = dstNode.nodeRect.left + dstNode.nodeRect.width
                y = linkPoints[-1][1]
            else:
                dx = x - linkPoints[-1][0]
                dy = linkPoints[-1][1] - y
                lineAngle = math.atan2(dy, dx)
                a = dstNode.nodeRect.rx
                b = dstNode.nodeRect.ry
                top = a * b
                bottom = (b * math.cos(lineAngle))**2 + (a * math.sin(lineAngle))**2
                ellipseR = top / math.sqrt(bottom)
                x = x - math.cos(lineAngle) * ellipseR
                y = y + math.sin(lineAngle) * ellipseR

            linkPoints.append((x, y, False))
            newSegment.append((x, y))

            points.append(WFDLineSegments(startItem, endItem, newSegment))

        return WFDScene(
                statuses,
                workflows,
                workflowStatuses,
                links,
                linkPoints,
                points
            )


