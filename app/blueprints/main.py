import os
from flask import Blueprint, current_app, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from app.ai_provider import AIProvider, get_ai_provider
from app.types import history, chats
from app.database import Database



main_bp = Blueprint('main', __name__)

DEFAULT_RAG_TOP_K = 4  # number of chunks placed in the prompt; override with RAG_TOP_K in the app config

ai_interface: AIProvider
db_interface: Database

@main_bp.record_once
def on_load(state):
    global ai_interface, db_interface
    ai_interface = get_ai_provider(state.app.config)
    db_interface = Database(state.app.config["CONNECTIONSTRING"])

def answer_with_rag(chat_id: int, user_message: str, chat_history: list[chats]) -> str:
    """Similarity search over this chat's stored chunks, then ask the model with only the relevant ones."""
    retrieved = []
    if db_interface.chat_has_chunks(chat_id):
        query_embedding = ai_interface.embed_query(user_message)
        top_k = current_app.config.get("RAG_TOP_K", DEFAULT_RAG_TOP_K)
        retrieved = db_interface.search_chunks(chat_id, query_embedding, top_k)

    return ai_interface.askQuestion(user_message, retrieved, chat_history)


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
    chat_history: history = db_interface.get_chat_history()
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
    chat_history = db_interface.get_chat_history()
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
    user_message = request.form.get("message")
    if not user_message:
        return "message form is needed", 422

    uploaded_files: list[FileStorage] = [f for f in request.files.getlist("uploaded_files") if f and f.filename]
    file_names = [secure_filename(f.filename) for f in uploaded_files if f.filename]

    # Chunk + embed the uploads first so an unsupported file fails before anything is saved
    try:
        chunks = ai_interface.chunk_and_embed(uploaded_files)
    except ValueError as e:
        return str(e), 400

    chat_name: str = ai_interface.generateNameofChat(user_message)
    chat_id = db_interface.create_chat(chat_name)

    try:
        # Chunks must be in the database before we can search them
        db_interface.add_user_message(chat_id, user_message, file_names, chunks)
        system_message = answer_with_rag(chat_id, user_message, [])
        db_interface.add_system_message(chat_id, system_message)
    except Exception:
        db_interface.delete_chat(chat_id)
        raise

    return {"chat_id": chat_id,
            "chat_name": chat_name,
            "message": system_message
            }

@main_bp.route("/send/<int:chat_id>", methods=['POST'])
def send_chat(chat_id: int):
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
    user_message = request.form.get("message")
    if not user_message:
         return "message form is needed", 422

    uploaded_files: list[FileStorage] = [f for f in request.files.getlist("uploaded_files") if f and f.filename]
    file_names: list[str] = [secure_filename(f.filename) for f in uploaded_files if f.filename]

    # Must be read BEFORE saving the new message, otherwise it would appear twice in the prompt
    current_chat: list[chats] = db_interface.get_chat(chat_id)
    if not current_chat:
        return "chat not found", 404

    try:
        chunks = ai_interface.chunk_and_embed(uploaded_files)
    except ValueError as e:
        return str(e), 400

    chat_dialog_id = db_interface.add_user_message(chat_id, user_message, file_names, chunks)
    try:
        system_message = answer_with_rag(chat_id, user_message, current_chat)
        db_interface.add_system_message(chat_id, system_message)
    except Exception:
        db_interface.delete_dialog_message(chat_dialog_id)  # cascades to this message's chunks
        raise

    return {"message": system_message}

@main_bp.route("/chat/<int:chat_id>", methods=['GET','POST'])
def chat(chat_id: int):
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

    current_chat: list[chats] = db_interface.get_chat(chat_id)

    # Get return the rendered_template
    if request.method == 'POST':
        return current_chat

    chat_history: history = db_interface.get_chat_history()

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

@main_bp.route('/flask-health-check')
def flask_health_check():
	return "success"

@main_bp.route('/health')
def healthk():
	return "success"

@main_bp.route('/info')
def info():

	resp = {
		'connecting_ip': request.headers['X-Real-IP'],
		'proxy_ip': request.headers['X-Forwarded-For'],
		'host': request.headers['Host'],
		'user-agent': request.headers['User-Agent']
	}

	return jsonify(resp)