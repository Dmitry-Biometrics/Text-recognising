import numpy as np
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pickle
import re
import cv2
import os
import emnist

import scipy.ndimage.morphology

import skimage
import skimage.morphology

#Пример изображения рукопечатного символа
#class HpSample:
#
#    def __init__(self, img, label, fid = -1, state=0):
#        self.img   = img    #изображение
#        self.label = label  #метка
#        self.fid   = fid    #ссылка на файл источник
#        self.state = state  #состояние (выделено, маркировано)

#Класс образов рукопечатных символов
class HpSamples:

    MODE_SCALE=0
    MODE_CENTER=1
    MODE_INSCRIBE=2

    def __init__(self):
        self.imgs   = [] #изображения np.array(,'u1'), оттенки серого
        self.labels = [] #метки
        self.fids   = [] #номера источников данных (файлов) или -1

    def __len__(self):
        return len(self.imgs)

    def findInSet(self, label_set):
        """Поиск элементов, промаркированных из множества label_set"""
        return [i for i in range(len(self.labels)) if self.labels[i] in label_set]

    def findSingle(self): #найти одиночные символы
        return [i for i in range(len(self.labels)) if len(self.labels[i])==1]

    def findLonger(self, n): #найти символы длинее n
        return [i for i in range(len(self.labels)) if len(self.labels[i])>n]

    def findShorter(self, n): #найти символы короче n
        return [i for i in range(len(self.labels)) if len(self.labels[i])<n]

    def findByRegEx(self, expr):
        pattern = re.compile(expr)  # обрабатывать исключения
        return [i for i in range(len(self.labels)) if pattern.match(self.labels[i])]

    def replaceLabels(self, ids, label): #замена меток
        for i in ids:
            self.labels[i] = label

    def replaceLabelsByDict(self, dic): #заменить по словарю {старое_значение:новое_значение,...}
        self.labels = [dic.get(v, v) for v in self.labels]

    def removeByIds(self, ids): #удалить по номерам
        what = frozenset(ids)
        n = len(self.imgs)
        print(len(ids))
        print(n, len(self.labels))
        self.imgs = [self.imgs[i] for i in range(n) if i not in what]
        self.labels = [self.labels[i] for i in range(n) if i not in what]
        self.fids   = [self.fids[i] for i in range(n) if i not in what]
        print(len(self.imgs), len(self.labels))

    def extend(self,hp):
        self.imgs.extend(hp.imgs)
        self.labels.extend(hp.labels)
        self.fids.extend(hp.fids)

    def append(self, img, label, fids=-1):
        self.imgs.append(img)
        self.labels.append(label)
        self.fids.append(fids)

    def slice(self, ids):
        """Формирование подмножества элементов по списку индексов
        :param ids: список выбранных номеров изображений
        :return: HpSamples
        """
        what = frozenset(ids)
        n = len(self.imgs)
        s = HpSamples()
        s.imgs   = [self.imgs[i] for i in range(n) if i in what]
        s.labels = [self.labels[i] for i in range(n) if i in what]
        s.fids   = [self.fids[i] for i in range(n) if i in what]
        return s


    def makeimage(self, start, count): #сформировать изображение из count элементов, начиная с позиции start
        xlen, ymax = 0, 0
        for i in range(count): #найти габариты результирующего изображения
            dx = self.imgs[start+i].shape[1] #x
            dy = self.imgs[start+i].shape[0] #y
            if dy>ymax: ymax=dy
            xlen+=dx
        #создать массив и скопировать в него
        im2 = np.ones([ymax,xlen],'u1')*255
        xpos = 0
        for i in range(count):
            src = self.imgs[start + i]
            im2[:src.shape[0],xpos:(xpos+src.shape[1])] = src
            xpos += src.shape[1]
        return im2 #результирующее изображение

    # int.from_bytes(some_bytes)

    def save(self, name):
        try:
            f = open(name, "wb")
            n = len(self.imgs) #считаем, что dtype=u1
            f.write(n.to_bytes(4,byteorder='big'))
            for i in range(n):
                label = self.labels[i].encode('utf-8') #преобразовать в bytes
                f.write(len(label).to_bytes(1,byteorder='big'))
                f.write(label)

                a = self.imgs[i]
                dy, dx = a.shape
                f.write(dx.to_bytes(4,byteorder='big'))
                f.write(dy.to_bytes(4,byteorder='big'))
                f.write(a.tobytes()) #np.array
            f.close()
            return True
        except:
            print("exception")
            return False

    #name   - имя файла smp
    #fileid - номер файла (условный, исп. внешними приложениями)
    #clearall - сбросить все примеры
    def loadFromSmp(self, name, fileid, clearall=False):
        if clearall: #удалить имеющиеся
            self.imgs = []      #изображения
            self.labels = []    #метки
            self.fids = []      #номера файлов
        try:
            f = open(name,"rb")
            n = int.from_bytes(f.read(4),byteorder='big') #число примеров
            for i in range(n):
                nlabel = int.from_bytes(f.read(1),byteorder='big')  #длина метки
                label = f.read(nlabel).decode('utf-8')              #метка

                dx, dy = int.from_bytes(f.read(4),byteorder='big'), int.from_bytes(f.read(4),byteorder='big')
                a = np.frombuffer(f.read(dx*dy),dtype='u1')
                img = a.reshape([dy, dx])
                self.imgs.append(img)
                self.labels.append(label)
                self.fids.append(fileid)
            f.close()
            return True
        except:
            print("exception")
            return False

    def imgsrects(self, ids):
        #возвращает ограничивающие прямоугольники изображений
        return [QRect(0, 0, self.imgs[i].shape[1],  self.imgs[i].shape[0]) for i in ids]

    def maxbounds(self, boxes):
        # рассчитать максимальный ограничивающий прямоугольник среди выбранных изображений
        maxx, maxy = 0, 0
        for r in boxes:
            dy, dx = r.height(), r.width()
            if dy > maxy: maxy = dy
            if dx > maxx: maxx = dx
        return QRect(0, 0, maxx, maxy)

    @staticmethod
    def nparray2qimage(im):
        """ Преобразование nparray в qimage с учетом выавнивания"""
        h,w = im.shape
        #if w % 4:
        #    bpl = w+(4-w % 4)
        #    aligned = np.empty([h,bpl],'u1')
        #    aligned[:,0:w]=im[:,0:w]
        #    return QImage(aligned, w, h, 1*bpl, QImage.Format_Grayscale8)
        #else:
        return QImage(im, w, h, 1 * w, QImage.Format_Grayscale8)

    @staticmethod
    def qimage2nparray(img):
        """  Converts a QImage into an opencv MAT format """
        img = img.convertToFormat(QImage.Format_Grayscale8) # если требуется
        w,h = img.width(), img.height()
        bpl = img.bytesPerLine()
        if bpl == w: # данные выровнены
            p = img.bits().asarray(w*h*1)  # не constBits!
            return np.array(p, 'u1').reshape(h, w)
        else: #данные не выровнены
            p = img.bits().asarray(bpl * h * 1)  # не constBits!
            a = np.array(p, 'u1').reshape(h, bpl)
            b = a[0:h,0:w]
            #print(b.shape)
            return b # убрать невыровненные байты


    def rescale(self, mode, groups, gkeys, bound=None):
        #Изменение масштабов изображений по заданному прваилу
        # mode:int {0 - MODE_SCALE,1 - MODE_CENTER,2 - MODE_INSCRIBE}
        size = len(self.imgs)
        samples = HpSamples()
        samples.imgs = [None]*size  # заполнить пустыми объектами
        samples.labels = self.labels
        samples.fids = self.fids
        p = QPainter()
        for k in gkeys:   # для каждой линии
            ids = groups[k]      # список номеров примеров в группе
            if bound is None or bound.isEmpty():
                boxes = self.imgsrects(ids)  # получить исходные размеры изображений
                bound = self.maxbounds(boxes)   # максимальные размеры в группе
            for index in ids:
                im = self.imgs[index]  # собственно изображение в виде np.array
                h, w = im.shape
                src = QImage(im, w, h, 1 * w, QImage.Format_Grayscale8)
                r = bound
                # центрировать изображение в регионе
                need = False
                if mode == self.MODE_CENTER:
                    if w>r.width() or h>r.height(): need = True #вписать, если больше области
                    else:
                        sx, sy = int((r.width()- w)/2), int((r.height()- h) / 2)
                        r = QRect(r.x()+sx, r.y()+sy, w, h)
                if mode == self.MODE_INSCRIBE or need:
                    rx, ry = w/r.width(), h/r.height() # отношение
                    if rx>ry:  # заполнение по x
                        h2 = int(h/rx)
                        sy = int((r.height() - h2) / 2)
                        r = QRect(r.x(), r.y()+sy, r.width(), h2)
                    else:  # заполнение по y
                        w2 = int(w/ry)
                        sx = int((r.width() - w2) / 2)
                        r = QRect(r.x()+sx, r.y(), w2, r.height())
                dst = QImage(bound.width(), bound.height(), QImage.Format_Grayscale8)  # результирующее изображение
                p.begin(dst)
                p.setPen(QPen(QColor(255, 255, 255)))
                p.setBrush(QBrush(QColor(255, 255, 255)))
                p.drawRect(QRect(QPoint(0, 0), dst.size()))
                p.drawImage(r, src, QRect(0, 0, w, h))
                p.end()
                samples.imgs[index] = HpSamples.qimage2nparray(dst)  # преобразовать к nparray
        return samples

    def groupByLabel(self):  #формирование словаря имен групп (значение ключа - список номеров изображений)
        groups = dict()
        for i in range(len(self.labels)):
            name = self.labels[i]
            groups.setdefault(name, [])
            groups[name].append(i)         # добавить порядковый номер
        return groups

    #получение строки расширения изображений WxH, либо "" для подмножества изображений,
    #если размеры отдельных изображений отличаются
    def sizeToWxH(self, ids):
        if self.hasSameSize(ids):
            im = self.imgs[ids[0]]
            if im.shape[1] == im.shape[0]: s = str(im.shape[1])
            else:                          s = str(im.shape[0]) + "x" + str(im.shape[1])
        else:
            return "" #нет имени
        return s

    #признак, что все указанные примеры одного размера
    def hasSameSize(self, ids):
        h = self.imgs[ids[0]].shape[1]
        w = self.imgs[ids[0]].shape[0]
        for i in ids:
            if self.imgs[i].shape[1] != h or self.imgs[i].shape[0] != w:
                print("not same",[w,h],i,self.imgs[i].shape)
                return False
        return True

    def save2(self, name): #сохранение в файл с name=xxx.smpWxH, xxx.lblWxH
        #файл smp содержит N изображений в виде byte[H*W]
        #файл lbl содержит N строк, каждая из которых определяет метку изображения
        try:
            pos = name.rfind(".smp")  # убрать расширение из имени файла
            lblname = name[:pos]
            lblname += ".lbl" + name[pos + 4:]
            smpname = name

            f = open(smpname, "wb")
            n = len(self.imgs)
            for i in range(n):
                a = self.imgs[i]
                a = 255 - a
                f.write(a.tobytes())  # np.array
            f.close()

            f = open(lblname, "wb")
            for i in range(n):
                label = self.labels[i].encode('utf-8')  # преобразовать в bytes
                f.write(label)
                f.write("\n".encode('utf-8'))
            f.close()
            return True
        except:
            print("exception")
            return False

    def loadFromSmpWxH(self, smpname, fileid, clearall=False): #загрузка из smpname=xxx.smpWxH, lblname=xxx.lblWxH
        if clearall: #удалить имеющиеся
            self.imgs = []
            self.labels = []
            self.fids = []
        try:
            pos = smpname.rfind(".smp")  # убрать расширение из имени файла
            if pos >= 0:
                dx = smpname[pos+4:]
                if dx.find("x") != -1: #если изображения не квадратные
                    dy = dx[dx.find("x")+1:]
                    dx = dx[:dx.find("x")]
                else:
                    dy = dx
                dx = int(dx)
                dy = int(dy)

            if pos >= 0: lblname = smpname[:pos]+".lbl" + smpname[pos+4:]
            else:        return False #нельзя сформировать имя lbl
            if not os.path.exists(lblname): return False

            f = open(smpname,"rb")
            line = f.read(dx*dy)
            while(line):
                a = np.frombuffer(line,dtype='u1')
                a = 255 - a
                img = a.reshape([dy, dx])
                self.imgs.append(img)
                self.fids.append(fileid)
                line = f.read(dx*dy)

            f.close()

            f = open(lblname,"rb")
            line = f.readline()
            while line:
                line = line[:-1]
                label = line.decode('utf-8')
                self.labels.append(label)
                line = f.readline()
            f.close()
            return True
        except:
            print("exception")
            return False

    def loadFromIdx(self,imgname,lblname,fileid,clearall=False): #загрузка данных из формата MNIST

        print("LOAD FROM IDX",imgname,lblname)
        images = emnist.readidx(imgname)   #t10k-images.idx3-ubyte
        labels = emnist.readidx(lblname)   #t10k-labels.idx1-ubyte

        alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" #для баз -byclass-
        #для -balanced- и -bymerge- другие метки и не все классы есть
        #(можно загружать в этом формате, а затем перенумеровывать)
        if images.shape[0]!=labels.shape[0]: return False #число изображений и меток отличается
        k = dict.fromkeys(labels.tolist()).keys()
        nk = len(k)
        if nk>len(alphabet): return False #сравнение алфавита с максимально возможным
        n = images.shape[0]
        if nk<=10:  imgs = [255-images[i,:,:] for i in range(n)] #только цифры не нужно транспонировать
        else:       imgs = [(255-images[i,:,:]).T.copy() for i in range(n)]    #выделение одной картинки и инверсия цветов
        lbls = [alphabet[labels[i]] for i in range(n)]  #преобразование номера в метку
        fids = [fileid for i in range(n)]

        self.imgs.extend(imgs)
        self.labels.extend(lbls)
        self.fids.extend(fids)
        return True

    def loadAuto(self,name,fileid,clearall=False):#загрузка с авт. определением формата по расширению файла
        ext1 = "images.idx3-ubyte"  #windows вариант
        ext2 = "images-idx3-ubyte"  #linux вариант
        if   name.rfind(ext1)>=0:
            lblname = name.replace(ext1,"labels.idx1-ubyte")
            return self.loadFromIdx(name,lblname,fileid,clearall)
        elif name.rfind(ext2)>=0:
            lblname = name.replace(ext2,"labels-idx1-ubyte")
            return self.loadFromIdx(name, lblname, fileid, clearall)
        else:
            pos = name.rfind(".smp")
            if (pos+4) == len(name):    return self.loadFromSmp(name,fileid,clearall)
            else:                       return self.loadFromSmpWxH(name,fileid,clearall)

    def flip(self, imgs, lbls):
        import random
        imgs2 = imgs.copy()
        lbls2 = lbls.copy()
        n = list(range(len(imgs)))
        random.shuffle(n)
        # n = random.sample(range(len(imgs) - 1), len(imgs) - 1)
        m = 0
        for i in n:
            imgs[m] = imgs2[i]
            lbls[m] = lbls2[i]
            m += 1


class HpOpFixRescale: #приведение к одному размеру всех изображений в зависимости от правила

    MODE_SCALE=0        #масштабировать по высоте и ширине
    MODE_CENTER=1       #центрировать (если больше, то вписать
    MODE_INSCRIBE=2     #вписать по большей стороне

    #если размер не задан, то приводятся к общему размеру

    def __init__(self, mode, bound, thickness=0): #параметры инициализации
        self.mode  = mode
        self.bound = bound
        self.border = thickness

    def __str__(self):
        return "FixScale(mode={0},bound={1},border={2})".format(self.mode,self.bound,self.border)

    @staticmethod
    def nparray2qimage(im):
        #Преобразование nparray в qimage с учетом выавнивания
        h,w = im.shape
        return QImage(im, w, h, 1 * w, QImage.Format_Grayscale8)

    @staticmethod
    def qimage2nparray(img):
        """  Converts a QImage into an opencv MAT format """
        img = img.convertToFormat(QImage.Format_Grayscale8) # если требуется
        w,h = img.width(), img.height()
        bpl = img.bytesPerLine()
        if bpl == w: # данные выровнены
            p = img.bits().asarray(w*h*1)  # не constBits!
            return np.array(p, 'u1').reshape(h, w)
        else: #данные не выровнены
            p = img.bits().asarray(bpl * h * 1)  # не constBits!
            a = np.array(p, 'u1').reshape(h, bpl)
            b = a[0:h,0:w]
            #print(b.shape)
            return b # убрать невыровненные байты

    def apply(self, samples):   #обрабатываемые примеры
        #Изменение масштабов изображений по заданному прваилу
        # mode:int {0 - MODE_SCALE,1 - MODE_CENTER,2 - MODE_INSCRIBE}
        n = len(samples.imgs)
        samples2 = HpSamples()
        samples2.imgs = [None]*n  # заполнить пустыми объектами
        samples2.labels = samples.labels
        p = QPainter()
        for index in range(n):   # для каждой линии
            im = samples.imgs[index]  # собственно изображение в виде np.array
            if im is None: continue
            h, w = im.shape
            src = QImage(im, w, h, 1 * w, QImage.Format_Grayscale8)
            r = self.bound
            t = self.border
            if t>0: r = QRect(r.x()+t, r.y()+t, r.width()-2*t, r.height()-2*t) #учесть рамку
            # центрировать изображение в регионе
            need = False
            if self.mode == self.MODE_CENTER:
                if w>r.width() or h>r.height(): need = True #вписать, если больше области
                else:
                    sx, sy = int((r.width()- w)/2), int((r.height()- h) / 2)
                    r = QRect(r.x()+sx, r.y()+sy, w, h)
            if self.mode == self.MODE_INSCRIBE or need:
                rx, ry = w/r.width(), h/r.height() # отношение
                if rx>ry:  # заполнение по x
                    h2 = int(h/rx)
                    sy = int((r.height() - h2) / 2)
                    r = QRect(r.x(), r.y()+sy, r.width(), h2)
                else:  # заполнение по y
                    w2 = int(w/ry)
                    sx = int((r.width() - w2) / 2)
                    r = QRect(r.x()+sx, r.y(), w2, r.height())
            dst = QImage(self.bound.width(), self.bound.height(), QImage.Format_Grayscale8)  # результирующее изображение
            p.begin(dst)
            p.setPen(QPen(QColor(255, 255, 255)))
            p.setBrush(QBrush(QColor(255, 255, 255)))
            p.drawRect(QRect(QPoint(0, 0), dst.size()))
            p.drawImage(r, src, QRect(0, 0, w, h))
            p.end()
            samples2.imgs[index] = HpOpFixRescale.qimage2nparray(dst)  # преобразовать к nparray
        return samples2


class HpOpMove:     #смещение

    def __init__(self, bounds, steps):
        """
        :param bounds:  диапазоны смещения отн. центральной точки, пример: QRect(-1,-1,2,2)
        :param steps:   шаг смещения по x и y направлениям, пример: QSize(1,1)
        """
        self.bounds = bounds
        self.steps  = steps

    def __str__(self):
        return "Move(bounds={0},steps={1})".format(self.bounds,self.steps)

    def apply(self, samples): #применить преобразование (метки останутся такими же)
        """
        :param samples: список исходных изображений
        :return: список результирующих изображений HpSamples.
                метки изображений соответствуют исходным меткам
        """
        s = self.steps
        bw, bh = self.bounds.width(), self.bounds.height()
        nx = int((bw + s.width())   / s.width())  # число точек по x
        ny = int((bh + s.height()) / s.height())  # число точек по y
        # в алгоритме не учитываются с какой стороны должно быть выделено больше памяти
        samples2 = HpSamples()
        for i in range(len(samples)):
            src = samples.imgs[i]
            if src is None: #пропускать пустые
                samples2.append(None, samples.labels[i], -1)
                continue
            h, w = src.shape
            for iy in range(ny):
                for ix in range(nx):
                    y, x = iy * s.height(), ix * s.width()
                    r = QRect(0, 0, w, h).united(QRect(x, y, w, h))  # координаты объединенного прямоугольника
                    dst = 255*np.ones([r.height(), r.width()], 'u1')  # не очень эффективно выделять каждый раз память
                    # сместить координаты, с учетом начала координат dst (0,0)
                    if r.left()< 0: x += r.left()
                    if r.top() < 0: y += r.top()
                    dst[y:(y+h), x:(x+w)] = src  # скопировать исходное, смещенное в заданную позицию
                    #print(QRect(x,y,w,h))
                    samples2.append(dst, samples.labels[i])
        return samples2

class HpOpScale:
    def __init__(self, pstart, pend, pstep):
        """
        Параметры масштабирования
        :param pstart: начальный масштаб изображения (% от исходного), например 50.7
        :param pend:   конечный масштаб изображения (%), например, 120
        :param pstep:  шаг увеличения (%), например, 10
        """
        self.pstart = pstart
        self.pend   = pend
        self.pstep  = pstep

    def __str__(self):
        return "Scale(start={0},end={1},step={2})".format(self.pstart,self.pend,self.pstep)

    def apply(self, samples):
        samples2 = HpSamples()
        for i in range(len(samples)):
            src = samples.imgs[i]  # собственно изображение в виде np.array
            if src is None: #пропускать пустые
                samples2.append(None, samples.labels[i], -1)
                continue
            h, w = src.shape
            nstep = int((self.pend-self.pstart + self.pstep) / self.pstep)  # число шагов
            for j in range(nstep):
                scale = self.pstart + j*self.pstep
                h2, w2 = int(scale*h/100), int(scale*w/100)
                dst = cv2.resize(src, dsize=(w2, h2), interpolation=cv2.INTER_CUBIC)
                samples2.append(dst, samples.labels[i])  # преобразовать к nparray
        return samples2


class HpOpRotate:
    def __init__(self, astart, aend, astep):
        self.astart = astart
        self.aend   = aend
        self.astep  = astep

    def __str__(self):
        return "Rotate(start={0},end={1},step={2})".format(self.astart,self.astep,self.aend)

    def apply(self, samples):
        from scipy import ndimage
        samples2 = HpSamples()
        for i in range(len(samples)):
            src = samples.imgs[i]  # собственно изображение в виде np.array
            if src is None: #пропускать пустые
                samples2.append(None, samples.labels[i], -1)
                continue
            nstep = int((self.aend-self.astart + self.astep) / self.astep)  # число шагов
            for j in range(nstep):
                angle = self.astart + j*self.astep
                dst = ndimage.rotate(255-src, angle)          # заполняет оставшиеся части черным цветом (поэтому нужно инвертировать)
                samples2.append(255-dst, samples.labels[i])  # преобразовать к nparray
        return samples2


class HpOpReplaceColor:

    MODE_SHIFT2BLACK = 0    #сдвиг к черному цвету
    MODE_BINARIZE = 1       #бинаризация по k (все что больше k - белый, меньше - черный)
    MODE_SCALE2RANGE = 2    #сдвинуть к черному и промасштабировать по k уровням
    MODE_SHIFTMID2BLACK = 3 #сдвиг среднего цвета к цвету k

    def __init__(self, mode, k=254): #k=0..255
        self.mode = mode
        self.k    = k

    def __str__(self):
        return "ReplaceColor(mode={0},k={1})".format(self.mode,self.k)

    #лучше по одному изображению, но тогда должен быть класс HpSample (а не HpSamples)
    def apply(self, samples):
        samples2 = HpSamples()
        if self.mode == self.MODE_SHIFT2BLACK:
            for i in range(len(samples)):
                src = samples.imgs[i]
                if src is None:  samples2.append(None, samples.labels[i], -1); continue
                c = src.min()
                T = np.arange(0,256,1,dtype='u1') #таблица замен по умолчанию
                if c>0:     T[:c]=0
                if c<255:   T[c:255]-=c
                T[255]=255
                dst = T[src]
                samples2.append(dst, samples.labels[i], -1)
        elif self.mode == self.MODE_BINARIZE:
            T = np.zeros(256, dtype='u1')
            if self.k<255:
                T[0:(self.k+1)] = 0
                T[(self.k+1):256] = 255
            for i in range(len(samples)):
                src = samples.imgs[i]
                if src is None:  samples2.append(None, samples.labels[i], -1); continue
                dst = T[src]
                samples2.append(dst, samples.labels[i], -1)
        elif self.mode == self.MODE_SCALE2RANGE:
            for i in range(len(samples)):
                #приводим диапазон cmin..cmax к 0..k
                #cmin нужно, т.е. могут быть светлые изображения
                src = samples.imgs[i]
                if src is None:  samples2.append(None, samples.labels[i], -1); continue
                cmin = src.min()        #мин значение цвета
                cmax = np.max(src+1)-1  #мак значение цвета, кроме 255
                #print("cmin=",cmin," cmax=",cmax)

                ck = self.k/(cmax-cmin+1) #масштабный коэффициент
                T = np.arange(0,256,1,dtype='u1') #таблица замен по умолчанию
                if cmin>0: T[:cmin] = 0
                for j in range(cmin,cmax+1):
                    T[j]=int((j-cmin)*ck)
                dst = T[src]
                samples2.append(dst, samples.labels[i], -1)
        elif self.mode == self.MODE_SHIFTMID2BLACK: #сдвиг среднего цвета к черному
            for i in range(len(samples)):
                #приводим диапазон cmin..cmax к 0..k
                #cmin нужно, т.е. могут быть светлые изображения
                src = samples.imgs[i]
                if src is None:  samples2.append(None, samples.labels[i], -1); continue
                msk = 255-src #инвертированное изображение (белый==0, черный==255)
                n = np.count_nonzero(msk) #число ненулевых (не белых)
                s = np.sum(msk)
                if n: cmid = int(255-s/n)  #средний ненулевой цвет (без белого)
                else: cmid = 255 #белый цвет
                #print("cmid=",cmid)

                #таблица сдвига
                T = np.arange(0, 256, 1, dtype='u1')  # таблица замен по умолчанию
                T[0:cmid]=0
                T[cmid:255]-=cmid #сдвинуть к черному (а белый оставить)
                dst = T[src]
                samples2.append(dst, samples.labels[i], -1)
        else:
            print("HpOpReplaceColor: режим не поддерживается")

        #ar = np.array()
        #cmin = ar.min()         #ближайший к черному цвет
        #cmax = (ar+1).max()-1   #найти максимальный элемент, ближайший к 255
        #режим по умолчанию - заменить цвета пикселей по таблице
        #dst = T[samples.imgs[i]] #заменить по таблице
        #samples2.append(dst,samples.labels[i],-1)
        return samples2


#сдвиг (верхней части относительно нижней)
class HpOpShift:  # сдвиг (верхней части относительно нижней)
    def __init__(self, astart, aend, astep):
        self.astart = astart
        self.aend = aend
        self.astep = astep

    def __str__(self):
        return "Shift(start={0},end={1},step={2})".format(self.astart,self.aend,self.aend)

    def apply(self, samples):  # применить преобразование (метки останутся такими же)
        samples2 = HpSamples()
        for i in range(len(samples)):
            src = samples.imgs[i]
            if src is None: #пропускать пустые
                samples2.append(None, samples.labels[i], -1)
                continue
            nstep = int((self.aend - self.astart + self.astep) / self.astep)  # число шагов
            h, w = src.shape
            for j in range(nstep):
                angle = self.astart + j * self.astep
                rad = -(90 - angle) * np.pi / 180
                a = np.tan(rad)
                coord = []
                for y in range(h):
                    for x in range(w):
                        if src[y, x] != 255:
                            new_x = int(y / a) + x
                            coord.append((y, new_x, src[y, x]))
                min_x = min(coord, key=lambda xx: xx[1])[1]
                max_x = max(coord, key=lambda xx: xx[1])[1]
                min_y = min(coord, key=lambda xx: xx[0])[0]
                max_y = max(coord, key=lambda xx: xx[0])[0]
                dst = 255 * np.ones([abs(max_y - min_y) + 1, abs(max_x - min_x) + 1], 'u1')

                for y in coord:
                    dst[y[0] - min_y, y[1] - min_x] = y[2]
                #сглаживание
                h1, w1 = dst.shape
                for y in range(0, h1 - 1):
                    for x in range(0, w1 - 1):
                        smooth_color = (int(dst[y, x]) + int(dst[y + 1, x]) + int(dst[y, x + 1]) + int(
                            dst[y + 1, x + 1])) / 4
                        dst[y, x] = smooth_color

                samples2.append(dst, samples.labels[i])
        return samples2


class HpOpDilate:

    MODE_DILATE_ONES2X2 = 0
    MODE_DILATE_ONES3X3 = 1
    MODE_DILATE_4POINT  = 2

    def __init__(self, mode):
        self.mode=mode

    def __str__(self):
        return "Dilate(mode={0})".format(self.mode)

    def apply(self,samples):
        samples2 = HpSamples()
        cross = scipy.ndimage.generate_binary_structure(2,1)
        for i in range(len(samples)):
            src = samples.imgs[i]
            if src is None: #пропускать пустые
                samples2.append(None, samples.labels[i], -1)
                continue
            #по умолчанию с размером 3*3
            if self.mode == self.MODE_DILATE_ONES2X2:
                dst = 255 - scipy.ndimage.morphology.grey_dilation(255-src, size=(2, 2))
            elif self.mode == self.MODE_DILATE_ONES3X3:
                dst = 255-scipy.ndimage.morphology.grey_dilation(255-src,size=(3,3))
            elif self.mode == self.MODE_DILATE_4POINT:
                dst = 255 - scipy.ndimage.morphology.grey_dilation(255 - src, footprint=cross)
            else:
                print("HpOpDilate: режим не поддерживается")
                break
            samples2.append(dst, samples.labels[i], -1)
        return samples2