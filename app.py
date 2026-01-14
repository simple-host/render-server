from flask import (
    Flask,
    request,
    redirect,
    url_for,
    render_template_string,
    abort,
    send_from_directory
)
import os
import random
import string
from werkzeug.utils import secure_filename

app = Flask(__name__)

# -------------------------
# Config
# -------------------------
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"html"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# -------------------------
# Helpers
# -------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def random_suffix():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=4))

def unique_filename(base):
    filename = f"{base}.html"
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if not os.path.exists(path):
        return filename

    return f"{base}-{random_suffix()}.html"

# -------------------------
# Routes
# -------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    message = ""

    if request.method == "POST":
        file = request.files.get("file")

        if not file or file.filename == "":
            message = "No file selected."
        elif not allowed_file(file.filename):
            message = "Only HTML files allowed."
        else:
            filename = unique_filename("simplehost")
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            page_name = filename.replace(".html", "")
            return redirect(url_for("uploaded", page_name=page_name))

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>SimpleHost</title>
<style>
body {
    background:#1c1c1c;
    color:#e0e0e0;
    font-family:Arial;
    display:flex;
    justify-content:center;
    align-items:center;
    height:100vh;
}
.container {
    text-align:center;
}
input, button {
    padding:15px;
    margin:10px;
    font-size:1.1em;
}
</style>
</head>
<body>
<div class="container">
<h1>SimpleHost</h1>
<p>Your site will be uploaded as:</p>
<b>https://simplehost.onrender.com/simplehost</b>
<br><br>
<form method="POST" enctype="multipart/form-data">
    <input type="file" name="file" required><br>
    <button>Upload HTML</button>
</form>
<p style="color:red;">{{ message }}</p>
</div>
</body>
</html>
""", message=message)

@app.route("/uploaded/<page_name>")
def uploaded(page_name):
    return f"""
    <h1>Upload successful!</h1>
    <p>Your site is live at:</p>
    <a href="/{page_name}">https://simplehost.onrender.com/{page_name}</a>
    """

@app.route("/<page>")
def serve_page(page):
    filename = f"{page}.html"
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if os.path.exists(path):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    abort(404)

# -------------------------
# Run (Render-safe)
# -------------------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
