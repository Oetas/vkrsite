# app/admin.py
from flask import Blueprint, render_template, request, url_for, redirect, flash
from flask_login import login_required
from app.utils import roles_required
from app.extensions import db
from app.models import Contact

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
