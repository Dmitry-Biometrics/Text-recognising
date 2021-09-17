import numpy as np
import os


# Force CPU
os.environ["CUDA_VISIBLE_DEVICES"]="0" #UPD "-1"
# INFO, WARNING, and ERROR messages are not printed
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

#NUM_PARALLEL_EXEC_UNITS = 4
#os.environ['OMP_NUM_THREADS'] = str(NUM_PARALLEL_EXEC_UNITS)
#os.environ["KMP_AFFINITY"] = "granularity=fine,verbose,compact,1,0"
#os.environ["KMP_AFFINITY"] = "verbose" # no affinity
#os.environ["KMP_AFFINITY"] = "none" # no affinity
os.environ["KMP_AFFINITY"] = "disabled" # completely disable thread pools

# Алфавит на котором обучена сеть
NET_LETTERS = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ж', 'З', 'И', 'Й', 'К', 'Л',
        'М', 'Н', 'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф',
        'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь', 'Э', 'Ю', 'Я']

# Класс предсказания символов
class LetPredictor(object):

    def __init__(self):
        self.model = None

    def alphabet(self):
        return NET_LETTERS

    # Подготовить данные
    def preparedata(self, x):
        nx = np.reshape(x, newshape=(x.shape[0], 28, 28, 1))
        nx = 255 - nx
        nx = nx.astype(np.float32)
        nx /= 255.0
        return nx

    # Предсказание каждого класса
    def predict(self, x):
        if self.model is None:
            return [] 
        px = self.preparedata(x)
        outs = self.model.predict(px)
        return outs

    # Загрузить обученную сеть
    def load(self, fname):
        self.model = None