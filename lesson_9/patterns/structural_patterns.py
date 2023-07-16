from functools import wraps
from time import time


# структурный паттерн - Декоратор
class Debug:

    def __init__(self, name):
        self.name = name

    def __call__(self, cls):
        '''
        сам декоратор
        '''

        # это вспомогательная функция будет декорировать каждый отдельный метод класса, см. ниже
        @wraps
        def timeit(method):
            '''
            нужен для того, чтобы декоратор класса wrapper обернул в timeit
            каждый метод декорируемого класса
            '''

            def timed(*args, **kwargs):
                ts = time()
                result = method(*args, **kwargs)
                te = time()
                delta = te - ts

                print(f'debug --> {cls.__name__} выполнялся {delta:2.2f} ms')
                return result

            return timed

        return timeit(cls)
