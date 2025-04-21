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


@app.route("/api/search", methods=["POST"])
@limiter.limit("30 per minute")
def search():
    """Seach endpoint for course data."""
    try:
        course_data = full_search(request.form)
        course_dicts = [course_data_to_dict(course) for course in course_data]
        return jsonify(course_dicts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
