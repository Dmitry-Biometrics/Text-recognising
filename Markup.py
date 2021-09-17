# coding=utf-8
import math
import copy
import bisect #модуль для работы с упорядоченными списками
import operator
import cv2
import numpy as np
import matplotlib
import matplotlib.image
import matplotlib.pyplot as plt
import skimage
import skimage.morphology
import base64
from CoordsObj import Coords

from PyQt5.QtCore import *
import HpSamples

def replacechars(text, what, than=' '): #замена отдельных символов строки на другой
    s=[]
    for i in range(len(text)):
        if text[i] in what: s.append(' ')
        else:               s.append(text[i])
    return ''.join(s)


def readNextBoxLine(f):
    s = replacechars(next(f),"[](),",' ').split() #остались одни цифры
    n = len(s)
    if n<1 or ((n-1) % 4)!=0:
        return None
    nbox = int(s[0])
    boxes=[]
    for i in range(nbox): #ВНИМАНИЕ! только целые числа
        boxes.append(QRect(int(s[1+i*4+0]),int(s[1+i*4+1]),int(s[1+i*4+2]),int(s[1+i*4+3]))) #x,y,dx,dy
    return boxes


def readNextLetter(f):
    s = replacechars(next(f), "(),", ' ').split()
    id_bbox = int(s[0])
    min_x = int(s[1])
    min_y = int(s[2])
    width = int(s[3])
    height = int(s[4])
    N = int(s[5])
    pc = []
    for i in range(N):
        pc.append((int(s[6 + i*2 + 0]), int(s[6 + i*2 + 1])))
    letter = Coords(min_x, min_y, width, height, pc, id_bbox, N)
    return letter

def loadBoxLines(name):
    bbox=[]
    lines=[]
    try:
        f=open(name,"r")
        nlines = int(replacechars(next(f),"[]",' '))
        if nlines<=0: return None
        num=0 #число уже считанных прямоугольников
        for i in range(nlines):
            boxes = readNextBoxLine(f)
            bbox.extend(boxes)
            lines.append([num+k for k in range(len(boxes))])
            num+=len(boxes)
        f.close()
        print("bbox load from file", name, "nlines=",nlines, "nboxes=", num)
        return bbox, lines
    except:
        print("error read",name)
        return bbox, lines


def saveBoxLines(name, bbox, lines):
    # сохранение прямоугольников
    # сохранение строк прямоугольников       [nboxes][[nline][x,y,dx,dy],...]
    try:
        f=open(name,"w")
        f.write("{0}\n".format(len(lines))) #число линий
        for line in lines:
            f.write("{0},".format(len(line))) #число прямоугольников
            for i in line:
                b = bbox[i]
                f.write("({0},{1},{2},{3}),".format(b.x(),b.y(),b.width(),b.height()))
            f.write("\n")
        f.close()
        return True
    except:
        return False


def loadText(name):
    try:
        f=open(name,"r")
        #text = f.read().splitlines() #прочитать и разделить на линии (\n - будут удалены)
        text = [line.rstrip('\n') for line in f]  # считать nlines и удалить последние \n
        f.close()
        return text
    except:
        print("error read",name)
        return []


def saveText(name, text):
    try:
        f = open(name, "w")
        # сохранить текст, записав даже пустые строки
        # (если строки пустые, их нужно дополнить)
        # (если строки не имеют \n, их нужно дополнить)
        for line in text:
            if not line: f.write('\n')
            else:        f.write(line+'\n') #добавить в конец
        f.close()
        return
    except:
        return

class MuParser:

    def __init__(self):
        return

    @staticmethod
    def parseDefault(nbox, text):
        #нахождение разметки одной линии
        #разметка - пары (b,c) где b - число прямоугольников, c - число соответствующих символов
        mu=[]
        b, t = 0, 0
        ntext = len(text)
        while t<ntext and b<nbox:
            if ord(text[t])<=32:
                mu.append([0, 1]) #пропустить непечатный символ
            else:
                mu.append([1, 1]) #связать символ и область
                b=b+1
            t=t+1
        if t<ntext: mu.append([0, ntext-t])   #оставшиеся символы
        if b<nbox:  mu.extend([[1, 0]]*(nbox-b))#оставшиеся прямоугольники
        return mu

    @staticmethod
    def muByBoxPos(muline, ibox): #нахождение текущей области по номеру прямоугольника
        if ibox<0: return -1
        pos = 0
        #print(mu)
        for i in range(len(muline)):
            if ibox<(pos+muline[i][0]): return i
            else: pos += muline[i][0]
        return -1

    @staticmethod
    def muPosByMu(muline,imu): #нахождение смещения box и text для заданного imu
        if imu<0: return -1,-1
        bpos, tpos = 0, 0
        for i in range(imu):
            bpos += muline[i][0]
            tpos += muline[i][1]
        return bpos,tpos


    @staticmethod
    def muByCharPos(muline, ichar): #нахождение текущей области по номеру символа
        if ichar<0: return -1
        pos = 0
        for i in range(len(muline)):
            if ichar<(pos+muline[i][1]): return i
            else: pos += muline[i][1]
        return -1

    @staticmethod
    def change(mu, imu, nbox, nchar):
        print("change", imu, nbox, nchar)
        #изменяет текущий прямоугольник на заданное значение
        #(1,1) change(1,2) -> (1,2)
        if imu<0 or nbox<0 or nchar<0: return mu
        mu[imu]=[nbox, nchar]
        return mu

    @staticmethod
    def andParseTailDefault(mu,imu,nbox,text): #обработка конца
        abox,achar = 0, 0
        for i in range(imu+1): #подсчитать число использованных символов
            abox  += mu[i][0]
            achar += mu[i][1]
        ntailbox  = nbox-abox       #осталось областей
        ntailchar = len(text)-achar #осталось символов
        #вырезать начало
        mu2 = mu[:(imu+1)]
        if ntailbox<=0: ntailbox=0
        if ntailchar<=0: tailtext=""
        else:            tailtext=text[achar:] #до конца
        #обработать до конца
        mu2.extend(MuParser.parseDefault(ntailbox,tailtext))
        return mu2

    @staticmethod
    def split(mu, imu, nbox, nchar):
        #отделяет (nbox,nch) от текущего
        #(2,1) split (1,1) -> (1,1)(1,0)
        #(1,1) split (1,0) -> (1,0)(0,1)
        #(2,2) split (2,2) -> (2,2) не добавляется (0,0)
        if imu < 0: return mu
        cbox, cchar = mu[imu] #предыдущий
        if (cbox>=nbox and cchar>nchar) or (cbox>nbox and cchar>=nchar): #отделяемые параметры не больше текущих
            mu[imu] = [cbox-nbox, cchar-nchar]
            mu.insert(imu, [nbox, nchar])
        return mu

    @staticmethod
    def unite(mu, imu, nmu):
        #объединяет до nmu областей без присоединения текста
        #(1,1)(2,1) unite(2) -> (3,2)
        #(1,0)(0,1) unite(2) -> (1,1)
        if imu < 0: return mu
        nbox, nchar = 0, 0
        for i in range(imu, imu+nmu): #перебрать все объединяемые
            nbox += mu[i][0]; nchar += mu[i][1]
        mu2 = mu[:imu] + mu[imu+nmu:]
        mu2.insert(imu, [nbox, nchar]) #такая позиция есть точно
        return mu2

    @staticmethod
    def uniteBoxes(boxes, ids):
        n = len(ids)
        if n<=0:    return QRect()
        elif n==1:  return boxes[ids[0]]
        u = QRect()
        for i in ids: u = u.united(boxes[i])
        return u

    @staticmethod
    def uniteExtBoxes(letters, ids):
        n = len(ids)
        if n<=0: return QRect()
        elif n==1:
            letter = letters[ids[0]]
            rect = QRect(letter.min_x, letter.min_y, letter.width, letter.height)
            return rect
        u = QRect()
        for i in ids:
            letter = letters[i]
            rect = QRect(letter.min_x, letter.min_y, letter.width, letter.height)
            u = u.united(rect)
        return u

class Markup:
    #npage = [] #число boxes на одной страницу (чтобы определять соответствие номеров boxes и номеров страниц)
    #pics = [] #страницы (сами изображения с буквами)

    def __init__(self):
        self.boxes = []  # [QRect,...] список прямоугольных областей, содержащих текст
        self.ids   = []  # [[int,...],...]список номеров, соответствующих строкам текста
        self.text  = []  # [string,...] строки текста
        self.mu    = []  # разметка [[(nb,nc),..],] - сколько прямоугольников ids соотв. скольки символам текста
        self.coords = []

    def setboxes(self,boxes,ids):
        self.boxes  = boxes
        self.ids    = ids
        nlines = len(self.ids)
        self.mu = [[]]*nlines #сбросить разметки для линий
        self.text = [""]*nlines #сбросить соответствующий текст для линий
        self.settextlines(0, self.text) #создать пустую разметку

    def setmarkup(self, boxes, ids, mu, text, coords):
        self.boxes, self.ids, self.text, self.mu, self.coords = boxes, ids, text, mu, coords
        if text is None: self.text = [""]*len(self.ids)
        if mu is None:
            self.mu = [[]] * len(self.ids)
            self.settextlines(0, self.text) #обновить разметку

    def extend(self,markup):
        markup = Markup()
        nbox = len(self.boxes)
        self.boxes.extend(markup.boxes)

        ncur   = len(self.ids)      #текущее число линий
        nlines = len(markup.ids)    #число добавляемых линий
        ids2 = [v.copy() for v in markup.ids] #полная копия номеров
        for j in range(nlines): ids2[j] = [v+nbox for v in ids2[j]] #сместить все номера на число уже имеющихся bbox
        self.ids.extend(ids2)

        if markup.text is None or (len(markup.text) != nlines): self.text.extend([""] * nlines)
        else:                                                   self.text.extend(markup.text)

        if markup.mu is None or (len(markup.mu)!=nlines):
            self.mu.extend([[]] * nlines)
            self.settextlines(ncur, self.text) #разметить автоматически
        else:
            self.mu.extend(markup.mu) #уже загружена

        if self.coords is None:         pass #нельзя корректно добавить
        else:
            if markup.coords is None:   self.coords = None #нельзя корректно добавить
            else:                       self.coords.extend(markup.coords) #добавление

    def updatetextline(self,iline,text):
        self.text[iline] = text  # просто обновить текст без изменения маркировки

    def settextline(self,iline, text): # заменить текст и разметку
        if iline < 0 or iline >= len(self.ids): return
        self.text[iline] = text  # если номер строки выходит за границы строка добавляется
        self.mu[iline] = MuParser.parseDefault(len(self.ids[iline]), text)

    def settextlines(self,istart,text): #замена текста на линиях и обновление разметки
        for i in range(len(text)):
            self.settextline(istart+i, text[i])

    def save(self, name, jpg=None): #сохранение разметки
        #сохранение прямоугольников и строк прямоугольников         [nboxes][[nline][x,y,dx,dy],...]
        #сохранение сохранение разметки                             [nlines]{[n][[nb,nc,prob,flags],..]}
        #сохранение строк текста                                    [string,...]
        #сохранение jpg:bytes изображения (если есть)
        bbox, ids, text, mu, coords = self.boxes, self.ids, self.text, self.mu, self.coords
        print(mu)
        print(text)
        try:
            f = open(name, "w")
            #сохранить прямоугольники
            print('kolvo bbox', len(bbox))
            f.write("{0}\n".format(len(ids)))  # число линий прямоугольников
            for line in ids:
                f.write("{0},".format(len(line)))  # число прямоугольников
                for i in line:
                    b = bbox[i]
                    f.write("({0},{1},{2},{3}),".format(b.x(), b.y(), b.width(), b.height()))
                f.write("\n")

            #сохранить разметку
            f.write("{0}\n".format(len(self.mu))) #число строк разметки
            for line in self.mu:
                f.write("{0},".format(len(line))) #число элементов на лизии
                for m in line:
                    nb, nc = m
                    f.write("({0},{1},{2},{3}),".format(nb, nc, 255, 0))
                f.write("\n")

            #сохранить текст, записав даже пустые строки
            # (если строки пустые, их нужно дополнить)
            # (если строки не имеют \n, их нужно дополнить)
            f.write("{0}\n".format(len(text))) #число строк текста
            for line in text:
                if not line:    f.write('\n')
                else:           f.write(line+'\n')


            # сохранить координаты, только у оставшихся bbox
            count=0                             #UPD
            if (coords is None) or (0==len(coords)):
                f.write("0\n")  # UPD
            else:
                for line in ids: count+=len(line)   #UPD
                f.write("{0}\n".format(count))      #UPD
                for line in ids:
                    for i in line:
                        letter = coords[i]
                        f.write("{0} ".format(count))  # id bbox'a
                        count += 1
                        f.write("({0},{1},{2},{3}) ".format(letter.min_x, letter.min_y, letter.width,
                                                            letter.height))  # число элементов на лизии
                        f.write("{0} ".format(letter.N))
                        for coord in letter.pc:
                            shift, color = coord
                            f.write("({0},{1}),".format(shift, color))
                        f.write("\n")

            #сохранить jpg изображение
            if jpg:
                print("read jpg",len(jpg))
                f.write(str(len(jpg))); f.write("\n")
                s = base64.encodebytes(jpg).decode("utf-8")
                f.write(s); f.write("\n")
            else:
                f.write(str(0))
                f.write("\n")


            f.close()
            return True
        except:
            return False

    def load(self, name): #загрузка разметки
        bbox, ids, mu, text, coords = [], [], [], [], []
        try:
            f = open(name, "r")
            nlines = int(next(f))
            if nlines <= 0: return None
            #считать линии областей символов
            num = 0  # число уже считанных прямоугольников
            for i in range(nlines):
                boxes = readNextBoxLine(f)
                bbox.extend(boxes)
                ids.append([num + k for k in range(len(boxes))])
                num += len(boxes)
            #считать линии областей разметки
            nlines = int(next(f))
            if nlines <= 0: return None
            for i in range(nlines):
                rec4 = readNextBoxLine(f) #тоже по 4 символа (целых, но меньшей разрядности)
                mu.append([[r.x(),r.y()] for r in rec4])
            #считать линии текста
            nlines = int(next(f)) #число строк текста
            if nlines <= 0: return None
            for i in range(nlines):
                text.append(next(f).rstrip('\n')) #считать nlines и удалить последние \n
            print(len(text))
            print(text)

            # попробовать считать координаты букв
            nletters = next(f)
            if int(nletters) == num:
                for i in range(int(nletters)):
                    letter = readNextLetter(f)
                    coords.append(letter)
                line = f.readline()
            else:
                line = nletters
                coords = None

            #попробовать считать изображение
            jpg = []
            if len(line) and int(line) and line>0:
                s = f.readlines()
                s = "".join(s)
                b = s.encode("utf-8")
                jpg = base64.decodebytes(b)
            f.close()
        except:
            print("error read", name)
        self.boxes, self.ids, self.mu, self.text, self.coords = bbox, ids, mu, text, coords
        return jpg

    def synth_letter(self, im, letter):
        for i in letter.pc:
            y = int(i[0]/letter.width)
            x = int(i[0]%letter.width)
            im[y, x] = i[1]
        return im

    def copymask_letter(self, im, letter, sx, sy):
        for i in letter.pc:
            y = int(i[0]/letter.width)
            x = int(i[0]%letter.width)
            im[sy+y, sx+x] = i[1]

    def extract(self, im):  # извлечение меток из изображения (без imoverlay)
        # для каждой записи mu определяется общая область изображения, полученная пересечением прямоугольников
        # после этого выполнятся копирование изображения в отдельную матрицу np.array для каждого прямоугольника mu
        # результату ставится в соответствие текст
        samples = HpSamples.HpSamples()
        adr = []  # список адресов (iline, im) для каждого найденного изображения
        for iline in range(len(self.mu)):
            ib, ic = 0, 0  # позиция от начала строки
            imu = 0
            for nb, nc in self.mu[iline]:  # по всем элементам линии
                if nb > 0 and nc > 0:  # есть bbox текст и
                    if self.coords: big_ex = MuParser.uniteExtBoxes(self.coords, self.ids[iline][ib:(ib + nb)])  # ограничивающий прямоугольник
                    else:           big_ex = MuParser.uniteBoxes(self.boxes, self.ids[iline][ib:(ib + nb)])
                    im2 = np.ones([big_ex.height(), big_ex.width()], 'u1') * 255
                    nlen = len(self.ids[iline])
                    if (ib + nb) > nlen: nb = nlen - ib  # если выходит за диапазон, нужно сократить число прямоугольников или пропустить или проверять
                    for i in range(nb):  # скопировать область изображения в другую область
                        pos = self.ids[iline][ib + i]
                        # координаты исходного прямоугольника
                        if self.coords:
                            letter = self.coords[pos]
                            sx = letter.min_x - big_ex.x()
                            sy = letter.min_y - big_ex.y()
                            self.copymask_letter(im2,letter,sx,sy)
                        else:
                            b = self.boxes[pos]
                            a = QRect(b.x() - big_ex.x(), b.y() - big_ex.y(), b.width(), b.height())
                            im2[a.y():(a.y() + a.height()), a.x():(a.x() + a.width())] = \
                                im[b.y():(b.y() + b.height()), b.x():(b.x() + b.width())]

                    label = self.text[iline][ic:(ic + nc)]  # соответствующий текст

                    samples.append(im2, label)  # сформированное изображение символа(ов)
                    adr.append((iline, imu))
                imu += 1
                ib += nb
                ic += nc
        return samples, adr

    def mupos(self, iline, ibox):#значение mu для заданной позиции
        if iline < 0 or ibox < 0: return -1
        return MuParser.muByBoxPos(self.mu[iline], ibox)

    def changeMu(self, iline, ibox, nbox, nchar): #изменение текущей области
        if iline < 0: return
        imu = MuParser.muByBoxPos(self.mu[iline], ibox)
        mu = self.mu[iline]
        mu2 = MuParser.change(mu, imu, nbox, nchar)
        mu2 = MuParser.andParseTailDefault(mu2,imu,len(self.ids[iline]),self.text[iline])
        self.mu[iline] = mu2

    def splitMu(self, iline, ibox, nbox, nchar): #отделение первых nbox и nchar от текущей области
        if iline < 0: return
        imu = MuParser.muByBoxPos(self.mu[iline], ibox)
        self.mu[iline] = MuParser.split(self.mu[iline], imu, nbox, nchar)

    def extractUnitedImage(self,ids): #извлечение одного объединенного изображения (без метки)
        if ids is None: return None
        if self.coords is None: return None #БЕЗ coords не подерживается
        big_ex = MuParser.uniteExtBoxes(self.coords, ids)  # ограничивающий прямоугольник
        im2 = np.ones([big_ex.height(), big_ex.width()], 'u1') * 255
        for id in ids:  # скопировать область изображения в другую область
            letter = self.coords[id]
            sx = letter.min_x - big_ex.x()
            sy = letter.min_y - big_ex.y()
            self.copymask_letter(im2, letter, sx, sy)
        return im2

    def lineDepthIds(self,line,level): #построение списка вариантов объединения сегментов глубиной не более level
        #для недопустимых гипотез возвращается None
        #level - максимальное число объединяемых элементов
        #line  - номер линии
        #возвращает: список объединяемых наборов сегментов для гипотез глубиной до level
        #число элементов ровно len(self.ids[line])*level
        comb = []
        ids = self.ids[line]    #номера элементов на линии
        nlen = len(ids)         #число сегментов линии
        for ib in range(nlen):
            for nb in range(1,1+level): #взять до nb сегментов
                if (ib+nb)>nlen: comb.append(None) #недопустимые комбинации внести как None (либо пустой матрицей)
                else:            comb.append(ids[ib:(ib + nb)])
        return comb

    def lineMarkedIds(self,line):
        #построение списка объединения в изображения по разметке и соотв. меток (если метки установлены)
        #возвращает: combs=[[],[],[],[],..] , lbls=['','','','','','',''], muids=[..]
        combs  = []
        labels = []
        muids  = []

        ids  = self.ids[line]
        text = self.text[line]
        nlen = len(ids)

        ib, ic = 0, 0  # позиция от начала строки
        for imu,m in enumerate(self.mu[line]):  # по всем элементам линии
            nb, nc = m
            if nb > 0:
                if (ib + nb) > nlen: nb = nlen - ib  # если выходит за диапазон, сократить число прямоугольников
                combs.append(ids[ib:(ib + nb)])
                muids.append(imu)
                if nc > 0:  labels.append(text[ic:(ic + nc)])   # соответствующий текст
                else:       labels.append('')                   #немаркированный элемент
            ib += nb
            ic += nc
        return combs, labels, muids

    def labeledCombs(self): #получение маркированного списка комбинаций
        # combs - номера bbox для каждой метки
        # labels - метка класса
        # poss - адрес (строка,столбец)
        if self.coords is None: return
        combs, labels, poss = [], [], []
        for i in range(len(self.mu)):
            co, lb, imu = self.lineMarkedIds(i)
            combs.extend(co)
            labels.extend(lb)
            poss.extend([(i,v) for v in imu]) #адрес элемента
        return combs, labels, poss
