import sys
from flask import Flask
from flasgger import Swagger
from config import DevelopmentConfig
import logging


# Configure root logger to output to stdout/stderr
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
    stream=sys.stdout
)

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

    return app