import xml.etree.ElementTree as ET

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QVBoxLayout

from workflow_designer.wfd_window import WorkflowDesignerWindow
import workflow_designer.wfd_objects as wfdo

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
        nodeList = createObjectList('test_data2.xml')
        print("OFD")
        print(nodeList)
        self.workflow_window = WorkflowDesignerWindow(nodeList)
        self.workflow_window.exec()

def createObjectList(filename: str) -> list:
    tree = ET.parse('test_data.xml')
    root = tree.getroot()

    nodeList: list[wfdo.Node] = []
    
    for child in root:
        if child.tag == 'Node':
            nodeRect = wfdo.Rect(
                int(child.attrib["Left"]),
                int(child.attrib["Top"]),
                int(child.attrib["Width"]),
                int(child.attrib["Height"])
                )

            nodeProps = {}
            nodeAttribs = {}
            for subchild in child:
                if subchild.tag in wfdo.NODEPROPS:
                    nodeProps[subchild.tag] = subchild.text
                elif subchild.tag in wfdo.NODEATTRIBS:
                    nodeAttribs[subchild.tag] = subchild.attrib

                #print(attrib.tag, attrib.attrib)

            nodeList.append(wfdo.Node(nodeRect, nodeProps, nodeAttribs))
            print(nodeList[-1])
        else:
            print(child.tag + ' - ' + str(child.attrib))

    quit()
    return nodeList

if __name__ == "__main__":
    # Going to do some xml testing here

    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec()
