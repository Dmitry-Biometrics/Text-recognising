# coding=utf-8
import numpy as np
from PyQt5.QtCore import *

class Coords:

    def __init__(self, min_x=0, min_y=0, width=0, height=0, pc=None, id_bbox=-1, n=0):
        self.min_x = min_x
        self.min_y = min_y
        self.width = width
        self.height = height
        self.pc = pc
        self.id_bbox = id_bbox
        self.N = n

    def rect(self):
        return QRect(self.min_x,self.min_y,self.width,self.height)

    def xrange(self): return range(self.min_x, self.min_x + self.width)
    def yrange(self): return range(self.min_y, self.min_y + self.height)

    def boundlines(self):
        sx, sy, w, h= self.min_x, self.min_y, self.width, self.height
        lines = [[sx+w,sx]]*h #по умолчанию мин., макс.
        for i in self.pc:
            y = int(i[0] / w)
            x = int(i[0] % w)+sx #сразу смещенное значение
            lines[y]= [min(x,lines[y][0]),max(x,lines[y][1])] #найти мин и макс значения для линии
        return lines

    def maxlinewidth(self):
        return max([l - r + 1 for l,r in self.boundlines()])

    @staticmethod
    def unitedrect(coords):
        u = QRect()
        for c in coords: u = u.united(c.rect())
        return u

    @staticmethod
    def maxunitedlinewidth(coords): #максимальное расстояние по линии после объединенния объектов Coords
        bounds = [c.boundlines() for c in coords]   #все линии
        u = Coords.unitedrect(coords)               #найти пересечение прямоугольников
        sy = u.y()                                      #смещение по y
        lines = [[u.x()+u.width(),u.x()]]*u.height()      #максимальные значения
        for c,bound in zip(coords,bounds):
            y = c.min_y
            for i,b in enumerate(bound):
                y = c.min_y-sy+i
                l,r = lines[y]
                lines[y] = [min(b[0],l),max(b[1],r)] #найти мин и макс значения для конкретной линии
        #выбрать максимальную разницу+1
        dist = [r-l+1 for l,r in lines]
        return max(dist)










