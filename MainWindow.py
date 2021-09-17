from PyQt5 import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.uic.properties import QtCore

import os
from SplitBoxArea import SplitBox
from Ui_MainWindow import Ui_MainWindow
from PageArea import *
import Markup
import PreProcess
from DlgFindLetters import *
from DlgText import *
from DlgHypChecker import *
from LetPredictor import *

from MarkupMetrics import MarkupMetrics

def info(text):
    QMessageBox(QMessageBox.Information, "Информация", text).exec_()


def questionYesNo(text):
    return QMessageBox(QMessageBox.Question, "Подтверждение", text, buttons=QMessageBox.Yes| QMessageBox.No).exec_()


def listfiles(path, filter='.smp'):
    """
    Перечисление файлов с расширением filter в каталоге path и вложенных в него
    :param path: каталог
    :param filter: расширение фильтра
    :return: список путей к файлам path/../filename
    """
    files = []
    for dirname, subdirs, filenames in os.walk(path):
        for f in filenames:
            if f.endswith(filter): #UPD if f.rfind(filter)>=0:
                files.append(dirname + '/' + f)
    return files


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.lawmlw = dict()
        self.lawcld = dict()

        self.area = None
        self.iline = -1
        self.ibox = -1
        self.filename = ""

        self.ui.tbLineSet.clicked.connect(self.onLineSet)
        self.ui.tbLineUpdate.clicked.connect(self.onLineUpdate)
        self.ui.btnExtractLetters.clicked.connect(self.onExtractLetters)
        self.ui.btnFindLetters.clicked.connect(self.onFindLetters)
        self.ui.tbEditText.clicked.connect(self.onEditText)
        self.ui.tbLineSet.setText("RST")
        self.ui.tbLineUpdate.setText("UPDATE")
        self.ui.tbEditText.setText("EDIT TEXT")

        self.ui.tb1b1c.clicked.connect(lambda: self.onChangeMuArg(1, 1))
        self.ui.tb2b1c.clicked.connect(lambda: self.onChangeMuArg(2, 1))
        self.ui.tb3b1c.clicked.connect(lambda: self.onChangeMuArg(3, 1))
        self.ui.tb1b2c.clicked.connect(lambda: self.onChangeMuArg(1, 2))
        self.ui.tb1b3c.clicked.connect(lambda: self.onChangeMuArg(1, 3))
        self.ui.tb3b2c.clicked.connect(lambda: self.onChangeMuArg(3, 2))
        self.ui.tb0b1c.clicked.connect(lambda: self.onChangeMuArg(0, 1)); self.ui.tb0b1c.setText("skip char")
        self.ui.tb1b0c.clicked.connect(lambda: self.onChangeMuArg(1, 0)); self.ui.tb1b0c.setText("skip box")

        self.ui.tbChange.clicked.connect(self.onChangeMu)   #применить разметку
        self.ui.tbSplit.clicked.connect(self.onSplitMu)     #отделить область
        self.ui.tbUnite.clicked.connect(self.onUniteMu)     #объединить области

        self.ui.tbMuLineUp.clicked.connect(self.onChangeMuLineUp)
        self.ui.tbMuLineDown.clicked.connect(self.onChangeMuLineDown)
        self.ui.tbLineDel.clicked.connect(self.onLineDel)
        self.ui.tbLineNew.clicked.connect(self.onLineNew)
        self.ui.tbExcludeBoxes.clicked.connect(self.onExcludeBoxes)

        self.menuChange = QMenu(self)

        self.act1 = QAction('2 box', self);  self.act1.triggered.connect(lambda: self.onChangeMuArg(2, 1))
        self.act2 = QAction('2 char', self); self.act2.triggered.connect(lambda: self.onChangeMuArg(1, 2))
        self.act3 = QAction('3 box', self);  self.act3.triggered.connect(lambda: self.onChangeMuArg(3, 1))
        self.act4 = QAction('3 char', self); self.act4.triggered.connect(lambda: self.onChangeMuArg(1, 3))
        self.act5 = QAction('4 box', self);  self.act5.triggered.connect(lambda: self.onChangeMuArg(4, 1))
        self.act6 = QAction('4 char', self); self.act6.triggered.connect(lambda: self.onChangeMuArg(1, 4)) #UPD
        self.act7 = QAction('2 box 3 char', self);  self.act7.triggered.connect(lambda: self.onChangeMuArg(2, 3)) #UPD
        self.act8 = QAction('2 box 2 char', self);  self.act8.triggered.connect(lambda: self.onChangeMuArg(2, 2)) #UPD
        self.act9 = QAction('3 box 2 char', self); self.act9.triggered.connect(lambda: self.onChangeMuArg(3, 2))  #UPD

        self.act10 = QAction('skip char', self); self.act10.triggered.connect(lambda: self.onChangeMuArg(0, 1))
        self.act11 = QAction('skip box', self); self.act11.triggered.connect(lambda: self.onChangeMuArg(1, 0))
        self.act12 = QAction('split box', self); self.act12.triggered.connect(lambda: self.onSplitBoxes())

        #UPD удалил, т.к. есть риск случайного нажатия, лучше Ctrl+W
        #self.act13 = QAction('swap box', self); self.act13.triggered.connect(lambda: self.onSwapBoxes())

        for a in [self.act1,self.act2,self.act3,self.act4,self.act5, self.act6, self.act7, self.act8, self.act9,
                  self.act10, self.act11, self.act12]: #, self.act13]:
            self.menuChange.addAction(a)

        #меню программы
        #файл
        self.ui.actOpenImage.triggered.connect(self.onOpenImage) #открыть предварительно обработанное изображение
        self.ui.actOpenAndProcessImage.triggered.connect(self.onProcessImage) #открыть необработанное изображение
        self.ui.actOpenBbox.triggered.connect(self.onOpenBbox)
        self.ui.actOpenText.triggered.connect(self.onOpenText)
        self.ui.actOpenMarkup.triggered.connect(self.onOpenMarkup)
        self.ui.actSaveImage.triggered.connect(self.onSaveImage)
        self.ui.actSaveMarkup.triggered.connect(self.onSaveMarkup)
        self.ui.actSaveText.triggered.connect(self.onSaveText)
        self.ui.actSaveBbox.triggered.connect(self.onSaveBbox)
        self.ui.actSaveSymbols.triggered.connect(self.onExtractLetters)
        self.ui.actExit.triggered.connect(self.close)

        self.ui.actCheckHyp.triggered.connect(self.onCheckHyp)
        self.ui.actBuildStatistics.triggered.connect(self.onBuildStatistics)

        self.ui.actPathConvertMkpSmp.triggered.connect(self.onPathCovertMkpSmp)
        #линия
        self.ui.actSelToUpLine.triggered.connect(self.onChangeMuLineUp)
        self.ui.actSelToDownLine.triggered.connect(self.onChangeMuLineDown)
        self.ui.actSelExclude.triggered.connect(self.onExcludeBoxes)
        self.ui.actSelToNewLine.triggered.connect(self.onLineNew)
        self.ui.actDelLine.triggered.connect(self.onLineDel)
        #текст
        self.ui.actTextEdit.triggered.connect(self.onEditText)
        self.ui.actTextLineSet.triggered.connect(self.onLineSet)
        self.ui.actTextLineUpdate.triggered.connect(self.onLineUpdate)

        self.ui.actSkipBoxLine.triggered.connect(self.onSkipBoxLine)
        self.ui.actSkipTextLine.triggered.connect(self.onSkipTextLine)

        self.im = None

        #предсказание
        self.net = LetPredictor()
        self.net.load("lbnt_letters_32.h5") #загрузить модель по умолчанию

    def convertJpgToRawIm(self,jpg):
        p = QPixmap()
        p.loadFromData(jpg, format="JPG")
        image = p.toImage()
        w, h, n_channels = image.width(), image.height(), 4
        s = image.bits().asstring(w * h * n_channels)
        rgb = np.fromstring(s, dtype=np.uint8).reshape((h, w, n_channels))
        return PreProcess.rgb2gray(rgb) #im


    def setImage(self, qimage, isRawData=False):
        #image = QImage(name) #image = QPixmap(name)
        self.area = PageArea(self)
        if isRawData:
            p = QPixmap()
            p.loadFromData(qimage, format="JPG")
            self.area.load(p)
            #восстановить в self.im
            image = p.toImage()
            w,h,n_channels = image.width(), image.height(),4
            s = image.bits().asstring(w*h*n_channels)
            rgb = np.fromstring(s, dtype=np.uint8).reshape((h,w,n_channels))
            self.im = PreProcess.rgb2gray(rgb)
        else:
            self.area.load(QPixmap.fromImage(qimage))
        self.ui.scrollArea.setWidget(self.area)
        self.area.boxActivated.connect(self.boxActivated)
        self.area.lineActivated.connect(self.lineActivated)
        self.area.rightClicked.connect(self.onAreaPopup)    #подключить сигнал

    def onOpenImage(self):
        name = QFileDialog.getOpenFileName(self, caption='Open file', directory='', filter="JPEG (*.jpg *.jpeg)")[0]
        if not name: return
        dpifrom = int(self.ui.cbDpiFrom.currentText())
        dpito   = int(self.ui.cbDpiTo.currentText())
        if dpifrom <= 0 or dpito <= 0: info("Недопустимое разрешение"); return
        self.filename = name
        self.im = PreProcess.loadImage(name,dpifrom,dpito)
        height, width = self.im.shape
        qimage = QImage(self.im, width, height, 1*width, QImage.Format_Grayscale8)
        self.setImage(qimage)
        self.setWindowTitle("PageMarker: " + name)

    def onProcessImage(self):
        if not self.filename:
            info("Изображение не загружено")
            return
        im, angle = PreProcess.alignAndCropImage(self.im,0)
        # повернуть страницу и выделить область текста
                                    #ВНИМАНИЕ: в отличие от версии с командной строкой почему до обновления bwlabel
                                    #оставались артефакты на границах листа
                                    #при вращении страницы. компенсировалось выбрасыванием больших регионов
        isExtended = self.ui.isExtended.isChecked()
        bbox, ids, coords = PreProcess.segmentateImage(im, isExtended)       #загрузить обработаную копию (в производном изображении)
        bbox = [QRect(b[0], b[1], b[2], b[3]) for b in bbox]#преобразовать bbox [[int,int,int,int]] в [QRect]
        #self.ui.edPos.setText()
        self.statusBar().showMessage("angle {0}".format(angle))
        #работает, только если делать копию изображения im.copy()!
        height, width = im.shape
        qimage = QImage(im.copy(), width, height, 1*width, QImage.Format_Grayscale8)
        self.setImage(qimage)
        self.area.setBoxes(bbox,ids, coords)
        self.im = im

    def onOpenBbox(self):
        if self.area is None: return
        # name = self.filename+'.bb' #файл разметки должен иметь то же имя, что и
        name = QFileDialog.getOpenFileName(self, caption='Open file', directory='', filter="Bbox (*.bb)")[0]
        if not len(name): return
        self.iline = -1; self.ibox = -1
        (boxes, lines) = Markup.loadBoxLines(name) #[QRect]
        self.area.setBoxes(boxes, lines)

    def onOpenText(self):
        if self.area is None or len(self.area.boxes)==0: return
        name = QFileDialog.getOpenFileName(self, caption='Open file', directory='', filter="Text (*.txt)")[0]
        if not len(name): return
        if self.iline>=0:   iline = self.iline
        else:               iline = 0
        text = Markup.loadText(name)
        self.area.setTextLines(iline, text) #загрузить текст с первой позиции (можно сделать с активной?)

    def onOpenMarkup(self):
        self.iline = -1
        self.ibox = -1
        name = QFileDialog.getOpenFileName(self, caption='Open file', directory='', filter="Markup (*.mkp)")[0]
        if not len(name): return
        mkp = Markup.Markup()
        jpg = mkp.load(name)
        if len(jpg):
            if not self.area or questionYesNo("Разметка содержит изображение. Заменить текущее?")==QMessageBox.Yes:
                self.setImage(jpg,isRawData=True)
                self.filename = name
        elif not self.area:
            info("Разметка не содержит изображение. Загрузите его отдельно")
            return
        self.area.setMarkup(mkp.boxes,mkp.ids,mkp.mu,mkp.text,mkp.coords)
        self.setWindowTitle("PageMarker: "+name)

    def onSaveImage(self):
        if self.filename and self.area:
            name = self.filename+'.jpg'
            pixmap = self.area.pixmap()
            pixmap.save(name)
            info("Изображение сохранено в\n" + name)

    def onSaveText(self):
        if self.filename and self.area:
            name = self.filename + '.txt'
            Markup.saveText(name,self.area.text)
            info("Текст сохранен в\n" + name)

    def onSaveMarkup(self):
        if self.filename and self.area:
            name = self.filename+'.mkp'
            a = self.area
            mkp = Markup.Markup()
            mkp.setmarkup(a.boxes,a.ids,a.mu,a.text,a.coords)

            if questionYesNo("Сохранить вместе с изображением?")==QMessageBox.Yes:
                jpgarr = QByteArray()
                buffer = QBuffer(jpgarr)
                buffer.open(QIODevice.WriteOnly)
                pixmap = self.area.pixmap()
                pixmap.save(buffer, "JPG")
                buffer.close()
                mkp.save(name,jpgarr) #сохранить вместе с изображением
            else:
                mkp.save(name)
            info("Разметка сохранена в\n" + name)
        return

    def onSaveBbox(self):
        if self.filename and self.area:
            name = self.filename+'.bb'
            Markup.saveBoxLines(name,self.area.boxes,self.area.ids)
            info("Области букв сохранены в\n" + name)

    def onSkipBoxLine(self): #пропустить строку с текстом (вставить пустую строку)
        if self.area: self.area.skipBoxLine(self.iline)

    def onSkipTextLine(self): #пропустить строку с текстом (удалить ее)
        if self.area: self.area.skipTextLine(self.iline)

    def onLineSet(self):#Замена текстовой линии со сбросом разметки
        if not self.area or self.iline<0: return
        self.area.setTextLine(self.iline, self.ui.edLine.text())

    def onLineUpdate(self):#Обновление линии без сброса линии в большей части
        if not self.area or self.iline < 0: return
        #self.area.changeTextLine(self.iline, self.ui.edLine.text())
        self.area.updateTextLine(self.iline, self.ui.edLine.text())

    def onChangeMuArg(self, nbox, nchar):
        if not self.area or self.iline < 0 or self.ibox < 0: return
        self.area.changeCurMu(nbox, nchar)

    def onChangeMu(self):
        nbox = self.ui.edNBox.value()
        nchar = self.ui.edNChar.value()
        self.area.changeCurMu(nbox, nchar)

    def onSplitMu(self):
        nbox = self.ui.edNBox.value()
        nchar = self.ui.edNChar.value()
        self.area.splitCurMu(nbox, nchar)


    def onUniteMu(self):
        nmu = self.ui.edNBox.value()
        self.area.uniteCurMu(nmu)

    def onChangeMuLineUp(self):        #перенести на линию вверх
        iline = self.area.currectLine()
        iboxes  = self.area.selectedBoxes()
        if len(iboxes) and questionYesNo("Перенести выделенное в верхнюю линию?") == QMessageBox.Yes:  # UPD
            self.area.moveBoxesToLine(iboxes,iline,iline-1)

    def onChangeMuLineDown(self):      #перенести mu на линию вниз
        iline = self.area.currectLine()
        iboxes  = self.area.selectedBoxes()
        if len(iboxes) and questionYesNo("Перенести выделенное в нижнюю линию?") == QMessageBox.Yes:  # UPD
            self.area.moveBoxesToLine(iboxes,iline,iline+1)

    def onLineNew(self):
        iline = self.area.currectLine()
        iboxes  = self.area.selectedBoxes()
        if len(iboxes) and questionYesNo("Создать новую строку сверху?") == QMessageBox.Yes: #UPD
            self.area.insertNewLine(iline) #вставить в новую линию
            self.area.moveBoxesToLine(iboxes, iline+1, iline) #перенести элементы

    def onLineDel(self):
        iline = self.area.currectLine()
        if questionYesNo("Удалить строку {0}?".format(iline))==QMessageBox.Yes:
            self.area.removeLine(iline)

    def onExcludeBoxes(self):
        iline = self.area.currectLine()
        iboxes = self.area.selectedBoxes()
        if len(iboxes) and questionYesNo("Удалить выделенные области?") == QMessageBox.Yes:
            self.area.excludeBoxes(iline,iboxes)

    @pyqtSlot(QPoint)
    def onAreaPopup(self, pos):
        if self.iline<0 or self.ibox<0: return
        self.menuChange.exec_(self.ui.scrollArea.mapToGlobal(self.area.mapToParent(pos)))

    def printKeyEvent(self,event, comment=None):
        key = int(event.key())
        mods = int(event.modifiers())
        if key & 0x01000000:  # special/standard key
            print(comment, 'logical key: mods {0:08X} key {1:08X}'.format(mods, key))
        else:
            cmods = u''
            if mods & Qt.ControlModifier: cmods += u'Ctl '
            if mods & Qt.AltModifier: cmods += u'Alt '
            if mods & Qt.ShiftModifier: cmods += u'Shft '
            if mods & Qt.KeypadModifier: cmods += u'Kpd '
            if mods & Qt.MetaModifier: cmods += u'Meta '
            cmods += "'{0:c}'".format(key)
            print(comment, u'data key: mods {0:08X} key {1:08X} {2}'.format(mods, key, cmods))

    def keyPressEvent(self, event):
        #горячие клавиши:
        #Ctrl+Tab, Ctrl+Shift+Tab   перемещение к следующему/предыдущему боксу/линии
        #Del                        удалить бокс
        #Space                      пропустить текущий бокс
        #Ctrl+U                     обновить текст
        #Ctrl+T                     разделить бокс
        ctrl = int(event.modifiers())& Qt.ControlModifier
        self.printKeyEvent(event)
        if not self.area: return
        if Qt.Key_0 <= event.key() <= Qt.Key_9: #использовать клавиши 0..9 для быстрого задания числа прямоугольников одному символу
            nbox = event.key()-Qt.Key_0
            self.onChangeMuArg(nbox,1)      #0 - число прямогольников (0,1) пропуск символа
        elif ctrl and event.key()==Qt.Key_Tab: #перейти к следующему элементу
            a = self.area
            iline, ibox = self.iline, self.ibox
            if ibox>=0 and iline>=0:
                a.activateBox(iline,(ibox+1) % a.boxLineCount(iline))
            elif iline>=0:
                a.activateLine((iline+1) % a.lineCount())
        elif event.key() == Qt.Key_Space:   #пропуск bbox
            self.onChangeMuArg(1, 0)
        elif ctrl and event.key()==Qt.Key_Backtab: #перейти к предыдущему элементу
            a = self.area
            iline, ibox = self.iline, self.ibox
            if ibox>=0 and iline>=0:
                a.activateBox(iline,(ibox-1+a.boxLineCount(iline)) % a.boxLineCount(iline))
            elif iline>=0:
                a.activateLine((iline-1+a.lineCount()) % a.lineCount())
        elif event.key()==Qt.Key_Delete:    #UPD удалить выделенные символы
            self.onExcludeBoxes()           #UPD
        elif event.key()==Qt.Key_PageUp: #UPD перенести в верхнюю линию
            self.onChangeMuLineUp()
        elif event.key() == Qt.Key_PageDown: #UPD перенести в нижнюю линию
            self.onChangeMuLineDown()
        elif event.key() == Qt.Key_Insert: #UPD создать новую линию сверху
            self.onLineNew()
        elif ctrl and event.key() == Qt.Key_U: #UPD обновление текста
            self.onLineUpdate()
        elif ctrl and event.key() == Qt.Key_D: #UPD разделить символ/посмотреть увеличенным
            self.onSplitBoxes()
        elif ctrl and event.key() == Qt.Key_W: #UPD обменять bbox местами в строке
            self.onSwapBoxes()
        #нет смысла использовать английские символы - основная раскладка русская
        event.accept()

    @pyqtSlot(int, int)
    def boxActivated(self, iline, ibox):
        self.iline, self.ibox = iline, ibox
        imu = self.area.currentMu()
        mu   = self.area.muValue(iline,imu)
        text = self.area.muText(iline,imu)

        #self.ui.edPos.setText("LINE {0} BOX {1} MU {2} {3}".format(iline,ibox,imu,mu))
        self.statusBar().showMessage("LINE {0} BOX {1} MU {2} {3} TEXT '{4}'".format(iline,ibox,imu,mu, text))
        return

    @pyqtSlot(int)
    def lineActivated(self, iline):
        self.iline, self.ibox = iline, -1
        text = self.area.textLine(iline)
        self.ui.edLine.setText(text)
        #self.ui.edPos.setText("LINE {0}".format(iline))
        self.statusBar().showMessage("LINE {0}".format(iline))
        return

    def extractLetters(self):
        a = self.area
        mkp = Markup.Markup()
        mkp.setmarkup(a.boxes, a.ids, a.mu, a.text, a.coords)
        return mkp.extract(self.im) #образцы (их можно показать в другом диалоговом окне

    def onExtractLetters(self):
        samples = self.extractLetters()[0]
        name = self.filename+'.smp'
        samples.save(name)
        info("Символы извлечены и сохранены в \n"+name)

    #обработать все файлы
    def onPathCovertMkpSmp(self):
        path = QFileDialog.getExistingDirectory(self, "Каталог с примерами", "./", QFileDialog.ShowDirsOnly)
        print(path)
        if len(path) == 0: return
        mkpnames = listfiles(path, filter='.mkp')
        for name in mkpnames:
            print("load: "+name)
            mkp = Markup.Markup()
            jpg = mkp.load(name) #сырой
            if len(jpg)<=0:
                if questionYesNo("Разметка не содержит изображения. Файл будет пропущен. Продолжить?")==QMessageBox.Yes:
                    print("skip")
                    continue
                return #без изображения разметка пропускается
            im = self.convertJpgToRawIm(jpg) #преобразовать в битовой
            samples = mkp.extract(im)[0]     #извлечь примеры по разметке
            samples.save(name+'.smp')
            print("save: "+name+'.smp')
        info("Обработка завершена")


    def onFindLetters(self):
        #извлечь буквы и из соответствие разметке (imu)
        samples, adr = self.extractLetters()
        if len(samples)<=0:
            info("Нет примеров")
            return
        #показать диалог
        dlg = DlgFindLetters()
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint)
        dlg.setSamples(samples)
        if dlg.exec_()==QDialog.Accepted:
            ids = dlg.selectedSamples() #получить список выделенных
            if len(ids):
                adr0 = adr[ids[0]]
                iline, ibox = self.area.activateMu(adr0[0],adr0[1]) #показать только первый
                self.area.split_active_line = iline
                self.area.split_active_box = ibox


    def onEditText(self):
        dlg = DlgText()
        #загрузить текст
        if self.filename and self.area:
            text = self.area.text
            i=len(text)-1
            while i>=0:
                if text[i]!="": break
                i-=1
            if i>=0: dlg.setText('\n'.join(text[:i+1]))
            else:    dlg.setText("")
        if dlg.exec_()==QDialog.Accepted:
            text = dlg.getText().splitlines()
            if len(text) < self.area.lineCount():
                text.extend([""]*(self.area.lineCount()-len(text)))
            self.area.updateTextLines(0,text) #UPD self.area.setTextLines(0,text)
            self.lineActivated(self.iline) #UPD обновить активную строку

    def onSplitBoxes(self):
        iline = self.area.currectLine()
        ibox = self.area.currentBox()
        if iline < 0 or ibox < 0:
            print("Not select");
            return  # объект не выбран
        gid = self.area.ids[iline][ibox]
        if self.area.coords is None:
            print("Not coords");
            return
        coord = self.area.coords[gid]
        dlg = SplitBox(coord, len(self.area.coords))
        dlg.set_image()
        if dlg.exec_() == QDialog.Accepted and dlg.pointCount():
            c1, c2, box1, box2, is_y = dlg.area.split_coords()
            if not c1:
                info("Неверно выделена область")
            else:
                self.area.sp_boxes(gid, c1, c2, box1, box2, is_y)
                self.area.changeCurMu(1, 1)

    def onSwapBoxes(self):
        #обменять текущие прямоугольники в принудительном порядке
        iline = self.area.currectLine()
        ibox = self.area.currentBox()
        if iline < 0 or ibox < 0: return  # объект не выбран
        self.area.swapBoxes(iline,ibox,ibox+1)

    def onCheckHyp(self):
        if not self.area: return
        #проверка гипотезы
        iline = self.area.currectLine()
        if iline<0: return

        a = self.area
        mkp = Markup.Markup()

        sel = self.area.selectedBoxes()
        if len(sel): #загрузить только выделенные элементы
            mkp.setmarkup(a.boxes, [[a.ids[iline][i] for i in sel]], None, None, a.coords)  # одна линия разметки
        else:   #загрузить всю строку с разметкой
            mkp.setmarkup(a.boxes, [a.ids[iline]], [a.mu[iline]], [a.text[iline]], a.coords) #одна линия разметки
        #(а можно даже для выделенных элементов определять разметку)
        dlg = DlgHypChecker()
        dlg.setNetModel(self.net)
        #заглушка с фикс. статистикой
        #только для 74 страницы
        self.lawmlw = {'О': (23.787037037037038, 2.6424277765312363), 'Р': (20.155555555555555, 2.210636464968158), 'К': (23.783783783783782, 3.005716491774669), 'Е': (25.06896551724138, 3.7777117182756474), 'С': (19.636363636363637, 3.6846790232165723), 'Т': (27.266666666666666, 5.322488974989886), 'З': (22.863636363636363, 2.3020831385637455), 'А': (23.882978723404257, 3.376566249586283), 'И': (23.0, 3.0131984799155), 'Г': (19.714285714285715, 2.2069771859536127), 'Л': (26.29090909090909, 4.198149927041357), 'Н': (20.469135802469136, 2.6992747985982852), 'Б': (23.58823529411765, 2.250720761142234), 'Ь': (21.88888888888889, 3.2126293988446575), 'У': (21.470588235294116, 2.199402246569402), 'Д': (39.04, 5.102783554100644), 'Я': (21.0, 3.116774889895918), 'П': (25.333333333333332, 2.160246899469287), 'Ю': (37.0, 2.0), 'М': (27.529411764705884, 3.688099256333467), '.': (5.642857142857143, 2.688790032102673), ' ': (6.391304347826087, 7.976809487697733), ',': (6.388888888888889, 4.097951912424451), 'В': (24.5, 2.7638539919628333), 'Э': (23.0, 2.516611478423583), 'Ж': (39.0, 4.4077853201547175), 'Й': (24.25, 2.680951323690902), 'Ы': (30.058823529411764, 3.588717421804622), 'Ц': (29.4, 5.782732917920384), 'Ч': (21.181818181818183, 1.5850541612875175), 'Ш': (31.0, 2.8284271247461903), '-': (15.166666666666666, 3.435921354681384), 'Щ': (38.666666666666664, 3.6817870057290873), 'Х': (21.0, 4.163331998932265)}
        dlg.setLawMLW(self.lawmlw)
        #только для 74 страницы
        self.lawcld = {'О': (0.5939210621647028, 1.5114247610656453), 'Р': (0.5437895617262609, 1.06160876371092), 'К': (0.34776702103482665, 1.09476354564698), 'Е': (0.5383098288313846, 1.221720838813538), 'С': (0.473828098332397, 1.36653209291826), 'Т': (0.5443616245362438, 1.6060633384946366), 'З': (0.22428711423626782, 1.1955832092651029), 'А': (0.2848349803949744, 1.1679123551225927), 'И': (-0.18322420774083673, 1.0543960616594867), 'Г': (0.9230070548936673, 1.5447237500921054), 'Л': (0.4331257890233095, 1.1593330067682754), 'Н': (0.2391980684509418, 1.2183477879180866), 'Б': (0.6010509989322614, 1.013785972847982), 'Ь': (0.1554841719699035, 1.2801013775705519), 'У': (-0.2073363203057129, 1.106654499202437), 'Д': (-3.706913144755448, 1.348797874165128), 'Я': (0.22001392378608184, 1.6325919001336406), 'П': (0.5244268973220053, 0.9529425845667147), 'Ю': (0.1972066699736009, 0.3782882505993673), 'М': (0.6139071920885529, 1.2436735866026245), '.': (-10.525014143637337, 1.3903619731025245), ' ': (12.545623580446184, 12.0074591433866), ',': (-16.47642891313033, 1.2439426136372431), 'В': (0.14059136429652833, 1.0683685793516196), 'Э': (2.520422318599875, 0.7856593176600013), 'Ж': (0.4494082607974974, 1.5023563582089379), 'Й': (2.670013723608868, 1.6673038466451944), 'Ы': (0.1503494614353442, 1.0316369983414244), 'Ц': (-5.590435396871084, 0.7165815433720197), 'Ч': (-0.19718669957386095, 1.1678833463121943), 'Ш': (0.49172715290569613, 0.5889544324301327), '-': (-1.5751987624175996, 2.2928072674035405), 'Щ': (-4.893052135045839, 0.5807471635761955), 'Х': (0.46794590830961624, 0.6851803495265547)}
        dlg.setLawCLD(self.lawcld)

        dlg.setLineMarkup(mkp) #установить разметку и сразу отфильтровать
        dlg.exec_()


    def onBuildStatistics(self):
        #собрать статистику по размеченному тексту
        if not self.area: return
        a = self.area
        mkp = Markup.Markup()
        mkp.setmarkup(a.boxes, a.ids, a.mu, a.text, a.coords) #mkp.setmarkup(a.boxes, [a.ids[iline]], [a.mu[iline]], [a.text[iline]], a.coords) #одна линия разметки
        #показать словари со статистикой
        mm = MarkupMetrics(mkp)
        mm.buildMetricDicts()
        print("DRECT",mm.drect)
        print("DMLW",mm.dmlw)
        print("DNSEG",mm.dnseg)
        print("DPOS", mm.dpos)

        self.lawmlw = mm.lawMLW() #апроксимация закона распределения значений по словаю
        print("LAW MLW:",self.lawmlw)

        ch = mm.detectCharHeight()
        print("CHARHEIGHT:",ch)

        cfs = mm.centralLines() #коэффициенты
        self.area.setCentralLines(cfs) #установить и показать на странице

        self.lawcld = mm.lawCLD()
        print("LAW CLD:", self.lawcld)

        #собрать статистику о расположении относительно центральной линии

