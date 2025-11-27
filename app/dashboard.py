# app/dashboard.py
from io import BytesIO
import os
import json
from datetime import datetime

from flask import Blueprint, render_template, request, url_for, redirect, flash, send_file, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from werkzeug.utils import secure_filename

from app.utils import roles_required, make_breadcrumbs
from app.extensions import db
from app.models import (
    Course, Enrollment, Lesson, Progress, File, Report, User, Contact
)
from app.export_utils import generate_certificate_docx, make_filename, save_bytes_to_uploads

dashboard_bp = Blueprint("dashboard", __name__, template_folder="templates", url_prefix="/dashboard")


# helper: compute progress percent по курсу (считается как completed lessons / total lessons)
def compute_course_progress(user_id, course_id):
    total = Lesson.query.filter_by(course_id=course_id).count()
    if total == 0:
        return 0
    completed = db.session.query(Progress).join(Lesson, Progress.lesson_id == Lesson.id)\
                .filter(Progress.user_id == user_id, Lesson.course_id == course_id, Progress.status == 'completed').count()
    return int(completed / total * 100)


# --- Dashboard root: редирект по роли ---
@dashboard_bp.route("/")
@login_required
def index():
    # если админ — оставить редирект на админку
    if current_user.has_role("admin"):
        return redirect(url_for("admin.dashboard"))
    if current_user.has_role("teacher"):
        return redirect(url_for("dashboard.instructor_dashboard"))
    # по умолчанию студент
    return redirect(url_for("dashboard.student_dashboard"))


# --- Student: личный кабинет ---
@dashboard_bp.route("/student")
@login_required
@roles_required("student")
def student_dashboard():
    enrolled_count = Enrollment.query.filter_by(user_id=current_user.id).count()
    certs = File.query.filter_by(owner_user_id=current_user.id).order_by(File.created_at.desc()).limit(5).all()
    breadcrumbs = make_breadcrumbs(("ЛК", "dashboard.index", None), ("Студент", None, None))
    return render_template("dashboard/student_dashboard.html", enrolled_count=enrolled_count, certs=certs, breadcrumbs=breadcrumbs)


@dashboard_bp.route("/student/courses")
@login_required
@roles_required("student")
def student_courses():
    page = request.args.get("page", 1, type=int)
    qs = Course.query.join(Enrollment, Enrollment.course_id == Course.id).filter(Enrollment.user_id == current_user.id)
    pagination = qs.order_by(Course.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    breadcrumbs = make_breadcrumbs(("ЛК", "dashboard.index", None), ("Мои курсы", None, None))
    return render_template("dashboard/student_courses.html", pagination=pagination, breadcrumbs=breadcrumbs)


@dashboard_bp.route("/student/course/<int:course_id>")
@login_required
@roles_required("student")
def student_course_detail(course_id):
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if not enrollment:
        flash("Вы не записаны на этот курс.", "danger")
        return redirect(url_for("dashboard.student_courses"))
    course = Course.query.get_or_404(course_id)
    percent = compute_course_progress(current_user.id, course_id)
    lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order_index).all()
    progress_map = {p.lesson_id: p for p in Progress.query.filter_by(user_id=current_user.id).join(Lesson, Progress.lesson_id == Lesson.id).filter(Lesson.course_id == course_id).all()}
    breadcrumbs = make_breadcrumbs(("ЛК", "dashboard.index", None), ("Мои курсы", "dashboard.student_courses", None), (course.title, None, None))
    return render_template("dashboard/student_course_detail.html", course=course, lessons=lessons, progress_map=progress_map, percent=percent, breadcrumbs=breadcrumbs)


@dashboard_bp.route("/student/course/<int:course_id>/certificate", methods=["GET"])
@login_required
@roles_required("student")
def student_certificate(course_id):
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if not enrollment:
        flash("Нет доступа к сертификату.", "danger")
        return redirect(url_for("dashboard.student_course_detail", course_id=course_id))

    course = Course.query.get_or_404(course_id)
    doc_bytes = generate_certificate_docx(current_user, course)
    filename = make_filename(f"certificate-{current_user.username}-{course.slug}", "docx")
    stored_name, size = save_bytes_to_uploads(doc_bytes, filename)
    new_file = File(owner_user_id=current_user.id, original_name=filename, path=stored_name,
                    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    size_bytes=size, visibility="private")
    db.session.add(new_file)
    db.session.commit()
    return redirect(url_for("main.download_file", file_id=new_file.id))


@dashboard_bp.route("/student/messages")
@login_required
@roles_required("student")
def student_messages():
    messages = db.session.query(Report).filter_by(user_id=current_user.id).order_by(Report.created_at.desc()).all()
    breadcrumbs = make_breadcrumbs(("ЛК", "dashboard.index", None), ("Сообщения", None, None))
    return render_template("dashboard/student_messages.html", messages=messages, breadcrumbs=breadcrumbs)


# --- Instructor: личный кабинет ---
@dashboard_bp.route("/instructor", endpoint="instructor_dashboard")
@login_required
@roles_required("teacher")
def instructor_dashboard():
    my_courses_count = Course.query.filter(Course.created_by == current_user.id).count()
    breadcrumbs = make_breadcrumbs(
        ("ЛК", "dashboard.index", None),
        ("Преподаватель", None, None)
    )
    return render_template(
        "dashboard/instructor_dashboard.html",
        my_courses_count=my_courses_count,
        breadcrumbs=breadcrumbs
    )



@dashboard_bp.route("/instructor/courses")
@login_required
@roles_required("teacher")
def instructor_courses():
    page = request.args.get("page", 1, type=int)
    pagination = Course.query.filter_by(created_by=current_user.id).order_by(Course.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    breadcrumbs = make_breadcrumbs(("ЛК", "dashboard.index", None), ("Мои курсы", None, None))
    return render_template("dashboard/instructor_courses.html", pagination=pagination, breadcrumbs=breadcrumbs)


@dashboard_bp.route("/instructor/course/<int:course_id>/students")
@login_required
@roles_required("teacher")
def instructor_course_students(course_id):
    course = Course.query.get_or_404(course_id)
    if course.created_by != current_user.id and not current_user.has_role("admin"):
        flash("Нет доступа к списку студентов этого курса.", "danger")
        return redirect(url_for("dashboard.instructor_courses"))
    students = db.session.query(User).join(Enrollment, Enrollment.user_id == User.id).filter(Enrollment.course_id == course_id).all()
    breadcrumbs = make_breadcrumbs(("ЛК", "dashboard.index", None), ("Мои курсы", "dashboard.instructor_courses", None), (f"Студенты: {course.title}", None, None))
    return render_template("dashboard/instructor_course_students.html", course=course, students=students, breadcrumbs=breadcrumbs)


@dashboard_bp.route("/instructor/reports")
@login_required
@roles_required("teacher")
def instructor_reports():
    course_ids = [c.id for c in Course.query.filter_by(created_by=current_user.id).all()]
    pagination = Report.query.filter(Report.course_id.in_(course_ids)).order_by(Report.created_at.desc()).paginate(page=request.args.get("page", 1, type=int), per_page=20, error_out=False)
    breadcrumbs = make_breadcrumbs(("ЛК", "dashboard.index", None), ("Отчёты", None, None))
    return render_template("dashboard/instructor_reports.html", pagination=pagination, breadcrumbs=breadcrumbs)


# --- Методические материалы ---
@dashboard_bp.route("/instructor/materials")
@login_required
@roles_required("teacher")
def instructor_materials():
    static_root = current_app.static_folder
    materials_dir = os.path.join(static_root, "materials")
    groups = []
    if os.path.exists(materials_dir):
        for course_slug in sorted(os.listdir(materials_dir)):
            course_path = os.path.join(materials_dir, course_slug)
            if not os.path.isdir(course_path):
                continue
            items = []
            for fname in sorted(os.listdir(course_path)):
                fpath = os.path.join(course_path, fname)
                if os.path.isfile(fpath):
                    items.append({
                        "name": fname,
                        "url": url_for("static", filename=f"materials/{course_slug}/{fname}")
                    })
            groups.append({"course_slug": course_slug, "items": items})
    breadcrumbs = [("Личный кабинет", url_for("dashboard.instructor_dashboard")), ("Методические материалы", None)]
    return render_template("dashboard/instructor_materials.html", groups=groups, breadcrumbs=breadcrumbs)


# --- Обратная связь от студентов (контакты) ---
@dashboard_bp.route("/instructor/contacts")
@login_required
@roles_required("teacher")
def instructor_contacts():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    pagination = Contact.query.order_by(Contact.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    breadcrumbs = [("Личный кабинет", url_for("dashboard.instructor_dashboard")), ("Обратная связь", None)]
    return render_template("dashboard/instructor_contacts.html", pagination=pagination, breadcrumbs=breadcrumbs)


@dashboard_bp.route("/instructor/contacts/<int:contact_id>")
@login_required
@roles_required("teacher")
def instructor_contact_detail(contact_id):
    c = Contact.query.get_or_404(contact_id)
    breadcrumbs = [("Личный кабинет", url_for("dashboard.instructor_dashboard")), ("Обратная связь", url_for("dashboard.instructor_contacts")), (f"Сообщение #{c.id}", None)]
    return render_template("dashboard/instructor_contact_detail.html", contact=c, breadcrumbs=breadcrumbs)


# --- Профиль преподавателя ---
@dashboard_bp.route("/instructor/profile", methods=["GET", "POST"])
@login_required
@roles_required("teacher")
def instructor_profile():
    profile = getattr(current_user, "profile", None)
    if request.method == "POST":
        first = request.form.get("first_name", "").strip()
        last = request.form.get("last_name", "").strip()
        phone = request.form.get("phone", "").strip()
        org = request.form.get("organization", "").strip()

        if profile is None:
            from app.models import Profile
            profile = Profile(user=current_user, first_name=first, last_name=last, phone=phone, organization=org)
            db.session.add(profile)
        else:
            profile.first_name = first
            profile.last_name = last
            profile.phone = phone
            profile.organization = org
        db.session.commit()
        flash("Профиль обновлён", "success")
        return redirect(url_for("dashboard.instructor_profile"))

    breadcrumbs = [("Личный кабинет", url_for("dashboard.instructor_dashboard")), ("Профиль", None)]
    return render_template("dashboard/instructor_profile.html", profile=profile, breadcrumbs=breadcrumbs)


# --- Расписание преподавателя ---
@dashboard_bp.route("/instructor/schedule")
@login_required
@roles_required("teacher")
def instructor_schedule():
    static_root = current_app.static_folder
    schedules_dir = os.path.join(static_root, "schedules")
    schedule = []
    schedule_file = os.path.join(schedules_dir, f"{current_user.username}.json")
    if os.path.exists(schedule_file):
        try:
            with open(schedule_file, "r", encoding="utf-8") as fh:
                schedule = json.load(fh)
        except Exception:
            schedule = []
    breadcrumbs = [("Личный кабинет", url_for("dashboard.instructor_dashboard")), ("Расписание", None)]
    for item in schedule:
        if "date" in item:
            try:
                item["date_obj"] = datetime.fromisoformat(item["date"])
            except Exception:
                item["date_obj"] = None
    return render_template("dashboard/instructor_schedule.html", schedule=schedule, breadcrumbs=breadcrumbs)

@dashboard_bp.route("/instructor/reports/upload", methods=["GET", "POST"])
@login_required
@roles_required("teacher")
def upload_report():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            flash("Файл не выбран!", "danger")
            return redirect(request.url)

        # Сохраняем файл
        filename = secure_filename(file.filename)
        filepath = os.path.join("uploads/reports", filename)
        os.makedirs("uploads/reports", exist_ok=True)
        file.save(filepath)

        # Записываем в БД
        report = Report(
            type="daily",
            status="загружен",
            file_id=filename,
        )
        db.session.add(report)
        db.session.commit()

        flash("Отчёт успешно загружен!", "success")
        return redirect(url_for("dashboard.instructor_reports"))

    breadcrumbs = [
        ("Личный кабинет", url_for("dashboard.instructor_dashboard")),
        ("Загрузить отчёт", None),
    ]
    return render_template("dashboard/upload_report.html", breadcrumbs=breadcrumbs)
