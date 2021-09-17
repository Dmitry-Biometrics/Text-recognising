from PyQt5 import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from CoordsObj import Coords
from SplitArea import SplitArea
from Ui_SplitBox import Ui_SplitBox

class SplitBox(QDialog):
    def __init__(self, letter, id_bbox):
        super(SplitBox, self).__init__()
        self.ui = Ui_SplitBox()
        self.ui.setupUi(self)
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)

        self.letter = letter
        self.last_bbox_id = id_bbox
        self.area = SplitArea(self, letter, id_bbox)
        self.ui.scrollArea.setWidget(self.area)

    def set_image(self):
        self.area.coordToImage()
        self.area.setImage()

    def pointCount(self): #число разделяющих точек
        return self.area.pointCount()