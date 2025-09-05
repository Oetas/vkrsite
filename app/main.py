from flask import Blueprint, render_template, request, url_for, redirect, flash
from app.extensions import db
from app.models import Course, Lesson, News, Contact  # используй свои модели

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
    breadcrumbs = [("Contacts", url_for("main.contacts"))]
    if request.method == "POST":
        name = request.form.get("name", "")
        email = request.form.get("email", "")
        subject = request.form.get("subject", "")
        message = request.form.get("message", "")
        if not name or not email or not message:
            flash("Пожалуйста, заполните имя, email и сообщение.", "danger")
            return render_template("contacts.html", breadcrumbs=breadcrumbs)
        contact = Contact(name=name, email=email, subject=subject, message=message)
        db.session.add(contact)
        db.session.commit()
        flash("Спасибо, сообщение отправлено!", "success")
        return redirect(url_for("main.contacts"))
    return render_template("contacts.html", breadcrumbs=breadcrumbs)

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
