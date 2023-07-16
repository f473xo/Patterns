from framework.api import API
from patterns.architectural_system_pattern_unit_of_work import UnitOfWork
from patterns.behavioral_patterns import (
    EmailNotifier,
    SmsNotifier,
    ListView,
    CreateView, BaseSerializer
)
from patterns.structural_patterns import Debug
from patterns.сreational_patterns import Engine, Logger, MapperRegistry

app = API()
site = Engine()
logger = Logger('main')
email_notifier = EmailNotifier()
sms_notifier = SmsNotifier()
UnitOfWork.new_current()
UnitOfWork.get_current().set_mapper_registry(MapperRegistry)


# Main page

@app.route("/")
class Index(ListView):
    queryset = site.root_categories
    template_name = 'index.html'


# Category

@app.route("/create-category/")
class CreateCategory:

    @staticmethod
    def get(request, response):
        response.text = app.template('create_category.html')

    @staticmethod
    @Debug(name='Create Category')
    def post(request, response):
        parent = None
        cat_id = request.params.get('id')
        if cat_id:
            parent = site.find_category_by_id(int(cat_id))
        name = request.params['name']
        new_category = site.create_category(name, parent=parent)
        logger.log(f'Создана категория "{new_category.name}"')
        response.text = app.template('category_list.html',
                                     context={
                                         'objects_list': site.root_categories,
                                         'id': cat_id
                                     })


@app.route('/category-list/')
class CategoryList:
    @staticmethod
    def get(request, response):
        categories = site.get_category_tree(with_courses=True)
        count_courses = site.count_courses
        render_category = site.render_category
        response.text = app.template('category_list.html',
                                     context={
                                         'categories': categories,
                                         'count_courses': count_courses,
                                         'render_category': render_category,
                                     })


# Courses


@app.route("/create-course/")
class CreateCourse:

    @staticmethod
    def get(request, response):
        cat = site.find_category_by_id(int(request.params['id']))
        response.text = app.template('create_course.html',
                                     context={
                                         'id': cat.id,
                                         'name': cat.name
                                     })

    @staticmethod
    @Debug(name='Create Course')
    def post(request, response):
        name = request.params['name']
        cat = site.find_category_by_id(int(request.params['id']))
        course = site.create_course('record', name, cat)
        # Добавляем наблюдателей на курс
        course.observers.append(email_notifier)
        course.observers.append(sms_notifier)

        site.courses.append(course)

        response.text = app.template('course_list.html',
                                     context={
                                         'id': cat.id,
                                         'name': cat.name,
                                         'objects_list': cat.courses
                                     })


@app.route("/courses-list/")
class CoursesList:
    @staticmethod
    def get(request, response):
        cat = site.find_category_by_id(int(request.params['id']))
        response.text = app.template('course_list.html',
                                     context={
                                         'id': cat.id,
                                         'name': cat.name,
                                         'objects_list': cat.courses
                                     })


@app.route(("/copy-course/"))
class CopyCourse:

    @staticmethod
    def get(request, response):
        name = site.get_course(request.params['name'])
        old_course = name
        cat = None
        if old_course:
            new_name = f'copy_{old_course.name}'
            new_course = old_course.clone()
            new_course.name = new_name
            site.courses.append(new_course)
            cat = site.find_category_by_id(new_course.category.id)
            cat.courses.append(new_course)
            logger.log(f'Создана копия курса "{old_course.name}"')
        response.text = app.template('course_list.html',
                                     context={
                                         'id': cat.id,
                                         'name': cat.name,
                                         'objects_list': cat.courses
                                     })


@app.route("/student-list/")
class StudentListView(ListView):
    template_name = 'student_list.html'

    def get_queryset(self):
        mapper = MapperRegistry.get_current_mapper('student')
        return mapper.all()


@app.route("/create-student/")
class StudentCreateView(CreateView):
    template_name = 'create_student.html'

    def create_obj(self, request):
        name = request.params.get('name')
        new_obj = site.create_user('student', name)
        site.students.append(new_obj)
        new_obj.mark_new()
        UnitOfWork.get_current().commit()

    def get_context_data(self):
        return {'objects_list': site.students}

    def post(self, request, response):
        self.create_obj(request)
        self.template_name = 'student_list.html'
        response.text = self.template(self.template_name)


@app.route("/add-student/")
class AddStudentByCourseCreateView(CreateView):
    template_name = 'add_student.html'

    def get_context_data(self):
        context = super().get_context_data()
        context['courses'] = site.courses
        context['students'] = site.students
        return context

    def create_obj(self, request):
        course_name = request.params['course_name']
        course = site.get_course(course_name)
        student_name = request.params['student_name']
        student = site.get_student(student_name)
        course.add_student(student)

    def post(self, request, response):
        self.create_obj(request)
        response.text = self.template(self.template_name)


@app.route("/api/")
class CourseApi:
    @Debug(name='CourseApi')
    def __call__(self, request):
        return '200 OK', BaseSerializer(site.courses).save()


# About

@app.route("/about/")
class About:

    @staticmethod
    def get(request, response):
        response.text = app.template('about.html')


# Contacts

@app.route("/contacts/")
class Contacts:

    @staticmethod
    def get(request, response):
        response.text = app.template('contacts.html')

    @staticmethod
    def post(request, response):
        response.text = app.template('contacts-resp.html',
                                     context={'data': request.params})
