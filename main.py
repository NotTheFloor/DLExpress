from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QVBoxLayout

from workflow_designer.wfd_window import WorkflowDesignerWindow

_DEF_WIN_X = 250
_DEF_WIN_Y = 400

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
        self.workflow_window = WorkflowDesignerWindow()
        self.workflow_window.exec()


if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec()
