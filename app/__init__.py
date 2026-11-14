from flask import Flask, render_template
from config import DevelopmentConfig

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register Blueprints
    from app.blueprints.main import main_bp
    app.register_blueprint(main_bp)

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(_error):
        return render_template('404.html', chat_history={}), 404

    return app