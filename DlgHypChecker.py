# coding=utf-8
from PyQt5 import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from Ui_DlgHypChecher import Ui_DlgHypChecker
from SmpArea import SmpArea
from HpSamples import *
import Markup
from MarkupMetrics import MarkupMetrics
import numpy as np
from LetPredictor import *
from CoordsObj import *
import numpy as np
import scipy
import scipy.stats

class DlgHypChecker(QDialog):

    DEFAULT_LABEL=" "

    def __init__(self):
        super(DlgHypChecker, self).__init__()
        self.ui = Ui_DlgHypChecker()
        self.ui.setupUi(self)

        self.segmLevel = 4 #уровень объединения сегментов (до 4х может быть)
        #self.mkp=Markup.Markup()

        #self.ui.buttonBox.accepted.connect(self.accept)
        #self.ui.buttonBox.rejected.connect(self.reject)

        self.net = None
        self.mkp = None
        self.mm = None
        self.ubox = []

        #создать область отображения (недопустимые элементы маркируются как None)
        self.smp = []   #метки и изображения
        self.comb = []  #комбинации (недопустимые None)
        self.resp = []  #отклики нейронной сети (недопустимые None)
        self.respmlw = []
        self.respcld = []

        self.lawmlw = dict() #закон зависимости отклонений от максимальной ширины линии буквы
        self.lawcld = dict() #закон зависимости отклонений от центральной линии

        self.mlw_metric  = [] #метрика максимальной ширины
        self.bbox_metric = []
        self.cld = []

        self.area = SmpArea(self)
        self.ui.scrollArea.setWidget(self.area)

        self.area.itemSelected.connect(self.onItemSelected)
        self.ui.tbPredict.clicked.connect(self.onPredict)

    def setNetModel(self,net):
        self.net = net

    def setLawMLW(self, lawmlw):
        self.lawmlw = lawmlw

    def setLawCLD(self,lawcld):
        self.lawcld = lawcld

    def setLineMarkup(self, markup): #разметка одной линии (boxes,ids) должны быть установлены
        MAX_LETTER_WIDTH = 52 #параметр фильтрации комбинаций (ДОЛЖЕН ОПРЕДЕЛЯТЬСЯ ПО СРЕДНЕМУ РАЗМЕРУ БУКВЫ)
        self.mkp = markup #тестовая разметка (если mu установлен)
        self.mm = MarkupMetrics(markup) #метрики
        if not markup.coords:
            print("Отсутствуют ptc данные")
            return
        #базовый список комбинаций элементов
        comb = markup.lineDepthIds(line=0,level=self.segmLevel) #извлекаются все гипотезы до 4 уровня
        self.comb = comb  # список допустимых комбинаций (не None)

        #вычислить метрики
        self.bbox_metric = self.calcBbox()
        self.mlw_metric = self.calcMaxLineWidth()

        #отфильтровать по расстоянию
        coords = self.mkp.coords #ТОЛЬКО ЕСЛИ COORDS заданы
        self.ubox = [QRect()]*len(comb)
        for j in range(len(comb)):
            c = comb[j]
            if comb[j] is None: continue
            boxes = [coords[id].rect() for id in c] #все прямоугольники
            ubox = Markup.MuParser.uniteExtBoxes(coords,c) #объединенный прямоугольник
            self.ubox[j] = ubox
            if j%self.segmLevel==0: continue #одиночные сегменты по длине не фильтруются
            #print("width=",box.width()," box_w=",boxes[0].width())
            if ubox.width()>MAX_LETTER_WIDTH: comb[j]=None #исключить

        self.cld = self.calcCentralLineDistances()

        self.resp = [None] * len(comb) #соответствующие отклики
        self.respmlw = [None] * len(comb) #отклики с учетом ширины символа
        self.respcld = [None] * len(comb)  # отклики также с учетом расположение символа
        self.smp  = self.calcSmpImage(markup,comb)

        #отфильтровать по предсказанию нейронной сети
        self.predict()
        for j in range(len(comb)):
            if self.respmlw[j] is None: continue
            #UPD if max(self.respmlw[j])<0.05: #порог 5 процентов
            #    self.comb[j]= None #исключить
            #    self.smp.imgs[j] = np.zeros((4,4),dtype='u1') #заменить на точку

        self.area.setCountInLine(self.segmLevel)
        self.area.setGroupedSamples(self.smp,self.smp.groupByLabel(),[self.DEFAULT_LABEL])

    def calcSmpImage(self,markup,comb):
        #обновить изображения по списку comb2
        smp = HpSamples()
        for c in comb:
            if c is None:   smp.append(None, self.DEFAULT_LABEL)     #добавить пустое
            else:           smp.append(markup.extractUnitedImage(c),self.DEFAULT_LABEL)
        smp = HpOpReplaceColor(HpOpReplaceColor.MODE_SHIFTMID2BLACK,k=254).apply(smp)
        smp = HpOpDilate(HpOpDilate.MODE_DILATE_ONES2X2).apply(smp) #нулевые изображения пропускаются
        smp = HpOpFixRescale(HpOpFixRescale.MODE_CENTER, QRect(0, 0, 28, 28), 2).apply(smp)
        for i in range(len(smp)): #заменить пустые изображения фиксированными
            if smp.imgs[i] is None: smp.imgs[i] = np.zeros((1,1),dtype='u1')
        return smp

    def calcMaxLineWidth(self):
        mlw = [None]*len(self.comb)
        for j,comb in enumerate(self.comb):
            if comb is None: continue #не вычислять
            coords = [self.mkp.coords[t] for t in comb]
            mlw[j] = Coords.maxunitedlinewidth(coords)
        return mlw

    def calcCentralLineDistances(self):
        self.mm.detectCharHeight()
        centralline = self.mm.centralLine(0) #одна линия
        #найти прямоугольные области, соответствующие
        cld = [None] * len(self.comb)
        for j,comb in enumerate(self.comb):
            if comb is None: continue #не вычислять
            cld[j] = MarkupMetrics.cldev(self.ubox[j],centralline)
        return cld

    def calcBbox(self):
        r = [None]*len(self.comb)
        for j,comb in enumerate(self.comb):
            if comb is None: continue  # не вычислять
            coords = [self.mkp.coords[t] for t in comb]
            r[j] = Coords.unitedrect(coords)
        return r

    @pyqtSlot(int)
    def onItemSelected(self, id):
        #выбран элемент
        self.area.deselectAll()
        self.area.selectItem(id)
        irow = int(id/4)
        icol = int(id%4)
        self.setWindowTitle("{0},{1}".format(irow,icol))
        if 0<=id<len(self.comb):
            if self.resp[id] is not None:
                self.ui.edResp.clear()
                self.ui.edResp.appendPlainText(self.resp2string('NET:',self.resp[id]))
                self.ui.edResp.appendPlainText(self.resp2string('MLW:',self.respmlw[id]))
                self.ui.edResp.appendPlainText(self.resp2string('CLD:',self.respcld[id]))
            else:
                self.ui.edResp.setPlainText("не вычислен")

            self.ui.edHyp.clear()
            bbox = self.bbox_metric[id]
            if bbox is not None:
                s = "width={0}\nheight={1}\n".format(bbox.width(),bbox.height())
                self.ui.edHyp.appendPlainText(s)
            mlw = self.mlw_metric[id]
            if mlw is not None: self.ui.edHyp.appendPlainText("maxlinewidth=" + str(mlw)+"\n")

    def predict(self):
        #упаковать только разрешенные изображения, которые необходимо распознать
        imgs = [self.smp.imgs[i] for i,c in enumerate(self.comb) if c is not None]
        data = np.array(imgs)

        r = self.net.predict(data)
        j=0
        for i in range(len(self.comb)):
            if self.comb[i] is not None:
                self.resp[i]=r[j,:]
                self.respmlw[i]=self.prodByLaw(self.resp[i],self.mlw_metric[i],self.lawmlw)
                #UPD self.respcld[i]=self.prodByLaw(self.respmlw[i],self.cld[i],self.lawcld) #второе умножение
                self.respcld[i] = self.prodByLaw(self.resp[i], self.cld[i], self.lawcld)  # ДЛЯ ОТЛАДКИ
                j+=1

    def onPredict(self):
        self.predict()

    def prodByLaw(self, resp, val, laws):
        #resp - отклик сети для изображения
        #val  - контроллируемое значение
        resp2 = resp.copy()
        for i,a in enumerate(self.net.alphabet()):
            if a not in laws: #буквы нет в модели (вероятность не может быть оценена)
                resp2[i] = 0.0
            else:
                params = laws[a] #параметры для буквы
                m = params[-2]
                s = params[-1]
                dist = scipy.stats.norm
                #умножаем на вероятность+пронормируем на макс. значение
                p = dist.pdf(val, *params[:-2], m, s) #/ dist.pdf(m, *params[:-2], m, s)
                resp2[i] *= p/(p+1/32) #эмпирически учитываем вероятность "не буква"
        return resp2


    def resp2string(self,text,resp):
        s = self.net.alphabet()
        #rlist = [float("%.2f" % item) for item in list(resp)]
        #d = dict(zip(s,rlist)) #создать из соотв. пар
        print(list(resp))
        ar = sorted(zip(s,list(resp)),reverse=True,key=lambda k:k[1])
        sentence = [a[0]+"=%.2f "%a[1] for a in ar if a[1]>0.01]
        return text+''.join(sentence)



