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

# News list
@main_bp.route("/news")
def news_list():
    page = request.args.get("page", 1, type=int)
    per_page = 8
    pagination = News.query.order_by(News.published_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    breadcrumbs = [("News", url_for("main.news_list"))]
    return render_template("news_list.html", pagination=pagination, breadcrumbs=breadcrumbs)

# News detail
@main_bp.route("/news/<int:news_id>")
def news_detail(news_id):
    item = News.query.get_or_404(news_id)
    breadcrumbs = [("News", url_for("main.news_list")), (item.title, None)]
    return render_template("news_detail.html", item=item, breadcrumbs=breadcrumbs)

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

