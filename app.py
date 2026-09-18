from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
DATABASE = "database.db"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image TEXT NOT NULL,
            crop TEXT NOT NULL,
            disease TEXT NOT NULL,
            confidence REAL NOT NULL,
            symptoms TEXT,
            treatment TEXT,
            prevention TEXT,
            created_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# -------------------------------------------------------
# DEMO AI PREDICTION
# Replace this function with your trained AI model later.
# -------------------------------------------------------

def predict_disease(image_path):

    return {
        "crop": "Tomato",
        "disease": "Early Blight",
        "confidence": 94.5,

        "symptoms":
            "Brown or dark circular spots can appear on leaves, "
            "often with yellowing around affected areas.",

        "treatment":
            "Remove severely affected leaves and improve air circulation. "
            "For chemical treatment, follow locally approved agricultural guidance.",

        "prevention":
            "Maintain adequate spacing, avoid unnecessary leaf wetness, "
            "and remove infected plant debris."
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/detect")
def detect():
    return render_template("detect.html")


@app.route("/predict", methods=["POST"])
def predict():

    if "image" not in request.files:
        return redirect(url_for("detect"))

    file = request.files["image"]

    if file.filename == "":
        return redirect(url_for("detect"))

    if not allowed_file(file.filename):
        return "Invalid image format. Please upload JPG, PNG or WEBP.", 400

    original_name = secure_filename(file.filename)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    filename = f"{timestamp}_{original_name}"

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(filepath)

    result = predict_disease(filepath)

    connection = get_db()

    connection.execute("""
        INSERT INTO detections
        (
            image,
            crop,
            disease,
            confidence,
            symptoms,
            treatment,
            prevention,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        filename,
        result["crop"],
        result["disease"],
        result["confidence"],
        result["symptoms"],
        result["treatment"],
        result["prevention"],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    connection.commit()
    connection.close()

    return render_template(
        "result.html",
        result=result,
        image=filename
    )


@app.route("/history")
def history():

    connection = get_db()

    detections = connection.execute("""
        SELECT *
        FROM detections
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    return render_template(
        "history.html",
        detections=detections
    )


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


@app.route("/delete-history/<int:detection_id>", methods=["POST"])
def delete_history(detection_id):

    connection = get_db()

    detection = connection.execute(
        "SELECT image FROM detections WHERE id = ?",
        (detection_id,)
    ).fetchone()

    if detection:
        image_path = os.path.join(
            UPLOAD_FOLDER,
            detection["image"]
        )

        if os.path.exists(image_path):
            os.remove(image_path)

        connection.execute(
            "DELETE FROM detections WHERE id = ?",
            (detection_id,)
        )

        connection.commit()

    connection.close()

    return redirect(url_for("history"))


if __name__ == "__main__":
    init_database()

    print("\n======================================")
    print(" Crop Disease Detection System")
    print("======================================")
    print("Website: http://127.0.0.1:5000")
    print("Press CTRL+C to stop the server\n")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )