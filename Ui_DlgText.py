# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Ui_DlgText.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DlgText(object):
    def setupUi(self, DlgText):
        DlgText.setObjectName("DlgText")
        DlgText.resize(710, 256)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(DlgText)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.plainTextEdit = QtWidgets.QPlainTextEdit(DlgText)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.verticalLayout.addWidget(self.plainTextEdit)
        self.buttonBox = QtWidgets.QDialogButtonBox(DlgText)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.retranslateUi(DlgText)
        QtCore.QMetaObject.connectSlotsByName(DlgText)

    def retranslateUi(self, DlgText):
        _translate = QtCore.QCoreApplication.translate
        DlgText.setWindowTitle(_translate("DlgText", "Редактирование текста (ВНИМАНИЕ! СБРАСЫВАЕТ ВСЮ РАЗМЕТКУ!)"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    DlgText = QtWidgets.QDialog()
    ui = Ui_DlgText()
    ui.setupUi(DlgText)
    DlgText.show()
    sys.exit(app.exec_())

