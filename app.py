import os
import random
from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Flask Tutorial: https://www.geeksforgeeks.org/python/flask-tutorial/

@app.route('/')
def welcome():
    chat_history = {
        "0110":"Testing",
        "0111":"Testing 22222222222222222222222222222222222222222",        
                }
    return render_template("index.html", chat_history=chat_history, chat_id="new", current_chat={})

@app.errorhandler(404)
def page_not_found(_error):
    return render_template('404.html', chat_history={}), 404


@app.route("/send/new", methods=['POST'])
def new_new_chat():
    message = request.form.get("message")
    return {"chat_id": random.randint(1, 0xFFFFFFFF),
            "message": f"Ai generated reponse: {message}"
            }

@app.route("/send/<int:chat_id>", methods=['POST'])
def send_chat(chat_id):
    message = request.form.get("message")
    return {"message": f"Ai generated reponse: {message}"}

@app.route("/chat/<int:chat_id>", methods=['GET','POST'])
def chat(chat_id):
    current_chat = [
        ("user", "Hello how are you."),
        ("system", "I am doing great, do you have any questions."),
        ("user", "pls let me pass on god."),
        ("system", "you are beyond help."),
    ]

    # Get return the rendered_template
    if request.method == 'POST':
        return current_chat

    chat_history = {
            "0110":"Testing",
            "0111":"Testing 22222222222222222222222222222222222222222",        
                    }
    
    return render_template("index.html", chat_history=chat_history, chat_id=chat_id, current_chat=current_chat)

@app.route('/file_upload', methods=['POST'])
def file_upload():
    file = request.files.get('file')

    if file is None or not file.filename:
        return "No file selected", 400

    filename = secure_filename(file.filename)
    file.save(filename)
    return "File uploaded successfully", 200

@app.route('/favicon.svg')
# https://emojipedia.org/emoji-mashup/twitter/twemoji-14.0?a=%F0%9F%98%87&b=%F0%9F%A4%96
# combination of 😇 🤖
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'assets'),
        'favicon.svg',
        mimetype='image/svg+xml'
    )
if __name__ == '__main__':
    app.run(debug=True, port=8001, host='127.0.0.1')
