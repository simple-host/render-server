from flask import Flask, request, send_from_directory, redirect, url_for, render_template_string
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'html'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ""
    if request.method == 'POST':
        if 'file' not in request.files:
            message = "No file selected."
        else:
            file = request.files['file']
            if file.filename == '':
                message = "No file selected."
            elif not allowed_file(file.filename):
                message = "Only HTML files are allowed."
            else:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(filepath):
                    message = f"{filename} already exists. Please choose a different name."
                else:
                    file.save(filepath)
                    page_name = filename.rsplit('.',1)[0]
                    return redirect(url_for('uploaded', page_name=page_name))

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SimpleHost</title>
        <link rel="icon" type="image/png" href="{{ url_for('favicon') }}">
        <style>
            body {
                background-color: #1c1c1c;
                color: #e0e0e0;
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                flex-direction: column;
                text-align: center;
            }
            h1 { font-size: 3em; margin-bottom: 30px; color:#b0b0b0; }
            input[type=file], input[type=submit] {
                padding: 15px 20px;
                margin: 15px 0;
                border-radius: 6px;
                border: none;
                font-size: 1.2em;
            }
            input[type=submit] {
                background-color: #333;
                color: #e0e0e0;
                font-weight: bold;
                cursor: pointer;
                transition: 0.3s;
            }
            input[type=submit]:hover {
                background-color: #555;
            }
            .message { margin-top: 20px; color: #ff5555; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>SimpleHost</h1>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" required><br>
            <input type="submit" value="Upload HTML">
        </form>
        {% if message %}
            <div class="message">{{ message }}</div>
        {% endif %}
    </body>
    </html>
    ''', message=message)

# Favicon route
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.png', mimetype='image/png')

# Success page after upload showing entire site HTML
@app.route('/uploaded/<page_name>')
def uploaded(page_name):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{page_name}.html")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            html_content = f.read()
    else:
        return "<h1>Error: file not found</h1>"

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Upload Successful - SimpleHost</title>
        <link rel="icon" type="image/png" href="{{ url_for('favicon') }}">
        <style>
            body {
                background-color: #1c1c1c;
                color: #e0e0e0;
                font-family: Arial, sans-serif;
                padding: 40px;
                line-height: 1.6;
            }
            h1 { color: #b0b0b0; }
            a { color: #ff6f61; text-decoration:none; }
            a:hover { text-decoration: underline; }
            pre {
                background-color: #111;
                color: #e0e0e0;
                padding: 20px;
                border-radius: 6px;
                overflow-x: auto;
            }
        </style>
    </head>
    <body>
        <h1>Upload Successful!</h1>
        <p>Your site is available at: <a href="/{{ page_name }}">/{{ page_name }}</a></p>
        <h2>Full HTML code of your uploaded site:</h2>
        <pre>{{ html_content | e }}</pre>
    </body>
    </html>
    ''', page_name=page_name, html_content=html_content)

# Serve uploaded pages
@app.route('/<page>')
def serve_page(page):
    filename = f"{page}.html"
    if filename in os.listdir(app.config['UPLOAD_FOLDER']):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    else:
        return "<h1>404 - Page Not Found</h1>", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
