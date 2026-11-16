import csv
import io
import os
import sqlite3
from datetime import datetime, timezone
from functools import wraps

import requests
from flask import Flask, Response, flash, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "visitors.db"))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-development-secret")
app.config["WTF_CSRF_TIME_LIMIT"] = 3600
csrf = CSRFProtect(app)


def db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS visitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                accuracy_m REAL,
                place TEXT,
                submitted_at TEXT NOT NULL
            )
        """)


def reverse_geocode(lat, lon):
    """Best-effort reverse geocoding. GPS coordinates are retained if lookup fails."""
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"format": "jsonv2", "lat": lat, "lon": lon, "zoom": 16},
            headers={"User-Agent": "GPSVisitorInfoProject/1.0 (configure-your-contact-email)"},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        address = data.get("address", {})
        parts = [
            address.get("suburb") or address.get("neighbourhood") or address.get("village"),
            address.get("town") or address.get("city") or address.get("county"),
            address.get("state"),
            address.get("country"),
        ]
        place = ", ".join(dict.fromkeys(p for p in parts if p))
        return place or data.get("display_name")
    except (requests.RequestException, ValueError, TypeError):
        return None


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/", methods=["GET"])
def register():
    return render_template("register.html")


@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    consent = request.form.get("location_consent")
    try:
        lat = float(request.form.get("latitude", ""))
        lon = float(request.form.get("longitude", ""))
        accuracy = float(request.form.get("accuracy", "") or 0)
    except (TypeError, ValueError):
        flash("We could not read your GPS location. Please allow location access and try again.", "error")
        return redirect(url_for("register"))

    if not name or len(name) > 100:
        flash("Please enter a valid name (maximum 100 characters).", "error")
        return redirect(url_for("register"))
    if len(email) > 254 or "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("register"))
    if consent != "yes":
        flash("Please provide permission to share your GPS location to submit this form.", "error")
        return redirect(url_for("register"))
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        flash("The GPS coordinates were invalid. Please try again.", "error")
        return redirect(url_for("register"))

    place = reverse_geocode(lat, lon)
    submitted_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with db() as conn:
        conn.execute(
            """INSERT INTO visitors
               (name, email, latitude, longitude, accuracy_m, place, submitted_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, email, lat, lon, accuracy, place, submitted_at),
        )

    return render_template("success.html", place=place)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        expected_user = os.environ.get("ADMIN_USERNAME", "admin")
        password_hash = os.environ.get("ADMIN_PASSWORD_HASH", "")
        if username == expected_user and password_hash and check_password_hash(password_hash, password):
            session.clear()
            session["admin_logged_in"] = True
            return redirect(url_for("dashboard"))
        flash("Invalid admin username or password. Check your environment settings.", "error")
    return render_template("login.html")


@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin", methods=["GET"])
@admin_required
def dashboard():
    q = request.args.get("q", "").strip()
    with db() as conn:
        if q:
            rows = conn.execute(
                """SELECT * FROM visitors
                   WHERE name LIKE ? OR email LIKE ? OR place LIKE ?
                   ORDER BY id DESC""",
                (f"%{q}%", f"%{q}%", f"%{q}%"),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM visitors ORDER BY id DESC").fetchall()
        total = conn.execute("SELECT COUNT(*) FROM visitors").fetchone()[0]
        locations = conn.execute(
            "SELECT latitude, longitude, name, place FROM visitors"
        ).fetchall()
    return render_template("dashboard.html", visitors=rows, total=total, locations=locations, q=q)


@app.route("/admin/export.csv", methods=["GET"])
@admin_required
def export_csv():
    with db() as conn:
        rows = conn.execute("SELECT * FROM visitors ORDER BY id DESC").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Email", "Latitude", "Longitude", "Accuracy (m)", "Place", "Submitted at (UTC)"])
    for row in rows:
        writer.writerow([row["id"], row["name"], row["email"], row["latitude"],
                         row["longitude"], row["accuracy_m"], row["place"], row["submitted_at"]])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=visitor_records.csv"},
    )


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
