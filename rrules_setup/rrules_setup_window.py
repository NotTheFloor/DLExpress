from PySide6.QtWidgets import QDialog 
#from PySide6.QtCore import Qt, QStringListModel

from doclink_py.sql.manager.doclink_manager import DoclinkManager

_DEF_WDW_SZ_X = 1600
_DEF_WDW_SZ_Y = 900

class RRulesSetupWindow(QDialog):
    def __init__(self, doclink: DoclinkManager):
        super().__init__()

        self.setWindowTitle("RRules Setup")
        self.setGeometry(150, 150, _DEF_WDW_SZ_X, _DEF_WDW_SZ_Y)

