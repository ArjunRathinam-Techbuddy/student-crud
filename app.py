from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "dev-secret-key"
DB_PATH = os.path.join(os.path.dirname(__file__), "students.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            department TEXT NOT NULL,
            year INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    search = request.args.get("search", "").strip()
    conn = get_db()
    if search:
        students = conn.execute(
            "SELECT * FROM students WHERE name LIKE ? OR roll_number LIKE ? ORDER BY id DESC",
            (f"%{search}%", f"%{search}%")
        ).fetchall()
    else:
        students = conn.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("index.html", students=students, search=search)


@app.route("/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        roll_number = request.form["roll_number"].strip()
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        department = request.form["department"].strip()
        year = request.form["year"].strip()

        if not all([roll_number, name, email, department, year]):
            flash("All fields are required.", "error")
            return redirect(url_for("add_student"))

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO students (roll_number, name, email, department, year) VALUES (?, ?, ?, ?, ?)",
                (roll_number, name, email, department, year)
            )
            conn.commit()
            flash(f"Student '{name}' added successfully.", "success")
        except sqlite3.IntegrityError:
            flash(f"Roll number '{roll_number}' already exists.", "error")
        finally:
            conn.close()
        return redirect(url_for("index"))

    return render_template("form.html", student=None, action="Add")


@app.route("/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()

    if student is None:
        conn.close()
        flash("Student not found.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        roll_number = request.form["roll_number"].strip()
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        department = request.form["department"].strip()
        year = request.form["year"].strip()

        if not all([roll_number, name, email, department, year]):
            flash("All fields are required.", "error")
            conn.close()
            return redirect(url_for("edit_student", student_id=student_id))

        try:
            conn.execute(
                "UPDATE students SET roll_number=?, name=?, email=?, department=?, year=? WHERE id=?",
                (roll_number, name, email, department, year, student_id)
            )
            conn.commit()
            flash(f"Student '{name}' updated successfully.", "success")
        except sqlite3.IntegrityError:
            flash(f"Roll number '{roll_number}' already exists.", "error")
        finally:
            conn.close()
        return redirect(url_for("index"))

    conn.close()
    return render_template("form.html", student=student, action="Edit")


@app.route("/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    conn = get_db()
    student = conn.execute("SELECT name FROM students WHERE id = ?", (student_id,)).fetchone()
    conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()
    if student:
        flash(f"Student '{student['name']}' deleted.", "success")
    return redirect(url_for("index"))


@app.route("/view/<int:student_id>")
def view_student(student_id):
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    conn.close()
    if student is None:
        flash("Student not found.", "error")
        return redirect(url_for("index"))
    return render_template("view.html", student=student)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
