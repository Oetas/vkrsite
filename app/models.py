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

# ---------- Courses / Lessons / Materials ----------
class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.BigInteger, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    level = db.Column(db.Enum("beginner","intermediate","advanced", name="course_level"), nullable=False, default="beginner")
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    created_by = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    author = db.relationship("User", back_populates="courses_created")
    lessons = db.relationship("Lesson", back_populates="course", cascade="all, delete-orphan")

class Lesson(db.Model):
    __tablename__ = "lessons"
    id = db.Column(db.BigInteger, primary_key=True)
    course_id = db.Column(db.BigInteger, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    order_index = db.Column(db.Integer, nullable=False, default=1)
    content = db.Column(db.Text)
    video_url = db.Column(db.String(500))
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    course = db.relationship("Course", back_populates="lessons")
    materials = db.relationship("Material", back_populates="lesson", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("course_id", "order_index", name="uq_lesson_order"),)

class Material(db.Model):
    __tablename__ = "materials"
    id = db.Column(db.BigInteger, primary_key=True)
    lesson_id = db.Column(db.BigInteger, db.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    type = db.Column(db.Enum("pdf","docx","xlsx","notebook","dataset","image","link","other", name="material_type"), nullable=False, default="other")
    title = db.Column(db.String(255))
    file_id = db.Column(db.BigInteger, db.ForeignKey("files.id", ondelete="SET NULL"))
    url = db.Column(db.String(1000))
    is_required = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    lesson = db.relationship("Lesson", back_populates="materials")
    file = db.relationship("File")

# ---------- Enrollments / Progress ----------
class Enrollment(db.Model):
    __tablename__ = "enrollments"
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = db.Column(db.BigInteger, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    status = db.Column(db.Enum("active","completed","dropped", name="enrollment_status"), nullable=False, default="active")
    enrolled_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_enrollment_user_course"),)

class Progress(db.Model):
    __tablename__ = "progress"
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = db.Column(db.BigInteger, db.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    status = db.Column(db.Enum("not_started","in_progress","completed", name="lesson_progress"), nullable=False, default="not_started")
    score = db.Column(db.Numeric(5,2))
    completed_at = db.Column(db.DateTime(timezone=True))
    last_viewed_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_progress_user_lesson"),)