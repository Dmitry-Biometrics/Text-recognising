from PyQt5 import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from Ui_DlgFindLetters import Ui_DlgFindLetters
from SmpArea import SmpArea
from HpSamples import HpSamples

class DlgFindLetters(QDialog):
    def __init__(self):
        super(DlgFindLetters, self).__init__()
        self.ui = Ui_DlgFindLetters()
        self.ui.setupUi(self)
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)

        #создать область отображения
        self.area = SmpArea(self) #создать компонент изображений примеров
        self.ui.scrollArea.setWidget(self.area)

    def setSamples(self, samples): #установить примеры
        groups = samples.groupByLabel()
        keys  = sorted(list(groups.keys()))
        self.area.setGroupedSamples(samples,groups,keys)

    def selectedSamples(self): #номера выбранных примеров
        return self.area.selected()

