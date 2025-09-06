from flask import render_template
from app import app

@app.route("/")
def index():
    return render_template("index.html")

breadcrumbs = make_breadcrumbs(("Courses","main.courses",None), (course.title, None, None))
