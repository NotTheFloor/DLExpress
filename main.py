import os
# The below is designed to fix/silence the debug output.. so far not working
os.environ["QT_QPA_EGLFS_NO_TOUCH"] = "1"
os.environ["QT_LOGGING_RULES"] = "qt.pointer.dispatch.debug=false"

from typing import Optional   

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QVBoxLayout
from PySide6.QtGui import QSurfaceFormat

from workflow_designer.wfd_window import WorkflowDesignerWindow
from connect_window import ConnectWindow

_DEF_WIN_X = 250
_DEF_WIN_Y = 400

# Needs to be moved
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.workflow_window: Optional[WorkflowDesignerWindow] = None

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

        self.connect_window = ConnectWindow()
        connection = self.connect_window.exec_connect_window()

        if connection:
            self.workflow_window = WorkflowDesignerWindow(connection)
            self.workflow_window.exec()
        else:
            print("Failed to connect to SQL")

        quit()


def setup_global_antialiasing():
    """
    Configure global surface format for optimal rendering quality.
    Must be called before QApplication creation.
    """
    try:
        # Set up global surface format for all OpenGL contexts
        surface_format = QSurfaceFormat()
        surface_format.setSamples(4)  # 4x MSAA - good balance of quality vs performance
        surface_format.setDepthBufferSize(24)
        surface_format.setStencilBufferSize(8)
        
        # Set as default format for all OpenGL contexts
        QSurfaceFormat.setDefaultFormat(surface_format)
        print(f"Global anti-aliasing configured: 4x MSAA")
        return True
        
    except Exception as e:
        print(f"Warning: Could not set global surface format: {e}")
        return False


if __name__ == "__main__":
    # Configure global anti-aliasing BEFORE creating QApplication
    setup_global_antialiasing()
    
    # Going to do some xml testing here
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec()
