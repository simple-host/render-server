from flask import Flask, request, redirect, url_for, render_template_string, abort
import os
import zipfile
import io
import random
import string
import mysql.connector
import mimetypes

app = Flask(__name__)

# -------------------------
# MySQL connection
# -------------------------
db = mysql.connector.connect(
    host=os.environ["MYSQL_HOST"],
    user=os.environ["MYSQL_USER"],
    password=os.environ["MYSQL_PASSWORD"],
    database=os.environ["MYSQL_DB"],
)
cursor = db.cursor(dictionary=True)

# -------------------------
# Helpers
# -------------------------
def random_suffix():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=4))

def site_exists(name):
    cursor.execute("SELECT id FROM sites WHERE name=%s", (name,))
    return cursor.fetchone()

def create_site():
    base = "simplehost"
    site = site_exists(base)
    name = base if not site else f"{base}-{random_suffix()}"

    cursor.execute("INSERT INTO sites (name) VALUES (%s)", (name,))
    db.commit()
    return cursor.lastrowid, name

# -------------------------
# Routes
# -------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    message = ""

    if request.method == "POST":
        zip_file = request.files.get("file")

        if not zip_file or not zip_file.filename.endswith(".zip"):
            message = "Please upload a ZIP file."
        else:
            site_id, site_name = create_site()

            z = zipfile.ZipFile(io.BytesIO(zip_file.read()))
            if "index.html" not in z.namelist():
                return "ZIP must contain index.html", 400

            for filename in z.namelist():
                if filename.endswith("/"):
                    continue

                content = z.read(filename)
                mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"

                cursor.execute("""
                    INSERT INTO files (site_id, filename, content, mimetype)
                    VALUES (%s, %s, %s, %s)
                """, (site_id, filename, content, mimetype))

            db.commit()
            return redirect(url_for("uploaded", page_name=site_name))

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
<p>Upload a ZIP file containing your site</p>
<form method="POST" enctype="multipart/form-data">
    <input type="file" name="file" accept=".zip" required><br>
    <button>Upload ZIP</button>
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
    <p>Your site:</p>
    <a href="/{page_name}/">https://simplehost.onrender.com/{page_name}/</a>
    """

@app.route("/<site>/")
@app.route("/<site>/<path:filename>")
def serve_site(site, filename="index.html"):
    cursor.execute("SELECT id FROM sites WHERE name=%s", (site,))
    site_row = cursor.fetchone()
    if not site_row:
        abort(404)

    cursor.execute("""
        SELECT content, mimetype
        FROM files
        WHERE site_id=%s AND filename=%s
    """, (site_row["id"], filename))
    file = cursor.fetchone()

    if not file:
        abort(404)

    return file["content"], 200, {"Content-Type": file["mimetype"]}

# -------------------------
# Run (Render-safe)
# -------------------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
