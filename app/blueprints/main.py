import os
import random
from flask import Blueprint, current_app, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
from app.ai_provider import AIProvider, get_ai_provider
from app.types import history, chats


main_bp = Blueprint('main', __name__)

ai_provider: AIProvider

@main_bp.record_once
def on_load(state):
    global ai_provider
    ai_provider = get_ai_provider(state.app.config)

# Flask Tutorial: https://www.geeksforgeeks.org/python/flask-tutorial/

chat_history: history = {
    110:"Testing",
    111:"Testing 22222222222222222222222222222222222222222",
        }

@main_bp.route('/')
def welcome():
    """Render the landing page.
        ---
        responses:
            200:
                description: Landing page with the empty new chat.
                examples:
                    text/html: '<html>Rendered index.html</html>'
    """
    # chat_history = get_chathistory(chat_id)
    return render_template("index.html", chat_history=chat_history, chat_id="new", current_chat={})

@main_bp.errorhandler(404)
def page_not_found(_error):
    """Render the custom 404 page when a route is not found.
        ---
        responses:
            404:
                description: The requested page was not found.
                examples:
                    text/html: '<html>Rendered 404.html</html>'
    """
    # chat_history = get_chathistory(chat_id)
    return render_template('404.html', chat_history=chat_history), 404

@main_bp.route("/send/new", methods=['POST'])
def new_new_chat():
    """Create a new chat and return a placeholder response.
        ---
        consumes:
            - multipart/form-data
        parameters:
            - in: formData
              name: message
              type: string
              required: true
              description: Message to send.
            - in: formData
              name: uploaded_files
              type: file
              required: false
              description: Optional file for context; repeat this field to upload multiple files.
        responses:
            200:
                description: Placeholder response for a newly created chat.
                schema:
                    type: object
                    properties:
                        chat_id:
                            type: integer
                            example: 12345
                        chat_name:
                            type: string
                            example: new chat name
                        message:
                            type: string
                            example: Ai generated reponse Hello
    """
    message = request.form.get("message")
    if not message:
        return "message form is needed", 422
    
    chat_name: str = ai_provider.generateNameofChat(message)

    response: str = ai_provider.askQuestion(message)

    return {"chat_id": random.randint(1, 0xFFFFFFFF),
            "chat_name": chat_name,
            "message": response
            }

@main_bp.route("/send/<int:chat_id>", methods=['POST'])
def send_chat(chat_id):
    """Send a message to an existing chat and return a placeholder response.
        ---
        consumes:
            - multipart/form-data
        parameters:
            - in: path
              name: chat_id
              type: integer
              required: true
              description: Chat identifier.
            - in: formData
              name: message
              type: string
              required: true
              description: Message to send.
            - in: formData
              name: uploaded_files
              type: file
              required: false
              description: Optional file for context; repeat this field to upload multiple files.
        responses:
            200:
                description: Placeholder response for the chat.
                schema:
                    type: object
                    properties:
                        message:
                            type: string
                            example: Ai generated reponse Hello
    """
    message = request.form.get("message")
    return {"message": f"Ai generated reponse: {message}"}

@main_bp.route("/chat/<int:chat_id>", methods=['GET','POST'])
def chat(chat_id):
    """Display a chat page or return its placeholder transcript.
        ---
        parameters:
            - in: path
              name: chat_id
              type: integer
              required: true
              description: Chat identifier.
        responses:
            200:
                description: For GET, the rendered chat page; for POST, the current placeholder transcript.
                schema:
                    type: array
                    items:
                        type: object
                        properties:
                            role:
                                type: string
                                enum: [user, system]
                            content:
                                type: string
                            files:
                                type: array
                                items:
                                    type: string
                examples:
                    application/json:
                        - role: user
                            content Hello how are you.
                            files [test1.txt, test2.txt]
            405:
                description: Method not allowed.
    """

    # example
    current_chat: list[chats] = [
        {'role': 'user', 'content': 'Hello how are you.', 'files': ["test1.txt", "test2.txt", "test3.txt"]},
        {'role': 'system', 'content': 'I am doing great, do you have any questions.', 'files': []},
        {'role': 'user', 'content': 'pls let me pass on god.', 'files': ["plshelp.pdf"]},
        {'role': 'system', 'content': 'you are beyond help.', 'files': []},
    ]

    # Get return the rendered_template
    if request.method == 'POST':
        return current_chat

    # chat_history = get_chathistory(chat_id)

    return render_template("index.html", chat_history=chat_history, chat_id=chat_id, current_chat=current_chat)

@main_bp.route('/favicon.svg')
# https://emojipedia.org/emoji-mashup/twitter/twemoji-14.0?a=%F0%9F%98%87&b=%F0%9F%A4%96
# combination of 😇 🤖
def favicon():
    """Return the site's SVG favicon.
        ---
        produces:
            - image/svg+xml
        responses:
            200:
                description: SVG favicon.
    """
    return send_from_directory(
        os.path.join(current_app.static_folder, 'assets'), # type: ignore
        'favicon.svg',
        mimetype='image/svg+xml'
    )

@main_bp.route('/file.svg')
# https://flowbite.com/icons/
# file-copy
def filesvg():
    """Return the file icon SVG.
        ---
        produces:
            - image/svg+xml
        responses:
            200:
                description: File icon SVG.
    """
    return send_from_directory(
        os.path.join(current_app.static_folder, 'assets'), # type: ignore
        'file.svg',
        mimetype='image/svg+xml'
    )