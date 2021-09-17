import math
import bisect  # модуль для работы с упорядоченными списками
import operator
import cv2
import numpy as np
import matplotlib
import matplotlib.image
import matplotlib.pyplot as plt
import scipy.ndimage.morphology
import skimage
import skimage.morphology
import matplotlib.patches as mpatches
import CoordsObj

def swapitem(a, i, j):  # обмен элементов в списке
    a[i], a[j] = a[j], a[i]


def replacechars(text, what, than=' '):  # замена отдельных символов строки на другой
    s = []
    for i in range(len(text)):
        if text[i] in what:
            s.append(' ')
        else:
            s.append(text[i])
    return ''.join(s)


def rgb2gray(rgb):
    '''
    Конвертация цветного изображения к оттенкам серого
    изображение представляет собой трехмерный массив [ширина,высота,цвет_плоскости]
    '''
    return np.dot(rgb[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint8)


def bwareaopen(im, size):
    bim = im < 128  # обратные цвета
    # im3 = morphology.remove_small_objects(bim, min_size=100, connectivity=2)
    bim = skimage.morphology.remove_small_objects(bim, min_size=size)
    # bim = skimage.morphology.remove_small_holes(bim, min_size=size)

    #расширение контура (чтобы объединить близко расположенные сегменты)
    #не работает - объединяются и буквы тоже
    #UPD bim2 = scipy.ndimage.morphology.binary_dilation(bim) #4 точечный метод
    #4 точечный метод struct1 = ndimage.generate_binary_structure(2, 1)
    #8 точечный метод struct1 = ndimage.generate_binary_structure(2, 2)
    #ndimage.binary_dilation(a, structure=struct1|struct2,  iterations=1).astype(a.dtype)
    #                                                       iterations=2 - повторит преобразование 2 раза

    # КАРТИНКА 3
    #plt.figure()
    #plt.imshow(~bim, cmap='gray', vmin=0, vmax=1) #отобразить бинарное изображение
    return bim #UPD bim2


def bwlabel(im):
    """
    Промаркировать регионы изображения
    если возвращать imoverlay, то только без точек исключенных регионов
    """
    delta = 26
    # совмещенная маска всех объектов
    mask, num = skimage.measure.label(im, return_num=True, background=False)  # каждый объект получает свой цвет
    # plt.imshow(labeled,cmap=None) изображение каждый цвет которого определяет отдельную метку
    imoverlay = skimage.color.label2rgb(mask, bg_label=0, bg_color=(255, 255, 255))  # раскраска объектов
    print(imoverlay.dtype)
    print(imoverlay[0, 0])

    # fig, ax = plt.subplots(figsize=(10, 6))
    # ax.imshow(imoverlay)

    labels = []
    for region in skimage.measure.regionprops(mask):
        if region.area >= 30:
            minr, minc, maxr, maxc = region.bbox
            bbox = (minc, minr, maxc - minc, maxr - minr)
            if bbox[2] > delta*3 or bbox[3] > delta*2:
                coords = region.coords
                for axes in coords:
                    mask[axes[0], axes[1]] = 0  #создаем очищенную маску, чтобы каждый bbox соответствовал
                    # одному непрерывному объекту
            else:
                labels.append(bbox)
        else:
            coords = region.coords
            for axes in coords:
                mask[axes[0], axes[1]] = 0

    return labels, len(labels), imoverlay, mask


def lineLetters(bbox, delta=26, minsquare=16*16):
    # примечание: БЕЗ ПРОГНОЗА РАБОТАЕТ ЛУЧШЕ
    # bbox(x,y,width,height)
    # delta = 26 #допустимое отклонение от среднего (пикселей)

    # проблема - высокие буквы по Y могут пропустить несколько предыдущих букв
    #
    num = len(bbox)  # число элементов
    g = []  # вектор групп элементов
    en = []  # признак разрешения группы (en=true(n,1))

    # рассчитать центры каждого прямоугольника
    cy = [(b[1] + b[3] / 2) for b in bbox]  # центры по oY
    gy = []  # среднее значение для каждой группы, вычисленной по последним nlast элементам

    for i in range(num):
        gid = -1  # номер ближайшей группы
        my = cy[i];  # центр добавляемого прямоугольника (oY)
        # найти ближайшие по Y значения
        left = bisect.bisect_left(gy, my - delta)
        right = bisect.bisect_right(gy, my + delta)
        # for j in range(len(g)): #для каждой незаблокированной группы (медленно, если перебирать без учета взаимного положения групп)
        for j in range(left, right):  # только в диапазоне
            if en[j] == False: continue
            if abs(gy[j] - my) <= delta:
                dx = abs(bbox[g[j][-1]][0] - bbox[i][0])  # расстояние по oX
                if dx > 3 * delta:  # элемент очень далеко, строку закрыть
                    # print("close",j,i,dx);
                    en[j] = False;
                    continue;
                gid = j;  # найдено пересечение
                break;
        if (gid >= 0):
            g[gid].append(i)  # элемент найден, добавить к текущей группе
            s = bbox[i][2]*bbox[i][3]
            if s>minsquare:
                gy[gid] = cy[i]  # просто установить последнее значение центра
            # поменять элементы, если новое значение gy[gid] нарушает отсортированность списка gy
            ngroup = len(g)
            k = gid;
            while (k > 0) and (gy[k - 1] > gy[k]):
                swapitem(gy, k, k - 1);
                swapitem(g, k, k - 1);
                swapitem(en, k, k - 1);
                --k
            while (k < (ngroup - 1)) and (gy[k + 1] < gy[k]):
                swapitem(gy, k, k + 1);
                swapitem(g, k, k + 1);
                swapitem(en, k, k + 1);
                ++k

        else:
            pos = bisect.bisect_left(gy, my)  # найти позицию вставки
            g.insert(pos, [i])
            gy.insert(pos, my)
            en.insert(pos, True)

    # Теперь есть маркировка группы для каждого элемента (упорядоченного по x)
    # поэтому можно отсортировать прямоугольники по группам
    # Для каждой группы, содержащей не менее 10 элементов
    # выполняем polyfit (и вычисляем угол наклона)
    # for g1 in g:
    #    print("group ",len(g1))
    a = [];
    ng = len(g)  # число групп

    for j in range(ng):
        x = [bbox[i][0] + bbox[i][2] / 2 for i in g[j]]  # х координаты элементов группы
        y = [bbox[i][1] + bbox[i][3] / 2 for i in g[j]]  # y координаты элементов группы
        # поиск вектора направления:
        # работает с точностью +-1 градус при наклоне до +-10 градусов
        if len(x) >= 8:  # только для длинных рядов (функция p = np.poly1d(коэффициенты np.polyfit(x,y,1)))
            p = np.polyfit(x, y, 1)
            a.append(p[0])  # угловой коэффициент
    angle = 0
    if len(a) > 0:
        # устанить грубые выбросы (t=isoutlier(a), angle=mean(a(~t)))
        elements = np.array(a)
        mean = np.mean(elements, axis=0)
        sd = np.std(elements, axis=0)
        a2 = [x for x in a if (x > mean - 2 * sd)]
        a2 = [x for x in a2 if (x < mean + 2 * sd)]
        print("outlier count =", len(a) - len(a2))
        angle = math.atan(np.mean(a2));  # среднее (с исключенными выбросами)
        print('angle= rad', angle, ' grad', 180 * angle / np.pi);
    return (g, angle)


def meanpoint(pts, indexes):
    # нахождение средней точки (x,y) для заданных элементов множества
    x = [pts[i][0] for i in indexes]
    y = [pts[i][1] for i in indexes]
    return np.mean(x), np.mean(y)


def dist2line(p1, p2, p3):  # расстояние от точки p3 до прямой (p1,p2)
    a1 = np.array(p1)
    a2 = np.array(p2)
    a3 = np.array(p3)
    d = np.linalg.norm(np.cross(a2 - a1, a1 - a3)) / np.linalg.norm(a2 - a1)
    return d


def rotatepoint(origin, point, theta):  # rotate x,y around xo,yo by theta (rad)
    xo, yo = origin
    x, y = point
    c = math.cos(theta)
    s = math.sin(theta)
    xr = c * (x - xo) - s * (y - yo) + xo
    yr = s * (x - xo) + c * (y - yo) + yo
    return [xr, yr]


def lineConnect(bbox, groups, angle, rotpoint=(0, 0)):
    delta = 26

    # вычислить центры прямоугольников
    cbox = [(b[0] + b[2] / 2, b[1] + b[3] / 2) for b in bbox]
    # повернуть центры точек на обратный угол относительно угла страницы
    # (можно было бы вращать относительно центра листа, а не его края, но это не важно)
    cbox = [rotatepoint(rotpoint, p, -angle) for p in cbox]

    # найти границы min max min max (центров прямоугольников)
    cx = [cb[0] for cb in cbox]
    cy = [cb[1] for cb in cbox]
    bounds = min(cx), max(cx), min(cy), max(cy)  # граничные значения

    # вычислить центры тяжести линий
    cline = [meanpoint(cbox, g) for g in groups]
    # отсортировать по X все структуры
    order = sorted(range(len(cline)), key=lambda k: cline[k][0])
    cline = [cline[i] for i in order]

    # найти номера тех групп, которые лежат на одной прямой
    g = []  # список номеров линий
    y = []  # список средних
    for i in range(len(cline)):
        gid = -1  # номер ближайшей группы
        for j in range(len(
                g)):  # для каждой незаблокированной группы (медленно, если перебирать без учета взаимного положения групп)
            if abs(y[j] - cline[i][1]) <= delta:  # найдено пересечение
                gid = j
                break
        if gid >= 0:
            g[gid].append(i)  # элемент найден, добавить к текущей группе
            y[gid] = cline[i][1]  # просто установить последнее значение центра
        else:
            g.append([i])  # добавить как отдельную линию
            y.append(cline[i][1])  # добавить значение
    # собрать прямоугольники групп в непрерывные списки

    longgroups = []
    for g1 in g:
        line = []
        for index in g1:
            line.extend(groups[order[index]])  # переместить все номера в новый список
        # отсортировать все примеры в группе по oX (редко, но бывают одиночные группы несортированные)
        byoX = sorted(range(len(line)), key=lambda k: bbox[line[k]][0])
        boxxsorted = [line[i] for i in byoX]
        longgroups.append(boxxsorted)  # добавить как отдельный

    # отсортировать длинные группы по оси Y (по центру первого прямоугольника)
    yline = [meanpoint(cbox, g) for g in longgroups]
    order = sorted(range(len(yline)),
                   key=lambda k: yline[k][1])  # нужны порядковые номера в k, а не значения longgroups
    longgroups = [longgroups[i] for i in order]

    return cbox, longgroups, angle, bounds


def rotateimregion(im, bbox, angle):  # получается попиксельное приближение
    """Поворот региона на изображении таким образом, чтобы он отобразился
    изображение размером bbox:(cx,cy,dx2,dy2).
    (dx,dy) определяют размер исходного изображения
    (cx,cy) определяют смещение изображения относительно начала координат
    Тогда исходный вращаемый регион имеет точки по углам (a,b,c,d) = rotate(bbox,angle)

    Зная точку результирующего изображения, можно вычислить точку на исходном изображении
    и взять ее в качестве соответствующей (можно брать окрестности, но накладнее)
    """
    im2 = np.zeros([bbox[3], bbox[2]], 'u1')

    height, width = im.shape[0], im.shape[1]
    height2, width2 = im2.shape[0], im2.shape[1]
    c = (bbox[0], bbox[1])
    for y2 in range(height2):
        for x2 in range(width2):
            x, y = rotatepoint((width / 2, height / 2), (x2 + c[0], y2 + c[1]),
                               angle)  # обратное вращение для вычисления исходной позицию точки
            x, y = int(x), int(y)
            # если значения меньше 0, то придется брать 0 (не должны получатся, если есть отступы от края)
            if x < 0 or x >= width:  print("error bound x"); return None
            if y < 0 or y >= height: print("error bound y"); return None
            im2[y2, x2] = im[y, x]
    return im2


# ПОКА МЕДЛЕННО, Т.К, КОД НА PYTHON
def rotateimregion4pt(im, bbox, angle):
    # четырехточечный метод позволяет каждую точку приблизить 4мя соседними
    # (из 9 возможных, в зависимости от того в какой квадратнт попадает восстановленный центр точки >0.5, <0.5)

    # return rotateimregion(im,bbox,angle)
    im2 = np.zeros([bbox[3], bbox[2]], 'u1')

    height, width = im.shape[0], im.shape[1]
    height2, width2 = im2.shape[0], im2.shape[1]
    sh = (bbox[0], bbox[1])
    mcos = math.cos(angle);
    msin = math.sin(angle)
    xo, yo = width / 2 - 0.5, height / 2 - 0.5  # и сдвинуть координату от края на 0.5 пикселя
    for y2 in range(height2):
        for x2 in range(width2):
            # xr,yr=rotatepoint((width/2,height/2),(x2+sh[0]+0.5,y2+sh[1]+0.5),angle) #обратное вращение для вычисления исходной позицию точки
            # можно вычислить координаты одной линии и использовать их для получения всех следующих координат с исп. шага приращения
            # (+mcos,+msin); (+msin,+mcos)
            dx, dy = x2 + sh[0] - xo, y2 + sh[1] - yo
            x = mcos * dx - msin * dy + xo
            y = msin * dx + mcos * dy + yo
            # найти остаток до 1
            xright = x - math.floor(x)
            xleft = 1.0 - xright
            ybot = y - math.floor(y)
            ytop = 1.0 - ybot
            s = (xleft * ytop, xright * ytop, xleft * ybot, xright * ybot)  # площади
            x, y = int(x), int(y)  # целочисленные координаты
            im2[y2, x2] = int(im[y, x] * s[0] + im[y, x + 1] * s[1] + im[y + 1, x] * s[2] + im[y + 1, x + 1] * s[
                3])  # вычислить пропорциональный цвет
            # (предполагается, что значения x,y не выходят за границы исходного изображения)
    return im2

def scaleimage(im, from_dpi, to_dpi):
    h,w = im.shape
    h2,w2 = int(h*to_dpi/from_dpi), int(w*to_dpi/from_dpi)
    return cv2.resize(im, dsize=(w2, h2), interpolation=cv2.INTER_CUBIC)


def rotateimage(im, angle):  # поворот изображения на заданный угол (в градусах)
    from scipy import ndimage
    return ndimage.rotate(im, angle)


# def rotateImage(image, angle):
#  image_center = tuple(np.array(image.shape[1::-1]) / 2)
#  rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
#  result = cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)
#  return result

def loadImage(name, dpifrom, dpito):
    im = matplotlib.image.imread(name)  # цветное изображение (3 плоскости цвета)
    if len(im.shape)==3:    im = rgb2gray(im)  # преобразовать цветное к серому
    elif len(im.shape)==2:  pass #ничего не делать
    if (dpifrom!=dpito): im = scaleimage(im, dpifrom, dpito)
    return im


def alignAndCropImage(im, mingrad=1): #name, dpifrom, dpito
    """
    Определение ориентации листа по линиям, первичная разметка
    Вырезание области с текстом и возвращение вырезанного изображения
    im      - изображение в формате grayscale
    mingrad - минимальный угол, при котором изображение считается уже выровненным
    """
    # бинаризация (0,1) и выделения объединенных точек
    threshold, im2 = cv2.threshold(im, 0, 255, cv2.THRESH_OTSU)  # сразу и бинаризует, но можно перевычислить

    threshold = 1.1 * threshold  # лучше чуть больше (не теряются линии E)
    _, im2 = cv2.threshold(im, threshold, 255, cv2.THRESH_TRUNC)  # бинаризовать по новому порогу
    print("threshold", threshold)

    # удалить все объекты, содержащие меньше 20 (30) пикселей (можно отфильтровать малые объекты в bwlabel)
    im3 = bwareaopen(im2, 30)  # получаем бинарное изображение без артефактов малого размера

    (bbox, num, imoverlay, _) = bwlabel(im3)  # P - получаем список всех объектов больше заданного размера
    bbox = sorted(bbox, key=operator.itemgetter(0))  # пересортировать по X, а не по Y
    (groups, angle) = lineLetters(bbox)  # найти направляющие букв
    print("len(bbox)",len(bbox))

    # (можно не объединять по линиям)
    width, height = im3.shape[1], im3.shape[0]
    center = (width / 2, height / 2)
    (cbox, lines, angle, bnd) = lineConnect(bbox, groups, angle, center)  # объединить в длинные линии после поворота

    grad = 180 * angle / np.pi  # перевести в градусы
    if abs(mingrad) <= abs(grad):  # нужно вращать
        print("rotate image", grad)
        imrotated = rotateimage(im, grad)  # rotateimage(im4,grad)
    else:
        imrotated = im

    dy = (imrotated.shape[0] - im3.shape[0]) / 2
    dx = (imrotated.shape[1] - im3.shape[1]) / 2
    minx, maxx, miny, maxy = bnd #возвращает область, занимаемую символами (нужно проверить выходит ли за границу)
    print("minx, maxx, miny, maxy",minx, maxx, miny, maxy)

    h,w = imrotated.shape
    delta = 26 #средний размер символа (нужно задавать)
    top = int(miny - delta + dy)
    bottom = int(dy + maxy + delta)
    left = int(minx - delta + dx)
    right = int(dx + maxx + delta)
    if top<0: top=0
    if bottom>h: bottom=h
    if left<0: left=0
    if right>w: right=w

    imcrop = imrotated[top:bottom, left:right]

    #plt.figure()
    #plt.imshow(imcrop, cmap='gray', vmin=0, vmax=255)  # отобразить серое изображение
    print("imcrop.shape", imcrop.shape)
    return imcrop, angle


def segmentateImage(im, isExtended):
    """
    Сегментация изображения и выделение областей с текстом
    (предварительно изображение должно быть повернуто, а область текста вырезана)
    """
    threshold, im2 = cv2.threshold(im, 0, 255, cv2.THRESH_OTSU)  # сразу и бинаризует, но можно перевычислить
    threshold = 1.1 * threshold  # лучше чуть больше (не теряются линии E)
    _, im2 = cv2.threshold(im, threshold, 255, cv2.THRESH_BINARY)  # бинаризовать по новому порогу
    # удалить все объекты, содержащие меньше 20 (30) пикселей
    im3 = bwareaopen(im2, 30)  # получаем бинарное изображение без артефактов
    # (можно отфильтровать малые объекты в bwlabel)
    # определить области объектов

    (bbox, num, imoverlay, mask) = bwlabel(im3)  #  - получаем список всех объектов больше заданного размера
    if isExtended:
        coords = save_coordsExtended(mask, im) # сохраняем координаты букв c обводкой
    else:
        coords = save_coords(mask, im)  # сохраняем координаты букв без обводки
    coords = [x for _,x in sorted(zip(bbox,coords),key=operator.itemgetter(0))]
    # нужно пересортировать по X, а не по Y
    bbox = sorted(bbox, key=operator.itemgetter(0))
    (groups, angle) = lineLetters(bbox)  # найти направляющие букв
    center = (im3.shape[1] / 2, im3.shape[0] / 2)
    (cbox, lines, angle, bnd) = lineConnect(bbox, groups, angle, center)  # объединить в длинные линии после поворота

    #plt.show()

    return bbox, lines, coords


# сохранение для каждой буквы всех координат в словарь
def save_coordsExtended(mask, img):
    print("UNSUPPORTED!!!")
    return []
    # coords = [] #готовый массив с координатыми букв в виде shift
    # num = 0
    # height = img.shape[0]
    # width = img.shape[1]
    #
    # for region in skimage.measure.regionprops(mask): #рассматриваем каждую непрерывную линию
    #     full = [] # массив для каждой буквы отдельно без shift
    #     lcoords = region.coords
    #     for axes in lcoords: # рассматриваем координаты каждой непрервыной линии
    #         x = axes[0]
    #         y = axes[1]
    #         full.append((x, y))
    #         x -= 1
    #         y -= 1
    #         while 0 <= x < height-1 and 0 <= y < width-1 and img[x, y] > img[x + 1, y + 1] and \
    #         img[x, y] < img[axes[0], axes[1]] * 3: #расширяем координаты в нескольких направлениях
    #             full.append((x, y))
    #             x -= 1
    #             y -= 1
    #         x = axes[0]
    #         y = axes[1]
    #         while 0 <= x < height-1 and img[x, y] > img[x + 1, y] and img[x, y] < img[axes[0], axes[1]] * 3:
    #             full.append((x, y))
    #             x -= 1
    #         x = axes[0]
    #         y = axes[1]
    #         while 0 <= y < width-1 and img[x, y] > img[x, y + 1] and img[x, y] < img[axes[0], axes[1]] * 3:
    #             full.append((x, y))
    #             y -= 1
    #         x = axes[0] + 1
    #         y = axes[1] + 1
    #         while x < height and y < width and img[x, y] > img[x - 1, y - 1] and img[x, y] < img[axes[0], axes[1]] * 3:
    #             full.append((x, y))
    #             x += 1
    #             y += 1
    #         x = axes[0] + 1
    #         y = axes[1]
    #         while x < height and img[x, y] > img[x - 1, y] and img[x, y] < img[axes[0], axes[1]] * 3:
    #             full.append((x, y))
    #             x += 1
    #         x = axes[0]
    #         y = axes[1] + 1
    #         while y < width and img[x, y] > img[x, y - 1] and img[x, y] < img[axes[0], axes[1]] * 3:
    #             full.append((x, y))
    #             y += 1
    #     coords.append(create_contour(full, img, num))
    #     num += 1
    #
    # return coords


# сохранение для каждой буквы всех координат в словарь
def save_coords(mask, img):
    coords = [] #готовый массив с координатыми букв в виде shift
    num = 0

    for region in skimage.measure.regionprops(mask):
        coords.append(create_contour(region.coords, region.bbox, img, num))
        num += 1
    return coords


#создание объекта контура
def create_contour(ar, box, im, num):
    width = box[3] - box[1]+1   #x (длина должна включать точку)
    height= box[2] - box[0]+1   #y
    minx = box[1]   #x
    miny = box[0]   #y

    #закодировать точки
    points = []
    for pt in ar:
        dx=pt[1]-minx
        dy=pt[0]-miny
        points.append((dy*width+dx,im[pt[0],pt[1]])) #(сдвиг, цвет)
    return CoordsObj.Coords(minx, miny, width, height, points, num, len(points))


def saveImage(name, im):
    matplotlib.image.imsave(name, im, cmap='gray')  # сохранить обработанную копию

#def preProcessImage(name):  # обработка изображения
    #im, angle = alignAndCropImage(name)  # повернуть страницу и выделить область текста
    #matplotlib.image.imsave(name+'.jpg',im,cmap='gray')
    #bbox, lines = segmentateImage(name + '.jpg')  # выделить прямоугольники (в производном изображении)
    #saveBoxLines(name + ".jpg.bb", bbox, lines)  # сохранить разметку и линии
    #showBoxLetters(name+".jpg") #показать ограничивающие прямоугольники после чтения файла bb
    #testTfParser(name + ".jpg")  # наложить текст .txt с управляющими символами на разметку .bb
    #return im,angle,bbox,lines


#preProcessImage('./00010004r10.jpg')
