import numpy as np
import scipy.stats
from CoordsObj import Coords
from Markup import Markup

#Высокие элементы должны быть разделены по линиям заранее (возможно с их распознаванием),
#    чтобы можно было формировать правильные гипотезы
#    для этого необходимо уметь определять линии границ букв
#Длинные элементы (несколько слившихся букв) будут разделяться на этапе распознавания


#Нахождение центра набора областей (с исп. фильтра по высоте)
#возвращает 2 значения: (x,y)
def segm_center(bbox, ids, dyfilter=None):
    if len(ids)<=0: return 0,0
    use_filter = dyfilter is not None
    sx=0
    sy=0
    count=0
    for i,id in enumerate(ids):
        b=bbox[id]
        if use_filter and not dyfilter[0]<=b.height()<=dyfilter[1]: continue #фильтр по высоте
        sx += b.x()+b.width()/2
        sy += b.y()+b.height()/2
        count+=1
    if count: return sx/count,sy/count
    else:     return 0,0


#Аппроксимация набора bbox линией
#dyfilter - минимальные размеры учитываемых bbox
#возвращает: коэффициенты аппроксимации (a,b)
def segm_lineapprox(bbox, ids, dyfilter=None):
    x=[]
    y=[]
    if dyfilter is None: what=[]
    else: what = [i for i in range(len(ids)) if dyfilter[0]<=bbox[ids[i]].height()<=dyfilter[1]]
    if len(what)==0: what = range(len(ids))
    for i in what:
        b = bbox[ids[i]]
        x.append(b.x()+b.width()/2)     #х координаты центров элементов группы
        y.append(b.y()+b.height()/2)    #y координаты центров элементов группы
    if len(x)==0:   return [0,0]
    elif len(x)==1: return [0,y[0]]
    else:           return np.polyfit(x,y,1)    #общий случай


#Оценка средней высоты символа
#можно добавить также ограничение минимальной и максимальной высоты символа
#(фильтр грубых выбросов maxy, miny)
def detect_char_height(bbox,sigma=0.8,ybounds=[10,40]):
    b=ybounds
    #по гистограмме определяет лучше, чем по мат. ожиданию
    n = len(bbox)
    dy = [bbox[i].height() for i in range(n)]
    h = np.histogram(dy,bins=list(range(max(dy)+1)))[0]
    #UPD i,s = 0,0
    #UPD while s < sigma * n: s += h[i]; i += 1 #найти такой размер, который больше sigma частей выборки
    #UPD return i

    left, right = b[0], min(b[1], len(h))
    if b[0]>=len(h): return left #все элементы меньше
    n2 = sum(h[left:right]) #число элементов в искомом диапазоне

    i,s = left,0
    while s < sigma * n2: s += h[i]; i += 1 #найти такой размер, который больше sigma частей выборки
    return i

#Нахождение уравнения центра линии
def approx_center_line(bbox,ids,charheight):
    dyfilter = [charheight/2, 3*charheight/2]
    pi180 = 3.14151692 / 180

    p = segm_lineapprox(bbox,ids,dyfilter)
    #КОРРЕКЦИЯ БОЛЬШИХ УГЛОВ
    ang = p[0]/pi180 #Если нужно применить ко всем линиям ang=100;
    if not -1.0<=ang<=1.0: #Тот же алгоритм что и в connect_lines2
        mx,my = segm_center(bbox,ids,dyfilter)
        if mx==0 and my==0: mx,my = segm_center(bbox,ids,None);
        yold = np.polyval(p,mx)
        p[0]=0                      #новое значение
        ynew = np.polyval(p,mx)     #новое значение
        p[1] = p[1] + yold - ynew   #пересчитать координаты
    return p















#вычисление метрик по разметке
class MarkupMetrics:

    def __init__(self, markup):
        self.mkp   = markup
        self.sigma = 0.8
        self.charheight = None
        self.centrallines = None
        self.dcomb, self.drect, self.dmlw, self.dnseg, self.dpos = None, None, None, None, None

    #def metricDicts(self):          #построение словарей
    #    pass

    #Оценка средней высоты символа
    def detectCharHeight(self):
        self.charheight = detect_char_height(self.mkp.boxes,self.sigma)
        return self.charheight

    #базовая линия - линия, на которой расположены буквы ограничивающая снизу буквы (A Z L Ш)
    #   на ней лежат символы . _ ... ,
    #центральная линия - линия, идущая по середине букв baseline+letterheight/2
    #   на ней лежат - = : > <
    #верхняя линия - линия, ограничивающая сверху baseline+letterheight
    #   на ней лежат ", галка Й, точки Ё

    def centralLine(self,iline):    #коэффициенты cfs центральной линии
        #чтобы y для x, нужно вызвать np.polyval(cfs, x)
        if not self.charheight: return
        return approx_center_line(self.mkp.boxes,self.mkp.ids[iline],self.charheight)

    def centralLines(self):  #нахождение уравнений центральных линий
        if not self.charheight: return
        self.centrallines = [self.centralLine(i) for i in range(len(self.mkp.ids))]
        return self.centrallines

    def baseLines(self,centrallines, charheight):   #нахождение уравнений нижних линий
        #можно корректировать по нижним краям букв
        if not self.charheight: return
        half = self.charheight()/2
        return [[c[0],c[1]+half] for c in centrallines]

    def upperLines(self,centrallines, charheight): #нахождение верхней линии
        #можно корректировать по верхним краям букв
        if not self.charheight: return
        half = self.charheight()/2
        return [[c[0],c[1]-half] for c in centrallines]

    @staticmethod
    def approxLawByDict(dic): #построение законов распределения групп значений
        law = dict()
        for k in dic.keys():
            if len(k)!=1: continue  #длина не равна 1 символу
            data = dic[k]
            if len(data)<2: continue #недостаточно статистики (нужно заменять фикс. диапазоном)
            y, x = np.histogram(data, density=True)  # собрать по ячейкам
            x = (x + np.roll(x, -1))[:-1] / 2.0
            params = scipy.stats.norm.fit(data)
            law.setdefault(k,params)
        return law

    #вычисление словарей метрик
    def buildMetricDicts(self): #построение словарей со статистикой
        #dcomb - списки объединенных в группы элементов,
        #drect - ограничивающий прямоугольник буквы
        #dmlw - макс. ширина линии букв
        #dnseg - число сегментов, составляющих букву
        if self.mkp.coords is None: return
        #вычислить комбинации по всей странице
        combs, labels, poss = self.mkp.labeledCombs()

        dcomb = dict() #словарь номеров сегментов, связанных с буквами
        drect = dict() #словарь размеров (width,height)
        dmlw  = dict() #словарь макс размера по линии
        dnseg = dict() #словарь числа сегментов [0,0,0,0,0].copy() макс. 5 сегментов иначе нельзя добавлять
        dpos  = dict()  #словарь номеров адресов (строка,столбец mu)
        for j in range(len(combs)):
            coords = [self.mkp.coords[c] for c in combs[j]] #список объектов координат для одного объединения
            ubox  = Coords.unitedrect(coords)           #размеры
            maxlw = Coords.maxunitedlinewidth(coords)   #макс. ширина линии

            label = labels[j]
            if len(label)==0: label=" " #вместо пустого имени

            dpos.setdefault(label,[])
            dpos[label].append(poss[j])

            dcomb.setdefault(label,[])
            dcomb[label].append(combs[j])

            drect.setdefault(label,[])
            drect[label].append(ubox)

            dmlw.setdefault(label,[])
            dmlw[label].append(maxlw)

            nseg = len(combs[j])
            dnseg.setdefault(label,[0,0,0,0,0,0]) #макс. число сегментов
            if nseg>6:  dnseg[label][5]+=1        #берем макс. собираемое значение
            else:       dnseg[label][nseg-1]+=1
        self.dcomb, self.drect, self.dmlw, self.dnseg, self.dpos = dcomb, drect, dmlw, dnseg, dpos

    def lawMLW(self): #аппроксимация распределений макс. ширины буквы по словарю букв
        return MarkupMetrics.approxLawByDict(self.dmlw)

    @staticmethod
    def cldev(r,cfs): #r:QRect cfs:(a,b)
        x = r.x() + r.width() / 2
        y = r.y() + r.height() / 2
        return np.polyval(cfs, x) - y  # меньшее значение сверху

    def lawCLD(self): #закон отклонения от центральной величины
        #построить словарь отклонений
        #y=rect.y-centralline(rect.cx)/charheight
        #если буква притягивается к нижней строке, то зависеть от charheight будет,
        #если к центру, то - не будет
        if self.charheight is None: self.detectCharHeight()
        if self.centrallines is None: self.centralLines()
        ch = self.charheight
        centrallines = self.centrallines
        ddev = dict() #словарь отклонений
        for k in self.drect.keys():
            rects = self.drect[k]
            poss  = self.dpos[k]
            ddev[k] = [MarkupMetrics.cldev(r,centrallines[p[0]]) for r,p in zip(rects,poss)]
        print("DDEV:",ddev)
        return MarkupMetrics.approxLawByDict(ddev) #приблизить законом распределения















