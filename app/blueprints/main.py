import os
import random
from flask import Blueprint, render_template, request, send_from_directory
from werkzeug.utils import secure_filename


main_bp = Blueprint('main', __name__)

# Flask Tutorial: https://www.geeksforgeeks.org/python/flask-tutorial/

@main_bp.route('/')
def welcome():
    """Render the landing page.

    Returns:
        The rendered "index.html" template
        the chat history: dict[(chat_id) int, (chat_name) str]

    """
    chat_history: dict[int, str] = {
        110:"Testing",
        111:"Testing 22222222222222222222222222222222222222222",        
                }
    return render_template("index.html", chat_history=chat_history, chat_id="new", current_chat={})

@main_bp.errorhandler(404)
def page_not_found(_error):
    """Render the custom 404 page when a route is not found.
    """
    return render_template('404.html', chat_history={}), 404


@main_bp.route("/send/new", methods=['POST'])
def new_new_chat():
    """Create a new chat session and return an AI generated response.

    The request body must contain a form field named message (string).

    Args:
        request.form["message"] str: The user's message to be sent to
            the AI model.

    Returns:
        dict[(chat_id) int, (chat_name) str]: A JSON payload containing:
            - chat_id (int): A random identifier for the newly created chat.
            - message (str): AI generated response string".
    """
    message = request.form.get("message")
    return {"chat_id": random.randint(1, 0xFFFFFFFF),
            "message": f"Ai generated reponse: {message}"
            }

@main_bp.route("/send/<int:chat_id>", methods=['POST'])
def send_chat(chat_id):
    """Send a message for an existing chat and return the generated response.

    Args:
        chat_id (int): The identifier for the existing chat thread.
        request.form["message"] str: The user's message to be sent.

    Returns:
        dict[str, str]: A JSON object with the generated AI response stored in
        the message key.
    """
    message = request.form.get("message")
    return {"message": f"Ai generated reponse: {message}"}

@main_bp.route("/chat/<int:chat_id>", methods=['GET','POST'])
def chat(chat_id):
    """Display a chat thread or return the current transcript for a given chat.

    For GET requests, this renders the chat page. For POST requests, it returns
    the in-memory chat transcript for the requested conversation.

    Args:
        chat_id (int): The numeric identifier of the chat conversation to load.

    Returns:
        list[tuple[str, str]]: On GET, the rendered "index.html"
        template with the chat history and current chat transcript. 
        On POST, the current conversation transcript as a list of (role, message) tuples.
    """
    current_chat = [
        ("user", "Hello how are you."),
        ("system", "I am doing great, do you have any questions."),
        ("user", "pls let me pass on god."),
        ("system", "you are beyond help."),
    ]

    # Get return the rendered_template
    if request.method == 'POST':
        return current_chat

    chat_history: dict[int, str] = {
            110:"Testing",
            111:"Testing 22222222222222222222222222222222222222222",        
                    }
    
    return render_template("index.html", chat_history=chat_history, chat_id=chat_id, current_chat=current_chat)


@main_bp.route('/favicon.svg')
# https://emojipedia.org/emoji-mashup/twitter/twemoji-14.0?a=%F0%9F%98%87&b=%F0%9F%A4%96
# combination of 😇 🤖
def favicon():
    return send_from_directory(
        os.path.join(main_bp.root_path, 'static', 'assets'),
        'favicon.svg',
        mimetype='image/svg+xml'
    )
