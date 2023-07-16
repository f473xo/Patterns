import os.path
import urllib.parse

from requests import Session as RequestsSession
from webob import Request, Response
from wsgiadapter import WSGIAdapter as RequestsWSGIAdapter

from framework.error_handlers import debug_exception_handler
from framework.exceptions import HTTPError
from framework.route import Route
from framework.templates import get_templates_env


def prepare_path(path):
    # декодирование url с кириллицей
    path = urllib.parse.unquote(path)
    # добавление закрывающего слеша
    return path if path.endswith('/') else f'{path}/'


class API:

    def __init__(self, templates_dir='templates', debug=True):
        self.templates = get_templates_env(os.path.abspath(templates_dir))
        self._routes = {}
        self._exception_handler = None
        self._debug = debug

        # cached requests session
        self._session = None

    @property
    def debug(self):
        return self._debug

    def __call__(self, environ, start_response):
        path_info = environ["PATH_INFO"]

        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def route(self, pattern, methods=None):
        """Декоратор, добавляющий новый маршрут"""

        def wrapper(handler):
            self.add_route(pattern, handler, methods)
            return handler

        return wrapper

    def add_route(self, pattern, handler, methods=None):
        """Добавляет новый маршрут"""
        assert pattern not in self._routes, "Такой маршрут уже существует"

        self._routes[pattern] = Route(path_pattern=pattern, handler=handler, methods=methods)

    def add_exception_handler(self, handler):
        self._exception_handler = handler

    def _handle_exception(self, request, response, exception):
        if self._exception_handler is not None:
            self._exception_handler(request, response, exception)
        else:
            if self._debug is False:
                raise exception

            debug_exception_handler(request, response, exception)

    def template(self, name, context=None):
        if context is None:
            context = {}
        return self.templates.get_template(name).render(**context)

    def dispatch_request(self, request):
        response = Response()

        route, kwargs = self.find_route(path=request.path)

        try:
            if route is None:
                raise HTTPError(status=404)

            route.handle_request(request, response, **kwargs)
        except Exception as e:
            self._handle_exception(request, response, e)

        return response

    def find_route(self, path):
        for pattern, route in self._routes.items():
            matched, kwargs = route.match(request_path=path)
            if matched is True:
                return route, kwargs

        return None, {}

    def session(self, base_url="http://testserver"):
        """Cached Testing HTTP client based on Requests by Kenneth Reitz."""
        if self._session is None:
            session = RequestsSession()
            session.mount(base_url, RequestsWSGIAdapter(self))
            self._session = session
        return self._session


class BaseApplication(API):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)


class DebugApplication(BaseApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, environ, start_response):
        print('DEBUG MODE')
        print(environ)
        return super().__call__(environ, start_response)


class FakeApplication(BaseApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [b'Hello from Fake']
