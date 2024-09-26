import xml.etree.ElementTree as ET

from workflow_designer.wfd_objects import Node, Link, Rect, NODEPROPS, NODEATTRIBS, LINKPROPS, LINKATTRIBS

from doclink_py.sql.doclink_sql import DocLinkSQLCredentials, DocLinkSQL
from doclink_py.doclink_types.workflows import Workflow, WorkflowActivity, WorkflowPlacement
from doclink_py.doclink_types.doclink_type_utilities import *   

class WorkflowSceneManager:
    def __init__(self, doclink):

        self.workflows: list[Workflow] = []
        self.workflows = doclink.get_workflows()

        self.statuses: list[WorkflowActivity]
        self.statuses = doclink.get_workflow_activities()

        self.placements: list[WorkflowPlacement] = []
        self.placements = doclink.get_workflow_placements()

        self.scenes: dict = {}

        self.build_scenes()

    def build_scenes(self) -> dict:
        for placement in self.placements:
            scene = self.createObjectListFromString(placement.LayoutData)
            
            wf = get_object_from_list(self.workflows, "WorkflowID", placement.WorkflowID)
            if wf is None:
                _ign = input("Error no such workflow from placement")
                quit()
            
            self.scenes[wf.Title] = scene
            
        return self.scenes


    def buildScene(self, nodeList: list[Node], linkList: list[Link]):
        statuses: dict = {}
        workflows: dict = {}
        links: dict = {}
        linkPoints: list[tuple] = []

        for node in nodeList:
            if node.nodeAttribs["LayoutNode"]["Type"] == 'Status':
                if node.nodeAttribs["LayoutNode"]["Key"] in statuses:
                    _ign = input("Error: node key already in statuses dict")

                statuses[node.nodeAttribs["LayoutNode"]["Key"]] = node

            elif node.nodeAttribs["LayoutNode"]["Type"] == 'Workflow':
                if node.nodeAttribs["LayoutNode"]["Key"] in workflows:
                    _ign = input("Error: node key already in workflows dict")

                workflows[node.nodeAttribs["LayoutNode"]["Key"]] = node

            else:
                _ign = input("Warning: unknown node type:" + node.nodeAtrribs["LayoutNode"]["Type"])

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
                    _ign = input("Error: layout org key not in workflow or status list: " + link.linkAttribs["LayoutLink"]["OrgKey"])

            dstNode = statuses.get(
                    link.linkAttribs["LayoutLink"]["DstKey"],
                    workflows.get(link.linkAttribs["LayoutLink"]["DstKey"], None)
                    )
            if dstNode == None:
                act = get_object_from_list(self.statuses, "WorkflowActivityKey", str(link.linkAttribs["LayoutLink"]["DstKey"]).upper())
                if act is not None:
                    dstNode = workflows.get(str(get_object_from_list(self.workflows, "WorkflowID", act.WorkflowID).WorkflowKey).lower())
                if dstNode is None:
                    _ign = input("Error: layout dst key not in workflow or status list: " + link.linkAttribs["LayoutLink"]["DstKey"])

            if orgNode is None or dstNode is None:
                print("Error orgNode or dstNode is None")
                quit()

            shouldPrint = False
            if (
                    link.linkAttribs["LayoutLink"]["DstKey"] == "71d212ff-cc78-4e9d-9be1-d0ef180844f3" or
                    link.linkAttribs["LayoutLink"]["OrgKey"] == "71d212ff-cc78-4e9d-9be1-d0ef180844f3"
                    ):
                shouldPrint = True
                print("*****ZOOOOOOPPP******")

            print("New link:")
            print(link.linkAttribs)
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
            print(f"\t{(x, y)}")
            linkPoints.append((x, y, True))

            if 'Point' in link.linkAttribs:
                for i in range(len(link.linkAttribs['Point'])):
                    print(f"\t{(float(link.linkAttribs['Point'][i]['X']), float(link.linkAttribs['Point'][i]['Y']))}")
                    linkPoints.append((float(link.linkAttribs['Point'][i]['X']), float(link.linkAttribs['Point'][i]['Y']), False))

            x = dstNode.nodeRect.cx
            y = dstNode.nodeRect.cy
            if dstNode.nodeAttribs["LayoutNode"]["Type"] == "Workflow":
                if linkPoints[-1][0] < dstNode.nodeRect.cx:
                    x = dstNode.nodeRect.left
                else:
                    x = dstNode.nodeRect.left + dstNode.nodeRect.width
                y = linkPoints[-1][1]
            print(f"\t{(x, y)}")
            linkPoints.append((x, y, False))

            if shouldPrint:
                pass
                #input("click")

        returnObject = {
                "statuses": statuses,
                "workflows": workflows,
                "links": links,
                "linkPoints": linkPoints
                }

        return returnObject

    def createObjectListFromFile(self, filename: str) -> list:
        tree = ET.parse(filename)
        root = tree.getroot()
        return self.createObjectList(root)
    
    def createObjectListFromString(self, xmlString: str) -> list:
        root = ET.fromstring(xmlString)
        return self.createObjectList(root)

    def createObjectList(self, root) -> list:

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
                        _ign = input("Unknown subchild.tag during node search: " + subchild.tag)

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
                        _ign = input("Unknown subchild.tag during link search: " + subchild.tag)

                
                if (
                        linkAttribs['LayoutLink']['DstKey'] == '71d212ff-cc78-4e9d-9be1-d0ef180844f3' or
                        linkAttribs['LayoutLink']['OrgKey'] == '71d212ff-cc78-4e9d-9be1-d0ef180844f3' 
                        ):
                    pass
                    #input(linkAttribs)
                linkList.append(Link(linkProps, linkAttribs))
            elif child.tag == "Version":
                continue
            else:
                input("Unkown child tag:" + child.tag)

        return self.buildScene(nodeList, linkList)


