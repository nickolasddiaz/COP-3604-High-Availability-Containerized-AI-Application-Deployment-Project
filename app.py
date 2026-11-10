import os
from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)


@app.route('/')
def welcome():    
    return render_template("index.html", test=67)

@app.errorhandler(404)
def page_not_found(_error):
    return render_template('404.html'), 404

@app.route("/post/<int:post_id>", methods=['POST'])
def post(post_id):
    return f"Post ID: {post_id}"

@app.route("/query_example")
def query_example():

    language = request.args.get("language")
    framework = request.args.get("framework")
    website = request.args.get("website")

    return f"""
    <h1>Language: {language}</h1>
    <h1>Framework: {framework}</h1>
    <h1>Website: {website}</h1>
    """

@app.route('/file_upload', methods=['POST'])
def file_upload():
    file = request.files.get('file')

    if file is None or not file.filename:
        return "No file selected", 400

    filename = secure_filename(file.filename)
    file.save(filename)
    return "File uploaded successfully", 200


@app.route('/favicon.png')
# https://emojipedia.org/emoji-mashup/twitter/twemoji-14.0?a=%F0%9F%98%87&b=%F0%9F%A4%96
# combination of 😇 🤖
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.png', 
        mimetype='image/png'
    )

if __name__ == '__main__':
    app.run(debug=True, port=8001, host='127.0.0.1')
