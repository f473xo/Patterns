import quopri
from copy import deepcopy
from sqlite3 import connect

# абстрактный пользователь
from patterns.architectural_system_pattern_unit_of_work import DomainObject
from patterns.behavioral_patterns import Subject


class User:
    def __init__(self, name):
        self.name = name


# преподаватель
class Teacher(User):
    pass


# студент
class Student(User, DomainObject):

    def __init__(self, name):
        self.courses = []
        super().__init__(name)


# порождающий паттерн Абстрактная фабрика - фабрика пользователей
class UserFactory:
    types = {
        'student': Student,
        'teacher': Teacher
    }

    # порождающий паттерн Фабричный метод
    @classmethod
    def create(cls, type_, name):
        return cls.types[type_](name)


# порождающий паттерн Прототип - Курс
class CoursePrototype:
    # прототип курсов обучения

    def clone(self):
        return deepcopy(self)


class Course(CoursePrototype, Subject):

    def __init__(self, name, category):
        self.name = name
        self.category = category
        self.category.courses.append(self)
        self.students = []
        super().__init__()

    def __getitem__(self, item):
        return self.students[item]

    def add_student(self, student: Student):
        self.students.append(student)
        student.courses.append(self)
        self.notify()


# интерактивный курс
class InteractiveCourse(Course):
    pass


# курс в записи
class RecordCourse(Course):
    pass


class CourseFactory:
    types = {
        'interactive': InteractiveCourse,
        'record': RecordCourse
    }

    # порождающий паттерн Фабричный метод
    @classmethod
    def create(cls, type_, name, category):
        return cls.types[type_](name, category)


# категория
class Category:
    auto_id = 0

    def __init__(self, name, parent=None):
        self.id = Category.auto_id
        Category.auto_id += 1
        self.name = name
        self.parent = parent
        self.children = []
        self.courses = []

        if parent is not None:
            parent.add_child(self)

    def add_child(self, child):
        self.children.append(child)

    def course_count(self):
        count = len(self.courses)
        for child in self.children:
            count += child.course_count()
        return count


# основной интерфейс проекта
class Engine:
    def __init__(self):
        self.teachers = []
        self.students = []
        self.courses = []
        self.root_categories = []

    @staticmethod
    def create_user(type_, name):
        return UserFactory.create(type_, name)

    def create_category(self, name, parent=None):
        category = Category(name, parent)
        if parent is None:
            self.root_categories.append(category)
        return category

    def find_category_by_id(self, id):
        for root in self.root_categories:
            category = self._find_category_by_id(id, root)
            if category is not None:
                return category
        raise Exception(f'Нет категории с id = {id}')

    def _find_category_by_id(self, id, category):
        if category.id == int(id):
            return category

        for child in category.children:
            subcategory = self._find_category_by_id(id, child)
            if subcategory is not None:
                return subcategory

        return None

    @staticmethod
    def create_course(type_, name, category):
        return CourseFactory.create(type_, name, category)

    def get_course(self, name):
        for item in self.courses:
            if item.name == name:
                return item
        return None

    def get_student(self, name) -> Student:
        for item in self.students:
            if item.name == name:
                return item

    def add_category(self, category):
        self.root_categories.append(category)

    def add_course(self, course):
        self.courses.append(course)

    def get_category_tree(self, category=None, with_courses=False):
        if category is None:
            categories = self.root_categories
        else:
            categories = category.children

        category_list = []
        for cat in categories:
            cat_info = {'name': cat.name, 'id': cat.id}

            if with_courses and cat.courses:
                cat_info['courses'] = [course.name for course in cat.courses]

            subcategories = self.get_category_tree(cat, with_courses)
            if subcategories:
                cat_info['subcategories'] = subcategories

            category_list.append(cat_info)

        return category_list

    def count_courses(self, category):
        count = len(category.get('courses', []))
        for subcategory in category.get('subcategories', []):
            count += self.count_courses(subcategory)
        return count

    def render_category(self, category):
        course_count = self.count_courses(category)
        subcategories = category.get('subcategories', [])
        courses = category.get('courses', [])
        category_id = category.get('id')
        category_name = category.get('name')

        html = f'<li>{category_name} <span>Количество курсов: {course_count}</span>'
        html += f'<a class="section_creation" href="/create-category/?id={category_id}">Создать субкатегорию</a>&nbsp;'
        html += f'<a class="section_creation" href="/create-course/?id={category_id}">Создать новый курс</a>'
        if courses:
            html += '<ul>'
            for course in courses:
                html += f'<li>{course}</li>'
            html += '</ul>'
        if subcategories:
            html += '<ul>'
            for subcategory in subcategories:
                html += self.render_category(subcategory)
            html += '</ul>'
        html += '</li>'

        return html

    @staticmethod
    def decode_value(data):
        new_data = {}
        for k, v in data.items():
            val = bytes(v.replace('%', '=').replace("+", " "), 'UTF-8')
            val_decode_str = quopri.decodestring(val).decode('UTF-8')
            new_data[k] = val_decode_str
        return new_data


# порождающий паттерн Синглтон
class SingletonByName(type):

    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls.__instance = {}

    def __call__(cls, *args, **kwargs):
        if args:
            name = args[0]
        if kwargs:
            name = kwargs['name']

        if name in cls.__instance:
            return cls.__instance[name]
        else:
            cls.__instance[name] = super().__call__(*args, **kwargs)
            return cls.__instance[name]


class Logger(metaclass=SingletonByName):

    def __init__(self, name):
        self.name = name

    @staticmethod
    def log(text):
        print('log--->', text)


class StudentMapper:

    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()
        self.tablename = 'student'

    def all(self):
        statement = f'SELECT * from {self.tablename}'
        self.cursor.execute(statement)
        result = []
        for item in self.cursor.fetchall():
            id, name = item
            student = Student(name)
            student.id = id
            result.append(student)
        return result

    def find_by_id(self, id):
        statement = f"SELECT id, name FROM {self.tablename} WHERE id=?"
        self.cursor.execute(statement, (id,))
        result = self.cursor.fetchone()
        if result:
            return Student(*result)
        else:
            raise RecordNotFoundException(f'record with id={id} not found')

    def insert(self, obj):
        statement = f"INSERT INTO {self.tablename} (name) VALUES (?)"
        self.cursor.execute(statement, (obj.name,))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbCommitException(e.args)

    def update(self, obj):
        statement = f"UPDATE {self.tablename} SET name=? WHERE id=?"

        self.cursor.execute(statement, (obj.name, obj.id))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbUpdateException(e.args)

    def delete(self, obj):
        statement = f"DELETE FROM {self.tablename} WHERE id=?"
        self.cursor.execute(statement, (obj.id,))
        try:
            self.connection.commit()
        except Exception as e:
            raise DbDeleteException(e.args)


connection = connect('patterns.sqlite')


# архитектурный системный паттерн - Data Mapper
class MapperRegistry:
    mappers = {
        'student': StudentMapper,
        # 'category': CategoryMapper
    }

    @staticmethod
    def get_mapper(obj):
        if isinstance(obj, Student):
            return StudentMapper(connection)

    @staticmethod
    def get_current_mapper(name):
        return MapperRegistry.mappers[name](connection)


class DbCommitException(Exception):
    def __init__(self, message):
        super().__init__(f'Db commit error: {message}')


class DbUpdateException(Exception):
    def __init__(self, message):
        super().__init__(f'Db update error: {message}')


class DbDeleteException(Exception):
    def __init__(self, message):
        super().__init__(f'Db delete error: {message}')


class RecordNotFoundException(Exception):
    def __init__(self, message):
        super().__init__(f'Record not found: {message}')
