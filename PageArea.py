from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import numpy as np

import CoordsObj
import Markup


class PageArea(QLabel):

    GRAY  = QColor(200, 200, 200)
    RED   = QColor(200, 100, 100)
    GREEN = QColor(100, 200, 100)
    BLACK = QColor(0, 0, 0)

    STATE_UNKNOWN = 0
    STATE_ACTIVE = 1
    STATE_EDITED = 2

    PENMAPSIZE = 512 #UPD 128
    penmap = [] #таблица заранее созданных цветов для раскраски прямоугольников
    colormap=[]

    def __init__(self, parent):
        super().__init__(parent)

        self.ids = []  # [[int,...],...] список номеров используемых областей на каждой линии
        self.boxes = []  # [QRect,...] список прямоугольных областей
        self.text = []  # [string,] строки с текстом для каждой линии
        self.mu = []  # [[(a,b),...],...] разметка для каждой строки a-число прямоугольников, b-число символов

        self.lines = []   # [QRect,...] ограничивающие прямоугольники для каждой линии
        self.states = []  # [int,] состояние каждой линии (0-не размечена, 1-редактируется, 2-размечена)
        self.iline  = -1  # текущая линия
        self.iboxes = []  # набор выделенных прямоугольников в текущей линии
        self.coords = [] # координаты букв

        self.clcfs= None #коэффициенты центральных линий (если заданы)
        #self.blcfs= None #коэффициенты базовых линий (если заданы)

        self.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        self.textshift = QPoint(0, -2)
        self.mousepos = QPoint()
        self.mousebut = 0

        #создать таблицу предопределенных цветов boxes (с фикс. расстоянием между элементами)
        #self.penmap = []
        self.colormap=[]
        i=0; cpred=[0,0,0] #UPD
        while i<self.PENMAPSIZE:    #UPD
            c=np.random.rand(3)*255
            if abs(c[0]-cpred[0])<64 and abs(c[1]-cpred[1])<64 and abs(c[2]-cpred[2])<64: continue #UPD
            i+=1; cpred=c #UPD
            color = QColor(int(c[0]), int(c[1]), int(c[2]))
            pen = QPen(color)
            pen.setWidth(2)
            self.penmap.append(pen)
            self.colormap.append(color)

    clicked       = pyqtSignal(QPoint)
    rightClicked  = pyqtSignal(QPoint)
    lineActivated = pyqtSignal(int) #какая линия активируется, какая гасится
    boxActivated  = pyqtSignal(int, int) #на какой линии, какой прямоугольник

    def setCentralLines(self,cfs): #установка коэффициентов центральных линий
        self.clcfs = cfs
        self.repaint()

    def mousePressEvent(self, ev):
        if Qt.LeftButton == ev.button():
            self.mousepos = ev.pos()
            self.mousebut = 0
            self.iboxes = []
            self.mousebut = Qt.LeftButton

    def sp_boxes(self, id, c1, c2, box1, box2, is_y):
        #id - глобальный номер разделяемого сегмента
        #с1, с2 - ptc для разделенных сегментов
        #box1, box2 - границы для разделенных сегментов
        #is_y - деление было по горизонтали
        ib = self.iboxes[0]
        il = self.iline

        self.coords[id] = c1
        self.coords.append(c2)
        self.ids[il].insert(ib + 1,(len(self.boxes))) #добавить второй номер
        self.boxes[id] = box1
        self.boxes.append(box2)

        # отсортировать результат по координатам X, начиная с позиции разделения
        self.ids[il][ib:] = sorted(self.ids[il][ib:],key=lambda k: self.boxes[k].x())
        self.repaint()

    def mouseReleaseEvent(self, ev: QMouseEvent):
        self.mousebut=0

        if Qt.RightButton == ev.button():
            self.rightClicked.emit(ev.pos()) #контекстное меню
        elif Qt.LeftButton == ev.button():
            if self.mousepos != ev.pos():
                #окончательно определить список активных элементов
                self.activateBoxes()
            else:
                self.clicked.emit(ev.pos())
                iline, ibox = self.findBoxInActiveLine(ev.pos())
                if ibox>=0: #выбран прямоугольник
                    self.activateBox(iline, ibox)
                    return
                iline = self.findActiveLine(ev.pos()) #активируется линия, вместо прямоугольников
                if iline>=0:
                    self.activateLine(iline)
                    return
            self.repaint()

    def mouseMoveEvent(self, ev: QMouseEvent):
        if self.mousebut==Qt.LeftButton:
            pos = ev.pos()
            x,y,w,h = min(self.mousepos.x(),pos.x()), min(self.mousepos.y(),pos.y()), self.mousepos.x()-pos.x(), self.mousepos.y()-pos.y()
            if w<0: w=-w
            if h<0: h=-h
            iline, iboxes = self.findBoxesInActiveLine(QRect(x,y,w,h))
            self.iline = iline
            self.iboxes=iboxes
            self.repaint()

    def activateLine(self, iline):
        #активация линии заключается в смене состояния линии
        if iline == self.iline:  # выбрана та же линия
            return

        for i in range(len(self.states)):
            if self.states[i]==self.STATE_ACTIVE:
                if len(self.text[i]):  self.states[i] = self.STATE_EDITED #неизвестное состояние, если текста нет
                else:                  self.states[i]= self.STATE_UNKNOWN
        self.states[iline]=self.STATE_ACTIVE #изменить состояние линии
        self.iline = iline
        self.iboxes = [] #сбросить состояние активного box
        #print("new line", iline)
        self.repaint()
        self.lineActivated.emit(iline) #только если линия отличается
        return

    def activateBoxes(self):
        if len(self.iboxes):
            self.boxActivated.emit(self.iline,self.iboxes[0]) #активирован первый из группы


    def activateBox(self, iline, ibox):
        if len(self.iboxes)==1 and ibox == self.iboxes[0]:  # выбран тот же прямоугольник
            #print("same box", ibox, self.ibox)
            return
        else:  # выбран другой прямоугольник
            self.iline = iline
            self.iboxes = [ibox]
            #print("new box", iline,ibox)  # сначала box, затем линию
            self.repaint()
            self.boxActivated.emit(iline, ibox)
        return

    def activateMu(self,iline,imu): #активация набора прямоугольников (активация первого из набора)
        if iline<0 or iline>=len(self.mu): return
        line = self.mu[iline]
        if imu < 0 or imu>=len(line): return
        ibox=0
        for m in line[:imu]: ibox+=m[0] #найти номер первого box mu как сумму до него
        if line[imu][0]>0: #если прямоугольник не пропущен в текущем mu
            self.activateLine(iline)
            self.activateBox(iline,ibox)
            print("ActivateMu")
        return iline, ibox


    def findActiveLine(self, pt): #найти активную линию
        iline = self.pointInBoxes(pt, self.lines)
        return iline

    def findBoxInActiveLine(self, pt): #найти активный прямоугольник
        for iline in range(len(self.states)):
            if self.states[iline]==self.STATE_ACTIVE: #редактируемое состояние линии
                ibox = self.pointInBoxesIds(pt,self.boxes,self.ids[iline]) #относительный номер на линии (не абсолютный)
                if ibox>=0: return iline, ibox #найден номер активного прямоугольника на линии
        return -1, -1 #не найден

    def findBoxesInActiveLine(self, rect):
        iboxes=[] #список активных
        for iline in range(len(self.states)):
            if self.states[iline] == self.STATE_ACTIVE:
                ids = self.ids[iline]
                iboxes.extend([i for i in range(len(ids)) if rect.intersects(self.boxes[ids[i]])]) #добавить, если пересекаются
                if len(iboxes): return iline, iboxes
        return -1, []

    def boxLineCount(self, iline):
        if iline<0 or iline>=len(self.ids): return 0
        return len(self.ids[iline])

    def lineCount(self):
        return len(self.ids)

    def load(self, pix):
        self.setPixmap(pix)

    def paintEvent(self, ev):
        super().paintEvent(ev)
        p = QPainter(self)
        p.setPen(QPen(Qt.red, 3, Qt.SolidLine))
        self.paintLines(p)


    def paintLines(self, p):
        gray = QPen(self.GRAY); gray.setWidth(2)
        green = QPen(self.GREEN); green.setWidth(2)
        red = QPen(self.RED); red.setWidth(2)
        pens = [red, gray, green]

        for i in range(len(self.states)):
            if self.states[i]!=self.STATE_ACTIVE:
                p.setPen(pens[self.states[i]]) #цвет определяется состоянием
                p.drawRect(self.lines[i])
                p.drawText(self.lines[i].topLeft() + QPoint(2,10), "{}".format(i))
            else: #вывести отдельные прямоугольники i-й линии
                #self.paintBoxes(p, i)
                self.paintMu(p, i)
                self.paintCentralLine(p,i)
        return

    def paintCentralLine(self,p,iline): #нарисовать центральную линию
        if self.clcfs is None: return
        cfs = self.clcfs[iline]
        ids = self.ids[iline]   #номера box по линии
        x0 = self.boxes[ids[0]].x() #первый
        b1 = self.boxes[ids[-1]] #последний
        x1 = b1.x()+b1.width()
        y0 = np.polyval(cfs,x0)
        y1 = np.polyval(cfs,x1)
        black = QPen(self.BLACK)
        #print([x0,y0,x1,y1])
        p.setPen(black)
        p.drawLine(x0,y0,x1,y1)


    #def paintBoxes(self, p, iline):
    #    ids = self.ids[iline]
    #    for i in range(len(ids)):
    #        if iline==self.iline and i==self.ibox: #если прямоугольник выделен
    #            pen=QPen(self.randPen(iline, i))
    #            pen.setWidth(5)
    #            p.setPen(pen)
    #        else:
    #           p.setPen(self.randPen(iline, i))
    #        p.drawRect(self.boxes[ids[i]])

    def paintMu(self, p, iline): #обработать линию
        ids = self.ids[iline]   #номера box по линии
        text = self.text[iline] #строка текста
        mu = self.mu[iline]   #разметка

        nbox = len(ids)
        ntext = len(text)
        ibox, ich = 0, 0
        black= QPen(self.BLACK); black.setWidth(2)
        for j in range(len(mu)): #для всех записей разметки
            nb, nc = mu[j]
            pen = QPen(self.randPen(iline, ibox)) #цвет для всех объединенных box (отвязаться от абс номера)
            for i in range(nb):
                pos = ibox+i
                if pos>=nbox: break #не прямоугольника с таким индексом
                #вывод прямоугольника
                if iline == self.iline and pos in self.iboxes: pen.setWidth(5)
                else: pen.setWidth(2)
                p.setPen(pen)
                p.drawRect(self.boxes[ids[pos]])
                #вывод текста
                if i==0 and nc>0 and (ich+nc)<=ntext:
                    p.setPen(black)
                    if nb>1:#если несколько прямоугольников
                        p.drawText(self.boxes[ids[pos]].topLeft()+self.textshift, "{0}[{1}]".format(text[ich:(ich + nc)],nb))
                    else: #если 1 прямоугольник
                        p.drawText(self.boxes[ids[pos]].topLeft()+self.textshift, text[ich:(ich+nc)])
            ibox+=nb; ich+=nc #новые позиции

    def randPen(self, iline, ibox):
        #возвращает случайный цвет из таблицы по заданному номеру строки и прямоугольника
        return self.penmap[(iline*47+ibox) % self.PENMAPSIZE] #UPD номер цвета

    def drawPoint(self, pt):
        id = self.pointInBoxes(pt, self.lines)
        if id>=0:
            if self.states[id]==1: self.states[id]=2
            else:                  self.states[id]=1
        #if id>=0: self.boxes.remove(self.boxes[id])                   #удалить при повторном нажатии
        #else:     self.boxes.append(QRect(pt.x(), pt.y(), 1000, 40)); #добваить
        self.repaint()
        return

    def pointInBoxes(self, pt, boxes):
        #нахождение точки внутри списка
        #возвращает номер прямоугольника или -1
        for i in range(len(boxes)):
            if boxes[i].contains(pt): return i
        return -1

    def pointInBoxesIds(self, pt, boxes, ids):
        for i in range(len(ids)):
            if boxes[ids[i]].contains(pt): return i #номер прямоугольника в списке, а не глобально
        return -1

    def setBoxes(self, boxes, ids, coords): #установка областей букв (текст и разметка сбрасывается)
        self.iboxes=[]
        self.iline=-1
        self.coords = coords
        self.boxes  = boxes
        self.ids    = ids
        self.lines  = [Markup.MuParser.uniteBoxes(boxes, idline) for idline in ids] #прямоугольники линий
        nlines = len(self.lines)
        self.states = [self.STATE_UNKNOWN] * nlines #установить начальные состояния каждой линии

        self.mu = [[]]*nlines #сбросить разметки для линий
        self.text = [""]*nlines #сбросить соответствующий текст для линий
        self.setTextLines(0, self.text) #создать пустую разметку
        self.repaint()

    def setMarkup(self, boxes, ids, mu, text, coords): #установка разметки (все сбрасывается)
        self.iboxes=[]
        self.iline=-1
        self.boxes = boxes
        self.ids = ids
        self.lines  = [Markup.MuParser.uniteBoxes(boxes, idline) for idline in ids] #прямоугольники линий
        nlines = len(self.lines)
        self.states = [self.STATE_UNKNOWN] * nlines #установить начальные состояния каждой линии

        self.mu = mu        #готовая разметка
        self.text = text    #текст
        self.coords = coords
        self.repaint()

    def currectLine(self):  return self.iline

    def currentBox(self):
        if len(self.iboxes): return self.iboxes[0]
        return -1

    def lineCount(self):    return len(self.ids)

    def selectedBoxes(self): return self.iboxes

    def textLine(self, iline): return self.text[iline]

    def muLine(self, iline): return self.mu[iline]

    def muValue(self, iline, imu): return self.mu[iline][imu]

    def muText(self, iline, imu):
        muline = self.mu[iline]
        bpos, tpos = Markup.MuParser.muPosByMu(muline,imu)
        return self.text[iline][tpos:(tpos+muline[imu][1])]

    def changeTextLine(self, iline, text):
        self.text[iline]=text #просто обновить текст без изменения маркировки
        self.repaint()

    def updateTextLine(self, iline, text):
        if iline < 0 or iline >= len(self.ids): return
        #Обновление строки, так чтобы маркировка в начале строки не изменялась, если в этом нет необходимости
        s0,s1 = self.text[iline], text
        if (s0==s1): return #если текст не поменялся, разметка не обновляется
        nc=-1 #позиция предыдущих совпавших символов
        for i in range(min(len(s0),len(s1))):
            if (ord(s0[i]) <= 32)!=(ord(s1[i]) <= 32): break; #если схема разбивки меняется, указать с какой позиции
            nc+=1
        self.text[iline]=text   #новый текст
        mu=self.mu[iline]
        imu = Markup.MuParser.muByCharPos(mu,nc) #позиция без отличий
        mu2 = Markup.MuParser.andParseTailDefault(mu,imu,len(self.ids[iline]),text)
        self.mu[iline]=mu2
        self.repaint()

    def updateTextLines(self, istart, text):#UPD обновление строк текста, начиная с заданной линии istart
        #text - [str,...] набор строк
        for i in range(len(text)):
            self.updateTextLine(istart+i, text[i])

    def skipBoxLine(self,iline):
        if iline < 0 or iline >= len(self.text): return
        self.text.insert(iline,"")
        self.updateDefaultMu(iline) #обновить всю разметку, начиная с текущей линии
        self.repaint()

    def skipTextLine(self,iline):
        if iline<0 or iline>=len(self.text): return
        del self.text[iline]
        if len(self.text) < len(self.ids): self.text.append("")
        self.updateDefaultMu(iline) #обновить всю разметку, начиная с текущей линии
        self.repaint()

    def updateDefaultMu(self, istart):
        for i in range(istart,len(self.ids)):
            self.mu[i] = Markup.MuParser.parseDefault(len(self.ids[i]), self.text[i])
        return

    def setTextLine(self, iline, text): #заменить текст и разметку
        if iline<0 or iline>=len(self.ids): return
        self.text[iline] = text #если номер строки выходит за границы строка добавляется
        self.mu[iline] = Markup.MuParser.parseDefault(len(self.ids[iline]), text)
        self.repaint()

    def setTextLines(self, istart, text):#добавление текста, начиная с заданной линии istart
        #text - [str,...] набор строк
        for i in range(len(text)):
            self.setTextLine(istart+i, text[i])
        print(self.mu)
        print(self.text)

    def currentMu(self):
        if self.iline < 0: return -1
        if len(self.iboxes)<=0: return -1
        return Markup.MuParser.muByBoxPos(self.mu[self.iline], self.iboxes[0])

    def changeCurMu(self, nbox, nchar): #изменение текущей области
        print(self.iboxes)
        if self.iline < 0: return
        if len(self.iboxes) <= 0: return
        print("changeCurMu")
        imu = Markup.MuParser.muByBoxPos(self.mu[self.iline], self.iboxes[0])
        print(self.iline, imu, nbox, nchar)
        mu = self.mu[self.iline]
        mu2 = Markup.MuParser.change(mu, imu, nbox, nchar)
        mu2 = Markup.MuParser.andParseTailDefault(mu2,imu,len(self.ids[self.iline]),self.text[self.iline])
        self.mu[self.iline] = mu2
        self.repaint()

    def splitCurMu(self, nbox, nchar): #отделение первых nbox и nchar от текущей области
        if self.iline < 0: return
        if len(self.iboxes)<=0: return
        imu = Markup.MuParser.muByBoxPos(self.mu[self.iline], self.iboxes[0])
        self.mu[self.iline] = Markup.MuParser.split(self.mu[self.iline], imu, nbox, nchar)
        self.repaint()

    def uniteCurMu(self, nmu): #число объединяемых областей
        if self.iline < 0 or nmu<1: return
        if len(self.iboxes) <= 0: return
        imu = Markup.MuParser.muByBoxPos(self.mu[self.iline], self.iboxes[0])
        self.mu[self.iline] = Markup.MuParser.unite(self.mu[self.iline], imu, nmu)
        self.repaint()

    def moveBoxesToLine(self, iboxes, linefrom, lineto):
        #сбросить выделение
        self.iline = -1
        self.iboxes = []
        if linefrom<0 or lineto<0 or linefrom>=self.lineCount() or lineto>self.lineCount() or len(iboxes)<=0:
            return
        #перенести прямоугольники и сбросить
        sel = [self.ids[linefrom][i] for i in iboxes] #номера выделенных идентификаторов
        self.ids[lineto].extend(sel)   #скопировать необходимые
        self.ids[lineto]    = sorted(self.ids[lineto], key=lambda k: self.boxes[k].x())  # отсортировать результат по порядку
        self.lines[lineto]  = Markup.MuParser.uniteBoxes(self.boxes, self.ids[lineto])
        self.mu[lineto]     = Markup.MuParser.parseDefault(len(self.ids[lineto]), self.text[lineto])
        self.states[lineto] = self.STATE_UNKNOWN
        #удалить из предыдущей линии
        self.excludeBoxes(linefrom,iboxes)

    def insertNewLine(self, lineto):
        self.iline = -1
        self.iboxes = []
        if lineto<0 or lineto>self.lineCount(): return
        #вставить новую строку
        self.ids.insert(lineto,[])
        self.text.insert(lineto, "")
        self.mu.insert(lineto, Markup.MuParser.parseDefault(len(self.ids[lineto]), self.text[lineto]))
        self.lines.insert(lineto,QRect())
        self.states.insert(lineto,self.STATE_UNKNOWN)
        self.repaint()

    def removeLine(self, iline):
        if iline<0 or iline>=len(self.lines): return
        self.iline = -1
        self.iboxes = []

        del self.lines[iline]
        del self.ids[iline]
        del self.mu[iline]
        del self.text[iline]
        del self.states[iline]

        self.repaint()

    def excludeBoxes(self, iline, iboxes): #исключить
        #найти и исключить
        curline=self.iline #UPD
        self.iline = -1
        self.iboxes = []
        line = self.ids[iline]
        self.ids[iline] = [line[i] for i in range(len(line)) if i not in iboxes]
        if len(self.ids[iline]):
            self.lines[iline]  = Markup.MuParser.uniteBoxes(self.boxes, self.ids[iline])
            self.mu[iline]     = Markup.MuParser.parseDefault(len(self.ids[iline]), self.text[iline])
            self.states[iline] = self.STATE_UNKNOWN
        else:
            self.removeLine(iline)
        if curline<self.lineCount(): self.activateLine(curline) #UPD
        self.repaint()

    def swapBoxes(self,iline, ibox, ibox2):
        w = len(self.ids[iline])
        if ibox<0 or ibox2<0 or ibox>=w or ibox2>=w: return
        self.ids[iline][ibox], self.ids[iline][ibox2] = self.ids[iline][ibox2], self.ids[iline][ibox]
        self.repaint()
