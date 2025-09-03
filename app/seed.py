# app/seed.py
from app.extensions import db
from app.models import Role, User

def seed_data():
    # создаём роли, если их нет
    roles = ["admin", "manager", "student"]
    role_objects = {}
    for r in roles:
        role = Role.query.filter_by(name=r).first()
        if not role:
            role = Role(name=r)
            db.session.add(role)
            db.session.commit()
        role_objects[r] = role

    # создаём админа, если его нет
    admin = User.query.filter_by(email="admin@vkr.local").first()
    if not admin:
        admin = User(
            email="admin@vkr.local",
            username="admin",
            password_hash="123456"
        )
        admin.roles.append(role_objects["admin"])
        db.session.add(admin)
        db.session.commit()

    print("✅ Сид-данные добавлены или уже существовали")
