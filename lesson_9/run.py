from wsgiref.simple_server import make_server

import views
from framework.variables import PORT

app = views.app

if __name__ == '__main__':
    # для отладки
    with make_server('', PORT, app) as httpd:
        print(f"Запуск на порту {PORT}...")
        httpd.serve_forever()
