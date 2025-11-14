# run_migrations_and_start.py
import os
import sys
from app import create_app
from flask_migrate import upgrade

# --------------------------------------------------------
# CONFIG
# --------------------------------------------------------
RUN_MIGRATIONS = os.getenv("RUN_MIGRATIONS", "false").lower() in ("1", "true", "yes")
RUN_SEEDS = os.getenv("RUN_SEEDS", "false").lower() in ("1", "true", "yes")


APP_MODULE = os.getenv("APP_MODULE", "app_entry:app")

app = create_app()

# --------------------------------------------------------
# APPLY MIGRATIONS
# --------------------------------------------------------
with app.app_context():
    if RUN_MIGRATIONS:
        try:
            print(">>> Running migrations...")
            upgrade()
            print(">>> MIGRATIONS APPLIED")
        except Exception as e:
            print(">>> MIGRATIONS FAILED:", e)

    # ----------------------------------------------------
    # SEED (create roles, admin, sample news)
    # ----------------------------------------------------
    if RUN_SEEDS:
        try:
            print(">>> Running SEEDS...")

            from app.extensions import db
            from app.models import Role, User, News
            from datetime import datetime

            # --- Role admin ---
            role = Role.query.filter_by(name="admin").first()
            if not role:
                role = Role(name="admin", description="Admin")
                db.session.add(role)
                db.session.commit()
                print("Created role: admin")

            # --- Admin user ---
            admin_email = "admin@example.com"
            admin = User.query.filter_by(email=admin_email).first()

            if not admin:
                admin = User(
                    username="admin",
                    email=admin_email
                )
                admin.set_password("admin123")
                admin.roles = [role]
                db.session.add(admin)
                db.session.commit()
                print("Created admin:", admin_email)

            # --- News ---
            if not News.query.first():
                n1 = News(
                    title="Запуск ML-Study",
                    slug="start-ml-study",
                    body="<p>Мы запустили ML-Study!</p>",
                    is_published=True,
                    published_at=datetime.utcnow(),
                    author_user_id=admin.id,
                )
                n2 = News(
                    title="Обновление интерфейса",
                    slug="ui-update",
                    body="<p>Интерфейс улучшен</p>",
                    is_published=True,
                    published_at=datetime.utcnow(),
                    author_user_id=admin.id,
                )
                db.session.add_all([n1, n2])
                db.session.commit()
                print("Added 2 news entries")
            else:
                print("News already exist")

            print(">>> SEEDS DONE")

        except Exception as e:
            print(">>> SEED FAILED:", e)

# --------------------------------------------------------
# START REAL SERVER (gunicorn)
# --------------------------------------------------------

port = os.getenv("PORT", "10000")

print(f">>> Starting gunicorn with {APP_MODULE} on port {port}")

os.execvp(
    "gunicorn",
    ["gunicorn", APP_MODULE, "-b", f"0.0.0.0:{port}", "--workers", "2"]
)
