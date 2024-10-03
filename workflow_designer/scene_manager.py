import xml.etree.ElementTree as ET
import math
from typing import Any 

from workflow_designer.wfd_objects import Node, Link, Rect, NODEPROPS, NODEATTRIBS, LINKPROPS, LINKATTRIBS, WFDClickableRect, WFDClickableLine, WFDClickableEllipse

from doclink_py.doclink_types.workflows import Workflow, WorkflowActivity, WorkflowPlacement
from doclink_py.doclink_types.doclink_type_utilities import *   

from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

class WorkflowSceneManager:
    def __init__(self, doclink):

        self.workflows: list[Workflow] = []
        self.workflows = doclink.get_workflows()

        self.statuses: list[WorkflowActivity]
        self.statuses = doclink.get_workflow_activities()

        self.placements: list[WorkflowPlacement] = []
        self.placements = doclink.get_workflow_placements()

        self.scenes: dict[str, Any] = {}
        self.g_scenes: dict[str, Any] = {}

        self.build_scenes()
        self.build_g_scenes()

    def getStatusSequence(self, workflowKey: str) -> list:

        workflow = get_object_from_list(self.workflows, "WorkflowKey", workflowKey.upper())
        if not workflow:
            print("No workflow found with workflow " + workflowKey)
            quit()

        workflowID = workflow.WorkflowID
        statusList = get_all_objects_from_list(self.statuses, "WorkflowID", workflowID)

        statusList = sorted(statusList, key=lambda x: x.Seq)

        return statusList

    def build_g_scenes(self):
        for key, scene in self.scenes.items():
            new_scene = QGraphicsScene()
            # Next step is creating the graphics items
            # Will need to focus on arrows or ignore breifly
            for wfKey, workflow in scene["workflows"].items():
                rect = WFDClickableRect(workflow.nodeRect.left, workflow.nodeRect.top, workflow.nodeRect.width, workflow.nodeRect.height)
                new_scene.addItem(rect)

            for stKey, status in scene["statuses"].items():
                ellipse = WFDClickableEllipse(status.nodeRect.cx, status.nodeRect.cy, status.nodeRect.rx, status.nodeRect.ry)
                new_scene.addItem(ellipse)

            for i in range(1, len(scene["linkPoints"])):
                line = WFDClickableLine(
                        scene["linkPoints"][i-1][0],
                        scene["linkPoints"][i-1][1],
                        scene["linkPoints"][i][0],
                        scene["linkPoints"][i][1]
                    )
                new_scene.addItem(line)

            self.g_scenes[key] = new_scene
                

    def build_scenes(self) -> dict:
        for placement in self.placements:
            scene = self.createObjectListFromString(placement.LayoutData)
            
            wf = get_object_from_list(self.workflows, "WorkflowID", placement.WorkflowID)
            if wf is None:
                input("Error no such workflow from placement")
                quit()
            
            self.scenes[wf.Title] = scene
            
        return self.scenes


    def buildScene(self, nodeList: list[Node], linkList: list[Link]) -> dict[str, Any]:
        statuses: dict = {}
        workflows: dict = {}
        workflowStatuses: dict = {} # This is so ineffecient it should be illegal
        links: dict = {}
        linkPoints: list[tuple] = []

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

            # Mid points
            if 'Point' in link.linkAttribs:
                for i in range(len(link.linkAttribs['Point'])):
                    linkPoints.append((float(link.linkAttribs['Point'][i]['X']), float(link.linkAttribs['Point'][i]['Y']), False))

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


        returnObject = {
                "statuses": statuses,
                "workflows": workflows,
                "workflowStatuses": workflowStatuses,
                "links": links,
                "linkPoints": linkPoints
                }

        return returnObject

    def createObjectListFromFile(self, filename: str) -> dict[str, Any]:
        tree = ET.parse(filename)
        root = tree.getroot()
        return self.createObjectList(root)
    
    def createObjectListFromString(self, xmlString: str) -> dict[str, Any]:
        root = ET.fromstring(xmlString)
        return self.createObjectList(root)

    def createObjectList(self, root) -> dict[str, Any]:

        nodeList: list[Node] = []
        linkList: list[Link] = []

        for child in root:
            if child.tag == 'Node':
                nodeRect = Rect(
                        float(child.attrib["Left"]),
                        float(child.attrib["Top"]),
                        float(child.attrib["Width"]),
                        float(child.attrib["Height"])
                        )

                nodeProps = {}
                nodeAttribs = {}
                for subchild in child:
                    if subchild.tag in NODEPROPS:
                        nodeProps[subchild.tag] = subchild.text
                    elif subchild.tag in NODEATTRIBS:
                        nodeAttribs[subchild.tag] = subchild.attrib
                    else:
                        input("Unknown subchild.tag during node search: " + subchild.tag)

                    #print(attrib.tag, attrib.attrib)

                nodeList.append(Node(nodeRect, nodeProps, nodeAttribs))
            elif child.tag == 'Link':
                linkProps = {} 
                linkAttribs = {} 

                for subchild in child:
                    if subchild.tag in LINKPROPS:
                        linkProps[subchild.tag] = subchild.text
                    elif subchild.tag in LINKATTRIBS:
                        if subchild.tag == "Point":
                            if subchild.tag not in linkAttribs:
                                linkAttribs[subchild.tag] = []    
                            linkAttribs[subchild.tag].append(subchild.attrib)
                        else:
                            linkAttribs[subchild.tag] = subchild.attrib
                    else:
                        input("Unknown subchild.tag during link search: " + subchild.tag)

                linkList.append(Link(linkProps, linkAttribs))
            elif child.tag == "Version":
                continue
            else:
                input("Unkown child tag:" + child.tag)

        return self.buildScene(nodeList, linkList)


