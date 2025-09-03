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

# ---------- Users / Profiles ----------
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.BigInteger, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    roles = db.relationship("Role", secondary=user_roles, backref=db.backref("users", lazy="dynamic"))
    profile = db.relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    courses_created = db.relationship("Course", back_populates="author", cascade="all, delete-orphan")

class Profile(db.Model):
    __tablename__ = "profiles"
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    patronymic = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    avatar_file_id = db.Column(db.BigInteger, db.ForeignKey("files.id", ondelete="SET NULL"))
    bio = db.Column(db.Text)
    organization = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="profile")
    avatar_file = db.relationship("File", foreign_keys=[avatar_file_id])