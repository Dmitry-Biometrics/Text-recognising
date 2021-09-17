from PyQt5 import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from Ui_DlgText import Ui_DlgText


class DlgText(QDialog):
    def __init__(self):
        super(DlgText, self).__init__()
        self.ui = Ui_DlgText()
        self.ui.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitle("Редактирование текста с сохранением разметки, где это возможно") #UPD

        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)

    def setText(self, textlines):
        self.ui.plainTextEdit.setPlainText(textlines)

    def getText(self):
        return self.ui.plainTextEdit.toPlainText()

