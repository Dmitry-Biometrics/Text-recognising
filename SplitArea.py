from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import numpy as np

import CoordsObj
from CoordsObj import Coords


class SplitArea(QLabel):

    black = QtGui.QColor(0, 0, 0)

    def __init__(self, parent, letter, id_bbox):
        super().__init__(parent)

        self.is_drawing = False
        self.mousebut = 0
        self.letter = letter
        self.image = np.ones((self.letter.height, self.letter.width))*255
        self.points = set()
        self.id_bbox = id_bbox


    def coordToImage(self):
        for i in self.letter.pc:
            y = int((i[0]) / (self.letter.width))
            x = i[0] - y * self.letter.width
            self.image[y, x] = i[1]

    def setImage(self):
        h, w = self.image.shape
        im_np = np.require(self.image, np.uint8, 'C')

        im = QImage(im_np.data, w, h, 1 * w, QImage.Format_Grayscale8)

        pixmap = QPixmap().fromImage(im)
        pixmap_r = pixmap.scaled(w*20, h*20)

        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setPixmap(pixmap_r)

    def pointCount(self): #число разделяющих точек
        return len(self.points)

    def split_coords(self):
        h, w = self.image.shape

        pc_l = []
        pc_r = []

        is_y = True
        is_x = False

        points_sort_x = sorted(self.points, key=lambda x: x[0])
        points_sort_y = sorted(self.points, key=lambda x: x[1])
        if points_sort_y[0][1] == 0:
            coords = self.check_full_coord(h, points_sort_y, is_y)
            if coords:

                h1, h2, w1, w2, max_y_l, max_y_r, min_y_l, min_y_r, max_x_l, max_x_r, min_x_l, min_x_r = \
                    self.find_min_max(coords, h, w, is_y)

                for i in self.letter.pc:
                        y = int((i[0]) / self.letter.width)
                        x = i[0] - int((i[0]) / self.letter.width) * self.letter.width
                        equ_y = coords[y]

                        if x < equ_y[0][0]:
                            y = y - min_y_l
                            new_shift = x - min_x_l + y * w1
                            pc_l.append((new_shift, i[1]))
                        else:
                            if len(equ_y) > 1:
                                if x > equ_y[1][0]:
                                    y = y - min_y_r
                                    new_shift = x - min_x_r + y * w2
                                    pc_r.append((new_shift, i[1]))
                            else:
                                y = y - min_y_r
                                new_shift = x - min_x_r + y * w2
                                pc_r.append((new_shift, i[1]))

                c1 = CoordsObj.Coords(self.letter.min_x, self.letter.min_y + min_y_l, w1, h1, pc_l, self.letter.id_bbox, len(pc_l))
                c2 = CoordsObj.Coords(self.letter.min_x + min_x_r, self.letter.min_y + min_y_r, w2, h2, pc_r, self.id_bbox, len(pc_r))

                box1 = QRect(self.letter.min_x + min_x_l, self.letter.min_y + min_y_l, w1, h1)
                box2 = QRect(self.letter.min_x + min_x_r, self.letter.min_y + min_y_r, w2, h2)
                return c1, c2, box1, box2, is_y

        elif points_sort_x[0][0] == 0:
            coords = self.check_full_coord(w, points_sort_x, is_x)
            if coords:

                h1, h2, w1, w2, max_y_l, max_y_r, min_y_l, min_y_r, max_x_l, max_x_r, min_x_l, min_x_r = \
                    self.find_min_max(coords, h, w, is_x)

                for i in self.letter.pc:
                    y = int((i[0]) / self.letter.width)
                    x = i[0] - int((i[0]) / self.letter.width) * self.letter.width
                    equ_y = coords[x]
                    if y > equ_y[0][1]:
                        y = y - min_y_l
                        new_shift = x - min_x_l + y * w1
                        pc_l.append((new_shift, i[1]))
                    else:
                        if len(equ_y) > 1:
                            if y < equ_y[1][1]:
                                y = y - min_y_r
                                new_shift = x - min_x_r + y * w2
                                pc_r.append((new_shift, i[1]))
                        else:
                            y = y - min_y_r
                            new_shift = x - min_x_r + y * w2
                            pc_r.append((new_shift, i[1]))

                c1 = CoordsObj.Coords(self.letter.min_x + min_x_l, self.letter.min_y  + min_y_l, w1, h1, pc_l,
                                      self.letter.id_bbox, len(pc_l))
                c2 = CoordsObj.Coords(self.letter.min_x + min_x_r, self.letter.min_y + min_y_r, w2, h2, pc_r, self.id_bbox, len(pc_r))

                box1 = QRect(self.letter.min_x + min_x_l, self.letter.min_y + min_y_l, w1, h1)
                box2 = QRect(self.letter.min_x + min_x_r, self.letter.min_y + min_y_r, w2, h2)
                return c1, c2, box1, box2, is_x
        return [], [], None, None, False

    def find_min_max(self, coords, h, w, is_y):
        max_y_l = 0
        max_y_r = 0

        min_y_l = h
        min_y_r = h

        max_x_l = 0
        max_x_r = 0

        min_x_l = w
        min_x_r = w

        cord_c = 0 if is_y else 1

        for i in self.letter.pc:
            y = int((i[0]) / self.letter.width)
            x = i[0] - y * self.letter.width
            if is_y:
                equ_y = coords[y]
                bools1 = x < equ_y[0][cord_c]
            else:
                equ_y = coords[x]
                bools1 = y > equ_y[0][cord_c]
            if y == 6 and x == 16:
                print(x, y)
            if bools1:
                if min_y_l >= y:
                    min_y_l = y
                if max_y_l <= y:
                    max_y_l = y
                if min_x_l >= x:
                    min_x_l = x
                if max_x_l <= x:
                    max_x_l = x
            else:
                if len(equ_y) > 1:
                    if is_y:
                        bools2 = x > equ_y[1][cord_c]
                    else:
                        bools2 = y < equ_y[1][cord_c]
                    if bools2:
                        if min_y_r > y:
                            min_y_r = y
                        if max_y_r <= y:
                            max_y_r = y
                        if min_x_r >= x:
                            min_x_r = x
                        if max_x_r <= x:
                            max_x_r = x
                else:
                    if min_y_r > y:
                        min_y_r = y
                    if max_y_r <= y:
                        max_y_r = y
                    if min_x_r >= x:
                        min_x_r = x
                    if max_x_r <= x:
                        max_x_r = x

        h1 = max_y_l - min_y_l + 1
        h2 = max_y_r - min_y_r + 1
        w1 = max_x_l - min_x_l + 1
        w2 = max_x_r - min_x_r + 1

        return h1, h2, w1, w2, max_y_l, max_y_r, min_y_l, min_y_r, max_x_l, max_x_r, min_x_l, min_x_r


    def check_full_coord(self, h, points, is_y):
        coords = []
        for i in range(h):
            coord = self.find_same_coord(i, points, is_y)
            if not coord:
                return []
            coords.append(coord)
            print(coord)
        return coords

    def find_same_coord(self, y, ar, is_y):
        new_ar = []
        coord_f = 1 if is_y else 0
        coord_l = 0 if is_y else 1
        for i in ar:
            if i[coord_f] < y:
                continue
            elif i[coord_f] == y:
                if new_ar:
                    tmp = new_ar[0]
                    if len(new_ar) == 1:
                        if i[coord_l] < new_ar[0][coord_l]:
                            new_ar.append(tmp)
                            new_ar[0] = i
                        else:
                            new_ar.append(i)
                    else:
                        if i[coord_l] < new_ar[0][coord_l]:
                            new_ar[0] = i
                        else:
                            if i[0] > new_ar[1][coord_l]:
                                new_ar[1] = i
                else:
                    new_ar.append(i)
            else:
                break
        return new_ar

    def mousePressEvent(self, ev):
        if Qt.LeftButton == ev.button():
            x, y = int(ev.pos().x() / 20), int(ev.pos().y() / 20)
            self.mousebut = Qt.LeftButton

            self.first_point = ev.pos()
            self.last_point = ev.pos()
            self.points.add((x, y))
            self.is_drawing = True

    def mouseMoveEvent(self, ev: QMouseEvent):
        if self.mousebut == Qt.LeftButton and self.is_drawing:
            self.last_point = ev.pos()
            x, y = int(ev.pos().x() / 20), int(ev.pos().y() / 20)
            if 0 <= x < self.image.shape[1] and 0 <= y < self.image.shape[0]:
                self.points.add((x, y))
                self.update()

    def mouseReleaseEvent(self, ev: QMouseEvent):
        self.mousebut = 0
        if Qt.LeftButton == ev.button() and self.is_drawing:
            self.is_drawing = False
            self.done = True

    def paintEvent(self, ev):
        super().paintEvent(ev)
        p = QPainter(self)
        p.setPen(QPen(Qt.red, 0, Qt.SolidLine))
        p.setBrush(QBrush(Qt.red))
        for i in self.points:
            p.drawRect(i[0] * 20, i[1] * 20, 20, 20)

