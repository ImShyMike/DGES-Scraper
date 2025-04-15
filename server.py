"""Website backend for course search."""

from flask import Flask, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from query import course_data_to_dict, get_full_course_data

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["2 per second"],
)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
@limiter.limit("30 per minute")
def search():
    course_name = request.form.get("name")
    if not course_name:
        return jsonify({"error": "Course code is required"}), 400

    try:
        course_data = get_full_course_data(course_name=course_name, limit=25)
        course_dicts = [course_data_to_dict(course) for course in course_data]
        return jsonify(course_dicts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
