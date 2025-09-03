from app.extensions import db
from datetime import datetime
from sqlalchemy import UniqueConstraint

# ---------- Roles ----------
class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

user_roles = db.Table(
    "user_roles",
    db.Column("user_id", db.BigInteger, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("role_id", db.BigInteger, db.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    db.Column("created_at", db.DateTime(timezone=True), default=datetime.utcnow),
    UniqueConstraint("user_id", "role_id", name="uq_user_role"),
)
