# coding=utf-8
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import numpy as np
from HpSamples import *

def info(text):    QMessageBox(QMessageBox.Information, "Информация", text).exec_()
def questionYesNoAll(text):
    return QMessageBox(QMessageBox.Question, "Подтверждение", text,
                       buttons=QMessageBox.Yes| QMessageBox.YesToAll| QMessageBox.No | QMessageBox.NoToAll | QMessageBox.Cancel).exec_()
def questionYesNo(text):
    return QMessageBox(QMessageBox.Question, "Подтверждение", text, buttons=QMessageBox.Yes| QMessageBox.No).exec_()

class SmpArea(QLabel):

    MAX_IMAGE_HEIGHT = 32768

    MODE_SCALE = 0          # растянуть
    MODE_CENTER = 1         # центрировать
    MODE_INSCRIBE = 2       # вписать по большей стороне

    FLAG_DEFAULT = 0
    FLAG_SELECTED = 1
    FLAG_MASKED = 2

    def __init__(self, parent):
        super().__init__(parent)

        self.pred = (-1,-1)

        #исходные примеры
        self.smp        = HpSamples()   #все примеры
        self.groups     = dict()        #сгруппированные номера примеров (не обязательно по алфавиту)
        self.names      = []            #список имен групп (в порядке отображения)

        self.grouprect  = []            #область, занимаемая одной группой
        self.itemrect   = []            #область, занимаемая конкретным элементом
        self.itemstate  = []            #состояния каждого примера (DEFAULT|SELECTED|MASKED)

        #параметры отображения прямоугольников по умолчанию
        self.scalemode  = self.MODE_CENTER  #центрировать
        self.fixbound   = QRect(0,0,32,32)
        self.pageWidth  = 800
        self.leftIndent = 20
        self.rightIndent= 20
        self.groupIndent= QSize(5, 5)
        self.itemIndent = QSize(5, 5)
        self.textSize   = 20
        self.countInLine = 0 #число элементов на линии (максимальное значение)

    # сигналы
    itemSelected    = pyqtSignal(int) #выбор элемента
    itemMasked      = pyqtSignal(int) #маскировка элемента

    def mousePressEvent(self, ev):
        #self.mousepos = ev.pos()
        if Qt.LeftButton == ev.button():
            self.pred = self.findBoxByPos(ev.pos())
            print("SELECT", self.pred)

    def mouseReleaseEvent(self, ev): #ev: QMouseEvent
        if Qt.LeftButton == ev.button():
            cur = self.findBoxByPos(ev.pos())
            curid, predid = self.idByBox(cur), self.idByBox(self.pred)
            print("SELECT", curid)
            if curid<0:
                if predid<0:
                    if self.selectedCount() and questionYesNo("Снять выделение со всех элементов?") == QMessageBox.Yes:
                        self.deselectAll()  # сбросить все выделенные элементы
                else: #убрал курсор с элемента
                    pass
            else: #id>=0
                if predid<0: #курсор появился на элементе
                    pass
                elif curid==predid: #тот же элемент, инвертировать выделение
                    self.inverseItem(curid)
                    self.itemSelected.emit(curid)
                    self.update()
                else: #групповое выделение с pred до id
                    if cur[0]>=self.pred[0]:start=self.pred; end= cur       #сначала с меньшим номером группы
                    else:                   start=cur;       end= self.pred

                    if start[0]==end[0]: #в одной группе
                        ids = self.idsByBoxRange(start[0],start[1],end[1])
                        self.inverseItems(ids)
                    else: #в разных группах
                        ids = self.idsByBoxRange(start[0],start[1],len(self.groups[self.names[start[0]]])-1)
                        self.inverseItems(ids) #выделить конец первой группы
                        for gid in range(start[0]+1,end[0]):
                            ids = self.idsByBoxRange(gid, 0, len(self.groups[self.names[gid]])-1)
                            self.inverseItems(ids) #выделить все промежуточные
                        ids = self.idsByBoxRange(end[0],0,end[1])
                        self.inverseItems(ids) #выделить начало последней
                    self.itemSelected.emit(curid)
                    self.update()


    # def mouseMoveEvent(self, ev: QMouseEvent):
    #    print("move",ev)
    #    return

    def pointInBoxes(self, pt, boxes):
        # нахождение точки внутри списка
        # возвращает номер прямоугольника или -1
        for i in range(len(boxes)):
            if boxes[i].contains(pt):
                return i
        return -1

    def findBoxByPos(self, pt): #нахождение пары (номер группы, номер элемента в группе)
        gpos = self.pointInBoxes(pt, self.grouprect) #номер группы
        if gpos < 0: return -1,-1
        boxes = [self.itemrect[i] for i in self.groups[self.names[gpos]]]
        ipos  = self.pointInBoxes(pt, boxes)
        if ipos<0:    return -1,-1       #выход за границу поиска
        else:         return gpos,ipos   #получить номер

    def idByBox(self,box): #преобразование адреса области изображения в номер элемента
        if box[0]<0 or box[1]<0: return -1
        return self.groups[self.names[box[0]]][box[1]]

    def idsByBoxRange(self,gpos,istart,iend):
        if iend > istart:   start = istart; end = iend
        else:               start = iend;   end = istart
        return [self.groups[self.names[gpos]][i] for i in range(start,end+1)]

    def selected(self):  # список номеров выбранных элементов
        return [i for i in range(len(self.itemstate)) if self.itemstate[i] & self.FLAG_SELECTED]

    def selectedCount(self):
        # python hack: либо выбран, либо выбрать и замаксирован
        return self.itemstate.count(self.FLAG_SELECTED)+self.itemstate.count(self.FLAG_MASKED|self.FLAG_SELECTED)

    def maskedItems(self):  # список номеров замаскированных элементов
        return [i for i in range(len(self.itemstate)) if self.itemstate[i] & self.FLAG_MASKED]

    def maskedCount(self): #число отмеченных элемеентов
        # python hack: либо маскирован, либо выбрать и замаксирован
        return self.itemstate.count(self.FLAG_MASKED) + self.itemstate.count(self.FLAG_MASKED|self.FLAG_SELECTED)


    def selectItems(self, ids):
        for i in ids:
            self.itemstate[i] |= self.FLAG_SELECTED
        self.update()


    def selectItem(self, id):   # выделить элемент
        if id<0: return
        self.itemstate[id] |= self.FLAG_SELECTED
        #self.itemSelected.emit(id) # выбран элемент
        self.update()

    def selectByName(self, groupname): #выделить все элементы группы
        print("selectByName",groupname)
        ids = self.groups[groupname]
        self.selectItems(ids)

    def deselectItem(self, id): #сбросить выделение
        if id<0: return
        self.itemstate[id] &= ~self.FLAG_SELECTED
        self.update()

    def deselectAll(self):
        self.itemstate = [state & ~self.FLAG_SELECTED for state in self.itemstate]
        self.update()

    def selectAll(self):
        self.itemstate = [state | self.FLAG_SELECTED for state in self.itemstate]
        self.update()


    def inverseItem(self, id):
        self.itemstate[id] ^= self.FLAG_SELECTED

    def inverseItems(self, ids):
        for id in ids:
            self.itemstate[id] ^= self.FLAG_SELECTED

    def inverseSelection(self):
        self.itemstate = [state ^ self.FLAG_SELECTED for state in self.itemstate] #инвертировать выделение
        self.update()


    def maskItem(self, id):   # выделить элемент
        if id<0: return
        self.itemstate[id] |= self.FLAG_MASKED
        #self.itemMasked.emit(id)  # выбран элемент
        self.update()

    def unmaskItem(self, id):  # сбросить выделение
        if id<0: return
        self.itemstate[id] &= ~self.FLAG_MASKED
        self.update()

    def unmaskAll(self):
        print("unmaskAll")
        self.itemstate = [state & ~self.FLAG_MASKED for state in self.itemstate]
        self.update()

    def maskSelected(self):
        print("maskSelected")
        self.itemstate = [state | ((state & ~self.FLAG_SELECTED) <<1) for state in self.itemstate]
        self.update()

    def unmaskSelected(self):
        print("unmaskSelected")
        self.itemstate = [state & ~((state & ~self.FLAG_SELECTED) << 1) for state in self.itemstate]
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)

        # Нарисовать маски
        red = QPen(QColor(255, 0, 0))
        red.setWidth(2)
        p.setPen(red)
        p.setBrush(QBrush(QColor(255, 0, 0, 50)))
        for igroup in range(len(self.names)):
            g = self.grouprect[igroup]
            if g.y()<0 or g.y()>=self.MAX_IMAGE_HEIGHT: continue #пропустить невидимую группу
            ids = self.groups[self.names[igroup]]
            for i in ids:
                if self.itemstate[i] & self.FLAG_MASKED:
                    p.drawLine(self.itemrect[i].bottomLeft(), self.itemrect[i].topRight())

        # Нарисовать выделенные элементы
        green = QPen(QColor(0, 255, 0))
        green.setWidth(2)
        p.setPen(green)
        p.setBrush(QBrush(QColor(0, 0, 0, 0)))
        for igroup in range(len(self.names)):
            g = self.grouprect[igroup]
            if g.y()<0 or g.y()>=self.MAX_IMAGE_HEIGHT: continue #пропустить невидимую группу
            ids = self.groups[self.names[igroup]]
            for i in ids:
                if self.itemstate[i] & self.FLAG_SELECTED:
                    p.drawRect(self.itemrect[i])

    def maxbounds(self, boxes):
        # рассчитать максимальный ограничивающий прямоугольник среды выбранных изображений
        maxx, maxy = 0, 0
        for r in boxes:
            dy, dx = r.height(), r.width()
            if dy > maxy: maxy = dy
            if dx > maxx: maxx = dx
        return QRect(0, 0, maxx, maxy)

    def uniteboxes(self, boxes, ids=None):
        # нахождение общего ограничивающего прямоугольника
        if ids is None:
            n = len(boxes)
            if n <= 0:
                return QRect()
            elif n == 1:
                return boxes[0]
            u = QRect()
            for i in range(n): u = u.united(boxes[i])
            return u
        else:
            n = len(ids)
            if n <= 0:
                return QRect()
            elif n == 1:
                return boxes[ids[0]]
            u = QRect()
            for i in ids: u = u.united(boxes[i])
            return u

    def getViewParams(self):
        return self.pageWidth, self.leftIndent, self.rightIndent, \
               self.groupIndent, self.itemIndent, self.textSize, self.scalemode, self.fixbound

    def setViewLimits(self, pageWidth, leftIndent, rightIndent, groupIndent, itemIndent, textSize):
        # pageWidth:int, leftIndent:int, rightIndent:int, groupIndent:QSize, itemIndent:QSize, textSize:int
        self.pageWidth = pageWidth
        self.leftIndent = leftIndent
        self.rightIndent = rightIndent
        self.groupIndent = groupIndent
        self.itemIndent = itemIndent
        self.textSize = textSize

    def setScaleMode(self, mode): #режим масштабирования (MODE_SCALE, MODE_CENTER, MODE_INSCRIBE)
        self.scalemode = mode

    def setFixBound(self, bound=None): #установка ограничивающего прямоугольника по умолчанию QRect
        self.fixbound = bound

    def setCountInLine(self, count=0): #установка предельного числа элементов на линии
        self.countInLine=count

    def placeboxes(self, bound, n, start, indent, count_in_line):
        """
        Размещение прямоугольных областей по линиям
        :param bound: QRect, QSize, размеры одной области (width, height)
        :param n: int, число формируемых прямоугольных областей
        :param start: QPoint - начальная точка
        :param indent: QPoint - интервал между символовами по X и по Y
        :param count_in_line: int - число прямоугольников на одной линии
        :return:
        """
        bw, bh = bound.width(), bound.height()
        w, h   = bw + indent.width(), bh + indent.height()
        boxes2=[]
        for i in range(n):
            x=start.x() + (i % count_in_line) * w
            y=start.y() + int(i / count_in_line) * h
            boxes2.append(QRect(x, y, bw, bh))
        return boxes2

    def setGroupedSamples(self, samples, groups, keysInOrder): #обновить все представление
        self.samples   = samples
        self.groups    = groups
        self.names     = keysInOrder    # порядок следования групп
        self.itemstate = [self.FLAG_DEFAULT]*len(self.samples)
        self.buildMeshAndImage()

    def setViewGroup(self,groupname): #установить группу, которая просматривается
        try:
            # поменять порядок следования элементов (перевычислить mesh, но не трогать состояния элементов)
            pos = self.names.index(groupname)
            print(groupname,pos)
            count = len(self.names)
            order = list(range(pos,count))+list(range(0,pos))
            self.names = [self.names[i] for i in order]
            self.buildMeshAndImage()
        except:
            print("setViewGroup: group not found")

    def changeGroupOrder(self,keysInOrder): #группы в другом порядке (число элементов и их состояния не изменились)
        self.names = keysInOrder
        self.buildMeshAndImage()

    def buildMeshAndImage(self): #пересчет позиций элементов (не вызывается напрямую)
        # Установить параметры разметки страницы
        pageWidth  = self.pageWidth         # максимальная ширина изображения
        boxindent  = self.itemIndent
        lineindent = self.groupIndent
        lineheaderheight = self.textSize    # максимальная высота изображения (текст над буквами)
        leftspace  = self.leftIndent        # отступ слева
        rightspace = self.rightIndent       # отступ справа

        # Рассчитать положение элементов групп на странице и запомнить их
        ngroups        = len(self.names)
        self.grouprect = [None]*len(self.names)     #области групп
        self.itemrect  = [None]*len(self.samples)   #области элементов

        #Рассчитать текущие положения itemrect
        x, y = leftspace, 0         # текущее положение
        for gid in range(ngroups):     # для каждой линии
            y += lineheaderheight   # сместить на высоту текста
            ids = self.groups[self.names[gid]]       # список номеров примеров в группе
            boxes = self.samples.imgsrects(ids)      # получить исходные размеры изображений
            if self.fixbound.isEmpty(): bound = self.maxbounds(boxes)       # максимальные размеры x,y
            else : bound = self.fixbound
            # рассчитать сколько помешается в одной линии (число boxindent на 1 меньше должно быть)
            if self.countInLine > 0:
                count_in_line = self.countInLine #зафиксированное значение
            else:
                count_in_line = int((pageWidth - leftspace - rightspace + boxindent.width()) / (bound.width() + boxindent.width()))

            mesh = self.placeboxes(bound, len(boxes), QPoint(x, y), boxindent, count_in_line)  # соответствующие элементы

            for i in range(len(ids)):
                self.itemrect[ids[i]] = mesh[i]
            self.grouprect[gid]=self.uniteboxes(mesh)
            if len(mesh): y = mesh[-1].y()+mesh[-1].height() # новое положение (если были изображения)
            y += lineindent.height()                    # расстояние между группами

        # теперь y содержит максимальную высоту, с учетом последней линии
        maxheight = y# - lineindent.height()
        if maxheight>self.MAX_IMAGE_HEIGHT: maxheight = self.MAX_IMAGE_HEIGHT
        print("image=",pageWidth,"*",maxheight)

        #Сформировать изображение
        wholeimage = QImage(pageWidth, maxheight, QImage.Format_Grayscale8) #исходное изображение
        p = QPainter()
        p.begin(wholeimage)
        p.setPen(QPen(QColor(255, 255, 255)))
        p.setBrush(QBrush(QColor(255,255,255)))
        p.drawRect(QRect(QPoint(0,0),wholeimage.size()))
        p.setBrush(QBrush(QColor(255, 255, 255, 0)))
        p.setPen(QPen(QColor(150, 150, 150)))
        pensize = 1
        p.setFont(QFont("Arial", 16))

        mode = self.scalemode
        for gid in range(ngroups):                # для каждой группы
            key = self.names[gid]
            g = self.grouprect[gid]
            if g.y() < 0 or g.y() >= self.MAX_IMAGE_HEIGHT: continue  # пропустить невидимую группу

            ids = self.groups[key]
            p.drawText(self.grouprect[gid].topLeft(), '{0}[{1}]'.format(key, len(ids)))
            for index in ids:
                im = self.samples.imgs[index]  # собственно изображение в виде np.array
                h, w = im.shape
                image = HpSamples.nparray2qimage(im) #не выровнено image = QImage(im, w, h, 1 * w, QImage.Format_Grayscale8)
                r = self.itemrect[index]
                # центрировать изображение в регионе
                need = False
                if mode == self.MODE_CENTER:
                    if w>r.width() or h>r.height(): need = True #вписать, если больше области
                    else:
                        sx, sy = int((r.width()- w)/2), int((r.height()- h) / 2)
                        r = QRect(r.x()+sx, r.y()+sy, w, h)
                if mode == self.MODE_INSCRIBE or need:
                    rx, ry = w/r.width(), h/r.height() # отношение
                    if rx>ry: # заполнение по x
                        h2 = int(h/rx)
                        sy = int((r.height() - h2) / 2)
                        r = QRect(r.x(), r.y()+sy, r.width(), h2)
                    else: # заполнение по y
                        w2 = int(w/ry)
                        sx = int((r.width() - w2) / 2)
                        r = QRect(r.x()+sx, r.y(), w2, r.height())
                p.drawImage(r, image, QRect(0, 0, w, h))
                rm = self.itemrect[index]
                p.drawRect(QRect(rm.x()-pensize,rm.y()-pensize,rm.width()+pensize,rm.height()+pensize))
        p.end()
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop) # иначе картинка будет расположена по центру и координаты мыши будут неправильные
        self.setPixmap(QPixmap().fromImage(wholeimage))
