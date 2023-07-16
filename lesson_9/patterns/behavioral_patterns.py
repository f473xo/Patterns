import os.path

from jsonpickle import dumps, loads

from framework.templates import get_templates_env


# поведенческий паттерн - наблюдатель
# Курс
class Observer:

    def update(self, subject):
        pass


class Subject:

    def __init__(self):
        self.observers = []

    def notify(self):
        for item in self.observers:
            item.update(self)


class SmsNotifier(Observer):

    def update(self, subject):
        print('SMS->', 'к нам присоединился', subject.students[-1].name)


class EmailNotifier(Observer):

    def update(self, subject):
        print('EMAIL->', 'к нам присоединился', subject.students[-1].name)


class BaseSerializer:

    def __init__(self, obj):
        self.obj = obj

    def save(self):
        return dumps(self.obj)

    @staticmethod
    def load(data):
        return loads(data)


# поведенческий паттерн - Шаблонный метод
class TemplateView:
    template_name = 'template.html'

    def __init__(self, templates_dir="templates"):
        self.templates = get_templates_env(os.path.abspath(templates_dir))

    def get_context_data(self):
        return {}

    def template(self, name):
        context = self.get_context_data()
        return self.templates.get_template(name).render(**context)

    def get(self, request, response):
        response.text = self.template(self.template_name)

    def post(self, request, response):
        response.text = self.template(self.template_name)


class ListView(TemplateView):
    queryset = []
    template_name = 'list.html'
    context_object_name = 'objects_list'

    def get_queryset(self):
        return self.queryset

    def get_context_object_name(self):
        return self.context_object_name

    def get_context_data(self):
        queryset = self.get_queryset()
        context_object_name = self.get_context_object_name()
        context = {context_object_name: queryset}
        return context


class CreateView(TemplateView):
    template_name = 'create.html'

    def create_obj(self, request):
        pass


# поведенческий паттерн - Стратегия
class ConsoleWriter:

    @staticmethod
    def write(text):
        print(text)


class FileWriter:

    def __init__(self):
        self.file_name = 'log'

    def write(self, text):
        with open(self.file_name, 'a', encoding='utf-8') as f:
            f.write(f'{text}\n')
