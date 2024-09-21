from workflow_designer.wfd_window import WorkflowDesignerWindow
from workflow_designer.wfd_objects import Node, Link, Rect

def buildScene(nodeList: list[Node], linkList: list[Link]):
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
        print(link)
        orgNode = statuses.get(
                link.linkAttribs["LayoutLink"]["OrgKey"],
                workflows.get(link.linkAttribs["LayoutLink"]["OrgKey"], None)
                )
        if orgNode == None:
            _ign = input("Error: layout org key not in workflow or status list: " + link.linkAttribs["LayoutLink"]["OrgKey"])

        dstNode = statuses.get(
                link.linkAttribs["LayoutLink"]["DstKey"],
                workflows.get(link.linkAttribs["LayoutLink"]["DstKey"], None)
                )
        if dstNode == None:
            _ign = input("Error: layout dst key not in workflow or status list: " + link.linkAttribs["LayoutLink"]["DstKey"])

        linkPoints.append((orgNode.nodeRect.cx, dstNode.nodeRect.cy))

    returnObject = {
            "statuses": statuses,
            "workflows": workflows,
            "links": links,
            "linkPoints": linkPoints
            }

    return returnObjects

def createObjectList(filename: str) -> list:
    tree = ET.parse(filename)
    root = tree.getroot()

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
                elif subchild.tag in wfo.LINKATTRIBS:
                    linkAttribs[subchild.tag] = subchild.attrib
                else:
                    _ign = input("Unknown subchild.tag during link search: " + subchild.tag)

            linkList.append(Link(linkProps, linkAttribs))
        elif child.tag == "Version":
            continue
        else:
            input("Unkown child tag:" + child.tag)

    return buildScene(nodeList, linkList)
