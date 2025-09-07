# app/admin.py
from flask import Blueprint, render_template, request, url_for, redirect, flash
from flask_login import login_required
from app.utils import roles_required
from app.extensions import db
from app.models import Contact
from app.decorators import admin_required

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



