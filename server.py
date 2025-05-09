"""Website backend for course search."""

from datetime import datetime

from flask import Flask, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from query import course_data_to_dict, full_search

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["2 per second"],
)


@app.route("/", methods=["GET"])
def index():
    """Main page."""
    return render_template("index.html", datetime=datetime.now())

@app.route("/c/<course_id>", methods=["GET"])
def course(course_id):
    """Course page."""
    try:
        course_id = int(course_id)
    except ValueError:
        return jsonify({"error": "Invalid course ID"}), 400

    course_data = full_search({"unique_id": course_id})
    if not course_data:
        return render_template("not_found.html"), 404

    return render_template("course.html", course_id=course_id)

@app.errorhandler(404)
def not_found(_):
    """404 error handler."""
    return render_template("not_found.html"), 404

@app.route("/api/search", methods=["POST"])
@limiter.limit("30 per minute")
def search():
    """Seach endpoint for course data."""
    try:
        course_data = full_search(request.form)
        course_dicts = [course_data_to_dict(course) for course in course_data]
        return jsonify(course_dicts)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
