import xml.etree.ElementTree as ET

from workflow_designer.wfd_objects import Node, Link, Rect, NODEPROPS, NODEATTRIBS, LINKPROPS, LINKATTRIBS, WFDClickableRect, WFDClickableLine, WFDClickableEllipse, WFDLineSegments
from workflow_designer.wfd_logger import logger

def createObjectListFromXMLFile(filename: str) -> tuple[list, list]:
    try:
        logger.debug(f"Parsing XML file: {filename}")
        tree = ET.parse(filename)
        root = tree.getroot()
        return createObjectListFromXML(root)
    except ET.ParseError as e:
        logger.error(f"XML parsing error in file {filename}: {e}")
        raise ValueError(f"Invalid XML in file {filename}: {e}")
    except FileNotFoundError:
        logger.error(f"XML file not found: {filename}")
        raise
    except Exception as e:
        logger.error(f"Error parsing XML file {filename}: {e}")
        raise

def createObjectListFromXMLString(xmlString: str) -> tuple[list, list]:
    try:
        logger.debug("Parsing XML string")
        root = ET.fromstring(xmlString)
        return createObjectListFromXML(root)
    except ET.ParseError as e:
        logger.error(f"XML parsing error in string: {e}")
        raise ValueError(f"Invalid XML string: {e}")
    except Exception as e:
        logger.error(f"Error parsing XML string: {e}")
        raise

def createObjectListFromXML(root) -> tuple[list, list]:
    """Creates node and link objects from XML data"""
    logger.debug("Converting XML to workflow objects")
    
    nodeList: list[Node] = []
    linkList: list[Link] = []

    try:
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
                        raise ValueError(f"Unknown subchild.tag during node search: {subchild.tag}")

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
                        raise ValueError(f"Unknown subchild.tag during link search: {subchild.tag}")

                linkList.append(Link(linkProps, linkAttribs))
            elif child.tag == "Version":
                continue
            else:
                raise ValueError(f"Unknown child tag: {child.tag}")
        
        logger.debug(f"Successfully parsed XML: {len(nodeList)} nodes, {len(linkList)} links")
        return nodeList, linkList
        
    except ValueError as e:
        logger.error(f"XML validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error parsing XML: {e}")
        raise


