# app/admin.py
from flask import Blueprint, render_template, request, url_for, redirect, flash
from flask_login import login_required
from app.utils import roles_required
from app.extensions import db
from app.models import Contact
from app.decorators import admin_required
from app.models import File
from flask import send_file, make_response
from io import BytesIO
from app.export_utils import generate_certificate_docx, make_filename, save_bytes_to_uploads
from app.models import Course, User


admin_bp = Blueprint("admin", __name__, template_folder="templates", url_prefix="/admin")

@admin_bp.route("/contacts")
@login_required
@roles_required("admin")
def contacts_list():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    pagination = Contact.query.order_by(Contact.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("admin/contacts_list.html", pagination=pagination)

@admin_bp.route("/contacts/<int:contact_id>")
@login_required
@roles_required("admin")
def contact_detail(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    return render_template("admin/contact_detail.html", contact=contact)

@admin_bp.route("/contacts/<int:contact_id>/mark-read", methods=["POST"])
@login_required
@admin_required
def mark_contact_read(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    contact.is_read = True
    db.session.commit()
    flash("Сообщение отмечено как прочитанное", "success")

    next_url = request.form.get("next") or url_for("admin.contacts_list")
    return redirect(next_url)

@admin_bp.route("/files")
@login_required
@roles_required("admin")
def admin_files():
    page = request.args.get("page", 1, type=int)
    per_page = 50
    pagination = File.query.order_by(File.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("admin/files_list.html", pagination=pagination)

@admin_bp.route("/export/certificate/<int:user_id>/<int:course_id>", methods=["GET"])
@login_required
@roles_required("admin", "instructor")  # кто может выдавать сертификаты
def export_certificate(user_id, course_id):
    user = User.query.get_or_404(user_id)
    course = Course.query.get_or_404(course_id)

    doc_bytes = generate_certificate_docx(user, course)

    filename = make_filename(f"certificate-{user.username}-{course.slug}", "docx")

    # Опция: сохраняем файл в uploads и создаём запись
    save_to_disk = True
    if save_to_disk:
        stored_name, size = save_bytes_to_uploads(doc_bytes, filename)
        # записать в БД
        new_file = File(
            owner_user_id = None,  # можно указать issuer/admin, или user.id
            original_name = filename,
            path = stored_name,
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size_bytes = size,
            visibility = "private"
        )
        db.session.add(new_file)
        db.session.commit()
        # вернуть ссылку для скачивания (через /files/<id>/download) или отдать сразу
        return redirect(url_for("main.download_file", file_id=new_file.id))

    # или вернуть в памяти
    return send_file(BytesIO(doc_bytes),
                     as_attachment=True,
                     download_name=filename,
                     mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

@admin_bp.route("/export/progress/course/<int:course_id>", methods=["GET"])
@login_required
@roles_required("admin", "instructor")
def export_course_progress(course_id):
    # собираем данные: для каждого прогресса берем student и lesson
    # Пример запроса:
    rows = []
    from app.models import Progress, Lesson, User, Enrollment
    # Найти всех прогрессов по курсу (join lessons)
    qs = db.session.query(
        User.username, User.email, Lesson.title, Progress.status, Progress.score, Progress.completed_at
    ).join(Progress, Progress.user_id == User.id
    ).join(Lesson, Progress.lesson_id == Lesson.id
    ).filter(Lesson.course_id == course_id).order_by(User.id, Lesson.order_index).all()

    # qs уже список кортежей
    xlsx_bytes = generate_progress_xlsx(course_id, qs)
    filename = make_filename(f"progress-course-{course_id}", "xlsx")

    # return as stream
    return send_file(BytesIO(xlsx_bytes),
                     as_attachment=True,
                     download_name=filename,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@admin_bp.route("/export/stats/course/<int:course_id>", methods=["GET"])
@login_required
@roles_required("admin", "instructor")
def export_course_stats(course_id):
    from sqlalchemy import func
    # подсчёты:
    total_enrolled = db.session.query(func.count(Enrollment.id)).filter(Enrollment.course_id==course_id).scalar()
    # завершили — enrollment статус == 'completed'
    completed = db.session.query(func.count(Enrollment.id)).filter(Enrollment.course_id==course_id, Enrollment.status=='completed').scalar()
    # avg score — средний по прогресс для уроков курса
    avg_score = db.session.query(func.avg(Progress.score)).join(Lesson, Progress.lesson_id==Lesson.id).filter(Lesson.course_id==course_id).scalar() or 0

    completion_rate = f"{(completed / total_enrolled * 100) if total_enrolled else 0:.2f}%"

    rows = [
        ("Course ID", course_id),
        ("Total enrolled", total_enrolled),
        ("Completed", completed),
        ("Completion rate", completion_rate),
        ("Avg score", round(float(avg_score),2) if avg_score else 0),
    ]
    xlsx_bytes = generate_stats_xlsx(rows, title=f"course-{course_id}-stats")
    filename = make_filename(f"course-{course_id}-stats", "xlsx")
    return send_file(BytesIO(xlsx_bytes),
                     as_attachment=True,
                     download_name=filename,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


