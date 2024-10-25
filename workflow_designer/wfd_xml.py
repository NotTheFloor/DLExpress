import xml.etree.ElementTree as ET

from workflow_designer.wfd_objects import Node, Link, Rect, NODEPROPS, NODEATTRIBS, LINKPROPS, LINKATTRIBS, WFDClickableRect, WFDClickableLine, WFDClickableEllipse, WFDLineSegments

def createObjectListFromXMLFile(filename: str) -> tuple[list, list]:
    tree = ET.parse(filename)
    root = tree.getroot()
    return createObjectListFromXML(root)

def createObjectListFromXMLString(xmlString: str) -> tuple[list, list]:
    root = ET.fromstring(xmlString)
    return createObjectListFromXML(root)

def createObjectListFromXML(root) -> tuple[list, list]:
    """Creates node and link objects from XML data"""

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

    return nodeList, linkList


