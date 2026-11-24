from flask import Flask, jsonify, render_template
from flasgger import Swagger
from config import DevelopmentConfig

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.config['SWAGGER'] = {
        'title': 'Tutor Chatbot',
        'versino': '1.0.0',
        'openapi': '3.0.3'
    }

    swagger = Swagger(app)

    # Register Blueprints
    from app.blueprints.main import main_bp
    app.register_blueprint(main_bp)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception("Unhandled Exception occurred:")
        return jsonify({"error": "Internal Server Error"}), 500

    return app