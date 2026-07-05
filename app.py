import os
from flask import Flask, request, jsonify, render_template
from werkzeug.exceptions import RequestEntityTooLarge
from dotenv import load_dotenv

from utils.parser import extract_text, UnsupportedFileType
from utils.analyzer import rule_based_analysis, ai_enhance

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit
latest_result = None
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[-1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/result")
def result():
    global latest_result

    if latest_result is None:
        return render_template("index.html")

    return render_template(
        "result.html",
        result=latest_result
    )

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/analyze", methods=["POST"])
def analyze():
    if "resume" not in request.files:
        return jsonify({"error": "No resume file was uploaded."}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type. Please upload a PDF, DOCX, or TXT file."}), 400

    job_description = request.form.get("job_description", "").strip()

    try:
        text = extract_text(file, file.filename)
    except UnsupportedFileType as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        return jsonify({"error": "Could not read that file. It may be corrupted or password protected."}), 422

    if len(text.strip()) < 30:
        return jsonify({"error": "We couldn't extract readable text from this file. If it's a scanned image, try uploading a text-based PDF or DOCX instead."}), 422

    rule_result = rule_based_analysis(text, job_description or None)
    feedback = ai_enhance(text, job_description or None, rule_result)
    
    global latest_result

    latest_result = {
    "overall_score": rule_result["overall_score"],
    "components": rule_result["components"],
    "details": rule_result["details"],
    "feedback": feedback,
}

    return jsonify({
    "success": True
})


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(e):
    return jsonify({"error": "File is too large. Please upload a resume under 5 MB."}), 413


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)