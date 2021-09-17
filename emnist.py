import cv2
import numpy as np
import struct


# 62 символа в базе EMNIST
# В базе EMNIST метка - это порядковый номер символа в алфавите
alphabet = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
             'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V',
              'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g',
               'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r',
                's', 't', 'u', 'v', 'w', 'x', 'y', 'z']


# Типы данных и число байт
# формата IDX
DATA_TYPES_IDX = {
    0x08: ('ubyte', 1),
    0x09: ('byte', 1),
    0x0B: ('>i2', 2),
    0x0C: ('>i4', 4),
    0x0D: ('>f4', 4),
    0x0E: ('>f8', 8)
}


# IDX-формат базы emnist:
# magic number (as 4 bytes)
# size in dimension 1 (as int = 4 bytes)
# size in dimension 2 (as int = 4 bytes)
# size in dimension 3 (as int = 4 bytes)
# . . .
# size in dimension N (as int = 4 bytes)
# data

# The IDX file format is a simple format
# for vectors and multidimensional matrices
# of various numerical types

# Первые два байта - нули
# Третий байт кодирует тип данных:
# 0x08: unsigned byte
# 0x09: signed byte
# 0x0B: short (2 bytes)
# 0x0C: int (4 bytes)
# 0x0D: float (4 bytes)
# 0x0E: double (8 bytes)
# Четвертый байт кодирует размерность
# (Для 60000 чб картинок из 28×28 пикселей
# размерность равна 3 )
# Следующие 4 байта - размер размерности 1
# Следующие 4 байта - размер размерности 2 и так для каждой
# размерности
# Следом идут данные в формате
def readidx(fname):
    f = open(fname, 'rb')
    magic = struct.unpack('>BBBB', f.read(4))
    # Тип данных
    dt = magic[2]
    # Размерность
    dd = magic[3]
    dims = struct.unpack('>' + 'I' * dd, f.read(4 * dd))
    sz = 1
    for i in range(len(dims)):
        sz = sz * dims[i]
    # Данные
    dtype, dbytes = DATA_TYPES_IDX[dt]
    data = np.frombuffer(f.read(sz * dbytes), dtype=np.dtype(dtype)).reshape(dims)
    f.close()
    return data


# Загрузить базу EMNIST
# imgfile - путь к файлу образцов символов
# lblfile - путь к файлу меток символов
# Если задан список символов, то считываются только
# символы в списке
def loademnist(imgfile, lblfile, letters=None):
    images = readidx(imgfile)
    labels = readidx(lblfile)
    print("Load EMNIST %s images" % len(images))
    if letters is None:
        return images, labels
    li = []
    d = {alphabet[i]:i for i in range(len(alphabet))}
    for l in letters:
        # Находим метку (порядковый номер)
        label = d[l] if l in d else []
        indices = np.nonzero((labels==label))[0]
        if len(indices) == 0:
            raise Exception("Can't find letter: {}".format(l)) 
        li.append(indices)
    imgs = np.vstack(([images[indices] for indices in li]))
    lbls = np.hstack([[i] * len(li[i]) for i in range(len(li))])
    return imgs, lbls

        


# Показать образцы символов в базе EMNIST
def showimages(images, labels, letters):
    for i in range(len(images)):
        # Транспонируем
        cv2.imshow(winname='Image letter',mat=images[i].T)
        print('Image letter {}:{}'.format(i, letters[labels[i]]))
        cv2.waitKey()


# Вывести число примеров каждого символа
def letterscount(images, labels, letters):
    ulbl = np.unique(labels)
    if len(ulbl) != len(letters):
        raise Exception("No match letters")
    counts = []
    for ul in ulbl:
        indices = np.nonzero(labels == ul)[0]
        cnt = len(indices)
        print('Letter {}={}'.format(letters[ul], cnt))
        counts.append(cnt)
    imin = np.argmin(counts)
    imax = np.argmax(counts)
    print('Min letter {}={}'.format(letters[imin], counts[imin]))
    print('Max letter {}={}'.format(letters[imax], counts[imax]))
    return counts


# # Вывести число примеров для каждого символа
# # Файл с образцами
# imgfile = './emnist/emnist-byclass-train-images-idx3-ubyte'
# # Файл с метками
# lblfile = './emnist/emnist-byclass-train-labels-idx1-ubyte'
# # letters = alphabet
# letters = ['A','B']
# images, labels = loademnist(imgfile, lblfile, letters)
# counts = letterscount(images, labels, letters)
# showimages(images, labels, letters)