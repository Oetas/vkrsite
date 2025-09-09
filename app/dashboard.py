# app/dashboard.py
from flask import Blueprint, render_template, request, url_for, redirect, flash, send_file
from flask_login import login_required, current_user
from app.utils import roles_required, make_breadcrumbs
from app.extensions import db
from app.models import Course, Enrollment, Lesson, Progress, File, Report, User
from io import BytesIO
from app.export_utils import generate_certificate_docx, make_filename, save_bytes_to_uploads

dashboard_bp = Blueprint("dashboard", __name__, template_folder="templates", url_prefix="/dashboard")


# helper: compute progress percent по курсу (считается как completed lessons / total lessons)
def compute_course_progress(user_id, course_id):
    total = Lesson.query.filter_by(course_id=course_id).count()
    if total == 0:
        return 0
    completed = db.session.query(Progress).join(Lesson, Progress.lesson_id==Lesson.id)\
                .filter(Progress.user_id==user_id, Lesson.course_id==course_id, Progress.status=='completed').count()
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
    # показать краткую статистику
    enrolled_count = Enrollment.query.filter_by(user_id=current_user.id).count()
    # последние сертификаты (файлы владельца)
    certs = File.query.filter_by(owner_user_id=current_user.id).order_by(File.created_at.desc()).limit(5).all()
    breadcrumbs = make_breadcrumbs(("ЛК","dashboard.index", None), ("Студент", None, None))
    return render_template("dashboard/student_dashboard.html", enrolled_count=enrolled_count, certs=certs, breadcrumbs=breadcrumbs)


@dashboard_bp.route("/student/courses")
@login_required
@roles_required("student")
def student_courses():
    page = request.args.get("page", 1, type=int)
    # список курсов, в которые зачислен студент
    qs = Course.query.join(Enrollment, Enrollment.course_id==Course.id).filter(Enrollment.user_id==current_user.id)
    pagination = qs.order_by(Course.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    breadcrumbs = make_breadcrumbs(("ЛК","dashboard.index", None), ("Мои курсы", None, None))
    return render_template("dashboard/student_courses.html", pagination=pagination, breadcrumbs=breadcrumbs)


@dashboard_bp.route("/student/course/<int:course_id>")
@login_required
@roles_required("student")
def student_course_detail(course_id):
    # проверяем, что студент записан на курс
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if not enrollment:
        flash("Вы не записаны на этот курс.", "danger")
        return redirect(url_for("dashboard.student_courses"))
    course = Course.query.get_or_404(course_id)
    # прогресс %
    percent = compute_course_progress(current_user.id, course_id)
    # подробности прогресса: прогресс по урокам
    lessons = Lesson.query.filter_by(course_id=course_id).order_by(Lesson.order_index).all()
    progress_map = {p.lesson_id: p for p in Progress.query.filter_by(user_id=current_user.id).join(Lesson, Progress.lesson_id==Lesson.id).filter(Lesson.course_id==course_id).all()}
    breadcrumbs = make_breadcrumbs(("ЛК","dashboard.index", None), ("Мои курсы","dashboard.student_courses", None), (course.title, None, None))
    return render_template("dashboard/student_course_detail.html", course=course, lessons=lessons, progress_map=progress_map, percent=percent, breadcrumbs=breadcrumbs)


# скачивание сертификата — студент может скачать свой сертификат (генерация как в admin)
@dashboard_bp.route("/student/course/<int:course_id>/certificate", methods=["GET"])
@login_required
@roles_required("student")
def student_certificate(course_id):
    # проверить, что студент завершил курс (или просто что он записан)
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if not enrollment:
        flash("Нет доступа к сертификату.", "danger")
        return redirect(url_for("dashboard.student_course_detail", course_id=course_id))

    course = Course.query.get_or_404(course_id)
    doc_bytes = generate_certificate_docx(current_user, course)
    filename = make_filename(f"certificate-{current_user.username}-{course.slug}", "docx")

    # можно как admin — сохранить в uploads + создать File
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
    # показываем обращения/feedback, которые принадлежат текущему пользователю
    # если у вас есть Contact с email, можно фильтровать по email, либо по user_id (если связь есть)
    messages = db.session.query(Report).filter_by(user_id=current_user.id).order_by(Report.created_at.desc()).all()
    breadcrumbs = make_breadcrumbs(("ЛК","dashboard.index", None), ("Сообщения", None, None))
    return render_template("dashboard/student_messages.html", messages=messages, breadcrumbs=breadcrumbs)


# --- Instructor: личный кабинет ---
@dashboard_bp.route("/instructor")
@login_required
@roles_required("teacher")
def instructor_dashboard():
    # краткая статистика: сколько курсов
    my_courses_count = Course.query.filter_by(created_by=current_user.id).count()
    breadcrumbs = make_breadcrumbs(("ЛК","dashboard.index", None), ("Преподаватель", None, None))
    return render_template("dashboard/instructor_dashboard.html", my_courses_count=my_courses_count, breadcrumbs=breadcrumbs)


@dashboard_bp.route("/instructor/courses")
@login_required
@roles_required("teacher")
def instructor_courses():
    page = request.args.get("page", 1, type=int)
    pagination = Course.query.filter_by(created_by=current_user.id).order_by(Course.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    breadcrumbs = make_breadcrumbs(("ЛК","dashboard.index", None), ("Мои курсы", None, None))
    return render_template("dashboard/instructor_courses.html", pagination=pagination, breadcrumbs=breadcrumbs)


@dashboard_bp.route("/instructor/course/<int:course_id>/students")
@login_required
@roles_required("teacher")
def instructor_course_students(course_id):
    # безопасность — убедиться, что текущий пользователь — автор курса
    course = Course.query.get_or_404(course_id)
    if course.created_by != current_user.id and not current_user.has_role("admin"):
        flash("Нет доступа к списку студентов этого курса.", "danger")
        return redirect(url_for("dashboard.instructor_courses"))
    # получить студентов через Enrollment
    students = db.session.query(User).join(Enrollment, Enrollment.user_id==User.id).filter(Enrollment.course_id==course_id).all()
    breadcrumbs = make_breadcrumbs(("ЛК","dashboard.index", None), ("Мои курсы","dashboard.instructor_courses", None), (f"Студенты: {course.title}", None, None))
    return render_template("dashboard/instructor_course_students.html", course=course, students=students, breadcrumbs=breadcrumbs)


# Отчёты — список преподавателя (те, что привязаны к его курсам)
@dashboard_bp.route("/instructor/reports")
@login_required
@roles_required("teacher")
def instructor_reports():
    # можно фильтровать по курсам текущего инструктора
    course_ids = [c.id for c in Course.query.filter_by(created_by=current_user.id).all()]
    pagination = Report.query.filter(Report.course_id.in_(course_ids)).order_by(Report.created_at.desc()).paginate(page=request.args.get("page",1,type=int), per_page=20, error_out=False)
    breadcrumbs = make_breadcrumbs(("ЛК","dashboard.index", None), ("Отчёты", None, None))
    return render_template("dashboard/instructor_reports.html", pagination=pagination, breadcrumbs=breadcrumbs)
