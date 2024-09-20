import xml.etree.ElementTree as ET

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QVBoxLayout

from workflow_designer.wfd_window import WorkflowDesignerWindow
import workflow_designer.wfd_objects as wfdo
from connect_window import ConnectWindow

_DEF_WIN_X = 250
_DEF_WIN_Y = 400

# Needs to be moved
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.workflow_window: WorkflowDesignerWindow = None

        self.setWindowTitle("Main Window")
        self.setGeometry(100, 100, _DEF_WIN_X, _DEF_WIN_Y)

        layout = QVBoxLayout()

        workflow_button = QPushButton("Workflow Designer")
        workflow_button.clicked.connect(self.open_workflow_designer)

        layout.addWidget(workflow_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def open_workflow_designer(self) -> None:
        # Called when the WFD button is pressed; Opens WFD window
        #scene = createObjectList('test_data2.xml')
        #print(scene)

        #self.workflow_window = WorkflowDesignerWindow(nodeList)
        #self.workflow_window.exec()
        self.connect_window = ConnectWindow()
        connection = self.connect_window.exec_connect_window()

        print(connection)

        quit()

def buildScene(nodeList: list[wfdo.Node], linkList: list[wfdo.Link]):
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

    nodeList: list[wfdo.Node] = []
    linkList: list[wfdo.Link] = []
    
    for child in root:
        if child.tag == 'Node':
            nodeRect = wfdo.Rect(
                float(child.attrib["Left"]),
                float(child.attrib["Top"]),
                float(child.attrib["Width"]),
                float(child.attrib["Height"])
                )

            nodeProps = {}
            nodeAttribs = {}
            for subchild in child:
                if subchild.tag in wfdo.NODEPROPS:
                    nodeProps[subchild.tag] = subchild.text
                elif subchild.tag in wfdo.NODEATTRIBS:
                    nodeAttribs[subchild.tag] = subchild.attrib
                else:
                    _ign = input("Unknown subchild.tag during node search: " + subchild.tag)

                #print(attrib.tag, attrib.attrib)

            nodeList.append(wfdo.Node(nodeRect, nodeProps, nodeAttribs))
        elif child.tag == 'Link':
            linkProps = {} 
            linkAttribs = {} 

            for subchild in child:
                if subchild.tag in wfdo.LINKPROPS:
                    linkProps[subchild.tag] = subchild.text
                elif subchild.tag in wfdo.LINKATTRIBS:
                    linkAttribs[subchild.tag] = subchild.attrib
                else:
                    _ign = input("Unknown subchild.tag during link search: " + subchild.tag)

            linkList.append(wfdo.Link(linkProps, linkAttribs))
        elif child.tag == "Version":
            continue
        else:
            input("Unkown child tag:" + child.tag)

    return buildScene(nodeList, linkList)

if __name__ == "__main__":
    # Going to do some xml testing here

    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec()
