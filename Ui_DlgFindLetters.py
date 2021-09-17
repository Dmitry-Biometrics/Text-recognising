# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Ui_DlgFindLetters.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DlgFindLetters(object):
    def setupUi(self, DlgFindLetters):
        DlgFindLetters.setObjectName("DlgFindLetters")
        DlgFindLetters.setWindowModality(QtCore.Qt.WindowModal)
        DlgFindLetters.resize(1028, 603)
        DlgFindLetters.setSizeGripEnabled(False)
        DlgFindLetters.setModal(False)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(DlgFindLetters)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.scrollArea = QtWidgets.QScrollArea(DlgFindLetters)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 1004, 548))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.buttonBox = QtWidgets.QDialogButtonBox(DlgFindLetters)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.retranslateUi(DlgFindLetters)
        QtCore.QMetaObject.connectSlotsByName(DlgFindLetters)

    def retranslateUi(self, DlgFindLetters):
        _translate = QtCore.QCoreApplication.translate
        DlgFindLetters.setWindowTitle(_translate("DlgFindLetters", "Найти символ"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    DlgFindLetters = QtWidgets.QDialog()
    ui = Ui_DlgFindLetters()
    ui.setupUi(DlgFindLetters)
    DlgFindLetters.show()
    sys.exit(app.exec_())

