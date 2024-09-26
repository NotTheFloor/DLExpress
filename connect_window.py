from PySide6.QtWidgets import QDialog, QSplitter, QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel
#from PySide6.QtGui import QLineEdit
from PySide6.QtCore import Qt, QTimer

from doclink_py.sql.doclink_sql import DocLinkSQLCredentials, DocLinkSQL

_DEF_WDW_SZ_X = 400
_DEF_WDW_SZ_Y = 400

_DEF_SVR_NAME = "192.168.1.24"
_DEF_DB_NAME = "doclink2"
_DEF_USR_NAME = "sa"

class ConnectWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.connection_handle = None

        self.setWindowTitle("Login")
        self.setGeometry(150, 150, _DEF_WDW_SZ_X, _DEF_WDW_SZ_Y)

        layout = QVBoxLayout()

        self.serverName_label = QLabel("Server name:")
        self.serverName_input = QLineEdit()
        self.serverName_input.setText(_DEF_SVR_NAME)

        self.databaseName_label = QLabel("Database name:")
        self.databaseName_input = QLineEdit()
        self.databaseName_input.setText(_DEF_DB_NAME)

        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.username_input.setText(_DEF_USR_NAME)

        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)  # Hide the password input

        layout.addWidget(self.serverName_label)
        layout.addWidget(self.serverName_input)

        layout.addWidget(self.databaseName_label)
        layout.addWidget(self.databaseName_input)

        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        layout.addStretch()

        QTimer.singleShot(0, self.password_input.setFocus)

#        ## Old
#        login = QLineEdit()
#        password = QLineEdit()
#        password.setEchoMode(QLineEdit.PasswordEchoOnEdit)
        
        connectButton = QPushButton("Connect")
        connectButton.clicked.connect(self.connect_action)

        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.reject)

        buttonBox = QHBoxLayout()
        buttonBox.addWidget(connectButton)
        buttonBox.addWidget(cancelButton)

#        layout.addWidget(username)
#        layout.addWidget(password)
        layout.addLayout(buttonBox)
        
        self.setLayout(layout)

    def connect_action(self):
        doclink = DocLinkSQL()
        credentials = DocLinkSQLCredentials(
                self.serverName_input.text(),
                self.databaseName_input.text(),
                self.username_input.text(),
                self.password_input.text()
            )
        doclink.connect(credentials)
        self.connection_handle = doclink
        self.accept()

    def exec_connect_window(self):
        if self.exec() == QDialog.Accepted:
            return self.connection_handle
        else:
            return None
