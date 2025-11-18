from flask import Blueprint, render_template, request, url_for, redirect, flash
from app.extensions import db
from app.models import Course, Lesson, News, Contact  # используем свои модели
from app.forms import ContactForm
import os
from flask import current_app, request, flash, redirect, url_for, render_template, send_from_directory, abort
from flask_login import login_required, current_user
from app.forms import FileUploadForm
from app.extensions import db
from app.models import File
from app.utils import save_uploaded_file


main_bp = Blueprint("main", __name__)

# Home
@main_bp.route("/")
def index():
    breadcrumbs = []
    return render_template("home.html", breadcrumbs=breadcrumbs)

# About
@main_bp.route("/about")
def about():
    breadcrumbs = [("About", url_for("main.about"))]
    return render_template("about.html", breadcrumbs=breadcrumbs)

# Courses list with simple pagination
@main_bp.route("/courses")
def courses():
    page = request.args.get("page", 1, type=int)
    per_page = 6
    pagination = Course.query.order_by(Course.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    breadcrumbs = [("Courses", url_for("main.courses"))]
    return render_template("courses.html", pagination=pagination, breadcrumbs=breadcrumbs)

# Course detail
@main_bp.route("/courses/<int:course_id>")
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    breadcrumbs = [("Courses", url_for("main.courses")), (course.title, None)]
    return render_template("course_detail.html", course=course, breadcrumbs=breadcrumbs)

# Lessons list (optionally per course)
@main_bp.route("/lessons")
def lessons():
    breadcrumbs = [("Lessons", url_for("main.lessons"))]
    lessons = Lesson.query.order_by(Lesson.created_at.desc()).all()
    return render_template("lessons.html", lessons=lessons, breadcrumbs=breadcrumbs)

# ============================
# Lesson Detail (simple view)
# ============================
@main_bp.route("/lessons/<int:lesson_id>")
def lesson_detail(lesson_id):
    newnew_lessons = {
        1: {
            "title": "Урок 1. Введение в курс и основные понятия",
            "text": "Этот урок представляет обзор курса по высшей математике, объясняя его значение и области применения в современной науке и технике. Студенты познакомятся с фундаментальными понятиями, такими как множества, функции и переменные, которые лежат в основе всей математики. Задача урока — заложить прочную основу для последующих разделов и помочь понять, почему изучение высшей математики важно и интересно."
        },
        2: {
            "title": "Урок 2. Линейные уравнения и системы",
            "text": "На этом занятии рассматриваются основные типы линейных уравнений и методы их решения, включая подстановку, исключение и метод матриц. Особое внимание уделяется системам уравнений с несколькими переменными, их анализу и решению. Студенты научатся находить решения, интерпретировать их и применять в различных практических задачах, например, в экономике, инженерии и естественных науках."
        },
        3: {
            "title": "Урок 3. Матрицы и определители",
            "text": "Урок посвящен операциям с матрицами, их свойствам и важности в линейной алгебре. Обучающиеся ознакомятся с вычислением определителей, их ролью в решении систем уравнений и анализе матриц. Также обсуждаются свойства матриц и применяются методы их использования для упрощения сложных задач."
        },
        4: {
            "title": "Урок 4. Векторная алгебра",
            "text": "Этот урок раскрывает понятия вектора, его свойства и операции, такие как скалярное и векторное произведения. Студенты узнают, как применять векторные методы в геометрии — например, для определения углов, площадей и объемов, а также в физике для описания сил, скоростей и движений. Практические примеры помогут закрепить теорию."
        },
        5: {
            "title": "Урок 5. Пределы и непрерывность",
            "text": "Данный урок вводит ключевые понятия пределов функций и непрерывности. Объясняется, что означает приближение функции к определенному значению и как определять пределы в различных ситуациях. Особое внимание уделяется свойствам непрерывных функций и их важности в математическом анализе с примерами вычислений. Этот материал необходим для понимания цепочки концепций, ведущих к дифференцированию и интегрированию."
        },
        6: {
            "title": "Урок 6. Производная и её применение",
            "text": "На последующем занятии студенты познакомятся с понятием производной, изучат основные правила дифференцирования (правила суммы, произведения, частного и сложной функции). Обсуждаются геометрический смысл производной как касательной к графику функции и практические задачи на поиск экстремумов, моделирование и оптимизацию процессов. Этот урок важен для развития навыков анализа функций и решения прикладных задач."
        },
    }

    lesson = newnew_lessons.get(lesson_id)
    if not lesson:
        abort(404)

    breadcrumbs = [
        ("Lessons", url_for("main.lessons")),
        (lesson["title"], None)
    ]

    return render_template("lesson_detail.html", lesson=lesson, breadcrumbs=breadcrumbs)


# News list
@main_bp.route("/news")
def news_list():
    news_list = News.query.order_by(News.created_at.desc()).all()
    return render_template("news_list.html", news_list=news_list)

@main_bp.route("/news/<int:news_id>")
def news_detail(news_id):
    news = News.query.get_or_404(news_id)
    latest_news = News.query.filter(News.id != news_id).order_by(News.created_at.desc()).limit(3).all()
    return render_template("news_detail.html", news=news, latest_news=latest_news)

# Contacts - form
@main_bp.route("/contacts", methods=["GET", "POST"])
def contacts():
    form = ContactForm()
    breadcrumbs = [("Контакты", url_for("main.contacts"))]

    if form.validate_on_submit():
        contact = Contact(
            name=form.name.data.strip(),
            email=form.email.data.strip(),
            subject=form.subject.data.strip() if form.subject.data else None,
            message=form.message.data.strip()
        )
        db.session.add(contact)
        db.session.commit()
        flash("Спасибо — сообщение отправлено. Мы скоро ответим.", "success")
        return redirect(url_for("main.contacts"))

    return render_template("contacts.html", form=form, breadcrumbs=breadcrumbs)


# FAQ, Instructors, Terms simple pages
@main_bp.route("/faq")
def faq():
    breadcrumbs = [("FAQ", url_for("main.faq"))]
    return render_template("faq.html", breadcrumbs=breadcrumbs)

@main_bp.route("/instructors")
def instructors():
    breadcrumbs = [("Instructors", url_for("main.instructors"))]
    return render_template("instructors.html", breadcrumbs=breadcrumbs)

@main_bp.route("/terms")
def terms():
    breadcrumbs = [("Terms", url_for("main.terms"))]
    return render_template("terms.html", breadcrumbs=breadcrumbs)

@main_bp.route("/files/upload", methods=["GET", "POST"])
@login_required
def upload_file():
    form = FileUploadForm()
    if form.validate_on_submit():
        f = form.file.data
        try:
            stored_name, original_name, size, content_type = save_uploaded_file(
                f,
                current_app.config["UPLOAD_FOLDER"],
                current_app.config["ALLOWED_UPLOAD_EXTENSIONS"]
            )
        except ValueError:
            flash("Неподдерживаемый формат файла", "danger")
            return redirect(url_for("main.upload_file"))

        # create DB record
        new_file = File(
            owner_user_id=current_user.id,
            original_name=original_name,
            path=stored_name,
            content_type=content_type,
            size_bytes=size,
            visibility="private"  # по умолчанию приватный
        )
        db.session.add(new_file)
        db.session.commit()
        flash("Файл загружен успешно", "success")
        return redirect(url_for("main.user_files"))

    return render_template("files/upload.html", form=form)

@main_bp.route("/files")
@login_required
def user_files():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    pagination = File.query.filter(
        (File.owner_user_id == current_user.id) | (File.visibility != "private")
    ).order_by(File.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("files/list.html", pagination=pagination)

@main_bp.route("/files/<int:file_id>/download")
@login_required
def download_file(file_id):
    file = File.query.get_or_404(file_id)

    # Правила доступа:
    # - владелец
    # - админ (если у тебя есть роль)
    # - или файл не приватный (visibility != 'private')
    if file.owner_user_id != current_user.id and not current_user.has_role("admin") and file.visibility == "private":
        abort(403)

    uploads = current_app.config["UPLOAD_FOLDER"]
    # send_from_directory безопасно, не отдаёт файлы вне папки
    # modern Flask: use download_name; older: attachment_filename
    try:
        return send_from_directory(uploads, file.path, as_attachment=True, download_name=file.original_name)
    except TypeError:
        # Fallback для старых версий Flask
        return send_from_directory(uploads, file.path, as_attachment=True, attachment_filename=file.original_name)

